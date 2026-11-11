#!/usr/bin/env python3
"""Guardrail hook for Claude Code (runs before every Bash / Read / Write / Edit call).

Policy
  * Inside the project folder: everything is allowed (create, edit, move, delete).
  * Outside the project folder: reading, editing and downloading are allowed,
    but nothing may be DELETED (rm, rmdir, unlink, find -delete, rsync --delete,
    moving files away with mv, Python rmtree/remove/unlink, ...).
  * The guardrails themselves can't be changed or deleted: .claude/ (settings, hooks,
    skills), CLAUDE.md, run-agent.sh, .env. The project folder itself and .git can't be deleted.
  * .env can't be read or printed (keeps the API key out of logs).
  * GitHub: only task/* branches may be pushed (no force, no deletes, never main), and only
    pull-request gh commands are allowed (create, merge, list, view, ...).

Exit code 2 blocks the call; the message on stderr is shown to Claude so it can adapt.
Shell parsing is best-effort: it covers the commands an agent normally uses.
"""

import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path

data = json.load(sys.stdin)
tool = data.get("tool_name", "")
tool_input = data.get("tool_input", {}) or {}

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()).resolve()
START_CWD = Path(data.get("cwd") or ROOT).resolve()

SCRATCH = {Path(p).resolve() for p in ("/tmp", "/private/tmp", "/var/tmp", tempfile.gettempdir())}
PROTECTED = [ROOT / ".claude", ROOT / "CLAUDE.md", ROOT / "run-agent.sh", ROOT / ".env"]
NO_DELETE = [ROOT, ROOT / ".git"]

DELETE_CMDS = {"rm", "rmdir", "unlink", "shred", "srm", "trash"}
EDIT_CMDS = {"sed", "perl", "tee", "truncate", "dd", "chmod", "chown", "touch", "cp", "install", "ln"}
WRAPPERS = {"sudo", "env", "nohup", "time", "command", "nice", "exec", "builtin"}
READ_CMDS = {"cat", "less", "more", "head", "tail", "grep", "egrep", "rg", "strings", "xxd", "od", "source", ".", "bat"}
SEPARATORS = {";", "&&", "||", "|", "&", "(", ")"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
INLINE_DELETE = re.compile(r"rmtree|\bremove\(|\bunlink\(|\brmdir\(|\brename\(|\breplace\(|\bmove\(")


def block(message: str) -> None:
    print(f"BLOCKED by guardrail: {message}", file=sys.stderr)
    sys.exit(2)


def to_path(raw: str, cwd: Path) -> Path:
    raw = os.path.expanduser(os.path.expandvars(raw))
    glob = re.search(r"[*?\[]", raw)
    if glob:  # judge a glob by its fixed prefix: "data/*" -> "data/"
        raw = raw[: glob.start()] or "."
    path = Path(raw)
    if not path.is_absolute():
        path = cwd / path
    return path.resolve()


def under(path: Path, base: Path) -> bool:
    return path == base or base in path.parents


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)) if under(path, ROOT) and path != ROOT else str(path)


def check_protected(path: Path, action: str) -> None:
    for p in PROTECTED:
        if under(path, p):
            block(f"{action} {rel(path)} isn't allowed: it's part of the guardrails.")


def check_delete(path: Path) -> None:
    if any(under(path, s) for s in SCRATCH):
        return
    if not under(path, ROOT):
        block(f"Deleting or moving away anything outside the project folder isn't allowed: {path}")
    if path in NO_DELETE:
        block(f"Deleting {'the project folder' if path == ROOT else rel(path)} isn't allowed.")
    check_protected(path, "Deleting")
    for p in PROTECTED + [ROOT / ".git"]:
        if path in p.parents:
            block(f"Deleting {rel(path)} would also remove {rel(p)}. Delete specific subfolders instead.")


def check_edit(path: Path) -> None:
    """Edits are allowed anywhere except the guardrail files."""
    check_protected(path, "Changing")


def check_env_read(path: Path) -> None:
    if path == ROOT / ".env":
        block(".env can't be read. The key is already available as the CENSUS_API_KEY environment variable.")


def positional(tokens: list[str]) -> list[str]:
    out, after_dashdash = [], False
    for t in tokens:
        if after_dashdash:
            out.append(t)
        elif t == "--":
            after_dashdash = True
        elif not t.startswith("-"):
            out.append(t)
    return out


TASK_BRANCH = re.compile(r"^task/[A-Za-z0-9._/-]+$")
PUSH_FORBIDDEN_FLAGS = {"-f", "--force", "--mirror", "--all", "--delete", "-d", "--prune", "--force-if-includes"}
GH_ALLOWED = {
    ("pr", "create"), ("pr", "merge"), ("pr", "list"), ("pr", "view"), ("pr", "status"),
    ("pr", "checks"), ("pr", "diff"), ("pr", "comment"), ("pr", "ready"),
    ("auth", "status"), ("repo", "view"),
}


def git_subcommand(rest: list[str]) -> tuple[str, list[str]]:
    """Skip git's global options (-C path, -c key=value, --no-pager...) to find the subcommand."""
    i = 0
    while i < len(rest):
        t = rest[i]
        if t in ("-C", "-c", "--git-dir", "--work-tree"):
            i += 2
        elif t.startswith("-"):
            i += 1
        else:
            return t, rest[i + 1 :]
    return "", []


