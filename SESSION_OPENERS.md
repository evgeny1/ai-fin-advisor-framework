# Session Openers — copy-paste templates by session type

**Why this file exists:** project instructions keep getting skipped because
there's no forcing function at the start of a session telling Claude where
to look. Each template below front-loads the specific files/checks that
session type needs, before any actual work starts. Paste the relevant block
as your first message in a new conversation.

`session_type` values for `advisor_write_back()` / your own notes, kept
consistent across sessions: `"full M05 session"`, `"coding"`,
`"re-evaluation"`, `"audit"`, `"ad-hoc"`.

---

## 1. Advisory session (normal)

Already lives in `Project_Instructions_MCP.md` under "Session opening
message format" — not duplicated here. Use that one as-is:

```
Advisory session, [DATE]. FULL_DESKTOP.

[Optional: paste hand-off block, or "check §8 for open items"]
[Optional: priority focus for this session]

Execute the full M05 SessionStartSequence now through Step 8 (briefing). Do not stop between steps.
```

---

## 2. Coding session (python/advisor/ or M0X module files)

```
Coding session, [DATE]. Working on python/advisor/ [or: M0X_*.md module files].

Before writing or editing anything:
1. Read README.md in full (repo root) — not from memory of a prior session.
2. Run the codebase-memory-mcp freshness check (README §14):
   git rev-parse HEAD on the real repo, compare to the ADR's commit marker
   (manage_adr mode=get). If stale or missing: delete_project → index_repository
   → get_architecture → redraft the ADR with the new HEAD commit. Don't proceed
   on a cached graph.
3. State which layer this touches (README §1): Layer 1 spec (.md modules),
   Layer 2 calibration data (Calibration_State.md), or Layer 3 Python — before
   writing anything.

Task: [describe the change]

If this changes mcp_server.py's tool name, parameters, or return shape:
update Project_Instructions_MCP.md in the same change (README §9 — explicitly
non-negotiable, ENG-1 is the precedent for why). Run the full test suite
before and after. If editing a module .md file, run
`python tools/validate_manifests.py` afterward.
```

---

## 3. Re-evaluation session (single instrument or role, ad-hoc trigger)

```
Re-evaluation session, [DATE]. Target: [role or ticker].

Before any new analysis:
1. Pull the FULL current §4.1 row for this role from Calibration_State.md —
   all six scenarios, current value, confidence tag, and
   ADOPTED / PENDING / never-reviewed status for each. Display it before
   doing anything else.
2. State explicitly which scenarios this session will review and which it
   will leave untouched, and why — not silently. (This is the rule that
   would have caught BMED's stale C value before it drove a hypothetical
   answer nobody had reason to trust — see Calibration_State.md §3,
   2026-06-29 entries, for the actual incident.)
3. Any cell you revise needs all 4 M16 layers (L1 anchor, L2 analogs, L3
   stress test, L4 cross-consistency at the neutral distribution) — even if
   you're reusing analogs already verified for a neighboring scenario.
   M16 is AI-judgment-only (README §2) — no MCP tool runs this for you.

Adoption: HIGH confidence + my explicit confirmation = same-session adoption,
written via Desktop Commander + git (never advisor_write_back — that tool
never touches Calibration_State.md, by design). MEDIUM or LOW confidence =
log to §6 with a [P0]/[P1]/[P2] tag and a concrete next step, not just
"pending." Never adopt only the convenient half of a split finding.

Trigger / question: [what prompted this review]
```

---

## 4. Audit session (scheduled, comprehensive)

```
Audit session, [DATE]. Q[N] audit.

1. Pull Calibration_State.md §6 in full, sorted by priority tag — [P0] items
   first, then [P1], then [P2].
2. For each item: check §3's log for whether a re-evaluation already
   happened this quarter before re-doing the work from scratch.
3. Same adoption rules as any re-evaluation session (above): HIGH confidence
   + confirmation adopts now; MEDIUM/LOW logs to §6 with a tag and a next
   step.
4. Close out items that are now fully resolved — don't leave a stale [P0]
   sitting in §6 after its actual fix already landed and was committed.
```

---

*If a session teaches you something this file should have said, add it —
same rule README.md applies to itself.*
