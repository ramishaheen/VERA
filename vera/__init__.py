"""
VERA (Verification, Execution, Reasoning, Arbitration) - Full Production System
A hybrid neuro-symbolic API layer that transforms LLMs into production-ready systems.
"""

__version__ = "1.0.0"
__author__ = "Dr. Rami Shaheen"

from .client import VERAClient

__all__ = ["VERAClient"]
