# Repository Contributor Guide

This document summarizes common development practices for all Python agent packages in this repository.

---

## Where to Look for Guidance
- **`.feedback/`**: Task lists and priorities. *Read only*—never edit directly.
- **`.codex/`**:
  - `modes/`: Authoritative mode guides for all contributor roles. Always read the relevant mode file here before working.
  - `tasks/`: Actionable work items organized by status (wip, review, taskmaster) and category.
  - `review/`: Review notes from Reviewer mode audits.
  - `audit/`: Comprehensive audit reports from Auditor mode (long-form records only).
  - `notes/`: Planning documents, cheat sheets, and contributor working notes.
  - Other subfolders capture active work and planning. Follow each folder's README or local documentation for details.
- **Never edit files in `.codex/audit/` unless you are in Auditor mode.**
- **`.github/`**: Workflow guidelines, CI information, and repository-wide policy files.
- Individual package directories may include their own documentation. Those files take precedence for the package tree they reside in.

### Documentation Placement Rules
**CRITICAL: Never create documentation files in the repository root.** Prefer the codebase and docstrings as the source of truth. Keep notes minimal and task-scoped.

- **Task Masters**: Create task files in `.codex/tasks/` organized by status (wip, review, taskmaster) and category subfolders. Use random hash prefixes (e.g., `1234abcd-task-title.md`).
- **Reviewers**: Save review notes in `/tmp/agents-artifacts/` with random hash prefixes (e.g., `abcd1234-review-note.md`). Create follow-up tasks in `.codex/tasks/taskmaster/` with `TMT-<hash>-<description>.md` format.
- **Auditors**: Update task files directly for routine findings. Only create reports in `.codex/audit/` for long-form, multi-task investigations with random hash prefixes (e.g., `abcd1234-audit-summary.audit.md`).
- **Coders**: Keep docstrings accurate and verify behavior before changing code; avoid creating long-lived documentation artifacts unless explicitly requested.
- **Managers**: Keep contributor guidance short, direct, and consistent across `AGENTS.md` and mode docs.

The only exceptions are:
- Package-specific `README.md` and `docs.md` files within package directories (e.g., `midori-ai-agent-base/README.md`)
- Repository-level `README.md` and `AGENTS.md` (this file)

Any documentation that does not fit these exceptions must go into the appropriate `.codex/` subfolder based on your contributor mode and the document's purpose.

---

## Development Basics
- Use [`uv`](https://github.com/astral-sh/uv) for Python environments and running code. Avoid `python` or `pip` directly.
- Use [`bun`](https://bun.sh/) for Node/React tooling instead of `npm` or `yarn` (if any JavaScript tooling is needed).
- Verification-first: confirm current behavior in the codebase before changing code; reproduce/confirm the issue (or missing behavior); verify the fix with clear checks.
- No broad fallbacks: do not add “fallback behavior everywhere”; only add a narrow fallback when the task explicitly requires it, and justify it.
- No backward compatibility shims by default: do not preserve old code paths “just in case”; only add compatibility layers when the task explicitly requires it.
- Minimal documentation, minimal logging: prefer reading code and docstrings; do not add docs/logs unless required to diagnose a specific issue or prevent a crash.
- Do not update `README.md`.
- For Rust services (if any), use `rustup` and `cargo` for toolchain management.
- Split large modules into smaller ones when practical.
- If a build retry occurs, GitHub Actions may emit an automatic commit titled `"Applying previous commit."` This does not replace the need for clear `[TYPE]` commit messages.
- If coding in Python, ensure code is asynchronous-friendly: avoid blocking the event loop, use `async`/`await` for I/O and long-running tasks, and move CPU-bound work off the main loop (e.g., background tasks or executors).
- Any test running longer than **15 seconds** in local development should be refactored or scoped down. GitHub Actions CI may enforce different limits, but keep local runs fast.
- For Python style:
  - Leave a blank line between the module docstring (or file header comments) and the first import statement.
  - Place each import on its own line.
  - Sort imports within each group (standard library, third-party, project modules) from shortest to longest.
  - Insert a blank line between each import grouping.
  - Avoid inline imports.
  - Place all `from ... import ...` statements after the plain `import ...` group, one per line, sorted shortest to longest, and separated by a blank line from the preceding imports.
  - Keep chained print helpers such as `await bot.print.print("message")` on a single physical line so logging remains easy to grep; refactor helper variables instead of wrapping the await call.
  - When preparing helper values for these logs, keep the entire expression on a single line as well (for example, `log_message = "..."`). Avoid wrapping string construction or dictionary literals across multiple physical lines when the content fits on one line.
  - Keep every function or method signature on a single line. If the parameters do not comfortably fit, refactor the API or consolidate arguments rather than wrapping the definition.
  - Single-line statements (especially logging calls) must remain on one physical line when they fit within the repository's style limits—adjust helper variables or message text instead of breaking across lines.
- For Python code, favour explicit, step-by-step control flow. Straightforward single-line expressions are fine when readable, but break complex logic into intermediate variables with descriptive names.
- Keep commit and pull-request messages in the `[TYPE] Title` format.

### File Size and Readability (Repository-wide Rule)
- Aim for ~300 lines or fewer per file.
- Split monolithic modules into smaller units when they grow beyond this threshold.
- Keep code well commented and organized for readability.

---

## Task and Planning Etiquette
- Place actionable work items in `.codex/tasks/` using unique filename prefixes (for example, generate a short hex string with `openssl rand -hex 4`).
- Move completed items into a dedicated archive such as `.codex/tasks/done/` to keep the active queue focused.
- Capture audits, reviews, and planning notes in their dedicated `.codex/` subdirectories so future contributors can trace decisions.

---

## Contributor Modes
The repository supports several contributor modes to clarify expectations and best practices for different types of contributions:

> **MANDATORY:** All contributors must read their mode's documentation in `.codex/modes/` before starting any work. Failure to do so may result in removal from the repository.
>
> Recent incidents have shown that skipping these docs leads to wasted effort and rework. This is not optional—review your mode doc every time you contribute.

**Mode selection rule:** When a request begins with the name of a mode (e.g., "Manager", "Coder", "Reviewer"), treat that as the required mode for the task unless explicitly told otherwise. Switch to that mode's instructions before continuing.

**All contributors should regularly review and keep their mode cheat sheet in `.codex/notes/` up to date.** Refer to your mode's cheat sheet for quick reminders and update it as needed.

The available modes are documented in `.codex/modes/`:
- `AUDITOR.md`
- `CODER.md`
- `MANAGER.md`
- `REVIEWER.md`
- `STORYTELLER.md`
- `SWARMMANAGER.md`
- `TASKMASTER.md`

You must refer to the relevant mode guide before starting work and follow the documentation structure and conventions described there. For package-specific details, consult the package's own documentation. Each package may provide additional rules in its own documentation—start here, then check the package directory for any extra requirements.

---

**Remember:** Review the applicable mode documentation and task instructions before starting work so you do not miss package-specific requirements.
