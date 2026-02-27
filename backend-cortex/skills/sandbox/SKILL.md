---
name: sandbox
description: Protocol for Code and Data Isolation (Git Worktree & Memory Sandbox).
metadata:
  version: "1.0"
  author: "Antigravity & Cortex"
---

# Sandbox Protocol (Isolation & Safety)

## Objective
To ensure that all high-stakes changes (Refactoring, Schema updates, Skill generation) are performed in a non-destructive, verifiable environment before being "Committed" to the production system.

## 🛡️ Protocol A: Code Sandboxing (Git-Based)
**Trigger**: [High Impact] Changes or Complex Refactoring.

1. **Isolation**: Never edit `main` for experimental features.
2. **Branching**: Propose `feat/xxx-sandbox`.
3. **Worktree**: Use `git worktree` if working on parallel versions to avoid IDE context pollution.
4. **Validation**: Run `pytest` or `tools/arch_check.py` within the branch before merge proposal.

## 📦 Protocol B: Data Sandboxing (Record-Based)
**Trigger**: Memory ingestion, Reflection, or Subconscious pruning.

1. **Local Isolation**: Always mirror `memories` to `data/memories/` (Local JSON).
2. **Mocking**: When testing RAG logic, use `data/test_memories.json` instead of the live Supabase table.
3. **Atomic Writes**: Validate JSON structure in a temporary variable before writing to the physical file.

## 🧠 Protocol C: Cognitive Sandboxing (Simulation)
**Trigger**: Proposing [Decision Matrix] or new Prompts.

1. **Prediction**: Before asking the user, the AI must internally simulate the "Synergy" of the proposed change.
2. **spec-first**: Define the `Spec Mode` (What) in a scratchpad/artifact before moving to `Plan Mode` (How).

## Integration Directive
The **Active Intelligence** protocol (v3.8.5) mandates that any multi-step optimization or full-stack sync MUST be performed using a Sandbox Protocol to ensure zero-downtime for the LifeOS system.
