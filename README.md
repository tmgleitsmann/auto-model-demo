# Auto Model demo

Watch Droid route different tasks to different models, then bring your own model and run the same suite on it.

This repo holds four small, self-contained coding tasks and a driver that runs each one through `droid exec` with **Auto Model** (canonically, the [Factory Router](https://docs.factory.com/model-independence/factory-router)). After each run, the driver reads the session transcript and reports which model served every step, what it cost, and how long it took.

## What you need

- The [Droid CLI](https://docs.factory.com/droid-cli/quickstart), signed in:

  ```bash
  curl -fsSL https://app.factory.ai/cli | sh
  ```

- Python 3.9 or newer

## Run it

```bash
git clone https://github.com/tmgleitsmann/auto-model-demo.git
cd auto-model-demo
python3 run_demo.py
```

Each task runs in a fresh copy of its workspace under `runs/`, so the source tasks stay untouched and every run is repeatable. The driver prints a routing report and writes the full version to `runs/report.md`.

Repeat the demo as often as you like: the driver never edits `tasks/`. If you (or someone in the room) run Droid directly inside a task workspace, restore the committed state and wipe `runs/` with:

```bash
python3 run_demo.py --reset
```

Before a live demo, preflight that Auto Model is available right now (free, no credits):

```bash
python3 run_demo.py --check
```

Auto Model's canonical id is `auto`; the driver prefers it and only falls back to `auto-fast` while the API gates `auto`.

## What the demo shows

Four tasks, one difficulty ladder:

| Task | What it asks for | What Auto Model did (sample run) |
|---|---|---|
| `01-mechanical-edit` | Add type hints and docstrings to two functions | `gpt-5.6-luna`, 5,504 credits, 24s |
| `02-bug-fix` | Fix a failing date-math test | `deepseek-v4-flash-0731`, 5,921 credits, 22s |
| `03-root-cause` | Diagnose a one-cent money bug, write it up, fix it | `deepseek-v4-flash-0731`, 8,029 credits, 44s |
| `04-feature-build` | Add due dates to a CLI app, with tests and docs | `claude-opus-5`, 229,706 credits, 145s |

That table is from a [real captured run](results/sample-run.md) (Droid CLI 0.213.0, 2026-10-05). The mechanical edit went to a fast model, the debugging and root-cause work went to a cost-efficient model, and the multi-step feature build went to a frontier model. Every task's own test suite passed.

Routing is decided per request, not per session, so your run will pick different models. That is the point: instead of locking a session to one model, the router weighs the work in front of it and chooses the best balance of quality, latency, and cost. In production it delivers 63% aggregate cost savings versus pricing the same workload at frontier-model rates, with 99.9%+ request reliability through provider failover ([source](https://docs.factory.com/model-independence/factory-router)).

## Bring your own model

Auto Model routes across Factory's models. To run this suite on a model of your own instead, connect it with [BYOK](https://docs.factory.com/model-independence/byok) and pass its id to the driver.

1. Add a `customModels` entry to `~/.factory/settings.json`. `byok/settings.example.json` has three ready-to-edit entries (OpenAI, OpenRouter, local Ollama):

   ```json
   {
     "customModels": [
       {
         "model": "qwen3-coder:30b",
         "displayName": "Ollama (local)",
         "baseUrl": "http://localhost:11434/v1",
         "provider": "generic-chat-completion-api",
         "maxOutputTokens": 32768
       }
     ]
   }
   ```

   The `provider` field sets the API format: `anthropic`, `openai`, or `generic-chat-completion-api` (OpenRouter, Fireworks, Together AI, Ollama, vLLM, and most open-source providers). API keys support `${ENV_VAR}` expansion and stay on your machine; Factory does not upload them. Custom models need at least 30B parameters to hold up on agentic coding tasks.

2. Run the suite on your model:

   ```bash
   python3 run_demo.py --model qwen3-coder:30b
   ```

3. Compare it against Auto Model in one report:

   ```bash
   python3 run_demo.py --model auto --model qwen3-coder:30b
   ```

The same four tasks, the same verification, side-by-side credits and wall time. In interactive sessions your custom models show up under "Custom models" in `/model`.

The `--model` flag also accepts any Factory-provided model id, so you can benchmark the suite against a single fixed model such as `gpt-5.6-sol` or `claude-opus-5`. See the [model list and multipliers](https://docs.factory.com/models).

## How the driver works

For each task, `run_demo.py`:

1. Copies the task's pristine `workspace/` to `runs/<model>/<task>/`.
2. Runs `droid exec -m auto --auto medium -o json --tag auto-model-demo -f TASK.md --cwd <run dir>`, which returns session id, turns, and credit usage as JSON.
3. Opens the session transcript at `~/.factory/sessions/**/<session id>.jsonl`. Every model response there records `modelId`, `apiProvider`, `routerId`, and `reasoningEffort`, which is how the report knows exactly which model served each step.
4. Runs the task's verify command (`task.json`) to confirm the work actually passes, and diffs the run directory against the pristine workspace to list changed files.

Add a task by creating `tasks/<name>/` with a `TASK.md` (the delegated task), a `workspace/` (the code), and a `task.json` (tier label + verify command). Nothing else in the driver is task-specific.

## Repo layout

```text
run_demo.py               driver: runs tasks, parses transcripts, renders the report
tasks/                    four tasks, each with TASK.md, workspace/, task.json
byok/settings.example.json  custom model templates (OpenAI, OpenRouter, Ollama)
results/sample-run.md     a real captured routing report
runs/                     created at runtime; workspaces and reports land here
```

## Troubleshooting

**`Invalid model: auto` during a run.** One-shot `droid exec` sessions default to a fixed model (`gpt-5.6-sol`), so the driver selects Auto Model explicitly with `-m` on every run. The Factory API intermittently gates the router ids at validation - a server-side flap, not a config problem. The driver probes with `droid exec --list-tools` (free; exits before any session starts), waits briefly (~30 seconds at most), and gives each affected task one recovery cycle. If the gate stays closed the run stops with a clear message: preflight with `python3 run_demo.py --check`, wait a few minutes and re-run, or demo on a fixed model meanwhile with `python3 run_demo.py --model gpt-5.6-sol`. Selecting Auto Model through a settings default instead of `-m` is possible but not recommended: when the id is gated, exec silently falls back to the fixed default instead of failing.

**A task missing from the report.** It did not run - the driver only records tasks that completed, and the report says so explicitly when a run is incomplete. Re-running redoes every task; finished ones simply overwrite their saved results.

## Learn more

- [Factory Router](https://docs.factory.com/model-independence/factory-router) - how Auto Model selects a model per task
- [Custom Models (BYOK)](https://docs.factory.com/model-independence/byok) - the full `customModels` field reference
- [Available models](https://docs.factory.com/models) - Factory-provided models and multipliers
- [Droid CLI quickstart](https://docs.factory.com/droid-cli/quickstart)

## License

[MIT](LICENSE)
