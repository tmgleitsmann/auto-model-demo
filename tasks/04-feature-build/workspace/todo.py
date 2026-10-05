#!/usr/bin/env python3
"""A tiny todo list CLI. Tasks are stored as JSON in .todo.json in the current directory."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STORE = Path(".todo.json")


def load_tasks():
    if STORE.exists():
        return json.loads(STORE.read_text())
    return []


def save_tasks(tasks):
    STORE.write_text(json.dumps(tasks, indent=2))


def cmd_add(title):
    tasks = load_tasks()
    tasks.append(
        {
            "id": len(tasks) + 1,
            "title": title,
            "done": False,
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )
    save_tasks(tasks)
    print(f"added #{tasks[-1]['id']}: {title}")


def cmd_list(show_all):
    tasks = load_tasks()
    if not show_all:
        tasks = [t for t in tasks if not t["done"]]
    if not tasks:
        print("no tasks")
        return
    for t in tasks:
        mark = "x" if t["done"] else " "
        print(f"[{mark}] {t['id']}. {t['title']}")


def cmd_done(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            save_tasks(tasks)
            print(f"done #{task_id}")
            return
    print(f"no task #{task_id}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="todo", description="A tiny todo list.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("title")

    p_list = sub.add_parser("list", help="list tasks")
    p_list.add_argument("--all", action="store_true", help="include done tasks")

    p_done = sub.add_parser("done", help="mark a task done")
    p_done.add_argument("id", type=int)

    args = parser.parse_args()
    if args.command == "add":
        cmd_add(args.title)
    elif args.command == "list":
        cmd_list(args.all)
    elif args.command == "done":
        cmd_done(args.id)


if __name__ == "__main__":
    main()
