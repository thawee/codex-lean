# Codex CLI Directives (Token-Safe & GTD)

## 1. Workflow Orchestration & GTD
- **Plan Mode Default:** For 3+ steps or architectural decisions, write checkable plan to `tasks/todo.md` before executing. Check in before starting.
- **Stop & Re-plan:** If a command or tool call fails unexpectedly, halt execution immediately, inspect stderr, and re-plan. Do not repeat failed tool calls with identical arguments.
- **Autonomous Bug Fixing:** Fix bugs and failing CI tests directly from compiler output, stack traces, and test results. Zero hand-holding.
- **Verification First:** Never mark complete without proving correctness. Run target test suites, verify diffs against `main`, and confirm runtime behavior.
- **Self-Improvement Loop:** After ANY correction from the user, immediately document the pattern and preventative rule in `tasks/lessons.md`. Review at session start.
- **Demand Elegance:** For non-trivial logic, pause and implement the elegant solution. Avoid hacky workarounds; skip over-engineering for simple fixes.

## 2. Execution Strategy & Task Splitting
- **Atomic Sub-tasks:** Break large operations into small, self-contained sub-tasks to eliminate connection timeouts and per-turn token limits.
- **Scratchpad Offload:** Offload complex scratch calculations, schema inspections, or experimental scripts to isolated scratch files before touching project code.
- **Single Objective:** Keep each execution turn focused on one discrete modification or validation step.

## 3. Strict Token Safety & Operational Boundaries
- **Output Truncation:** Never run commands that produce runaway terminal output. Pipe through `tail -n 50`, `head -n 50`, or `rg -m 20`.
- **No Interactive Commands:** Never execute commands that open interactive pagers (`less`, `vim`), waiting loops, or interactive prompts.
- **Surgical Diff Edits:** Make minimal, elegant modifications. Do not touch unrelated files or reformat untouched functions.
- **Safety Boundaries:** Never execute destructive commands (`rm -rf`, `git push --force`, schema drops) without explicit confirmation.
- **No Guessing Policy:** If a requirement, API, flag, or configuration is unclear, verify via repository code/docs or ask immediately. Clarity over speed.
- **Concise Mastery:** High-density output with structured bullets or tables. No pleasantries.

## Lean multi-agent workflow

- The main agent uses GPT-6.1 Sol / medium and owns planning, integration, and final verification.
- Handle simple tasks directly. Delegate when a bounded subtask benefits from separate work; this instruction authorizes delegation for such tasks.
- Use explorer (GPT-6 Luna / high) for code investigation, worker (GPT-6.1 Sol / high) for implementation and tests, and researcher (GPT-6 Luna / high) for targeted research.
- Give each helper a clear scope and expected output. Assign only one agent to edit any given file at a time.
- Parallelize independent work and sequence dependent work. Spawn only the helpers the task needs.
- Close finished helpers before starting additional ones; keep at most three helpers open concurrently.
- Use reviewer (GPT-6 Astra / low) only for unresolved correctness concerns, difficult architecture, or conflicting evidence.
- The main agent checks helper results, resolves conflicts, and runs final validation before reporting completion.
