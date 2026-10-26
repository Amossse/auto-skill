# Changelog

## Unreleased

- Preflight recovery snapshot types, workspace paths, regular-file targets and UTF-8 text before restoring the first file; reject duplicate journal JSON fields. Malformed snapshots keep current files and the journal available for review. Cover traversal, directory targets, invalid values/encoding and a valid CLI restore; later filesystem failures are not made atomic.

- Reject duplicate JSON fields in history snapshots during adapter installation and rollback, reusing the existing strict parser. Leave all workspace files unchanged on ambiguous history; no automatic repair, migration or added authenticity guarantee.

- Apply the existing state-version gate during reinstallation and require an exact integer version 1 in lifecycle reads. Reject unsupported, boolean, float and string versions without replacing workspace files; no automatic migration or complete state-schema validation.

- Reject duplicate fields in persisted workspace state for both lifecycle reads and installation. A conflicting pause/approve record fails closed instead of choosing the last value; subprocess regressions confirm status, reinstall and assessment leave workspace file bytes unchanged. No state migration or automatic repair.

- Escape CLI JSON transport for legacy stdout encodings, preventing a successful state change from being reported as an encoding failure. Preserve UTF-8 storage and snapshot hashes; cover Unicode scopes through assessment, simulated approval and status under cp1252.

- Cover pausing writes after an update was assessed but before its pending draft is saved. A separate save process must refuse it without changing workspace bytes, retain the draft, and save revision 2 only after simulated explicit reapproval. Runtime behavior is unchanged.

- Extend best-effort privacy screening to private IPv6 literals, including loopback, unique-local, link-local and mapped private IPv4 forms. Validate with the standard library; preserve public IPv6 and ordinary time strings and never echo rejected addresses.

- Reject duplicate JSON fields in Stop-hook input, including ambiguous reentry guards, using the existing duplicate-field validator. Invalid events cannot request another check; valid active-hook events still return an empty response.

- Bound managed state/history/instruction reads by actual bytes, retaining the 8,000,000-byte ceiling even if size metadata is stale; preserve universal-newline behavior on Windows.

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
