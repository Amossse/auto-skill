# auto-skill v0.1.1

Fix Windows legacy-console output in the fictional offline demo. A new regression test runs
the complete demo with cp1252 output encoding; the suite now has 28 tests.

Includes the v0.1.0 portable controller, Codex/Claude installers, consented ongoing local updates,
version history, rollback and privacy/conflict checks. The original v0.1.0 tag is unchanged.

```sh
uv tool install git+https://github.com/Amossse/auto-skill.git@v0.1.1
auto-skill --workspace . install --agent all
```

Live host prompting/creation/iteration remains unverified due to release-environment limitations.
See [validation](https://github.com/Amossse/auto-skill/blob/v0.1.1/docs/validation.md).
The CLI does not make network/model calls or publish your experience. Privacy filtering is best-effort.
