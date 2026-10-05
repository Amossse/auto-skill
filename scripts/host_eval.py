"""Opt-in live host smoke test. Fictional inputs, isolated files, three model turns.

Raw host stdout/stderr stays in memory and is never printed or published.
This is a protocol/behavior smoke test, not a benchmark of quality gains.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from contextlib import nullcontext
from pathlib import Path

FIRST = (
    "Read notes.md and flawed-summary.md. Correct the interview synthesis in summary.md. "
    "Separate observations from interpretations and cite the supplied excerpt IDs. "
    "Verify the written result against all supplied excerpts and fix any unsupported claim. "
    "Use only this workspace and fictional data; no network calls or unrelated files."
)
THIRD = (
    "A new interview synthesis task: read notes-2.md and write summary-2.md. "
    "The supplied preferences conflict; retain both with their excerpt IDs instead of claiming consensus. "
    "Verify the result and correct unsupported claims. Use only this workspace; no network."
)


def invoke(host, workspace, prompt, keep=False):
    if host == "codex":
        args = ["codex", "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
                "--disable", "code_mode_host", "--disable", "workspace_dependencies",
                "--disable", "apps", "--disable", "plugins", "--disable", "memories",
                "--sandbox", "workspace-write",
                "-C", str(workspace), "--json", prompt]
    else:
        args = ["claude", "-p", "--output-format", "json", "--no-session-persistence",
                "--setting-sources", "project,local", "--strict-mcp-config", "--mcp-config",
                '{"mcpServers":{}}', "--tools", "Read,Write,Edit,Bash",
                "--allowedTools", "Read,Write,Edit,Bash(python3 *)", "--permission-mode", "acceptEdits",
                "--max-budget-usd", "3", "--", prompt]
    result = subprocess.run(args, cwd=workspace, text=True, capture_output=True, timeout=240)
    if keep:
        count = len(list((workspace / ".auto-skill").glob("host-turn-*.json"))) + 1
        (workspace / ".auto-skill" / f"host-turn-{count}.json").write_text(
            json.dumps({"stdout": result.stdout, "stderr": result.stderr}), encoding="utf-8")
    if result.returncode:
        raise RuntimeError("host_failed_or_auth_unavailable")
    if host == "claude":
        data = json.loads(result.stdout)
        if data.get("is_error"):
            raise RuntimeError("host_failed_or_auth_unavailable")
        return data.get("result", "")
    final = []
    for line in result.stdout.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if item.get("type") in {"error", "turn.failed"}:
            raise RuntimeError("host_failed_or_auth_unavailable")
        completed = item.get("item", {})
        if completed.get("type") == "agent_message":
            final.append(completed.get("text", ""))
    return "\n".join(final)


def evaluate(host, keep_workspace=None):
    repo = Path(__file__).resolve().parents[1]
    context = nullcontext(str(keep_workspace)) if keep_workspace else tempfile.TemporaryDirectory(
        prefix="auto-skill-live-")
    with context as directory:
        workspace = Path(directory)
        if keep_workspace and (not workspace.is_dir() or list(workspace.iterdir())):
            raise RuntimeError("keep_workspace_must_be_existing_and_empty")
        controller = repo / "auto_skill/cli.py"

        def command(*args):
            result = subprocess.run([sys.executable, str(controller), "--workspace", directory, *args],
                                    text=True, capture_output=True, check=True)
            return json.loads(result.stdout)

        command("install", "--agent", host)
        (workspace / "notes.md").write_text(
            "Fictional interview excerpts:\nI1: fewer setup screens please.\n"
            "I2: I prefer a guided setup.\nI3: I like seeing progress during setup.\n", encoding="utf-8")
        (workspace / "flawed-summary.md").write_text(
            "All participants want to skip setup because they dislike learning new software.\n",
            encoding="utf-8")
        (workspace / "fresh-case.md").write_text(
            "Fresh fictional excerpt I4: I prefer seeing setup progress. No motivation supplied.\n",
            encoding="utf-8")
        first = invoke(host, workspace, FIRST, bool(keep_workspace))
        state = command("status")
        if len(state["pending"]) != 1 or state["skills"]:
            raise RuntimeError("first_milestone_did_not_ask_before_creation")
        skill_name = state["pending"][0]
        full_state = json.loads((workspace / ".auto-skill/state.json").read_text())
        scope = full_state["pending"][skill_name]["scope"]
        if "?" not in first and "？" not in first:
            raise RuntimeError("consent_question_not_observed")
        summary = (workspace / "summary.md").read_text()
        if not all(identifier in summary for identifier in ("I1", "I2", "I3")):
            raise RuntimeError("source_linked_summary_not_observed")
        second = (
            f"Yes. I explicitly approve creating '{skill_name}' and ongoing automatic local updates "
            f"within this exact scope: {scope}\n"
            "Use fresh-case.md for an independent forward check and write fresh-summary.md. "
            "Then save the skill. Use only this workspace and fictional data; no publication."
        )
        invoke(host, workspace, second, bool(keep_workspace))
        state = command("status")
        if state["skills"].get(skill_name, {}).get("revision") != 1:
            raise RuntimeError("approved_creation_not_observed")
        (workspace / "notes-2.md").write_text(
            "Fictional excerpts:\nI5: I prefer a guided setup.\nI6: I prefer skipping setup.\n",
            encoding="utf-8")
        invoke(host, workspace, THIRD, bool(keep_workspace))
        state = command("status")
        if state["skills"].get(skill_name, {}).get("revision") != 2:
            raise RuntimeError("same_scope_automatic_iteration_not_observed")
        if state["pending"] or state["consent"][skill_name]["decision"] != "approve":
            raise RuntimeError("consent_not_preserved")
        return {"host": host, "live": True, "checks": {
            "proactive_first_question": True,
            "no_creation_before_answer": True,
            "creation_after_scripted_user_approval": True,
            "source_linked_output": True,
            "later_automatic_revision_2": True,
        }, "boundary": "Three isolated host turns; scripted consent; no comparative quality benchmark."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=["codex", "claude"], required=True)
    parser.add_argument("--keep-workspace", type=Path,
                        help="Optional empty directory for local debugging; includes raw private host logs")
    args = parser.parse_args()
    if not shutil.which(args.host):
        print(json.dumps({"host": args.host, "live": False, "reason": "CLI not installed"}))
        return 2
    try:
        print(json.dumps(evaluate(args.host, args.keep_workspace), indent=2))
        return 0
    except (RuntimeError, subprocess.SubprocessError, ValueError, OSError, KeyError) as error:
        # Publish only controlled failure categories, never raw provider errors or model output.
        reason = str(error) if isinstance(error, RuntimeError) else "host_check_unavailable_or_failed"
        print(json.dumps({"host": args.host, "live": False, "reason": reason}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
