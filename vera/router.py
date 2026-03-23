"""
Router module: Routes tasks to appropriate execution engines.
"""

from .models import Task, TaskType, EngineType, ExecutionGraph


class Router:
    """Routes tasks to the appropriate execution engine based on task type."""

    def __init__(self):
        self.routing_rules = {
            TaskType.MATH: EngineType.DETERMINISTIC_SANDBOX,
            TaskType.LOGIC: EngineType.DETERMINISTIC_SANDBOX,
            TaskType.FACT: EngineType.RAG_ENGINE,
            TaskType.SEMANTIC: EngineType.SEMANTIC_ENGINE,
            TaskType.UNKNOWN: EngineType.SEMANTIC_ENGINE,
        }

    def route(self, execution_graph: ExecutionGraph) -> ExecutionGraph:
        """Route all tasks in the execution graph to appropriate engines."""
        for task in execution_graph.tasks.values():
            engine = self.routing_rules.get(task.type, EngineType.SEMANTIC_ENGINE)
            task.engine = engine
        return execution_graph

    def get_routing_confidence(self, task: Task) -> float:
        """Get confidence score for the routing decision."""
        if task.type in [TaskType.MATH, TaskType.LOGIC]:
            return 0.95
        elif task.type == TaskType.FACT:
            return 0.85
        elif task.type == TaskType.SEMANTIC:
            return 0.70
        else:
            return 0.50
