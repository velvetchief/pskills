# Voice checklist (example)

This file shows the format. The rows are made-up examples. Your real checklist is built by the sent-diff-miner skill from your own edits, and every row there shows a real pair.

The checklist is guidance, not a lock. The owner can break any rule.
A rule needs at least 2 real pairs. Status is proposed or approved. Only approved rules are used.

| # | Rule | Seen in | Before (bot) | After (owner) | Status |
|---|------|---------|--------------|---------------|--------|
| 1 | Cut the explanation tail. Stop after the point. | 2 pairs | "We moved the launch. That's why the page looks different." | "We moved the launch." | approved |
| 2 | No soft check-in opener. Start with the ask. | 2 pairs | "Just wanted to check in on the contract." | "Is the contract ready to sign?" | approved |
| 3 | Do not announce. Say the thing. | 2 pairs | "Excited to share our new site." | "Our new site is live." | approved |

## Gate rules

Only approved rules with a clear word pattern go here. The gate reads this block.
Format: `block: <regex> | <reason>` or `warn: <regex> | <reason>`. Put a space on each side of the bar that comes before the reason.

```gate
block: \bjust wanted to (?:check in|follow up|reach out)\b | soft opener the owner always cuts (rule 2)
warn: \bexcited to (?:share|announce)\b | the owner usually cuts this (rule 3)
```
