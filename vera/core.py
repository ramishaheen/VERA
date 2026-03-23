"""
Core VERA orchestrator: Ties all components together.
"""

import os
import time
import logging
from typing import Dict, Optional

from dotenv import load_dotenv

from .models import VERAResponse, ExecutionGraph, EngineType
from .segmenter import Segmenter
from .router import Router
from .engines import DeterministicSandbox, RAGEngine, SemanticEngine
from .arbitrator import Arbitrator

load_dotenv()

logger = logging.getLogger(__name__)


class VERACore:
    """
    Main VERA orchestrator.

    Supports OpenAI, LM Studio (local), and any OpenAI-compatible endpoint.

    Args:
        model:    LLM model name (e.g. "gpt-4o-mini", "llama-3.2" for LM Studio).
        api_key:  API key. Falls back to OPENAI_API_KEY env var.
        base_url: Custom API base URL. Use "http://localhost:1234/v1" for LM Studio.
                  Falls back to VERA_BASE_URL env var, then OpenAI default.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model or os.getenv("VERA_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("VERA_BASE_URL")

        self.segmenter = Segmenter()
        self.router = Router()
        self.deterministic_sandbox = DeterministicSandbox()
        self.rag_engine = RAGEngine()
        self.semantic_engine = SemanticEngine(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
        )
        self.arbitrator = Arbitrator()

        logger.info(
            "VERACore initialised: model=%s, base_url=%s",
            self.model,
            self.base_url or "OpenAI default",
        )

    def reconfigure(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        """Update LLM configuration at runtime (used by the settings endpoint)."""
        if model:
            self.model = model
        if api_key is not None:
            self.api_key = api_key
        if base_url is not None:
            self.base_url = base_url or None  # empty string → None
        self.semantic_engine.reconfigure(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
        )
        logger.info(
            "VERACore reconfigured: model=%s, base_url=%s",
            self.model,
            self.base_url or "OpenAI default",
        )

    def process(self, prompt: str) -> VERAResponse:
        """
        Process a prompt through the full VERA pipeline.

        Pipeline: Segment → Route → Execute → Verify & Synthesise
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        start_time = time.time()
        logger.info("Processing prompt: '%s'", prompt[:80])

        # Step 1: Segmentation
        execution_graph = self.segmenter.segment(prompt)
        logger.debug("Segmented into %d tasks", len(execution_graph.tasks))

        # Step 2: Routing
        execution_graph = self.router.route(execution_graph)

        # Step 3: Execution
        execution_graph = self._execute_graph(execution_graph)

        # Step 4: Verification and Arbitration
        final_response, verification_results, overall_confidence = (
            self.arbitrator.verify_and_synthesize(execution_graph)
        )

        latency_ms = (time.time() - start_time) * 1000

        vera_response = VERAResponse(
            response=final_response,
            verified=overall_confidence > 0.6,
            confidence=round(overall_confidence, 4),
            execution_graph=execution_graph,
            verification_results=verification_results,
            latency_ms=round(latency_ms, 2),
            model_used=self.model,
        )

        logger.info(
            "Done: verified=%s, confidence=%.2f, latency=%.0fms",
            vera_response.verified,
            vera_response.confidence,
            vera_response.latency_ms,
        )
        return vera_response

    def _execute_graph(self, execution_graph: ExecutionGraph) -> ExecutionGraph:
        """Execute all tasks in topological order."""
        task_results: Dict[str, str] = {}

        for task_id in execution_graph.execution_order:
            task = execution_graph.tasks[task_id]
            context = self._gather_context(task, task_results)

            if task.engine == EngineType.DETERMINISTIC_SANDBOX:
                result, success = self.deterministic_sandbox.execute(task.content)
                # Fallback: if sandbox couldn't extract a formula, let the LLM handle it
                if not success:
                    logger.debug("Sandbox failed for '%s', falling back to LLM", task.content)
                    result, success = self.semantic_engine.execute(task.content, context)
                    task.engine = EngineType.SEMANTIC_ENGINE
            elif task.engine == EngineType.RAG_ENGINE:
                result, success = self.rag_engine.execute(task.content)
                # Fallback: if Wikipedia found nothing, let the LLM answer from training data
                if not success:
                    logger.debug("RAG found nothing for '%s', falling back to LLM", task.content)
                    result, success = self.semantic_engine.execute(task.content, context)
                    task.engine = EngineType.SEMANTIC_ENGINE
            elif task.engine == EngineType.SEMANTIC_ENGINE:
                result, success = self.semantic_engine.execute(task.content, context)
            else:
                result, success = "Unknown engine type", False

            task.result = result
            task.verified = success
            task_results[task_id] = result

        return execution_graph

    def _gather_context(self, task, task_results: Dict[str, str]) -> Optional[str]:
        """Gather results from dependency tasks as context."""
        if not task.dependencies:
            return None
        parts = [task_results[dep] for dep in task.dependencies if dep in task_results]
        return "\n".join(parts) if parts else None