def check_push(args: list[str]) -> None:
    """Only task/* branches may be pushed; no force, no deletes, nothing to main."""
    for t in args:
        if t in PUSH_FORBIDDEN_FLAGS or t.startswith("--force") or re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", t):
            block(f"`git push {t}` isn't allowed. Push task branches normally: git push -u origin task/<name>")
    refs = positional([t for t in args if t not in ("-u", "--set-upstream")])[1:]  # drop the remote name
    if not refs:
        block("Name the branch explicitly: git push -u origin task/<phase>-<slug>")
    for ref in refs:
        src, _, dst = ref.partition(":")
        dst = dst or src
        if ref.startswith("+") or not src:
            block("Force pushes and remote branch deletion aren't allowed.")
        if not (TASK_BRANCH.match(src) and TASK_BRANCH.match(dst)):
            block(f"Only task/* branches can be pushed (got '{ref}'). main changes only through merged pull requests.")


def check_gh(args: list[str]) -> None:
    words = [t for t in args if not t.startswith("-")][:2]
    if tuple(words) not in GH_ALLOWED:
        block(f"`gh {' '.join(words)}` isn't allowed. Allowed: gh pr create/merge/list/view/status/checks/diff/comment/ready, gh auth status, gh repo view.")
    if words == ["pr", "merge"] and "--admin" in args:
        block("`gh pr merge --admin` isn't allowed.")


def check_inline_code(code: str, cwd: Path) -> None:
    """python -c / node -e: block delete calls on paths outside the project."""
    if not INLINE_DELETE.search(code):
        return
    for literal in re.findall(r"""['"]((?:/|~|\.\.)[^'"]*)['"]""", code):
        check_delete(to_path(literal, cwd))


def check_segment(tokens: list[str], cwd: Path) -> Path:
    """Check one simple command; returns the cwd after it (to follow `cd`)."""
    for i, tok in enumerate(tokens[:-1]):
        if tok in REDIRECTS:
            check_edit(to_path(tokens[i + 1], cwd))
    tokens = [t for i, t in enumerate(tokens) if t not in REDIRECTS and (i == 0 or tokens[i - 1] not in REDIRECTS)]

    while tokens and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]) or tokens[0] in WRAPPERS):
        tokens = tokens[1:]
    if not tokens:
        return cwd

    cmd, rest = os.path.basename(tokens[0]), tokens[1:]
    joined = " ".join(rest)
    args = positional(rest)

    if cmd in ("cd", "pushd"):
        return to_path(args[0], cwd) if args else Path.home()

    deletes = (
        cmd in DELETE_CMDS
        or cmd == "mv"
        or (cmd == "find" and re.search(r"-delete|-exec", joined))
        or (cmd == "rsync" and "--delete" in joined)
    )
    if deletes and re.search(r"\$\(|`", joined):
        block("Don't use $(...) or backticks in delete/move commands. Write the paths out explicitly.")

    if cmd in DELETE_CMDS:
        for a in args:
            check_delete(to_path(a, cwd))
    elif cmd == "mv":
        for a in args[:-1]:  # sources disappear from where they were
            check_delete(to_path(a, cwd))
        if args:
            check_edit(to_path(args[-1], cwd))
    elif cmd == "find" and re.search(r"-delete|-exec(dir)?\s+(rm|mv|shred|unlink|rmdir)\b", joined):
        starts = []
        for t in rest:
            if t.startswith("-") or t in ("(", "!"):
                break
            starts.append(t)
        for s in starts or ["."]:
            check_delete(to_path(s, cwd))
    elif cmd == "rsync" and "--delete" in joined and args:
        check_delete(to_path(args[-1], cwd))
    elif cmd == "xargs" and re.search(r"\b(rm|mv|shred|unlink|rmdir)\b", joined):
        block("Don't pipe into `xargs rm/mv`. Use `find <path-in-project> ... -delete` or explicit paths.")
    elif cmd == "git":
        if rest[:1] == ["-C"] and len(rest) > 1 and re.search(r"\b(clean|rm|reset|checkout|restore)\b", joined):
            check_delete(to_path(rest[1], cwd))
        sub, sub_args = git_subcommand(rest)
        if sub == "push":
            check_push(sub_args)
    elif cmd == "gh":
        check_gh(rest)
    elif cmd in EDIT_CMDS:
        for a in args:
            p = to_path(a, cwd)
            if under(p, ROOT):
                check_edit(p)
    elif re.fullmatch(r"python[0-9.]*|node|ruby", cmd):
        for i, t in enumerate(rest):
            if t in ("-c", "-e") and i + 1 < len(rest):
                check_inline_code(rest[i + 1], cwd)

    if cmd in READ_CMDS:
        for a in args:
            if os.path.basename(a) == ".env":
                check_env_read(to_path(a, cwd))
    return cwd


DELETE_WORDS = re.compile(r"(^|[\s;&|(])(rm|rmdir|unlink|shred|srm|trash|mv)\s|-delete\b|--delete\b")
SUBSTITUTION = re.compile(r"\$\(|`")


def check_bash(command: str) -> None:
    # Paths built at run time can't be checked, so don't allow them in delete/move commands.
    if SUBSTITUTION.search(command) and DELETE_WORDS.search(command):
        block("Don't use $(...) or backticks in delete/move commands. Write the paths out explicitly.")

    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        block("Couldn't parse this command (unbalanced quotes?). Simplify it or put it in a script file.")

    cwd, segment = START_CWD, []
    for tok in tokens + [";"]:
        if tok in SEPARATORS:
            if segment:
                cwd = check_segment(segment, cwd)
            segment = []
        else:
            segment.append(tok)


if tool == "Bash":
    check_bash(tool_input.get("command", ""))
elif tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if target:
        check_edit(to_path(target, START_CWD))
elif tool == "Read":
    target = tool_input.get("file_path")
    if target:
        check_env_read(to_path(target, START_CWD))

sys.exit(0)
