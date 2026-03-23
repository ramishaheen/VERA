"""
Data models for VERA system.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import json


class TaskType(Enum):
    """Enumeration of task types that VERA can handle."""
    MATH = "math"
    LOGIC = "logic"
    FACT = "fact"
    SEMANTIC = "semantic"
    UNKNOWN = "unknown"


class EngineType(Enum):
    """Enumeration of execution engines."""
    DETERMINISTIC_SANDBOX = "deterministic_sandbox"
    RAG_ENGINE = "rag_engine"
    SEMANTIC_ENGINE = "semantic_engine"
    ARBITRATOR = "arbitrator"


@dataclass
class Task:
    """Represents a single atomic task in the DAG."""
    id: str
    type: TaskType
    content: str
    dependencies: List[str]
    engine: Optional[EngineType] = None
    result: Optional[str] = None
    error: Optional[str] = None
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "dependencies": self.dependencies,
            "engine": self.engine.value if self.engine else None,
            "result": self.result,
            "error": self.error,
            "verified": self.verified,
        }


@dataclass
class ExecutionGraph:
    """Represents the DAG of tasks to be executed."""
    tasks: Dict[str, Task]
    execution_order: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "execution_order": self.execution_order,
            "metadata": self.metadata,
        }


@dataclass
class VerificationResult:
    """Result of verification for a task output."""
    task_id: str
    verified: bool
    confidence: float
    details: str
    corrected_output: Optional[str] = None


@dataclass
class VERAResponse:
    """Final response from VERA system."""
    response: str
    verified: bool
    confidence: float
    execution_graph: ExecutionGraph
    verification_results: List[VerificationResult]
    latency_ms: float
    model_used: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "response": self.response,
            "verified": self.verified,
            "confidence": self.confidence,
            "execution_graph": self.execution_graph.to_dict(),
            "verification_results": [
                {
                    "task_id": vr.task_id,
                    "verified": vr.verified,
                    "confidence": vr.confidence,
                    "details": vr.details,
                    "corrected_output": vr.corrected_output,
                }
                for vr in self.verification_results
            ],
            "latency_ms": self.latency_ms,
            "model_used": self.model_used,
        }

    def to_json(self) -> str:
        """Convert response to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class ChatMessage:
    """Represents a chat message in the conversation."""
    def __init__(self, role: str, content: str):
        self.role = role  # "user", "assistant", "system"
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}
