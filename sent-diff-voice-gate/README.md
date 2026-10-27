# Sent-Diff Voice Gate

Your bot writes drafts. You fix them before you send. Most bots never learn from those fixes.

This template does. It compares each bot draft with what you actually sent. Each edit you repeat becomes one rule, with a real before and after. Each pair becomes a test case. Then a script checks every new draft against your rules and your confirmed facts before you see it.

## What you get

| Part | What it does |
|------|--------------|
| `sent-diff-getting-started` skill | First run. Asks where drafts and sent items live, mines the last 2 weeks, and shows the first checklist for you to approve. Then it turns on the gate. |
| `sent-diff-miner` skill | Pairs drafts with sent mail, X posts, or pasted pairs. Labels each edit. Proposes one rule per pattern seen in 2 or more real pairs. Writes `voice-checklist.md` and `gate-tests.json`. |
| `presend-gate` skill and `presend_gate.py` | Runs on every draft before you see it. Exit 1 blocks. Python standard library only. Comes with 68 tests. |

## What the gate blocks

- **Facts you did not confirm.** A number claim about you (years, team size, any claim you set) must match your facts file. A missing fact blocks. So does a range.
- **The same about-me fact in a 3rd draft inside 48 hours.**
- **Packs of more than 3 drafts.**
- **Banned hooks**, such as "Everyone's..." and "Skip the X." openers, plus any you add.
- Em dashes, hashtags, "not X, it's Y" tails, unfilled placeholders, passwords and keys, deadline lines to outsiders, internal ticket codes in email, "link in reply" on X, and the phrases your approved rules ban.

It warns, but does not block, on signpost lines and on flat sentence rhythm.

## How it differs from Presend

Presend (getpresend.com) is a browser extension that scores a draft against your sent mail and lets you add custom rules. Sent-Diff Voice Gate does three things it does not:

1. **It turns your edits into rules.** Each rule shows a real draft and what you sent, plus a count. You approve each rule.
2. **It turns pairs into tests.** Every pair goes into `gate-tests.json`. What you sent must always pass, so the gate cannot drift stricter than you are.
3. **It adds a facts gate.** Claims about you are checked against a facts file you signed off. The bot cannot round, guess, or reuse an old number.

It also runs inside your bot, on any channel (X, email, LinkedIn, or generic), not only in the browser.

## Proof

From one owner's 3-week review of real drafts against what was sent:
- 36 matched draft and sent pairs.
- 29 of 36 were changed before sending.
- The top edit, cutting the explanation tail or the "not X, it's Y" contrast, showed up in 11 of 36 pairs.

That top edit is now a built-in block in the gate.

## Setup

1. Copy the 3 skill folders into your agent's skills folder. The presend-gate skill downloads its script and tests on first run.
2. Start a chat and say "set up my voice gate". The getting-started skill asks 5 short questions.
3. Approve the first checklist. The gate turns on.

To check the gate itself: `cd presend-gate && python3 test_presend_gate.py`.

## Optional extras

Two standing rules are worth saving as memories: the checklist is guidance, not a lock, and facts about you come only from your confirmed facts file. A weekly re-mine on Monday mornings keeps the checklist fresh. It proposes rules and waits for your yes.

## Limits

- It needs at least 2 real pairs to make a rule. With few sent items, the first checklist is short.
- It reads sent mail and posts. It never sends, posts, or replies.
- The checklist is guidance, not a lock. You can break any rule.
