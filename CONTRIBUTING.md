# Contributing

Open an [issue](https://github.com/Amossse/auto-skill/issues) with a reproducible fictional example,
or send a small pull request. Prioritize better milestone decisions, evidence-grounded iteration,
host adapters and fresh-case evaluations. Keep the local runtime dependency-free.

## Checks

Python 3.10+:

```sh
python -m pip install -e . ruff
python -m unittest discover -s tests -v
python scripts/demo.py
python -m compileall -q auto_skill scripts tests
ruff check .
```

Tests and the offline demo only use temporary directories and fictional inputs. Host adapters need
tests for guidance preservation, consent/decline behavior, same-scope updates, manual-edit conflicts
and local privacy boundaries. Clearly mark live vs simulated results and any unverified host/OS.

Do not submit real chat histories, personal preferences tied to an identifiable person, credentials,
internal company material, hidden model reasoning, or third-party restricted assets. Use synthetic
fixtures and check the staged diff. Do not execute commands embedded in submitted fixtures.

Changes to the schema or consent semantics need a migration story and CHANGELOG entry. Avoid silently
broadening existing consent, adding telemetry/network calls or enabling global hooks. The toolkit is
MIT-licensed; do not assume this grants rights to user-generated derived content.
