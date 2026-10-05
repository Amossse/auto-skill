# auto-skill v0.1.0

Turn verified task experience into a portable, versioned Agent Skill.

- Workspace installers for Codex and Claude Code; generic Agent Skills adapter.
- Ask before creating a new topic and enabling ongoing local updates.
- Same-scope iteration, evidence records, fresh-case validation, history and rollback.
- Manual-edit protection, atomic writes and recovery; zero runtime dependencies beyond Python 3.10+.
- Optional Claude Stop checkpoint, English/Chinese docs and a fictional lifecycle demo.

Install from the tagged GitHub source (not PyPI):

```sh
uv tool install git+https://github.com/Amossse/auto-skill.git@v0.1.0
auto-skill --workspace . install --agent all
```

27 local tests and the offline lifecycle passed. Live host behavior remains unverified because
the release environment could not complete its Claude/Codex checks. Automatic triggering depends
on host instructions/hooks. See [the validation report](https://github.com/Amossse/auto-skill/blob/v0.1.0/docs/validation.md).

The CLI makes no network/model calls and never publishes your experience. Privacy screening is
best-effort, not a confidentiality guarantee. Review generated skills before sharing.
