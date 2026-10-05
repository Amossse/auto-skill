"""Reproducible offline lifecycle demo using fictional records, no model calls."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    repo = Path(__file__).resolve().parents[1]
    controller = repo / "auto_skill/cli.py"
    with tempfile.TemporaryDirectory(prefix="auto-skill-demo-") as directory:
        workspace = Path(directory)

        def run(*args):
            result = subprocess.run([sys.executable, str(controller), "--workspace", str(workspace), *args],
                                    text=True, capture_output=True, check=True)
            return json.loads(result.stdout)

        assert run("install", "--agent", "all")["action"] == "installed"
        first = run("assess", "--event", str(repo / "examples/milestone.json"))
        assert first["action"] == "ask"
        print("assess → ask (no skill created)")
        assert not (workspace / ".agents/skills/summarize-interviews/SKILL.md").exists()
        # Simulation only: a real host must wait for an actual human response before this command.
        run("consent", "--name", "summarize-interviews", "--decision", "approve")
        assert run("save", "--recipe", str(repo / "examples/recipe.json"))["revision"] == 1
        print("simulated human approval → revision 1")
        assert run("assess", "--event", str(repo / "examples/update-milestone.json"))["action"] == "update"
        assert run("save", "--recipe", str(repo / "examples/update-recipe.json"))["revision"] == 2
        print("new same-scope milestone → revision 2 (no second question)")
        a = workspace / ".agents/skills/summarize-interviews/SKILL.md"
        b = workspace / ".claude/skills/summarize-interviews/SKILL.md"
        assert a.read_text() == b.read_text()
        assert "opposing preferences" in a.read_text()
        assert run("rollback", "--name", "summarize-interviews", "--revision", "1")["revision"] == 3
        assert "opposing preferences" not in a.read_text()
        print("rollback revision 1 → revision 3; Claude/Codex files match")
        run("consent", "--name", "summarize-interviews", "--decision", "pause")
        print("pause → local automatic updates disabled")
        print("PASS: offline lifecycle only; no real model evaluation")


if __name__ == "__main__":
    main()
