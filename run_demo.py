#!/usr/bin/env python3
"""Auto Model demo driver.

Runs the curated tasks in tasks/ through `droid exec`, then reads each
session transcript to report which model served every step of every task.

Auto Model (Factory Router) picks a model per task. The point of this demo
is to watch those decisions happen and see the cost and latency each one
produced. Pass --model to run the same suite on any single model instead,
including a model you bring yourself through BYOK (byok/settings.example.json).

Usage:
  python3 run_demo.py                                   # all tasks, Auto Model
  python3 run_demo.py --model auto --model gpt-5.6-sol  # compare two models
  python3 run_demo.py --task bug-fix                    # subset (repeatable)
  python3 run_demo.py --report-only                     # re-render saved report
  python3 run_demo.py --clean                           # wipe runs/ first
  python3 run_demo.py --reset                           # restore tasks/, wipe runs/, exit

Requires the Droid CLI, signed in: https://docs.factory.ai
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS_DIR = ROOT / "tasks"
RUNS_DIR = ROOT / "runs"
RUNS_JSON = RUNS_DIR / "runs.json"
REPORT_MD = RUNS_DIR / "report.md"
SESSIONS_DIR = Path.home() / ".factory" / "sessions"

# Auto Model IDs across CLI releases: "auto" where available, else "auto-fast".
AUTO_MODEL_IDS = ["auto", "auto-fast"]

EXEC_TIMEOUT_S = 900
VERIFY_TIMEOUT_S = 180


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def find_droid() -> str:
    droid = shutil.which("droid")
    if not droid:
        sys.exit(
            "droid CLI not found. Install it first: https://docs.factory.ai\n"
            "  curl -fsSL https://app.factory.ai/cli | sh"
        )
    return droid


def slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name)


def discover_tasks() -> list[dict]:
    if not TASKS_DIR.is_dir():
        sys.exit(f"no tasks directory at {TASKS_DIR}")
    tasks = []
    for task_dir in sorted(TASKS_DIR.iterdir()):
        if not (task_dir.is_dir() and (task_dir / "TASK.md").is_file()):
            continue
        meta = {}
        meta_path = task_dir / "task.json"
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text())
        if not (task_dir / "workspace").is_dir():
            sys.exit(f"{task_dir.name}: missing workspace/")
        tasks.append(
            {
                "name": task_dir.name,
                "dir": task_dir,
                "tier": meta.get("tier", ""),
                "verify": meta.get("verify", ""),
            }
        )
    if not tasks:
        sys.exit("no tasks found in tasks/")
    return tasks


def parse_exec_result(stdout: str) -> dict | None:
    """droid exec -o json prints one result object; take the last JSON line."""
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def transcript_path(session_id: str) -> Path | None:
    if not session_id or not SESSIONS_DIR.is_dir():
        return None
    for path in SESSIONS_DIR.rglob(f"{session_id}.jsonl"):
        return path
    return None


def extract_routing(session_id: str) -> dict:
    """Pull per-step model decisions out of the session transcript."""
    routing = {"router": None, "steps": [], "counts": {}}
    path = transcript_path(session_id)
    if path is None:
        return routing
    for line in path.read_text(errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "message":
            continue
        message = entry.get("message") or {}
        if message.get("role") != "assistant" or not message.get("modelId"):
            continue
        routing["router"] = routing["router"] or message.get("routerId")
        routing["steps"].append(
            {
                "model": message["modelId"],
                "provider": message.get("apiProvider", ""),
                "effort": message.get("reasoningEffort", ""),
            }
        )
        routing["counts"][message["modelId"]] = routing["counts"].get(message["modelId"], 0) + 1
    return routing


def changed_files(pristine: Path, run_dir: Path) -> list[str]:
    def snapshot(root: Path) -> dict:
        out = {}
        for p in root.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store":
                out[str(p.relative_to(root))] = p.read_bytes()
        return out

    before, after = snapshot(pristine), snapshot(run_dir)
    return sorted(
        name for name in set(before) | set(after) if before.get(name) != after.get(name)
    )


def verify_task(verify_cmd: str, run_dir: Path) -> bool:
    quoted = f'"{sys.executable}"' if " " in sys.executable else sys.executable
    cmd = verify_cmd.replace("{python}", quoted)
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=run_dir, capture_output=True, text=True, timeout=VERIFY_TIMEOUT_S
        )
    except subprocess.TimeoutExpired:
        return False
    return proc.returncode == 0


def run_task(droid: str, model: str, task: dict) -> tuple[dict | None, str | None]:
    """Run one task in a fresh copy of its workspace. (record, fatal_error)"""
    run_dir = RUNS_DIR / slug(model) / task["name"]
    pristine = task["dir"] / "workspace"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(pristine, run_dir)

    cmd = [
        droid, "exec",
        "-m", model,
        "--auto", "medium",
        "-o", "json",
        "--tag", "auto-model-demo",
        "-f", str(task["dir"] / "TASK.md"),
        "--cwd", str(run_dir),
    ]
    print(f"\n>> {task['name']} [{model}]: running droid exec ...")
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=EXEC_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, f"{task['name']}: droid exec timed out after {EXEC_TIMEOUT_S}s"
    wall = round(time.monotonic() - started, 1)

    combined = (proc.stdout or "") + (proc.stderr or "")
    if "Invalid model" in combined:
        excerpt = " | ".join(combined.strip().splitlines()[:3])[:300]
        return None, f"INVALID_MODEL ({excerpt})"

    result = parse_exec_result(proc.stdout or "")
    if result is None:
        tail = combined.strip().splitlines()[-1:] or ["(no output)"]
        return None, f"{task['name']}: no result JSON from droid exec: {tail[0][:200]}"

    session_id = result.get("session_id", "")
    routing = extract_routing(session_id)
    usage = result.get("usage") or {}
    ok = result.get("is_error") is False and result.get("subtype") == "success"

    verified = "skip"
    if task["verify"]:
        verified = "pass" if verify_task(task["verify"], run_dir) else "fail"

    models_detail = []
    for model_id, steps in routing["counts"].items():
        first = next(s for s in routing["steps"] if s["model"] == model_id)
        models_detail.append(
            {
                "model": model_id,
                "steps": steps,
                "provider": first["provider"],
                "effort": first["effort"],
            }
        )

    record = {
        "task": task["name"],
        "tier": task["tier"],
        "model": model,
        "router": routing["router"],
        "models": models_detail,
        "turns": result.get("num_turns"),
        "credits": usage.get("factory_credits"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "duration_s": wall,
        "ok": ok,
        "verify": verified,
        "files_changed": changed_files(pristine, run_dir),
        "session_id": session_id,
        "result": (result.get("result") or "")[:280],
        "ts": utcnow(),
    }
    return record, None


def load_runs() -> list[dict]:
    if RUNS_JSON.is_file():
        return json.loads(RUNS_JSON.read_text())
    return []


def save_run(records: list[dict], record: dict) -> list[dict]:
    records = [
        r
        for r in records
        if not (r["model"] == record["model"] and r["task"] == record["task"])
    ]
    records.append(record)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_JSON.write_text(json.dumps(records, indent=2))
    return records


def verify_mark(v: str) -> str:
    return {"pass": "PASS", "fail": "FAIL", "skip": "-"}.get(v, str(v))


def print_report(records: list[dict]) -> None:
    print("\n" + "=" * 78)
    print("AUTO MODEL DEMO - ROUTING REPORT")
    print("=" * 78)
    for model in dict.fromkeys(r["model"] for r in records):
        rows = sorted((r for r in records if r["model"] == model), key=lambda r: r["task"])
        print(f"\nModel: {model}")
        print("-" * 78)
        total = 0
        for r in rows:
            credits = r.get("credits") or 0
            total += credits
            status = "ok" if r.get("ok") else "ERROR"
            used = " + ".join(f"{m['model']} x{m['steps']}" for m in r["models"]) or "unknown"
            print(
                f"{r['task']:<24}{r['tier']:<11}{str(r.get('turns')):>3} turns"
                f"{credits:>10,} cr{r['duration_s']:>8.1f}s   {verify_mark(r['verify']):<5} {status}"
            )
            print(f"{'':24}models: {used}")
        print(f"{'':24}{'TOTAL':<11}{'':>3}{total:>10,} cr")
    print("\nFull report saved to: " + str(REPORT_MD))


def render_markdown(records: list[dict]) -> str:
    lines = [
        "# Auto Model demo - routing report",
        "",
        f"_Generated {utcnow()} by `run_demo.py`._",
        "",
        "Each row is one task run through `droid exec`. **Models** lists the model",
        "that served each step, as recorded in the session transcript.",
        "",
    ]
    for model in dict.fromkeys(r["model"] for r in records):
        rows = sorted((r for r in records if r["model"] == model), key=lambda r: r["task"])
        total = sum(r.get("credits") or 0 for r in rows)
        lines += [
            f"## Model: `{model}`",
            "",
            "| Task | Tier | Turns | Models (steps) | Credits | Wall time | Verify |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in rows:
            used = "<br>".join(f"`{m['model']}` x{m['steps']}" for m in r["models"]) or "unknown"
            credits = f"{r['credits']:,}" if r.get("credits") is not None else "-"
            lines.append(
                f"| {r['task']} | {r['tier']} | {r.get('turns')} | {used} | {credits} "
                f"| {r['duration_s']}s | {r['verify']} |"
            )
        lines += ["", f"**Total credits: {total:,}**", ""]
        for r in rows:
            lines.append(f"### {r['task']} (`{model}`)")
            lines.append("")
            if r.get("router"):
                lines.append(f"- Router: `{r['router']}`")
            for m in r["models"]:
                bits = [f"`{m['model']}` x{m['steps']}"]
                if m.get("provider"):
                    bits.append(f"provider `{m['provider']}`")
                if m.get("effort"):
                    bits.append(f"effort `{m['effort']}`")
                lines.append("- " + ", ".join(bits))
            if r.get("files_changed"):
                lines.append("- Files changed: " + ", ".join(f"`{f}`" for f in r["files_changed"]))
            if r.get("session_id"):
                lines.append(f"- Session: `{r['session_id']}` - inspect with `droid --resume {r['session_id']}`")
            if r.get("result"):
                lines.append("- Final message: " + str(r["result"]).replace("\n", " ")[:240])
            lines.append("")
    return "\n".join(lines)


def reset_demo() -> None:
    """Restore tasks/ to its committed state and wipe runs/.

    The driver never edits tasks/ - every run works on a fresh copy under
    runs/. This covers the remaining case: someone ran Droid (or anything
    else) directly inside a task workspace. Uncommitted changes under tasks/
    are reverted and untracked residue (test caches, ROOT_CAUSE.md, .todo.json)
    is removed.
    """
    inside = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    if shutil.which("git") and inside.stdout.strip() == "true":
        subprocess.run(["git", "-C", str(ROOT), "restore", "--", "tasks/"], check=True)
        subprocess.run(["git", "-C", str(ROOT), "clean", "-fdx", "--", "tasks/"], check=True)
        print("reset: tasks/ restored to committed state (edits reverted, residue removed)")
    else:
        # No git work tree: best-effort removal of known run residue.
        removed = 0
        for junk in TASKS_DIR.glob("*/workspace/**/__pycache__"):
            shutil.rmtree(junk, ignore_errors=True)
            removed += 1
        for name in ("ROOT_CAUSE.md", ".todo.json"):
            for junk in TASKS_DIR.glob(f"*/workspace/**/{name}"):
                junk.unlink(missing_ok=True)
                removed += 1
        print(
            f"reset: no git work tree; removed {removed} residue files "
            "(modified files could not be reverted - re-clone to restore)"
        )
    if RUNS_DIR.exists():
        shutil.rmtree(RUNS_DIR)
        print("reset: runs/ wiped")
    print("Pristine again. Run the demo with: python3 run_demo.py")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--model",
        action="append",
        default=[],
        help="model id to run the suite on (repeatable). Default: Auto Model "
        "(`auto`, falling back to `auto-fast` on older CLIs). BYOK custom model ids work too.",
    )
    ap.add_argument(
        "--task", action="append", default=[], help="task name or substring (repeatable)"
    )
    ap.add_argument(
        "--report-only", action="store_true", help="render report from runs/runs.json without running"
    )
    ap.add_argument("--clean", action="store_true", help="delete runs/ before starting")
    ap.add_argument(
        "--reset",
        action="store_true",
        help="restore tasks/ to committed state, wipe runs/, and exit (covers running Droid directly inside a task workspace)",
    )
    args = ap.parse_args()

    if args.reset:
        reset_demo()
        return

    if args.clean and RUNS_DIR.exists():
        shutil.rmtree(RUNS_DIR)

    records = load_runs()

    if args.report_only:
        if not records:
            sys.exit("no saved runs yet; run the demo first")
        print_report(records)
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_MD.write_text(render_markdown(records))
        return

    droid = find_droid()
    all_tasks = discover_tasks()
    tasks = all_tasks
    if args.task:
        tasks = [t for t in all_tasks if any(pat in t["name"] for pat in args.task)]
        if not tasks:
            sys.exit(
                f"no tasks match {args.task}; available: {[t['name'] for t in all_tasks]}"
            )

    for requested in args.model or [None]:
        current = requested if requested else AUTO_MODEL_IDS[0]
        fell_back = False
        for task in tasks:
            record, error = run_task(droid, current, task)
            if error and error.startswith("INVALID_MODEL"):
                # Router ids can be rejected transiently; retry once before
                # treating the rejection as permanent.
                print("  note: model id rejected; retrying once after 15s ...")
                time.sleep(15)
                record, error = run_task(droid, current, task)
            if (
                error
                and error.startswith("INVALID_MODEL")
                and requested is None
                and not fell_back
                and len(AUTO_MODEL_IDS) > 1
            ):
                fell_back = True
                current = AUTO_MODEL_IDS[1]
                print(f"  note: `{AUTO_MODEL_IDS[0]}` not accepted; using `{current}` for Auto Model")
                record, error = run_task(droid, current, task)
            if error:
                print(f"  FAILED {error}", file=sys.stderr)
                continue
            if record:
                records = save_run(records, record)

    if not records:
        sys.exit("no runs recorded")
    print_report(records)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(render_markdown(records))


if __name__ == "__main__":
    main()
