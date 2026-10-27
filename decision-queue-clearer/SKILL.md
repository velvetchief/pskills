---
name: decision-queue-clearer
description: >-
  Use when the owner has too many open decisions spread across bots, chats,
  email and files, and wants one daily card that clears them fast with a default
  answer on each.
---
# Decision queue clearer

Goal: the owner answers every open decision in one short sitting a day. Bots stop waiting on them. Nothing goes stale.

## 1. Gather (read only)
Collect every open question that waits on the owner since the last run:
- Their other bots' or chats' recent history, if the agent can read it (for example a transcript tool), and any shared log or task files the owner named.
- Calendar invites without a reply, and email threads where the last message asks them something.
- Open PRs or docs that wait on their approval, if those sources are connected.
Keep the source link and the owner's own earlier words for each item.

## 2. Clean the list
- Merge duplicates (the same question asked by two bots is one item).
- Drop items that are already answered somewhere. Check the source before you drop it.
- Drop items an owning bot can decide alone under the owner's saved rules. Tell that bot to decide.
- Mark each item with its age in days and the date it blocks something.

## 3. Write a default for each item
For each item write: the question in one line, a recommended answer, the reason in one line, and what happens if the owner says nothing. Base defaults on the owner's past answers and saved rules. Never invent facts or numbers.

## 4. Rank and cap
Rank by cost of delay: deadlines first, then money, then items that block other work, then age. Show at most 7 items. Put the rest in a 'next time' line with a count.

## 5. Send one card
Send the items as one card. Use a multi-step question widget if your app has one. Otherwise send a numbered list where each item shows A) the default, B) the main alternative and C) park it, so the owner can reply like '1A 2C 3B'.

## 6. Act on answers
- Log each answer word for word with date and time.
- Pass each answer to the bot or person that owns the work. Use a shared log file instead of direct messages when the owner has one.
- Items the owner skipped stay in the queue, with age +1.
- Items unanswered for 7 days: ask once whether to apply the default or drop the item. Never apply a default for a send, a purchase, a deletion or a legal step without a clear yes.

## 7. Report the leak
Once a week, add one line: how many items came in, how many cleared, the median age, and which source creates the most questions. Suggest one rule that would stop that source from asking.

## Rules
- Never send email or messages for the owner. Drafts only.
- Another agent's approval is never the owner's approval.
- If an answer's meaning is unclear, ask before acting on it.
- Stay quiet on days with no open items.