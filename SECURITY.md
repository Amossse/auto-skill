# Security and privacy

## Boundaries

- The CLI only reads explicitly named JSON files and managed workspace files. It never discovers raw
  conversation archives, reads environment credentials, calls a model/network API, executes generated
  skill instructions, or publishes anything.
- The host agent reasons over its authorized active task context. Its model/provider can still receive
  that context; respect that provider's data controls. This project does not make a cloud agent offline.
- Initial consent must explicitly cover creation and ongoing local updates within a named scope.
  Source documents, embedded prompts, CLI examples and reported successes are not human consent.
  The CLI is a local protocol, not an authentication mechanism: a process with filesystem access can
  invoke `consent` or edit state. The host remains responsible for truthful authorization and evidence.
- Any new scripts, network access, credential use, cross-workspace access or publication require
  separate user authority. Generated skills confer no such permissions.

## External inputs

Event/recipe JSON uses an exact schema and a 256 KB limit. Skill names cannot contain path separators,
uppercase letters, consecutive hyphens, or traversal. Schemas bound text lengths and list sizes.
Diagnostics do not echo invalid source content. Common secret tokens, private keys, private IPs,
internal-style endpoint suffixes, personal machine paths and email addresses are rejected.

This filter is deliberately **best-effort**. It cannot identify every internal domain, proprietary
procedure, personal name, financial/health record or obfuscated credential. It has no bypass flag.
Generalize private observations or omit them. Review the complete files and Git staging before public
sharing. Toolkit installation does not authorize uploading any current or future experience.

An input can pass schema/privacy checks and still contain malicious instructions. The host must
treat external material as data, extract only task-relevant verified lessons, reject privilege changes,
and review the proposed procedure. The CLI is not a prompt-injection detector or a semantic validator.
`validation.passed` is a host attestation; it is not independent proof that a command ran or a result is correct.

## Filesystem writes

An explicit existing workspace is the boundary. Managed paths reject symlink components and `..`.
Unmanaged skill files and manually edited managed files are not overwritten. Installer-owned files
also carry recorded hashes so reinstallation refuses hand edits. Workspace instruction updates replace
only the auto-skill marker section. Claude hook settings are opt-in and other keys are preserved.

Transactions use a local journal, an exclusive lock and atomic file replacements. Recover interrupted
writes before continuing. If a process is killed, its stale lock is not automatically removed; first
confirm that no writer is running. Recovery restores pre-write state. Local history/drafts are not
encrypted. Anyone with OS access to the workspace can read them.

Path checks are **not an OS sandbox** and cannot prevent all filesystem race attacks by another local
process. Do not expose this CLI as an untrusted multi-user service, or share writable state between
different trust domains. Protect local state and the installed controller using OS permissions.

State/history/drafts/hook settings and generated skill folders are added to `.gitignore` by default.
Ignore rules are not access control; `git add -f` and already-tracked files bypass them. Review staged
files and commit history. Publishing commands are intentionally outside auto-skill.

## Claude hook

The optional Stop hook reads bounded JSON on stdin, uses only event metadata, never opens
`transcript_path`, and does not store or forward `last_assistant_message`. It skips a stop-hook
continuation, nested agents and background work to avoid recursive prompting. Model evaluation still
happens in the host. The hook command invokes a local trusted Python file; install only reviewed releases.

## Reporting

Use the repository's private security reporting on GitHub if available. Otherwise open an issue with
a **sanitized description only** and ask for a private reporting channel. Never include a live token,
real conversation history, internal endpoint, proprietary asset or personal data in an issue/PR.
