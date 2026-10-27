---
name: sent-diff-miner
description: >-
  Use when the owner wants their drafts to sound like them, after they edit or
  rewrite a bot draft before sending, or when the weekly re-mine runs. Pairs
  each bot draft with what the owner actually sent, classifies every edit, and
  turns repeated edits into checklist rules and test cases.
---
# Sent-diff miner

Goal: learn the owner's voice from what they changed, not from what they say they like. Each repeated edit becomes one rule in `voice-checklist.md`. Each pair becomes one test case in `gate-tests.json`.

Files live in the voice folder the owner picked at setup (for example `voice/`):
- `voice-checklist.md`: the rules. Format: see `voice-checklist.example.md` in the presend-gate skill.
- `gate-tests.json`: one case per pair. Format: see `gate-tests.example.json`.
- `pairs.jsonl`: the raw pairs, one per line, so the next run can skip them.
- `owner-facts.md`: the facts the owner confirmed. Read only. This skill never adds facts.

## Steps

1. **Collect drafts.** Find every draft the bot showed the owner in the window (default: since the last run, or the last 14 days on the first run). Sources: the bot's own chat history and draft files, and any draft folder the owner named. Keep the draft text, the channel (x, email, linkedin, generic), and the time.

2. **Collect what was sent.** Read only. Do not send, post, like or reply.
   - Email: the owner's Sent folder for the same window.
   - X: the owner's own posts and replies for the same window.
   - Pasted: if the owner pastes "draft" and "sent" text, use that pair as is.
   - Any other channel the owner named at setup.

3. **Match pairs.** Match each sent item to the draft it came from. Use the recipient or thread, the time (sent within 72 hours after the draft), and word overlap. Keep a pair only when the match is clear. If two drafts could match, take the one with the most shared words. If you are not sure, leave it out and list it as "unmatched" in your report. Never pair a sent item with a draft that came after it.

4. **Classify each pair.**
   - `same`: sent word for word or close to it (only spacing, a name, or a typo changed).
   - `edited`: the owner changed the wording. Write down each edit as one short label, for example: cut the explanation tail, cut the opener, shorter sentences, removed a claim, changed a fact, plainer word, removed a hashtag, removed an em dash, softer ask, harder ask, added a detail only the owner knew.
   - `rewritten`: less than half of the words stayed. Note what the owner did instead.
   - `dropped`: the draft was never sent. Count it, but make no rule from it alone.

5. **Find patterns.** Group the edit labels across all pairs, old and new. A pattern needs **at least 2 real pairs**. With 1 pair, keep it in a "watch" list and do not make a rule.

6. **Write or update rules.** For each pattern with 2 or more pairs:
   - One rule per pattern. One short line that says what to do.
   - "Seen in": the count, for example "11 of 36 pairs".
   - Before and After: quote one real pair, word for word, from `pairs.jsonl`. **Never invent or tidy an example.** If a quote has private details, cut it to the part that shows the edit and mark the cut with "...".
   - Status: `proposed`. Only the owner can make a rule `approved`.
   - If the rule has a clear word pattern (a phrase, an opener, a punctuation mark), also write a proposed gate line, for example `block: \bjust wanted to\b | soft opener (rule 4)`. Add it to the `gate` block only after the owner approves the rule.
   - If a new pattern goes against an approved rule, do not change the rule. Show both to the owner.

7. **Write test cases.** Add one case per new pair to `gate-tests.json`: `id`, `rule`, `channel`, `source` (where it came from, no private links), `before`, `after`, and `expect_before`. Set `expect_before` to `block` only when an approved gate rule covers the edit. Otherwise set it to `none`.

8. **Check.** Run `python3 presend_gate.py --run-tests gate-tests.json --config <config>` from the presend-gate skill folder. Every `after` must pass, because the owner sent it. If an `after` is blocked, the gate is too strict: report the rule that blocked it and propose a fix. Do not change the owner's sent text.

9. **Report to the owner.** Keep it short:
   - Pairs found, how many `same`, `edited`, `rewritten`, `dropped`, `unmatched`.
   - The top 3 edits with counts.
   - Each new proposed rule with its real before and after. Ask: approve, change, or drop?
   - Test result: "N of N cases pass".

## Rules
- Read sent mail and posts only. Never send, post, reply, like, or move anything.
- No rule from fewer than 2 real pairs. No made-up examples. No made-up counts.
- New rules start as `proposed`. Never mark a rule `approved` yourself.
- Never add or change a fact in `owner-facts.md`. If a sent item shows a new fact, list it and ask the owner to confirm it.
- The checklist is guidance, not a lock. A rule the owner breaks on purpose is not a mistake.
