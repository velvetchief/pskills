#!/usr/bin/env python3
"""Tests for presend_gate.py. Neutral examples only. Run: python3 test_presend_gate.py"""
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

import presend_gate as g

HERE = os.path.dirname(os.path.abspath(__file__))
NOW = "2026-01-15T12:00:00+00:00"


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        for src, dst in (("gate-config.example.json", "gate-config.json"),
                         ("owner-facts.example.md", "owner-facts.md"),
                         ("voice-checklist.example.md", "voice-checklist.md")):
            shutil.copy(os.path.join(HERE, src), os.path.join(self.dir, dst))
        self.cfg = os.path.join(self.dir, "gate-config.json")
        self.log = os.path.join(self.dir, "gate-log.jsonl")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def run_gate(self, text, *args, channel="generic", no_log=True):
        p = os.path.join(self.dir, "draft.txt")
        open(p, "w", encoding="utf-8").write(text)
        argv = [p, "--channel", channel, "--config", self.cfg, "--now", NOW] + list(args)
        if no_log:
            argv.append("--no-log")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = g.main(argv)
        return code, out.getvalue()

    def ok(self, text, *a, **k):
        code, out = self.run_gate(text, *a, **k)
        self.assertEqual(code, 0, out)
        return out

    def blocked(self, text, rule, *a, **k):
        code, out = self.run_gate(text, *a, **k)
        self.assertEqual(code, 1, out)
        self.assertIn(f"[{rule}]", out)
        return out


class Pass(Base):
    def test_plain_post(self):
        self.ok("Shipped the new search today. It finds old notes in under a second.", channel="x")

    def test_plain_reply_with_check(self):
        self.ok("Good catch. Fixed in the next build.", "--kind", "reply", "--reply-checked", "thread, 7 days, none each way", channel="x")

    def test_short_email(self):
        self.ok("Hi Sam,\n\nThanks for the notes. I moved the call to Thursday at 3.\n\nBest,\nAlex", channel="email")

    def test_linkedin_plain(self):
        self.ok("We opened two roles on the data team. Both are remote.", channel="linkedin")

    def test_insider_deadline_ok(self):
        self.ok("Can you send the slides by Friday?", "--audience", "insider", channel="email")

    def test_confirmed_years_line(self):
        self.ok("I have 9 years in product and this is the first tool I use every day.")

    def test_confirmed_team_size(self):
        self.ok("Our team of 4 shipped it in a week.")

    def test_years_not_about_owner(self):
        self.ok("The bridge took 12 years to build.")

    def test_congrats_only_warns(self):
        out = self.ok("Congrats, well earned.", channel="x")
        self.assertIn("[low-signal]", out)

    def test_signpost_warns(self):
        out = self.ok("Here's the thing about search. Most people never use filters at all.")
        self.assertIn("[signpost]", out)

    def test_allow_skips_rule(self):
        out = self.ok("I built a small tool for this last year.", "--allow", "self-claim")
        self.assertIn("skipped on purpose", out)

    def test_everyone_mid_sentence_fine(self):
        self.ok("We asked and everyone wanted the old layout back.")

    def test_skip_mid_sentence_fine(self):
        self.ok("You can skip the intro and go to page two.")

    def test_link_in_main_post_fine(self):
        self.ok("Notes from the talk: https://example.com/notes", channel="x")

    def test_task_code_fine_on_x(self):
        self.ok("Fixed in PR #42.", channel="x")


