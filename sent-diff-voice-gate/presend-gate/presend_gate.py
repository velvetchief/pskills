#!/usr/bin/env python3
"""presend_gate.py: the check every draft passes before the owner sees it.

Usage
  presend_gate.py DRAFT --channel x|email|linkedin|generic [options]
  presend_gate.py --pack PACK --channel ...      PACK = one file with drafts split by a line "---", or a folder
  presend_gate.py --run-tests gate-tests.json    replay mined before/after pairs
  DRAFT may be "-" for stdin.

Options
  --config PATH        Config JSON (default: $PRESEND_GATE_CONFIG, else ./gate-config.json).
                       Paths inside it are relative to the config file.
  --kind post|reply|quote
                       reply and quote need --reply-checked "where you looked, window, last message each way".
  --audience outsider|insider   Default outsider. Deadline and pressure lines block only for outsiders.
  --allow RULE         Skip one rule on purpose. It is printed in the result. Say why to the owner.
  --no-log             Do not write the about-me log (dry runs, tests). The log is still read.
  --now ISO            Fixed clock (tests).

Exit codes: 0 = pass (warnings may print), 1 = blocked, 2 = input problem.
Only the Python standard library is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

CHANNELS = ["x", "email", "linkedin", "generic"]
DEFAULTS = {
    "checklist": "voice-checklist.md",
    "facts": "owner-facts.md",
    "log": "gate-log.jsonl",
    "pack_max": 3,
    "about_me_window_hours": 48,
    "about_me_max_uses": 2,
    "about_me_facts": {},
    "claims": [],
    "unknown_years_blocks": True,
    "banned_hooks": [],
    "banned_phrases": [],
    "disable": [],
}
APOS = r"['\u2019]"

# ---------------------------------------------------------------- built-in rules
EM_DASH = re.compile(r"[\u2014\u2015]|\s\u2013\s|\s--\s")
HASHTAG = re.compile(r"(?<![\w&/#])#[A-Za-z][A-Za-z0-9_]*")
NOT_X = [
    (re.compile(r"\b(?:isn" + APOS + r"?t|is not|aren" + APOS + r"?t|are not|wasn" + APOS + r"?t|was not)\b[^.!?\n]{1,80}[.,;:]\s*(?:it" + APOS + r"?s|it is|they" + APOS + r"?re|they are|that" + APOS + r"?s)\b", re.I),
     "'not X, it's Y' contrast"),
    (re.compile(r"\bnot (?:just |only |about |really )?[^.,;!?\n]{1,50}[,;]\s*(?:it" + APOS + r"?s|it is|but)\b", re.I),
     "'not X, it's Y' contrast"),
    (re.compile(r",\s*not (?!sure\b|yet\b|really\b|now\b|always\b|that\b)[a-z][^.,;!?\n]{0,40}(?:[.!]|$)", re.I | re.M),
     "'X, not Y' tail"),
    (re.compile(r"\b(?:that|this)" + APOS + r"?s why\b|\b(?:that|this) is why\b|\bwhich is why\b", re.I),
     "'that's why' tail"),
]
PLACEHOLDER = [
    re.compile(r"\[(?=[^\]\n]*[A-Z]{2,})[^\]\n]{1,60}\](?!\()"),
    re.compile(r"\{\{?\s*[A-Za-z_][\w .-]{0,30}\}\}?"),
    re.compile(r"(?<![A-Za-z])(?:TODO|TBD|TBC|FIXME|XXX|TK)(?![A-Za-z])"),
    re.compile(r"<\s*(?:first ?name|name|company|date|day|time|link|url|title|role)\s*>", re.I),
    re.compile(r"\blorem ipsum\b", re.I),
]
SECRET = [
    (re.compile(r"\b(?:password|passcode|passwd|pwd)\b\s*(?:[:=]|is\b)\s*\S+", re.I), "password in plain text"),
    (re.compile(r"\b(?:api[_ -]?key|secret|access[_ -]?token|auth[_ -]?token|bearer)\b\s*[:=]\s*\S{6,}", re.I), "secret or token"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}"), "GitHub token"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b|\bxox[abprs]-[A-Za-z0-9-]{10,}"), "API key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
]
SELF_CLAIM = re.compile(r"\b(?:i|i" + APOS + r"?ve|i have|we|we" + APOS + r"?ve)\s+(?:built|created)\b(?!\s+(?:relationships?|a relationship|trust|rapport))|\bapp i built\b", re.I)
DEADLINE = [
    re.compile(r"\bby (?:this |next )?(?:mon|tues|wednes|thurs|fri|satur|sun)day\b", re.I),
    re.compile(r"\bby (?:the )?(?:end of (?:the )?(?:day|week|month)|eod|eow|cob|tomorrow|tonight|next week|this week)\b", re.I),
    re.compile(r"\bby (?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.? \d{1,2}\b", re.I),
    re.compile(r"\bby \d{1,2}/\d{1,2}\b", re.I),
    re.compile(r"\bideally by\b|\bthat would be ideal\b|\bif you can manage it\b|\bno later than\b", re.I),
    re.compile(r"\bat your earliest convenience\b|\basap\b|\btime[- ]sensitive\b|\burgent(?:ly)?\b|\bdeadline\b", re.I),
]
TASK_CODE = re.compile(r"\bPR ?#\d+\b|(?<![\w-])#\d{2,4}\b|\b[A-Z]{2,6}-\d{1,5}\b")
LINK_IN_REPLY = [
    re.compile(r"\blinks? (?:is |are )?(?:in|below|in the) (?:the )?(?:first )?(?:reply|replies|comments?|thread)\b", re.I),
    re.compile(r"\blink below\b|\blinks? in (?:the )?(?:first )?comment\b", re.I),
    re.compile(r"\b(?:x|twitter|the algorithm)\b[^.\n]{0,40}\b(?:penali[sz]es|punishes|buries|throttles|deboosts)\b[^.\n]{0,20}\blinks?\b", re.I),
]
LEAD_HANDLES = re.compile(r"^(?:@\w+\s+)+")
EVERYONE_OPENER = re.compile(r"^\s*(?:everyone|everybody)(?:" + APOS + r"?s| is| keeps| wants| thinks| says| talks)\b", re.I)
SKIP_OPENER = re.compile(r"^\s*(?:skip|forget|ignore) the [\w -]{1,30}[.!]", re.I)
DEFAULT_SLOP = [
    (r"\bthe (?:one |only |real )?specs? that matters?\b", "'the spec that matters' line"),
    (r"\bthe future is (?:here|now)\b", "'the future is here' line"),
    (r"\bgame[- ]chang(?:er|ing)\b", "'game changer'"),
    (r"\bin today" + APOS + r"?s (?:fast[- ]paced )?world\b", "'in today's world' opener"),
    (r"\blet" + APOS + r"?s dive in\b|\bdelve\b", "'dive in' or 'delve'"),
]
SIGNPOST = re.compile(r"\bhere(?:" + APOS + r"?s| is) the thing\b|\bbottom line\b|\bto sum (?:it )?up\b|\bthe (?:key |main |big )?takeaways?\b", re.I)
CONGRATS_ONLY = re.compile(r"^\s*(?:congrats|congratulations|well done|well earned|so real|makes (?:so much )?sense|love this|great (?:post|read))\b[^.!?]{0,40}[.!]*\s*$", re.I)
BULLET_LINE = re.compile(r"^\s*(?:[-*\u2022>]|\d{1,2}[.)])\s+")
WORD = re.compile(r"[A-Za-z0-9$@][\w'\u2019$%.,@-]*")
FIRST_PERSON = re.compile(r"\b(?:i|i" + APOS + r"?ve|i have|i" + APOS + r"?m|my|me|we|our|we" + APOS + r"?ve)\b", re.I)
NUM_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen twenty".split())}
NUM = r"(\d{1,3}|" + "|".join(NUM_WORDS) + r")"
YEARS = re.compile(r"\b" + NUM + r"(?:\s*(?:-|to|\u2013)\s*(\d{1,2}))?\s*\+?\s*(?:years?|yrs?)\b", re.I)
GATE_BLOCK = re.compile(r"^```gate\s*\n(.*?)^```", re.M | re.S)


# ---------------------------------------------------------------- loading
def load_config(path: str | None) -> dict:
    path = path or os.environ.get("PRESEND_GATE_CONFIG") or "gate-config.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"config not found: {path}. Copy gate-config.example.json and set the paths")
    with open(path, encoding="utf-8") as f:
        cfg = {**DEFAULTS, **json.load(f)}
    base = os.path.dirname(os.path.abspath(path))
    for k in ("checklist", "facts", "log"):
        if cfg.get(k) and not os.path.isabs(cfg[k]):
            cfg[k] = os.path.join(base, cfg[k])
    return cfg


def load_facts(path: str) -> dict:
    """KEY: value lines (upper-case keys) anywhere in the facts file."""
    facts = {}
    try:
        for line in open(path, encoding="utf-8"):
            m = re.match(r"^\s*([A-Z][A-Z0-9_]+):\s*(.+?)\s*$", line)
            if m:
                facts[m.group(1)] = m.group(2)
    except OSError:
        pass
    return facts


def load_checklist_rules(path: str) -> list[tuple[str, re.Pattern, str]]:
    """Rules inside ```gate blocks of the checklist. One per line:
       block: <regex> | <reason>      or      warn: <regex> | <reason>"""
    rules = []
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return rules
    for block in GATE_BLOCK.findall(text):
        for line in block.splitlines():
            m = re.match(r"^\s*(block|warn)\s*:\s*(.+)$", line)
            if not m or " | " not in m.group(2):
                continue
            pattern, reason = (x.strip() for x in m.group(2).rsplit(" | ", 1))
            try:
                rules.append((m.group(1), re.compile(pattern, re.I), reason))
            except re.error as e:
                raise ValueError(f"bad gate rule in {path}: '{pattern}' ({e})")
    return rules


def read_log(path: str) -> list[dict]:
    out = []
    try:
        for line in open(path, encoding="utf-8"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    except OSError:
        pass
    return out


def _ts(s: str) -> datetime:
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _num(tok: str) -> int:
    return int(tok) if tok.isdigit() else NUM_WORDS[tok.lower()]


def sentences(text: str):
    for s in re.split(r"(?<=[.!?])\s+|\n+", text):
        if s.strip():
            yield s


def opener_sentences(text: str):
    for para in re.split(r"\n\s*\n", text):
        para = LEAD_HANDLES.sub("", para.strip(), count=1).lstrip()
        if para:
            yield next(iter(re.split(r"(?<=[.!?])\s+|\n", para)), para)


# ---------------------------------------------------------------- checks
def check_claims(text: str, cfg: dict, facts: dict, fails: list) -> None:
    """Number claims about the owner must match the confirmed facts file."""
    for s in sentences(text):
        if not FIRST_PERSON.search(s):
            continue
        spans = []
        for c in cfg["claims"]:
            for m in re.finditer(c["pattern"], s, re.I):
                spans.append((m.start(), m.end()))
                key = c["fact"]
                want = facts.get(key)
                if want is None:
                    fails.append(("facts", f"'{m.group(0)}' ({c['name']}): {key} is not in the facts file. Ask the owner, do not guess"))
                    continue
                got = m.group(1) if m.groups() else m.group(0)
                try:
                    ok = _num(got) == int(want)
                except (ValueError, KeyError):
                    ok = got.strip().lower() == want.strip().lower()
                if not ok:
                    fails.append(("facts", f"'{m.group(0)}' ({c['name']}) differs from the facts file ({key}: {want})"))
        if not cfg.get("unknown_years_blocks"):
            continue
        for m in YEARS.finditer(s):
            if any(a < m.end() and m.start() < b for a, b in spans):
                continue
            if m.group(2):
                fails.append(("facts", f"'{m.group(0)}' is a range of years. Use the exact line from the facts file"))
            else:
                fails.append(("facts", f"'{m.group(0)}' is a years claim that no facts-file rule covers. Use a confirmed fact or cut it"))


def about_me_in(text: str, cfg: dict) -> list[str]:
    return [k for k, rx in cfg["about_me_facts"].items() if re.search(rx, text, re.I)]


def check_about_me_repeat(text, sha, log, now, cfg, fails) -> list[str]:
    found = about_me_in(text, cfg)
    cutoff = now - timedelta(hours=cfg["about_me_window_hours"])
    for key in found:
        prior = {r.get("sha") for r in log
                 if r.get("fact") == key and r.get("sha") != sha
                 and _ts(r.get("ts", "1970-01-01T00:00:00+00:00")) >= cutoff}
        if len(prior) >= cfg["about_me_max_uses"]:
            fails.append(("about-me-repeat", f"about-me fact '{key}' is already in {len(prior)} drafts from the last "
                                             f"{cfg['about_me_window_hours']} h. Pick another angle"))
    return found


def check_rhythm(body: str, warns: list) -> None:
    blocks, cur = [], []
    for line in body.splitlines():
        line = line.strip()
        if not line or BULLET_LINE.match(line) or len(line.split()) < 2:
            if cur:
                blocks.append(cur)
                cur = []
            continue
        for sent in re.split(r"(?<=[.!?])[\"\u201d')]*\s+", line):
            words = WORD.findall(sent)
            if len(words) < 3:
                if cur:
                    blocks.append(cur)
                    cur = []
                continue
            cur.append(words)
    if cur:
        blocks.append(cur)
    seen = set()
    for block in blocks:
        for i in range(len(block) - 2):
            run = block[i:i + 3]
            lens = [len(w) for w in run]
            if "rhythm-length" not in seen and max(lens) - min(lens) <= 2:
                seen.add("rhythm-length")
                warns.append(("rhythm-length", f"3 sentences in a row of about the same length ({', '.join(map(str, lens))} words). Vary them"))
            if "rhythm-opener" not in seen and len({re.sub(r"\W", "", w[0]).lower() for w in run}) == 1:
                seen.add("rhythm-opener")
                warns.append(("rhythm-opener", f"3 sentences in a row start with '{run[0][0]}'. Vary the openings"))


def lint(text: str, channel: str, audience: str, cfg: dict, facts: dict, rules: list) -> tuple[list, list]:
    fails, warns = [], []
    body = re.sub(r"https?://\S+", " URL ", text)
    if EM_DASH.search(body):
        fails.append(("em-dash", "em dash or spaced dash: use a comma, a full stop or a new line"))
    for m in HASHTAG.finditer(body):
        fails.append(("hashtag", f"hashtag '{m.group(0)}'"))
    for rx, why in NOT_X:
        for m in rx.finditer(body):
            fails.append(("not-x", f"{why}: '{m.group(0).strip()}'. Put the main point first and cut the contrast"))
    for rx in PLACEHOLDER:
        for m in rx.finditer(body):
            fails.append(("placeholder", f"unfilled placeholder '{m.group(0)}': fill it or cut the line"))
    for rx, why in SECRET:
        if rx.search(text):
            fails.append(("secret", f"{why}: never put it in a draft (value hidden)"))
    for m in SELF_CLAIM.finditer(body):
        fails.append(("self-claim", f"'{m.group(0)}': lead with their world, not what you built"))
    if audience == "outsider":
        for rx in DEADLINE:
            for m in rx.finditer(body):
                fails.append(("deadline", f"deadline or pressure line to an outsider: '{m.group(0)}'"))
    if channel in ("email", "linkedin"):
        for m in TASK_CODE.finditer(body):
            fails.append(("task-code", f"internal code '{m.group(0)}': the reader does not know it. Say what it is"))
    if channel == "x":
        for rx in LINK_IN_REPLY:
            for m in rx.finditer(text):
                fails.append(("link-in-reply", f"'{m.group(0)}': put the link in the main post"))
        lines = [l for l in body.splitlines() if l.strip()]
        if lines and len(lines) <= 2 and CONGRATS_ONLY.match(" ".join(lines)):
            warns.append(("low-signal", "agreement or congrats only. Send it only if it carries one real thing"))
    hooks = [(re.compile(h, re.I), "banned hook") for h in cfg["banned_hooks"]]
    for first in opener_sentences(body):
        if EVERYONE_OPENER.match(first):
            fails.append(("banned-hook", f"'Everyone's...' setup opener: '{first[:60]}'. Start with the fact or the take"))
        if SKIP_OPENER.match(first):
            fails.append(("banned-hook", f"'Skip the X.' opener: '{first[:60]}'. Start with the fact or the take"))
        for rx, why in hooks:
            if rx.search(first):
                fails.append(("banned-hook", f"{why}: '{first[:60]}'"))
    slop = [(re.compile(p, re.I), w) for p, w in DEFAULT_SLOP] + [(re.compile(p, re.I), "banned phrase") for p in cfg["banned_phrases"]]
    for rx, why in slop:
        for m in rx.finditer(body):
            fails.append(("slop-phrase", f"{why}: '{m.group(0)}'. Cut it"))
    for kind, rx, why in rules:
        for m in rx.finditer(body):
            (fails if kind == "block" else warns).append(("checklist", f"{why}: '{m.group(0)}'"))
    for m in SIGNPOST.finditer(body):
        warns.append(("signpost", f"'{m.group(0)}': make the point instead of announcing it"))
    check_rhythm(body, warns)
    check_claims(body, cfg, facts, fails)
    return fails, warns


def check_one(text, a, cfg, facts, rules, log, now):
    fails, warns = lint(text, a.channel, a.audience, cfg, facts, rules)
    if a.kind in ("reply", "quote") and not a.reply_checked:
        fails.append(("reply-check", "reply or quote: read what the owner already sent there, then pass --reply-checked "
                                     "'where, window, last message each way'"))
    sha = hashlib.sha256(re.sub(r"\s+", " ", text.strip()).encode()).hexdigest()[:16]
    found = check_about_me_repeat(text, sha, log, now, cfg, fails)
    skip = set(a.allow or []) | set(cfg["disable"])
    fails = [f for f in fails if f[0] not in skip]
    warns = [w for w in warns if w[0] not in skip]
    return fails, warns, found, sha


def split_pack(path: str) -> list[tuple[str, str]]:
    if os.path.isdir(path):
        return [(os.path.join(path, f), open(os.path.join(path, f), encoding="utf-8").read())
                for f in sorted(os.listdir(path)) if os.path.isfile(os.path.join(path, f)) and not f.startswith(".")]
    raw = open(path, encoding="utf-8").read()
    parts = [p.strip() for p in re.split(r"^\s*---+\s*$", raw, flags=re.M)]
    return [(f"{path}#{i+1}", p) for i, p in enumerate(parts) if p]


def report(label, fails, warns, allow) -> None:
    print(f"== {label}")
    for code, why in fails:
        print(f"FAIL [{code}] {why}")
    for code, why in warns:
        print(f"WARN [{code}] {why}")
    if allow:
        print(f"NOTE rules skipped on purpose: {', '.join(sorted(allow))}")
    print("PASS" if not fails else f"BLOCKED: {len(fails)} problem(s). Fix them before the owner sees this draft")


def run_tests(path: str, a, cfg, facts, rules, now) -> int:
    """Replay mined pairs. 'after' (what the owner sent) must pass.
    'before' must be blocked when expect_before is 'block'."""
    cases = json.load(open(path, encoding="utf-8"))
    bad = 0
    for c in cases:
        a.channel = c.get("channel", "generic")
        a.kind = c.get("kind", "post")
        a.reply_checked = "test"
        a.audience = c.get("audience", "outsider")
        a.allow = c.get("allow", [])
        fa, _, _, _ = check_one(c["after"], a, cfg, facts, rules, [], now)
        ok = not fa
        if c.get("expect_before") == "block":
            fb, _, _, _ = check_one(c["before"], a, cfg, facts, rules, [], now)
            ok = ok and bool(fb)
        print(f"{'ok  ' if ok else 'FAIL'} {c.get('id', '?')} ({c.get('rule', '')})")
        if not ok:
            bad += 1
            for code, why in fa:
                print(f"     after blocked: [{code}] {why}")
    print(f"{len(cases) - bad} of {len(cases)} cases pass")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", nargs="?")
    ap.add_argument("--pack")
    ap.add_argument("--run-tests")
    ap.add_argument("--channel", choices=CHANNELS, default=None)
    ap.add_argument("--kind", choices=["post", "reply", "quote"], default="post")
    ap.add_argument("--audience", choices=["outsider", "insider"], default="outsider")
    ap.add_argument("--reply-checked")
    ap.add_argument("--allow", action="append", default=[])
    ap.add_argument("--config")
    ap.add_argument("--no-log", action="store_true")
    ap.add_argument("--now")
    a = ap.parse_args(argv)
    try:
        cfg = load_config(a.config)
        now = _ts(a.now) if a.now else datetime.now(timezone.utc)
        facts = load_facts(cfg["facts"])
        rules = load_checklist_rules(cfg["checklist"])
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if not facts:
        print(f"WARN [facts] no KEY: value lines found in {cfg['facts']}. Claims about the owner will all block")
    if a.run_tests:
        return run_tests(a.run_tests, a, cfg, facts, rules, now)
    if not a.channel:
        print("ERROR: --channel is required", file=sys.stderr)
        return 2
    if bool(a.draft) == bool(a.pack):
        print("ERROR: give one DRAFT or --pack", file=sys.stderr)
        return 2
    try:
        if a.pack:
            drafts = split_pack(a.pack)
        else:
            text = sys.stdin.read() if a.draft == "-" else open(a.draft, encoding="utf-8").read()
            drafts = [(a.draft, text)]
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if not any(t.strip() for _, t in drafts):
        print("ERROR: empty draft", file=sys.stderr)
        return 2
    if a.pack and len(drafts) > cfg["pack_max"]:
        print(f"== pack {a.pack}")
        print(f"FAIL [pack-size] {len(drafts)} drafts in one pack. Max is {cfg['pack_max']}. Keep the best, plain option first")
        print("BLOCKED")
        return 1
    log = read_log(cfg["log"])
    any_fail, new_log = False, []
    for label, text in drafts:
        fails, warns, found, sha = check_one(text, a, cfg, facts, rules, log + new_log, now)
        report(label, fails, warns, set(a.allow))
        if fails:
            any_fail = True
        else:
            new_log += [{"ts": now.isoformat(), "fact": k, "sha": sha, "channel": a.channel} for k in found]
    if new_log and not a.no_log and not any_fail:
        os.makedirs(os.path.dirname(cfg["log"]) or ".", exist_ok=True)
        with open(cfg["log"], "a", encoding="utf-8") as f:
            for r in new_log:
                f.write(json.dumps(r) + "\n")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
