"""
VERA Test Suite.

Tests are split into:
  - Unit tests (no API key required): segmenter, router, deterministic sandbox
  - Integration tests (API key required): RAG engine, full VERA core
  - Network tests (requires internet): Wikipedia RAG

Run unit tests only (no key needed):
    pytest tests/test_vera.py -v -m "not integration and not network"

Run all tests (requires OPENAI_API_KEY):
    pytest tests/test_vera.py -v
"""

import os
import sys
import pytest

# Make sure we can import from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vera.segmenter import Segmenter
from vera.router import Router
from vera.engines import DeterministicSandbox, RAGEngine, SemanticEngine
from vera.arbitrator import Arbitrator
from vera.models import TaskType, EngineType, Task, ExecutionGraph


# ── Segmenter ─────────────────────────────────────────────────────────────
class TestSegmenter:
    def setup_method(self):
        self.seg = Segmenter()

    def test_math_classification(self):
        graph = self.seg.segment("Calculate 5 + 3")
        tasks = list(graph.tasks.values())
        assert any(t.type == TaskType.MATH for t in tasks)

    def test_fact_classification(self):
        graph = self.seg.segment("Who is Jane Austen?")
        tasks = list(graph.tasks.values())
        assert any(t.type == TaskType.FACT for t in tasks)

    def test_semantic_fallback(self):
        graph = self.seg.segment("Write me a poem about the moon")
        tasks = list(graph.tasks.values())
        assert any(t.type == TaskType.SEMANTIC for t in tasks)

    def test_execution_order_set(self):
        graph = self.seg.segment("Calculate 10% of 500 and then explain what that means")
        assert len(graph.execution_order) > 0
        assert set(graph.execution_order) == set(graph.tasks.keys())

    def test_empty_prompt_yields_semantic_task(self):
        # Very short text → falls through to semantic fallback
        graph = self.seg.segment("hello world this is a sentence")
        assert len(graph.tasks) >= 1

    def test_metadata_populated(self):
        graph = self.seg.segment("Calculate 5 + 3")
        assert "original_prompt" in graph.metadata
        assert graph.metadata["num_tasks"] == len(graph.tasks)


# ── Router ────────────────────────────────────────────────────────────────
class TestRouter:
    def setup_method(self):
        self.seg = Segmenter()
        self.router = Router()

    def test_math_routes_to_sandbox(self):
        graph = self.seg.segment("Calculate 5 + 3")
        graph = self.router.route(graph)
        math_tasks = [t for t in graph.tasks.values() if t.type == TaskType.MATH]
        assert all(t.engine == EngineType.DETERMINISTIC_SANDBOX for t in math_tasks)

    def test_fact_routes_to_rag(self):
        graph = self.seg.segment("Who is Marie Curie?")
        graph = self.router.route(graph)
        fact_tasks = [t for t in graph.tasks.values() if t.type == TaskType.FACT]
        assert all(t.engine == EngineType.RAG_ENGINE for t in fact_tasks)

    def test_semantic_routes_to_llm(self):
        graph = self.seg.segment("Write a formal email")
        graph = self.router.route(graph)
        sem_tasks = [t for t in graph.tasks.values() if t.type == TaskType.SEMANTIC]
        assert all(t.engine == EngineType.SEMANTIC_ENGINE for t in sem_tasks)

    def test_all_tasks_get_engines(self):
        graph = self.seg.segment("Calculate 10 + 5 and tell me about Einstein")
        graph = self.router.route(graph)
        assert all(t.engine is not None for t in graph.tasks.values())


