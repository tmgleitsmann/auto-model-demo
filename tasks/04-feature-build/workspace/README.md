# todo

A tiny todo list CLI in one file.

## Usage

    python3 todo.py add "Write the demo script"
    python3 todo.py list
    python3 todo.py list --all
    python3 todo.py done 1

Tasks are stored in `.todo.json` in the current directory. `list` hides done tasks; `--all` includes them.
