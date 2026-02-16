# CGAlpha v2 Context Directory

This directory contains persistent context for LLM-based reconstruction of CGAlpha.

## Purpose

- Enable LLMs to resume work with full context awareness
- Track architectural decisions (ADRs)
- Document migration progress
- Provide prompts for Actor-Critic workflow

## Directory Structure

```
.context/
├── CHANGELOG.md           # Detailed change history
├── migration_status.json  # Current migration status (machine-readable)
├── decisions.jsonl        # Architecture Decision Records (JSONL format)
├── prompts/               # Pre-compiled prompts for each phase
│   └── phase_2_2.md
└── vector_store/          # Embeddings for RAG (future)
    ├── embeddings.faiss
    ├── chunks.jsonl
    └── metadata.json
```

## How LLMs Should Use This

### Starting a New Session

1. Read `migration_status.json` to understand current state
2. Read `decisions.jsonl` to understand architectural decisions
3. Read `CHANGELOG.md` for recent changes
4. Read the appropriate prompt from `prompts/` directory

### After Making Changes

1. Update `CHANGELOG.md` with what was changed
2. Update `migration_status.json` with new status
3. Add any new decisions to `decisions.jsonl`

### File Formats

#### migration_status.json

```json
{
  "version": "0.2.0-alpha",
  "last_updated": "ISO-8601 timestamp",
  "phases": {
    "2.1": {
      "name": "Foundation",
      "status": "COMPLETE|PENDING|IN_PROGRESS",
      "components": {...}
    }
  }
}
```

#### decisions.jsonl

Each line is a JSON object:
```json
{"timestamp": "ISO-8601", "decision_id": "ADR-XXX", "title": "...", "rationale": "...", "impact": "...", "status": "approved"}
```

## Actor-Critic Workflow

### CRITIC (Advanced LLM)

1. Reviews code and architecture
2. Makes decisions (adds to decisions.jsonl)
3. Creates prompts in prompts/ directory
4. Approves or rejects ACTOR implementations

### ACTOR (Local LLM)

1. Reads prompts from prompts/ directory
2. Implements code in cgalpha_v2/
3. Updates CHANGELOG.md after each file
4. Reports to CRITIC for review

## Vector Store (Future)

The `vector_store/` directory will contain:
- FAISS index of codebase embeddings
- Original code chunks for retrieval
- Metadata for filtering

This enables RAG-based context retrieval for better LLM performance.

## Current Status

- **Phase 2.1**: Foundation - COMPLETE
- **Phase 2.2**: Signal Detection - PENDING
- **Next Step**: Implement Signal Detection services

## Quick Reference

| File | Purpose | Update Frequency |
|------|---------|------------------|
| CHANGELOG.md | Human-readable history | After each file |
| migration_status.json | Machine-readable status | After each phase |
| decisions.jsonl | Architectural decisions | When decisions made |
| prompts/*.md | Actor instructions | Before each phase |