# ── DeterministicSandbox ──────────────────────────────────────────────────
class TestDeterministicSandbox:
    """No API key required."""

    def setup_method(self):
        self.sandbox = DeterministicSandbox()

    def test_simple_addition(self):
        result, success = self.sandbox.execute("Calculate 5 + 3")
        assert success
        assert result == "8"

    def test_multiplication(self):
        result, success = self.sandbox.execute("Calculate 10 * 5")
        assert success
        assert result == "50"

    def test_percentage(self):
        result, success = self.sandbox.execute("Calculate 5% of 1000")
        assert success
        assert result == "50"

    def test_percentage_decimal(self):
        result, success = self.sandbox.execute("Calculate 15% of 2000")
        assert success
        assert result == "300"

    def test_compound_interest(self):
        result, success = self.sandbox.execute(
            "Calculate compound interest on 10000 at 5% for 2 years"
        )
        assert success
        # A=10000*(1+0.05)^2 = 11025
        assert "11025" in result

    def test_no_expression_returns_false(self):
        result, success = self.sandbox.execute("Tell me about history")
        assert not success

    def test_does_not_require_api_key(self):
        """DeterministicSandbox must work without any environment variables."""
        import os
        original = os.environ.pop("OPENAI_API_KEY", None)
        try:
            sb = DeterministicSandbox()
            result, success = sb.execute("Calculate 7 + 7")
            assert success
            assert result == "14"
        finally:
            if original:
                os.environ["OPENAI_API_KEY"] = original


# ── Arbitrator ────────────────────────────────────────────────────────────
class TestArbitrator:
    def setup_method(self):
        self.arb = Arbitrator()

    def _make_graph(self, engine: EngineType, result: str) -> ExecutionGraph:
        task = Task(
            id="task_0",
            type=TaskType.MATH if engine == EngineType.DETERMINISTIC_SANDBOX else TaskType.SEMANTIC,
            content="test task",
            dependencies=[],
            engine=engine,
            result=result,
            verified=True,
        )
        return ExecutionGraph(
            tasks={"task_0": task},
            execution_order=["task_0"],
            metadata={},
        )

    def test_math_result_high_confidence(self):
        graph = self._make_graph(EngineType.DETERMINISTIC_SANDBOX, "42")
        _, vrs, conf = self.arb.verify_and_synthesize(graph)
        assert vrs[0].confidence == 0.99
        assert vrs[0].verified

    def test_fact_result_confidence(self):
        graph = self._make_graph(EngineType.RAG_ENGINE, "A " * 20)
        _, vrs, conf = self.arb.verify_and_synthesize(graph)
        assert vrs[0].confidence == 0.90

    def test_none_result_unverified(self):
        task = Task("task_0", TaskType.MATH, "x", [], EngineType.DETERMINISTIC_SANDBOX, None)
        graph = ExecutionGraph({"task_0": task}, ["task_0"], {})
        _, vrs, conf = self.arb.verify_and_synthesize(graph)
        assert not vrs[0].verified
        assert conf < 1.0

    def test_synthesis_joins_results(self):
        task1 = Task("task_0", TaskType.MATH, "5+3", [], EngineType.DETERMINISTIC_SANDBOX, "8")
        task2 = Task("task_1", TaskType.SEMANTIC, "explain", ["task_0"], EngineType.SEMANTIC_ENGINE, "Eight is the answer.")
        graph = ExecutionGraph({"task_0": task1, "task_1": task2}, ["task_0", "task_1"], {})
        response, _, _ = self.arb.verify_and_synthesize(graph)
        assert "Eight" in response or "8" in response


# ── Network / Integration ─────────────────────────────────────────────────
@pytest.mark.network
class TestRAGEngine:
    """Requires internet access."""

    def setup_method(self):
        self.rag = RAGEngine()

    def test_known_person(self):
        result, success = self.rag.execute("Who is Marie Curie?")
        assert success
        assert len(result) > 20

    def test_unknown_entity_graceful(self):
        result, success = self.rag.execute("Who is xyzabcnonexistent12345?")
        # Should fail gracefully, not crash
        assert isinstance(result, str)


@pytest.mark.integration
class TestVERACore:
    """Requires OPENAI_API_KEY in environment."""

    def setup_method(self):
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        from vera.core import VERACore
        self.vera = VERACore()

    def test_math_end_to_end(self):
        response = self.vera.process("Calculate 5 + 3")
        assert response.verified
        assert "8" in response.response
        assert response.confidence > 0.6
        assert response.latency_ms > 0

    def test_empty_prompt_raises(self):
        with pytest.raises(ValueError):
            self.vera.process("")

    def test_response_has_all_fields(self):
        response = self.vera.process("Calculate 10 * 5")
        assert response.response
        assert response.execution_graph
        assert len(response.verification_results) > 0
        assert response.model_used


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration and not network"])
