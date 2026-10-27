# pskills

skills for running a business on agents. copy them into your own agent.

- [lead-bot](lead-bot/SKILL.md): the one bot you talk to. it turns requests into tasks, hands each to one worker bot, chases it, and sends a morning brief.
- [decision-queue-clearer](decision-queue-clearer/SKILL.md): each day it gathers every open question waiting on you, writes a default answer for each, and sends one short card you clear in a few minutes. works in any agent that can read files; the daily run needs a scheduled-task feature or a manual kick.
- [sent-diff-voice-gate](sent-diff-voice-gate/README.md): learns your voice from how you edit its drafts. each repeated edit becomes a rule and a test, and a script checks every new draft against your rules and confirmed facts before you see it.

## how to use

drop a SKILL.md into your agent's skills folder, or paste it into its instructions. edit it to fit your work.