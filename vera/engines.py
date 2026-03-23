"""
Execution engines for VERA: Math, Fact, and Semantic.

Supports: OpenAI, LM Studio (local), and any OpenAI-compatible endpoint.
"""

import re
import logging
from typing import Optional, Tuple

from sympy import sympify, simplify, SympifyError
import requests
from openai import OpenAI

logger = logging.getLogger(__name__)


class DeterministicSandbox:
    """
    Executes mathematical expressions deterministically using SymPy.
    Requires NO API key — purely local computation.
    """

    def execute(self, task_content: str) -> Tuple[str, bool]:
        """Execute a mathematical or logical task."""
        try:
            expression = self._extract_expression(task_content)
            if expression:
                result = self._evaluate_expression(expression)
                logger.debug("DeterministicSandbox: '%s' → %s", expression, result)
                return result, True
            return "Could not extract mathematical expression", False
        except Exception as e:
            logger.warning("DeterministicSandbox error: %s", e)
            return f"Error: {str(e)}", False

    def _extract_expression(self, task_content: str) -> Optional[str]:
        """Extract a mathematical expression from natural language."""
        # Simple arithmetic: "5 + 3", "10 * 5"
        match = re.search(r'(\d+(?:\.\d+)?\s*[+\-*/]\s*\d+(?:\.\d+)?)', task_content)
        if match:
            return match.group(1)

        # Percentage: "5% of 1000"
        match = re.search(r'(\d+(?:\.\d+)?)%\s*of\s*(\d+(?:\.\d+)?)', task_content)
        if match:
            return f"{match.group(1)} / 100 * {match.group(2)}"

        # Compound interest: "10000 at 5% for 2 years"
        match = re.search(
            r'(\d+(?:\.\d+)?)\s*at\s*(\d+(?:\.\d+)?)%\s*for\s*(\d+(?:\.\d+)?)',
            task_content,
        )
        if match:
            principal, rate, years = match.group(1), match.group(2), match.group(3)
            return f"{principal} * (1 + {rate}/100) ** {years}"

        return None

    def _evaluate_expression(self, expression: str) -> str:
        """Evaluate a mathematical expression using SymPy."""
        try:
            result = sympify(expression)
            simplified = simplify(result)
            # Return integer if it's a whole number, otherwise float
            numeric = float(simplified)
            return str(int(numeric)) if numeric == int(numeric) else f"{numeric:.4f}".rstrip("0").rstrip(".")
        except (SympifyError, Exception) as e:
            raise ValueError(f"Failed to evaluate '{expression}': {e}")


class RAGEngine:
    """Retrieves and verifies facts from Wikipedia."""

    WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

    def execute(self, task_content: str) -> Tuple[str, bool]:
        """Execute a fact retrieval task."""
        try:
            query = self._extract_query(task_content)
            if query:
                result = self._retrieve_from_wikipedia(query)
                if result:
                    logger.debug("RAGEngine: retrieved fact for '%s'", query)
                    return result, True
                return f"No information found for '{query}'", False
            return "Could not extract query from task", False
        except Exception as e:
            logger.warning("RAGEngine error: %s", e)
            return f"Error: {str(e)}", False

    def _extract_query(self, task_content: str) -> Optional[str]:
        """Extract search query from task content."""
        for pattern in [
            r'who is\s+(.+?)(?:\?|$)',
            r'what is\s+(.+?)(?:\?|$)',
            r'tell me about\s+(.+?)(?:\?|$)',
            r'information about\s+(.+?)(?:\?|$)',
            r'explain\s+(.+?)(?:\?|$)',
            r'describe\s+(.+?)(?:\?|$)',
        ]:
            match = re.search(pattern, task_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return task_content.strip()

    def _retrieve_from_wikipedia(self, query: str) -> Optional[str]:
        """
        Retrieve a summary from Wikipedia.
        Step 1: search to find the correct article title (handles case, typos, short names).
        Step 2: fetch the intro extract for that title.
        """
        try:
            # Step 1 — search
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": 1,
            }
            # Wikipedia requires a descriptive User-Agent header
            headers = {"User-Agent": "VERA/1.0 (https://vera-ai.com; rami@vera-ai.com) python-requests"}
            sr = requests.get(self.WIKIPEDIA_API, params=search_params, headers=headers, timeout=8)
            sr.raise_for_status()
            results = sr.json().get("query", {}).get("search", [])
            if not results:
                logger.debug("Wikipedia: no search results for '%s'", query)
                return None

            title = results[0]["title"]
            logger.debug("Wikipedia: resolved '%s' → '%s'", query, title)

            # Step 2 — fetch extract
            extract_params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
            }
            er = requests.get(self.WIKIPEDIA_API, params=extract_params, headers=headers, timeout=8)
            er.raise_for_status()
            pages = er.json().get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    continue
                extract = page_data.get("extract", "").strip()
                if extract:
                    return extract[:700] + "…" if len(extract) > 700 else extract
            return None
        except Exception as e:
            logger.warning("Wikipedia retrieval failed: %s", e)
            return None


class SemanticEngine:
    """
    Generates semantic responses using an OpenAI-compatible LLM.

    Supports:
    - OpenAI (api_key required, base_url=None)
    - LM Studio (api_key="lm-studio", base_url="http://localhost:1234/v1")
    - Any OpenAI-compatible endpoint (custom base_url)
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self._api_key = api_key
        self._base_url = base_url
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """Lazy-initialise the OpenAI client (only when first needed)."""
        if self._client is None:
            kwargs = {}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def reconfigure(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        """Update configuration and reset client."""
        if model:
            self.model = model
        if api_key is not None:
            self._api_key = api_key
        if base_url is not None:
            self._base_url = base_url
        self._client = None  # force re-init on next call

    def execute(self, task_content: str, context: Optional[str] = None) -> Tuple[str, bool]:
        """Execute a semantic task using the configured LLM."""
        try:
            prompt = task_content
            if context:
                prompt = f"Context from previous steps:\n{context}\n\nTask: {task_content}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1024,
            )
            result = response.choices[0].message.content
            logger.debug("SemanticEngine: model=%s, tokens=%d", self.model, len(result.split()))
            return result, True
        except Exception as e:
            logger.error("SemanticEngine error: %s", e)
            return f"LLM Error: {str(e)}", False
