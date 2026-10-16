# Changelog

## Unreleased

- Verify the current history snapshot's content hash before installation can synchronize managed skills; a mismatch leaves existing mirrors and state unchanged.

- Reject unpaired Unicode surrogates during event/recipe validation, before hashing or lifecycle writes; normal Unicode remains supported.

- Bound actual event/recipe reads to the input budget plus one byte instead of trusting file-size metadata; growing files cannot bypass the size check.
- Add a regression with stale size metadata while retaining strict UTF-8 decoding and duplicate-field rejection.

- Reject duplicate JSON fields in event and recipe inputs, including nested validation fields, rather than silently accepting the last value.
- Add negative regressions for ambiguous verification and validation records; consent and state formats are unchanged.

## 0.1.1 — 2026-10-06

- Fix offline demo output on Windows legacy console encodings; add a cp1252 regression test.
- Preserve v0.1.0 as published; recommend the corrected v0.1.1 tag for installation.

## 0.1.0 — 2026-10-06

- Portable experience-distillation controller with verified milestone criteria and fresh-case validation.
- Workspace-scoped Codex/Claude installers; generic instruction adapter and optional Claude Stop hook.
- First human consent, same-scope ongoing iteration, persistent decline/pause, and fresh consent for scope changes.
- Version snapshots, rollback, deduplication, manual-edit protection and interrupted-write recovery.
- Bounded structured inputs, best-effort privacy filter and ignored generated experience folders.
- English/Chinese documentation, synthetic lifecycle demo, tests and validation report.
