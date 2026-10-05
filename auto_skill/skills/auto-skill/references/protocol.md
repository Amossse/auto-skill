# Local protocol v1

Run from the installed workspace root. Use the Python command configured during installation.
Replace `<controller>` with `.agents/skills/auto-skill/scripts/auto_skill.py` (Codex/generic)
or `.claude/skills/auto-skill/scripts/auto_skill.py` (Claude).

```sh
python3 <controller> --workspace . status
python3 <controller> --workspace . assess --event .auto-skill/event.json
# Only after the human has approved creation AND ongoing same-scope local updates:
python3 <controller> --workspace . consent --name summarize-interviews --decision approve
python3 <controller> --workspace . save --recipe .auto-skill/recipe.json
python3 <controller> --workspace . consent --name summarize-interviews --decision pause
python3 <controller> --workspace . rollback --name summarize-interviews --revision 1
```

## Event

All shown keys are required, additional keys are rejected. `schema_version` is integer 1;
`outcome` is success/failure/unknown; `verified` is a boolean; `lessons` has at most 20 items.
Identifiers use ASCII letters/digits/underscore/hyphen, at most 80 characters.
Skill names use lowercase letters/digits and single hyphens, at most 64 characters;
`auto-skill` is reserved. `scope` is stable human-readable text defining permitted reuse.
Text fields are bounded at 2,000 characters. No raw transcripts, absolute personal paths or secrets.

```json
{
  "schema_version": 1,
  "session_id": "demo-session",
  "milestone_id": "interview-1",
  "skill_name": "summarize-interviews",
  "scope": "Summarize anonymized interview notes using only supplied evidence.",
  "task": "Summarize three supplied fictional interviews.",
  "outcome": "success",
  "verified": true,
  "lessons": [{
    "kind": "correction",
    "finding": "Keep participant observations separate from analyst interpretations.",
    "evidence": "The revised summary linked every observation to a supplied excerpt."
  }]
}
```

`kind` is correction/procedure/preference. Evidence must report actual observations. CLI privacy
screening is best-effort; it does not recognize all personal or internal information.
Events pending consent are minimal local summaries, not full conversations. Keep `scope` identical
when updating; any change triggers fresh consent. Assessment is idempotent after an event is saved;
before consent it asks once per topic/scope, including across sessions in this workspace.

## Full recipe

All shown keys are required. Arrays contain nonempty strings, at most 30 items each;
`steps` and `checks` cannot be empty. `description` is at most 1,024 characters and specifies
when to use the skill. `lesson_indices` points into the current event's lessons.
`validation.passed` must be true. These are host-reported records, not independently measured scores.

```json
{
  "schema_version": 1,
  "skill_name": "summarize-interviews",
  "description": "Summarizes supplied interview notes with source-linked observations. Use when synthesizing anonymized interviews.",
  "scope": "Summarize anonymized interview notes using only supplied evidence.",
  "steps": ["Identify supplied excerpt IDs.", "Group observations and cite their excerpt IDs.", "Label analyst interpretations separately."],
  "checks": ["Every observation has a supplied excerpt ID.", "No invented participant facts."],
  "pitfalls": ["Do not present an interpretation as a direct observation."],
  "lesson_indices": [0],
  "validation": {
    "case": "Fresh fictional excerpt I4: Participant prefers shorter setup.",
    "expected": "Source-linked observation; no invented motivation.",
    "actual": "Observation: shorter setup preferred [I4]. Motivation: not established.",
    "passed": true
  }
}
```

For updates submit the **full merged recipe**, not just a new lesson. Earlier event/recipe pairs remain
in local version history. Rendered files have name/description frontmatter and procedure, checks,
pitfalls, current evidence, validation record, and permission boundary.

## State and recovery

Local consent, pending events and deduplication: `.auto-skill/state.json`.
Version snapshots: `.auto-skill/history/<name>/<revision>.json`.
Managed skills: the installed Agent's skill root. Claude and Codex installs share consent/history.
Atomic file replacement, an exclusive workspace lock and a recovery journal protect writes.
If a process crashes, confirm it is no longer running before removing its stale `.auto-skill/.lock`;
then run `recover`. Recovery undoes an interrupted transaction; it does not complete it.
Reassess/resave afterward. Do not delete the transaction journal before recovery.

All commands emit JSON, exit 0 on success and 2 on controlled errors. No input contents are echoed
on error. `skip`, `pending_consent` and successful installation are not claims of a distilled skill.
