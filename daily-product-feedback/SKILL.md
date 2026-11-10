---
name: daily-product-feedback
description: Use when you want your bot to collect product bugs during the day, queue them, and ask in the end-of-day update whether to send a report to the product team. You press Send. The bot does not send the report.
---

# Daily product feedback

## When to use

Use this skill to set up a daily product feedback loop for your bot.

The bot logs product bugs as they appear during the day. It keeps them in a queue file. The end-of-day update shows new items and asks if you want them sent to the feedback contact. If you say yes, the bot drafts the report on an email card from your inbox. You press Send. The bot does not send the message.

## What counts as a product bug

Log a product bug when a product tool, card, attachment, routine, or message delivery fails, and you have evidence of the failure.

Each entry must have:

- The date and local time
- What happened
- An impact line that states what the failure cost (extra steps, a missed message, delay, or lost work)
- Evidence, such as a chat line, a tool error, or a file. If the exact error text was not saved, say so.

Leave these out of the report:

- Account usage limits, when a run stopped because no usage was left
- Failures in other products, or in repo CI
- Operator mistakes that were already corrected, such as a wrong field name
- Missing features that are not product failures
- Items already sent, or already reported

## Queue file format

Keep a queue file, for example at `<workspace>/bug-queue.md`.

Use dated sections. A pending section follows this shape:

```
## Pending for the end-of-day update YYYY-MM-DD (shown to the user, awaiting their OK)
1. YYYY-MM-DD ~HH:MM local: what happened. Impact: the cost of the failure. Evidence: the source.
- Left out: the skipped item and why
```

When a report has been sent, move the items into a Sent section:

```
## Sent YYYY-MM-DD HH:MM local
Items from the pending list were sent to <feedback contact> from <your inbox>. The user pressed Send.
```

Keep a dated record of what was already reported, for example `<workspace>/bug-reported-YYYY-MM-DD.md`, so later runs can skip those items.

## Collect bugs during the day

When you see a product failure, append it to the queue the same day. Do not wait for the end-of-day routine.

Before you add an item, read the queue and the reported files. If the same failure was already reported, leave it out and note it as a repeat.

## Daily routine

Schedule the end-of-day update for 5:14 PM local.

Paste the prompt below into that routine. This is a reusable prompt for the observed end-of-day flow. It is not a copy of a live saved routine prompt.

### Routine prompt

```
End-of-day product feedback. Run at 5:14 PM local.

1. Read the bug queue file and any bug-reported files.
2. Scan today's work for new product failures: tool errors, failed cards, failed attachments, failed routines, and failed message delivery. Add any new item to the queue in the format in this skill, with local time, what happened, an impact line, and evidence.
3. Skip items already in a Sent section or in a bug-reported file. Skip usage limits, other-product or repo CI failures, self-fixed operator mistakes, and missing features. Note what you left out and why.
4. In the end-of-day update, add a Product bugs section.
   If there are new pending items, list each one with its impact line. Then ask, in these words: "Do you want me to send this to <feedback contact>?"
   If there are no new product bugs, say so, or leave the section out.
5. Do not draft or send a report until the user says yes.
6. If the user says yes, draft the report on an email card from <your inbox> to <feedback contact>. Put the pending items in the body, each with local time, what happened, and impact. Do not add private names, private addresses, or project details the user did not approve. Then stop. The user presses Send.
7. After the user sends the message, confirm it in the Sent folder. Move the items to a Sent section in the queue, and copy them into a bug-reported file for that day. Clear the pending list.
```

## Ask first, and the user presses Send

Never send the report yourself. Ask first, in the end-of-day update, next to the Product bugs list.

If the user says yes, draft the email card and wait. The user presses Send.

If the user says no, or does not answer, leave the items pending in the queue. Do not send them.

After a send, open the Sent folder and confirm that the message went out. If you cannot confirm it, mark the item unconfirmed. Do not call it sent.

## Deduplicate

Before you show or draft a report, check the Sent sections in the queue and the bug-reported files.

Do not send the same bug again. A later occurrence of the same failure can be noted as a repeat. It does not go out unless the user asks to send an update.

## Example entry

The block below is example data. It is a sanitized copy of a real queue entry, and it is here only to show the format.

```
## Pending for the end-of-day update 2026-11-09 (shown to the user, awaiting their OK)
1. 2026-11-09 ~9:09 AM local: an image attachment from one bot to another did not go through. The sending bot gave a file path instead. Impact: one extra step to view the image. Evidence: the bot's own message. The tool error text was not seen.
```
