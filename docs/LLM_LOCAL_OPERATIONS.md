# Local LLM Operations Guide

## Objective

This guide standardizes local LLM usage for two separate jobs:
- **Mentor**: explain system architecture and daily workflow.
- **Requirements Architect**: convert vague ideas into structured specs.

This separation avoids role confusion and improves output quality.

## Available CLI Entry Points

### Health check

```bash
cgalpha ask-health --smoke
```

### Interactive setup (recommended first step)

```bash
cgalpha ask-setup
```

Use it to set:
- default model
- default role (`mentor` or `requirements`)
- default response format (`markdown` or `json`)
- generation settings

### Mentor role

```bash
cgalpha ask "Explain daily V03 workflow in 4 steps"
```

### Requirements role

```bash
cgalpha ask-requirements "Define acceptance criteria for data-quality gate" --response-format json
```

### One command, explicit role

```bash
cgalpha ask "Draft scope for phase transition" --profile requirements --response-format json
```

## Recommended Settings by Hardware Profile

Given low-to-mid CPU environments, use conservative defaults.

### Balanced (default)
- model: `qwen2.5:1.5b`
- max_files: 2
- max_chars: 450-600
- num_predict: 120-220
- num_ctx: 1536
- timeout: 600-900

### Higher quality (slower)
- model: `qwen2.5:3b` or `deepseek-coder:1.3b`
- num_predict: 220-320
- timeout: 900-1200

## Role Contract

### Mentor
- Explain before proposing changes.
- Keep high-level orientation.
- Do not push unnecessary refactors.
- Ask for exact file when context is missing.

### Requirements Architect
- No coding output.
- Provide strict scope in/out.
- Provide assumptions and acceptance criteria.
- Provide risks and mitigation plan.
- Produce structured output (prefer JSON for handoff).

## Prompt Patterns

### Mentor pattern

`Explain X in 3-5 steps, mention where in CGAlpha each step lives, and what not to change yet.`

### Requirements pattern

`Translate this idea into: problem_statement, scope_in, scope_out, assumptions, requirements, acceptance_criteria, risks, execution_plan. No code.`

## Quality Checklist (Before Trusting Output)

1. Does it separate facts from assumptions?
2. Does it avoid inventing files or fake data?
3. Does it include measurable acceptance criteria?
4. Does it keep changes incremental?
5. Does it align with constitution constraints?

If one answer fails this checklist, run another prompt with tighter scope.

## Typical Failure Modes

- Too generic answer: increase context quality, not only token count.
- Too short answer: raise `num_predict`.
- Timeout: reduce `max_files`, `max_chars`, and/or use smaller model.
- Role drift: force `--profile requirements` or use `ask-requirements`.

## Suggested Daily Routine with Local LLM

1. `cgalpha ask-health --smoke`
2. `cgalpha ask` for orientation on today target.
3. `cgalpha ask-requirements` for structured task contract.
4. Execute technical task in coding workflow.
5. Re-check gates and summarize in memory/logs.

## Why this matters

A local LLM is not only for coding help.
In CGAlpha it is a navigation and decision support layer:
- lower cognitive load
- more repeatable planning
- cleaner handoff between human and coding agent
