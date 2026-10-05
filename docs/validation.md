# Validation report

Release candidate: v0.1.0. Local checks performed on 2026-10-06.

## Verified locally

- 27 Python unit tests passed on Python 3.10 and 3.11.
- The fictional offline lifecycle demo passed: ask without creating, explicit simulated approval,
  revision 1, same-scope revision 2 without another question, rollback as revision 3, and pause.
- Codex/Claude generated skill contents matched in that demo.
- Tests cover consent, changed scope, persistent decline, duplicate events, manual edits,
  unmanaged skills, symlinks/traversal, installer idempotence, lock/journal recovery,
  bounded input and privacy rejection, and the optional Claude Stop-hook recursion guard.
- Python compilation, Ruff lint, wheel build/install, and installed CLI invocation passed.
- The source skill passed the Agent Skills structure validator.
- The public source tree was reviewed for private context and scanned with Gitleaks.
  No detected secrets is not proof that every possible confidential detail is absent.

The examples and approval in the offline demo are synthetic. The structured validation record is
an attestation supplied by a host, not independently verified by the CLI.

## Live host checks: not passed

An isolated three-turn harness is available:

```sh
python scripts/host_eval.py --host codex
python scripts/host_eval.py --host claude
```

The release environment did not complete either live host check:

- Claude Code: authentication was unavailable.
- Codex: a model session started, but its local command tool failed before the task could execute.
  This did not establish whether the milestone workflow would trigger successfully.

Therefore **proactive prompting, model-generated skill creation and later automatic iteration in
real host sessions remain unverified** for v0.1.0. The installer and deterministic lifecycle are
tested; they are not a substitute for those host checks. Raw diagnostic output is not published.
The optional Claude hook was unit-tested, not tested in an authenticated live Claude session.
Generic hosts and Windows native-shell hook execution have not been live-tested.

## Continuous integration

GitHub Actions runs tests, the offline demo, compilation and lint on Linux (Python 3.10/3.13),
macOS (3.11) and Windows (3.11). Consult the repository's Actions results for current run status;
the workflow definition alone does not prove a run passed. CI does not invoke a paid agent model.

## What this report does not prove

No comparative model-quality improvement, guaranteed automatic triggering, universal host support,
complete confidentiality detection, or prompt-injection resistance is claimed. Before trusting
ongoing updates, run a small non-sensitive task in your own host, inspect the first consent question,
approve the exact scope, and inspect the resulting skill and its fresh-case validation.
