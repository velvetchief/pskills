---
name: presend-gate
description: >-
  Use before you show the owner any draft for X, email, LinkedIn, or anything
  else that will go out under their name. Runs the bundled presend_gate.py
  against the owner's approved voice checklist and confirmed facts file. Exit
  1 means fix the draft before the owner sees it.
---
# Presend gate

Every draft passes this gate before the owner sees it. The gate is a script, so it gives the same answer every time.

## Setup (once)

1. Download the gate and its tests into the voice folder the owner picked (for example `voice/`):
   ```
   cd voice
   curl -fsSLO https://raw.githubusercontent.com/velvetchief/pskills/main/sent-diff-voice-gate/presend-gate/presend_gate.py
   curl -fsSLO https://raw.githubusercontent.com/velvetchief/pskills/main/sent-diff-voice-gate/presend-gate/test_presend_gate.py
   curl -fsSLO https://raw.githubusercontent.com/velvetchief/pskills/main/sent-diff-voice-gate/presend-gate/gate-config.example.json
   curl -fsSLO https://raw.githubusercontent.com/velvetchief/pskills/main/sent-diff-voice-gate/presend-gate/owner-facts.example.md
   curl -fsSLO https://raw.githubusercontent.com/velvetchief/pskills/main/sent-diff-voice-gate/presend-gate/voice-checklist.example.md
   ```
   Note: these URLs work once the pull request that adds this folder is merged into main.
2. Write `gate-config.json` from the example: `cp gate-config.example.json gate-config.json`. Set `checklist`, `facts` and `log` (paths are relative to the config file). Put the owner's confirmed number claims in `claims`, and the about-me facts to rate-limit in `about_me_facts`.
3. If `owner-facts.md` and `voice-checklist.md` do not exist yet, start them from the example files.
4. Run `python3 test_presend_gate.py`. All tests must pass. Python 3 standard library only.

Files:
- `presend_gate.py`: the gate.
- `test_presend_gate.py`: the gate's own tests. It needs the 3 example files next to it.
- `gate-config.example.json`, `owner-facts.example.md`, `voice-checklist.example.md`, `gate-tests.example.json`: formats.

## Steps

1. Write the draft. Read `voice-checklist.md` first and follow the approved rules.
2. Save it to a file. For a pack of options, put a line with only `---` between drafts. **At most 3 drafts per pack.** Put the plainest option first.
3. Run:
   `python3 presend_gate.py DRAFT --channel x|email|linkedin|generic --config <voice folder>/gate-config.json`
   - For a pack: `--pack PACK` instead of `DRAFT`.
   - For a reply or quote: add `--kind reply` (or `quote`) and `--reply-checked "where you looked, time window, last message each way"`. Read what the owner already sent in that thread first.
   - Insiders (the owner's own team): add `--audience insider`. Deadline and pressure lines then pass.
   - Dry run: add `--no-log`.
4. Read the result.
   - Exit 0: pass. Warnings may print. Fix them if it is easy.
   - Exit 1: blocked. Fix every FAIL line and run again. Do not show a blocked draft.
   - Exit 2: input problem (no config, empty draft, bad rule). Fix the input.
5. Show the owner only drafts that passed. If you skipped a rule with `--allow RULE`, tell the owner which rule and why.

## What it checks

Blocks:
- **Facts**: a number claim about the owner (years, team size, any claim set in the config) that is not in the confirmed facts file or does not match it. A years claim no rule covers also blocks.
- **About-me repeat**: the same about-me fact in a 3rd draft inside 48 hours. Pick another angle.
- **Pack size**: more than 3 drafts in one pack.
- **Banned hooks**: "Everyone's..." and "Skip the X." openers, plus hooks in the config.
- Em dashes, hashtags, "not X, it's Y" and "that's why" tails, unfilled placeholders, passwords and keys, "I built" claims, deadline lines to outsiders, internal ticket codes in email and LinkedIn, "link in reply" on X, slop phrases, and `block:` lines in the checklist's gate block.
- A reply or quote without `--reply-checked`.

Warns only: signpost lines ("here's the thing"), 3 sentences in a row of the same length or with the same first word, congrats-only replies on X, and `warn:` lines in the checklist.

The about-me log is written only when every draft in the run passes.

## Rules
- No draft reaches the owner without a pass. No exceptions for "quick" replies.
- Facts about the owner come only from the facts file the owner confirmed. If a fact is missing, ask. Do not guess, round, or use a range.
- `--allow` is for a rule that is wrong for this one draft. Name it to the owner. If you skip the same rule often, propose a checklist change instead.
- The gate does not send anything. Sending stays with the owner.