class Fail(Base):
    def test_not_x_its_y(self):
        self.blocked("This isn't a chat app. It's a notebook that answers back.", "not-x")

    def test_x_not_y_tail(self):
        self.blocked("Ship the small version first, not the big plan.", "not-x")

    def test_thats_why(self):
        self.blocked("Search was slow. That's why we rebuilt it.", "not-x")

    def test_not_just_but(self):
        self.blocked("It is not just faster, but cheaper too.", "not-x")

    def test_em_dash(self):
        self.blocked("We shipped it \u2014 finally.", "em-dash")

    def test_spaced_double_dash(self):
        self.blocked("We shipped it -- finally.", "em-dash")

    def test_hashtag(self):
        self.blocked("New release out today #buildinpublic", "hashtag", channel="x")

    def test_placeholder_brackets(self):
        self.blocked("Hi [FIRST NAME], thanks for the call.", "placeholder", channel="email")

    def test_placeholder_curly_and_todo(self):
        out = self.blocked("Hi {name}, the date is TODO.", "placeholder", channel="email")
        self.assertGreaterEqual(out.count("[placeholder]"), 2)

    def test_placeholder_angle(self):
        self.blocked("Thanks <first name>, talk soon.", "placeholder", channel="email")

    def test_password(self):
        out = self.blocked("The login is ready. Password: hunter2", "secret", "--audience", "insider")
        self.assertNotIn("hunter2", out)

    def test_api_key(self):
        self.blocked("Use api_key=abcd1234efgh5678 for now.", "secret", "--audience", "insider")

    def test_self_claim(self):
        self.blocked("I built a tool that fixes this.", "self-claim")

    def test_deadline_to_outsider(self):
        self.blocked("Could you reply by Friday?", "deadline", channel="email")

    def test_ideally_by(self):
        self.blocked("Ideally by end of week, if possible.", "deadline", channel="email")

    def test_link_in_reply(self):
        self.blocked("Full write-up, link in the first reply.", "link-in-reply", channel="x")

    def test_task_code_email(self):
        self.blocked("Fixed in PR #42.", "task-code", channel="email")

    def test_ticket_code_linkedin(self):
        self.blocked("This closes OPS-118 for us.", "task-code", channel="linkedin")

    def test_reply_needs_check(self):
        self.blocked("Good catch, fixed.", "reply-check", "--kind", "reply", channel="x")

    def test_email_reply_needs_check(self):
        self.blocked("Thanks, see you then.", "reply-check", "--kind", "reply", channel="email")


class Facts(Base):
    def test_wrong_years(self):
        self.blocked("I have 12 years in product.", "facts")

    def test_word_number_years_wrong(self):
        self.blocked("After five years in product I still love it.", "facts")

    def test_years_range(self):
        self.blocked("I spent 8-10 years doing this.", "facts")

    def test_unknown_years_claim(self):
        self.blocked("I have 20 years of experience overall.", "facts")

    def test_wrong_team_size(self):
        self.blocked("Our team of 7 shipped it.", "facts")

    def test_missing_fact_key_blocks(self):
        path = os.path.join(self.dir, "owner-facts.md")
        open(path, "w").write("# Facts\n\nTEAM_SIZE: 4\n")
        self.blocked("I have 9 years in product.", "facts")

    def test_empty_facts_file_warns_and_blocks_claims(self):
        open(os.path.join(self.dir, "owner-facts.md"), "w").write("nothing confirmed yet\n")
        out = self.blocked("Our team of 4 shipped it.", "facts")
        self.assertIn("no KEY: value lines", out)


class Hooks(Base):
    def test_everyone_opener(self):
        self.blocked("Everyone's talking about agents. Most are demos.", "banned-hook", channel="x")

    def test_everybody_variant(self):
        self.blocked("Everybody wants a faster inbox. Here is mine.", "banned-hook", channel="x")

    def test_everyone_after_handles(self):
        self.blocked("@sam @lee Everyone's asking the same thing.", "banned-hook", channel="x")

    def test_everyone_later_paragraph(self):
        self.blocked("Small update.\n\nEveryone thinks this is hard. It is not that hard.", "banned-hook", channel="x")

    def test_skip_the_opener(self):
        self.blocked("Skip the hype. The tool saves an hour a day.", "banned-hook", channel="x")

    def test_config_banned_hook(self):
        self.blocked("Hot take: most dashboards go unread.", "banned-hook", channel="x")

    def test_default_slop(self):
        self.blocked("This is a game changer for small teams.", "slop-phrase")

    def test_config_banned_phrase(self):
        self.blocked("It will supercharge your mornings.", "slop-phrase")

    def test_checklist_block_rule(self):
        self.blocked("Just wanted to check in on the contract.", "checklist", channel="email")

    def test_checklist_warn_rule(self):
        out = self.ok("Excited to share our new site.", channel="linkedin")
        self.assertIn("[checklist]", out)

    def test_disable_in_config(self):
        cfg = json.load(open(self.cfg))
        cfg["disable"] = ["hashtag"]
        json.dump(cfg, open(self.cfg, "w"))
        self.ok("New release out today #release", channel="x")


