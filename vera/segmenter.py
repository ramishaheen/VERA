"""
Segmenter module: Parses natural language prompts into atomic tasks.
"""

import re
from typing import List, Dict
from .models import Task, TaskType, ExecutionGraph


class Segmenter:
    """Parses prompts into a DAG of atomic tasks."""

    def __init__(self):
        """Initialize the Segmenter."""
        self.math_patterns = [
            r'\b(calculate|compute|solve|what is|find)\b.*?(\d+\s*[+\-*/]\s*\d+|\d+%\s*of\s*\d+)',
            r'\b(add|subtract|multiply|divide|percentage)\b',
            r'\b(sum|total|average|mean)\b',
        ]
        self.fact_patterns = [
            r'\b(who is|what is|when was|where is|how many)\b',
            r'\b(tell me about|explain|describe|information about)\b',
            r'\b(born|died|founded|located|population)\b',
        ]
        self.logic_patterns = [
            r'\b(if|then|and|or|because|therefore)\b',
            r'\b(prove|verify|check|validate)\b',
        ]

    def segment(self, prompt: str) -> ExecutionGraph:
        """
        Segment a prompt into atomic tasks and build a DAG.

        Args:
            prompt: The user's natural language prompt.

        Returns:
            An ExecutionGraph representing the segmented tasks.
        """
        sentences = self._split_sentences(prompt)

        tasks: Dict[str, Task] = {}
        task_counter = 0

        for sentence in sentences:
            task_type = self._classify_task(sentence)
            if task_type != TaskType.UNKNOWN:
                task_id = f"task_{task_counter}"
                task = Task(
                    id=task_id,
                    type=task_type,
                    content=sentence.strip(),
                    dependencies=[],
                )
                tasks[task_id] = task
                task_counter += 1

        # Fallback: treat entire prompt as semantic
        if not tasks:
            task_id = "task_0"
            task = Task(
                id=task_id,
                type=TaskType.SEMANTIC,
                content=prompt,
                dependencies=[],
            )
            tasks[task_id] = task

        # Build dependency graph (later tasks that reference earlier ones)
        task_list = list(tasks.values())
        for i in range(1, len(task_list)):
            current = task_list[i]
            for j in range(i):
                previous = task_list[j]
                if self._has_dependency(current.content, previous.content):
                    current.dependencies.append(previous.id)

        execution_order = self._topological_sort(tasks)

        metadata = {
            "original_prompt": prompt,
            "num_tasks": len(tasks),
            "task_types": [t.type.value for t in tasks.values()],
        }

        return ExecutionGraph(tasks=tasks, execution_order=execution_order, metadata=metadata)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r'[.!?;]', text)
        return [s.strip() for s in sentences if s.strip()]

    def _classify_task(self, sentence: str) -> TaskType:
        """Classify a sentence into a task type."""
        sentence_lower = sentence.lower()

        for pattern in self.math_patterns:
            if re.search(pattern, sentence_lower):
                return TaskType.MATH

        for pattern in self.logic_patterns:
            if re.search(pattern, sentence_lower):
                return TaskType.LOGIC

        for pattern in self.fact_patterns:
            if re.search(pattern, sentence_lower):
                return TaskType.FACT

        if len(sentence) > 10:
            return TaskType.SEMANTIC

        return TaskType.UNKNOWN

    def _has_dependency(self, current: str, previous: str) -> bool:
        """Check if current task depends on previous task."""
        current_lower = current.lower()
        previous_words = set(previous.lower().split())

        for word in previous_words:
            if len(word) > 3 and word in current_lower:
                return True

        if re.search(r'\b(it|this|that|then|so)\b', current_lower):
            return True

        return False

    def _topological_sort(self, tasks: Dict[str, Task]) -> List[str]:
        """Perform topological sort on the task DAG (Kahn's algorithm)."""
        in_degree = {task_id: len(task.dependencies) for task_id, task in tasks.items()}
        adjacency: Dict[str, List[str]] = {task_id: [] for task_id in tasks}

        for task_id, task in tasks.items():
            for dep in task.dependencies:
                if dep in adjacency:
                    adjacency[dep].append(task_id)

        queue = [task_id for task_id in tasks if in_degree[task_id] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Cycle fallback
        if len(result) != len(tasks):
            return list(tasks.keys())

        return result
