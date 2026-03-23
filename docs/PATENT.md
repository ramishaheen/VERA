# VERA — WIPO PCT Patent Application

**Title:** System and Method for Segmented Neuro-Symbolic Routing and Verification of Large Language Model Prompts (VERA)

**Inventor:** Dr. Rami Shaheen
**Filing Status:** Patent-Ready

---

## Abstract

A system and method for enhancing the reliability, factual accuracy, and logical consistency of Large Language Models (LLMs). The invention, termed VERA (Verification, Execution, Reasoning, Arbitration), operates as an intermediary API layer between a user interface and an LLM. The system intercepts natural language prompts, segments them into a Directed Acyclic Graph (DAG) of atomic tasks, and routes each task to a specialized execution engine based on task classification. Mathematical and logical tasks are routed to a deterministic code execution sandbox; factual queries are routed to a verified Retrieval-Augmented Generation (RAG) engine; and semantic synthesis tasks are routed to the core LLM. An arbitration module synthesises the outputs, verifies constraints, and triggers localised retry loops upon failure, thereby preventing hallucinations, logical errors, and multi-step reasoning failures inherent in standard token-prediction models.

---

## Background of the Invention

Large Language Models (LLMs) have demonstrated significant capabilities in natural language generation. However, because their underlying architecture relies on probabilistic next-token prediction rather than formal reasoning or factual grounding, they are prone to critical failure modes. These include "hallucinations" (generating plausible but false information), logical contradictions, and catastrophic error accumulation during multi-step reasoning tasks.

Current mitigation strategies, such as standard Retrieval-Augmented Generation (RAG) or post-hoc verification, are insufficient because they either fail to enforce strict logical constraints during generation or require computationally expensive, manual neuro-symbolic programming. There exists a need for a universal, model-agnostic system that can deterministically verify and execute specific components of a prompt while leveraging the LLM solely for semantic synthesis.

---

## Summary of the Invention

The present invention solves the aforementioned problems by decoupling the reasoning, execution, and synthesis phases of natural language processing. Instead of relying on a single LLM to perform mathematical calculation, factual recall, and language generation simultaneously, the invention introduces a routing architecture.

The system comprises:

1. **A Segmenter Module** configured to parse an input prompt into discrete, atomic tasks and map their dependencies as a Directed Acyclic Graph.
2. **A Router Module** configured to classify each atomic task and direct it to an optimal execution engine.
3. **A Plurality of Execution Engines**, including at least one deterministic sandbox for executing code/logic, and at least one factual retrieval engine.
4. **An Arbitrator Module** configured to receive outputs from the execution engines, verify them against predefined constraints, and synthesise a final, verified natural language response.

---

## Detailed Description

The VERA system operates as an API wrapper. When a client submits a prompt, the Segmenter Module utilises a classifier to identify distinct logical requirements within the text. For example, a prompt requesting a financial calculation followed by an email draft is split into two nodes.

The Router Module evaluates the nodes. Node 1 (calculation) is translated into formal code (SymPy) and executed within the Deterministic Sandbox, guaranteeing mathematical accuracy and bypassing the LLM's probabilistic math limitations. Node 2 (email draft) is routed to the core LLM, with the exact output of Node 1 injected into its context window.

The Arbitrator Module monitors the execution graph. If the Deterministic Sandbox throws an error (e.g., due to an unparseable equation), the Arbitrator intercepts the failure before it reaches the user, either routing to the LLM or returning a structured error, thus preventing hallucinated answers.

---

## Claims

**What is claimed is:**

1. A system for processing natural language prompts, comprising:
   - a segmenter module configured to receive an input prompt and decompose said prompt into a plurality of atomic tasks forming a directed acyclic graph;
   - a router module configured to classify each of said atomic tasks into one of a plurality of task types, including at least a mathematical/logical type, a factual type, and a semantic type;
   - a plurality of execution engines comprising at least a deterministic code execution sandbox and a natural language generation model;
   - wherein the router module directs mathematical/logical tasks to the deterministic code execution sandbox and semantic tasks to the natural language generation model; and
   - an arbitrator module configured to receive outputs from the plurality of execution engines, verify said outputs, and synthesise a final natural language response.

2. The system of claim 1, wherein the segmenter module constructs the directed acyclic graph using topological sorting to determine execution order based on inter-task dependencies.

3. The system of claim 1, wherein the deterministic code execution sandbox comprises a symbolic mathematics library configured to evaluate mathematical expressions with 100% accuracy.

4. The system of claim 1, further comprising a factual retrieval engine configured to query external knowledge sources and return grounded facts, wherein the router module directs factual query tasks to said factual retrieval engine.

5. The system of claim 1, wherein the arbitrator module is configured to trigger a localised retry loop upon detection of an engine failure, wherein said retry routes the failed task to an alternative execution engine.

6. The system of claim 1, wherein the system exposes an API endpoint compatible with the OpenAI Chat Completions API format.

7. The system of claim 1, wherein the system is model-agnostic and configurable to route semantic tasks to any OpenAI-compatible language model endpoint.

8. A method for processing natural language prompts, comprising:
   - receiving a natural language prompt at an intermediary API layer;
   - decomposing the prompt into a directed acyclic graph of atomic tasks using a segmenter module;
   - classifying each atomic task and routing it to a designated execution engine using a router module;
   - executing each task in topological order, passing outputs of upstream tasks as context to downstream tasks;
   - verifying each task output using an arbitrator module; and
   - synthesising and returning a final verified natural language response.

---

## Abstract of the Drawings

**Figure 1** — System architecture diagram showing the Segmenter, Router, Execution Engines, and Arbitrator in sequence.

**Figure 2** — Directed Acyclic Graph representation of a multi-step prompt decomposition.

**Figure 3** — Routing decision tree for task classification.

**Figure 4** — Mathematical proof of reliability improvement at N-step reasoning depth.

---

*All rights reserved. © 2026 Dr. Rami Shaheen*