class AboutMeRepeat(Base):
    TEXT = "After 9 years in product I still write specs by hand."

    def test_third_use_blocked(self):
        self.assertEqual(self.run_gate(self.TEXT, no_log=False)[0], 0)
        self.assertEqual(self.run_gate(self.TEXT + " Every week.", no_log=False)[0], 0)
        self.assertEqual(len(g.read_log(self.log)), 2)
        self.blocked(self.TEXT + " Still true.", "about-me-repeat")

    def test_same_draft_twice_not_counted(self):
        for _ in range(3):
            self.assertEqual(self.run_gate(self.TEXT, no_log=False)[0], 0)

    def test_old_uses_expire(self):
        old = "2026-01-10T12:00:00+00:00"
        with open(self.log, "w") as f:
            for sha in ("a", "b"):
                f.write(json.dumps({"ts": old, "fact": "career-years", "sha": sha}) + "\n")
        self.ok(self.TEXT)

    def test_no_log_writes_nothing(self):
        self.ok(self.TEXT)
        self.assertFalse(os.path.exists(self.log))

    def test_blocked_draft_not_logged(self):
        self.run_gate(self.TEXT + " #tips", no_log=False)
        self.assertFalse(os.path.exists(self.log))


class Pack(Base):
    def pack(self, n):
        p = os.path.join(self.dir, "pack.txt")
        open(p, "w").write("\n---\n".join(f"Option {i}: we moved the call to Thursday." for i in range(1, n + 1)))
        return p

    def run_pack(self, p):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = g.main(["--pack", p, "--channel", "email", "--config", self.cfg, "--now", NOW, "--no-log"])
        return code, out.getvalue()

    def test_pack_of_4_blocked(self):
        code, out = self.run_pack(self.pack(4))
        self.assertEqual(code, 1)
        self.assertIn("[pack-size]", out)

    def test_pack_of_3_passes(self):
        code, out = self.run_pack(self.pack(3))
        self.assertEqual(code, 0, out)
        self.assertEqual(out.count("PASS"), 3)

    def test_pack_folder(self):
        d = os.path.join(self.dir, "packdir")
        os.mkdir(d)
        for i in range(2):
            open(os.path.join(d, f"{i}.txt"), "w").write("We moved the call to Thursday.")
        code, _ = self.run_pack(d)
        self.assertEqual(code, 0)


class Inputs(Base):
    def test_missing_config_exit_2(self):
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(g.main(["x.txt", "--channel", "x", "--config", "/nonexistent/c.json"]), 2)

    def test_empty_draft_exit_2(self):
        self.assertEqual(self.run_gate("   \n")[0], 2)

    def test_no_channel_exit_2(self):
        p = os.path.join(self.dir, "d.txt")
        open(p, "w").write("hello there friend")
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(g.main([p, "--config", self.cfg]), 2)


class BadRule(Base):
    def test_bad_gate_regex_exit_2(self):
        p = os.path.join(self.dir, "voice-checklist.md")
        open(p, "w").write("```gate\nblock: (unclosed | broken rule\n```\n")
        self.assertEqual(self.run_gate("We moved the call.")[0], 2)


class GateTests(Base):
    def run_cases(self, cases):
        p = os.path.join(self.dir, "gate-tests.json")
        json.dump(cases, open(p, "w"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = g.main(["--run-tests", p, "--config", self.cfg, "--now", NOW])
        return code, out.getvalue()

    def test_mined_pairs_pass(self):
        code, out = self.run_cases([
            {"id": "p1", "rule": "cut the why tail", "channel": "x", "expect_before": "block",
             "before": "We moved the launch. That's why the page looks different.", "after": "We moved the launch."},
            {"id": "p2", "rule": "plain opener", "channel": "email", "expect_before": "none",
             "before": "Hope you are well. The draft is attached.", "after": "The draft is attached."}])
        self.assertEqual(code, 0, out)
        self.assertIn("2 of 2 cases pass", out)

    def test_after_that_blocks_fails_suite(self):
        code, out = self.run_cases([{"id": "p3", "rule": "x", "channel": "x", "before": "a b c", "after": "Big news #launch"}])
        self.assertEqual(code, 1)

    def test_before_must_block_when_expected(self):
        code, _ = self.run_cases([{"id": "p4", "rule": "x", "channel": "x", "expect_before": "block",
                                   "before": "We moved the launch.", "after": "We moved the launch."}])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
