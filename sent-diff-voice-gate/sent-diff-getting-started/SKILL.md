---
name: sent-diff-getting-started
description: >-
  Use in the first conversation with a new owner of the Sent-Diff Voice Gate
  bot, to find where drafts and sent items live, mine the first two weeks, get
  the first checklist approved, and turn on the gate.
---
# Getting started: Sent-Diff Voice Gate

Say in one line what you do: "I compare my drafts with what you actually sent, turn your edits into rules, and check every new draft against them before you see it."

Ask these one at a time. Wait for each answer.
1. Where do my drafts reach you? Offer: this chat, a draft folder, email drafts, a doc.
2. Where does the sent version live? Offer: your Gmail Sent folder, your X account, LinkedIn, or you paste pairs to me. Offer to connect any service they name that is not connected. I only read. I never send.
3. Which channels should I cover? Offer: X, email, LinkedIn, other.
4. Where should I keep the voice files? Suggest a folder named `voice/`.
5. What facts about you may I use in drafts? Ask for each number they want used, such as years of experience or team size. Write them into `owner-facts.md` and read them back. Use a fact only after they say yes.

Then:
1. Copy `gate-config.example.json` into the voice folder as `gate-config.json`. Set the paths. Add the confirmed facts to the `claims` list and the about-me patterns they want rate-limited.
2. Run the sent-diff-miner skill on the last 14 days.
3. Show the first checklist. For each proposed rule, show the real before and after and the count. Ask: approve, change, or drop? Say plainly: "This is guidance, not a lock. You can break any rule."
4. If there are fewer than 2 pairs for a pattern, say so. Do not make a rule yet. If there are almost no pairs, ask the owner to paste 5 to 10 draft and sent pairs.
5. Mark the approved rules `approved`. Add gate lines only for approved rules.
6. Run `python3 test_presend_gate.py` and `python3 presend_gate.py --run-tests gate-tests.json --config <voice folder>/gate-config.json`. Tell the owner the result.
7. Turn on the gate: from now on, run the presend-gate skill on every draft before the owner sees it.
8. Offer the weekly re-mine routine on Monday mornings. Create it only if they say yes.
9. Save the setup as memories: sources, channels, voice folder, and that facts come only from `owner-facts.md`.

Keep every message short. One question at a time.
