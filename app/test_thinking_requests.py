"""Tests for asking providers for visible thinking (genius_client): which request field each
model gets, that an unticked "Show thinking" box sends none, and that what comes back is
routed to the thinking channel and, for Claude, returned intact on a tool round. No network."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import genius_client
from genius_client import _ThoughtTagSplitter, anthropic_thinking_config, gemini_thinking_extra

GEMINI = "https://generativelanguage.googleapis.com/v1beta/openai"


class FakeResponse:
    def __init__(self, events):
        self.lines = iter([("data: " + (e if isinstance(e, str) else json.dumps(e)) + "\n\n").encode("utf-8") for e in events])

    def __iter__(self):
        return self.lines

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class WhichFieldEachModelGets(unittest.TestCase):
    def test_claude_config_by_generation(self):
        adaptive = {"type": "adaptive", "display": "summarized"}
        budget = {"type": "enabled", "budget_tokens": genius_client.ANTHROPIC_THINKING_BUDGET}
        for model, want in [
            ("claude-opus-5-5", adaptive), ("claude-sonnet-5-5", adaptive), ("claude-haiku-5-5", adaptive),
            ("claude-sonnet-5", adaptive), ("claude-opus-4-8", adaptive), ("claude-opus-4-7", adaptive),
            ("claude-fable-5-1", adaptive), ("claude-mythos-5-1", adaptive),
            ("claude-opus-4-6", {"type": "adaptive"}), ("claude-sonnet-4-6", {"type": "adaptive"}),
            ("claude-haiku-4-5", budget), ("claude-sonnet-4-5", budget), ("claude-opus-4-1", budget),
            ("claude-sonnet-4-20250514", budget), ("claude-opus-4-5-20251101", budget), ("claude-3-7-sonnet-latest", budget),
            ("claude-3-5-sonnet-latest", None), ("claude-3-5-haiku-latest", None), ("claude-3-opus-latest", None), ("", None),
        ]:
            self.assertEqual(anthropic_thinking_config({}, model), want, model)

    def test_gemini_extra_only_for_thinking_gemini_models_on_googles_endpoint(self):
        want = {"google": {"thinking_config": {"include_thoughts": True}}}
        self.assertEqual(gemini_thinking_extra({}, "gemini-3.8-flash", GEMINI), want)
        self.assertEqual(gemini_thinking_extra({}, "models/gemini-2.5-pro", GEMINI), want)
        self.assertIsNone(gemini_thinking_extra({}, "gemini-2.0-flash", GEMINI))
        self.assertIsNone(gemini_thinking_extra({}, "gemma-4-31b-it", GEMINI))
        self.assertIsNone(gemini_thinking_extra({}, "gemini-3.8-flash", "https://my-proxy.example/v1"))
        self.assertIsNone(gemini_thinking_extra({}, "grok-4.6", "https://api.x.ai/v1"))

    def test_show_thinking_off_asks_for_nothing(self):
        off = {"show_thinking": False}
        self.assertIsNone(anthropic_thinking_config(off, "claude-opus-5-5"))
        self.assertIsNone(gemini_thinking_extra(off, "gemini-3.8-flash", GEMINI))


class ThoughtTags(unittest.TestCase):
    def run_chunks(self, chunks):
        sp, answer, think = _ThoughtTagSplitter(), "", ""
        for c in chunks + [None]:
            a, t = sp.flush() if c is None else sp.feed(c)
            answer, think = answer + a, think + t
        return answer, think

    def test_splits_whatever_the_chunking(self):
        text = "<thought>plan the mix</thought>Here is the answer. <thought>more</thought>Done."
        want = ("Here is the answer. Done.", "plan the mixmore")
        self.assertEqual(self.run_chunks([text]), want)
        self.assertEqual(self.run_chunks(list(text)), want)                       # every tag split across chunks
        self.assertEqual(self.run_chunks([text[:5], text[5:27], text[27:]]), want)

    def test_text_that_only_looks_like_a_tag_is_kept(self):
        self.assertEqual(self.run_chunks(["a < b and <though", "tful> stays, x <t"]), ("a < b and <thoughtful> stays, x <t", ""))
        self.assertEqual(self.run_chunks(["no tags at all"]), ("no tags at all", ""))

    def test_an_unpaired_tag_is_dropped_not_shown(self):
        for chunks in (["</thought>On it."], ["</thou", "ght></thought>On it."], list("</thought></thought>On it.")):
            self.assertEqual(self.run_chunks(chunks), ("On it.", ""))
        self.assertEqual(self.run_chunks(["<thought>a<thought>b</thought>c"]), ("c", "ab"))


class GeminiStream(unittest.TestCase):
    def stream(self, deltas):
        events = [{"choices": [{"delta": d}]} for d in deltas] + ["[DONE]"]
        think, said = [], []
        with patch("urllib.request.urlopen", return_value=FakeResponse(events)):
            content, calls = genius_client._stream_round(GEMINI + "/chat/completions", "k", {"model": "gemini-3.8-flash", "messages": []},
                                                         on_thinking=think.append, on_content=said.append)
        return content, calls, "".join(think), "".join(said)

    def test_flagged_thought_chunks_go_to_thinking_not_the_answer(self):
        content, calls, think, said = self.stream([
            {"content": "Weighing options.", "extra_content": {"google": {"thought": True}}},
            {"content": "Use a high-pass."},
        ])
        self.assertEqual((content, think, said, calls), ("Use a high-pass.", "Weighing options.", "Use a high-pass.", []))

    def test_a_flagged_thought_closed_in_plain_content_leaves_no_tag_anywhere(self):
        content, calls, think, said = self.stream([
            {"content": "<thought>Read the track", "extra_content": {"google": {"thought": True}}},
            {"content": " first.", "extra_content": {"google": {"thought": True}}},
            {"content": "</thought>"},
            {"tool_calls": [{"index": 0, "id": "c1", "function": {"name": "live_read_track", "arguments": "{}"}}]},
        ])
        self.assertEqual((content, think, said), ("", "Read the track first.", ""))
        self.assertEqual(calls[0]["name"], "live_read_track")

    def test_tagged_thoughts_go_to_thinking_and_a_tool_call_keeps_its_own_signature(self):
        content, calls, think, said = self.stream([
            {"content": "<thought>Check the"}, {"content": " set first.</thou"}, {"content": "ght>On it."},
            {"content": "x", "extra_content": {"google": {"thought": True}}},
            {"tool_calls": [{"index": 0, "id": "c1", "function": {"name": "live_connect", "arguments": "{}"},
                             "extra_content": {"google": {"thought_signature": "sig1"}}}]},
        ])
        self.assertEqual((content, think, said), ("On it.", "Check the set first.x", "On it."))
        self.assertEqual(calls[0]["extra_content"], {"google": {"thought_signature": "sig1"}})

    def test_the_request_carries_the_field_and_a_refusal_is_retried_without_it(self):
        sent = []

        def fake_stream(endpoint, api_key, payload, **kwargs):
            sent.append(dict(payload))
            if "extra_body" in payload:
                raise RuntimeError("API 400: Unknown name \"extra_body\"")
            return "ok", []

        settings = {"api_key": "k", "api_base": GEMINI, "model": "gemini-3.8-flash"}
        with patch.object(genius_client, "_stream_round", side_effect=fake_stream):
            self.assertEqual(genius_client._ask_genius_openai(settings, [{"role": "user", "content": "hi"}], "unknown"), "ok")
        self.assertEqual(sent[0]["extra_body"], {"google": {"thinking_config": {"include_thoughts": True}}})
        self.assertNotIn("extra_body", sent[1])
        sent.clear()
        with patch.object(genius_client, "_stream_round", side_effect=lambda e, k, p, **kw: (sent.append(dict(p)), ("ok", []))[1]):
            genius_client._ask_genius_openai(dict(settings, show_thinking=False), [{"role": "user", "content": "hi"}], "unknown")
            genius_client._ask_genius_openai(dict(settings, model="grok-4.6", api_base="https://api.x.ai/v1"), [{"role": "user", "content": "hi"}], "unknown")
        self.assertTrue(all("extra_body" not in p for p in sent))


class ClaudeStream(unittest.TestCase):
    EVENTS = [
        {"type": "content_block_start", "index": 0, "content_block": {"type": "thinking", "thinking": "", "signature": ""}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "Need the "}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "track list."}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "signature_delta", "signature": "SIG=="}},
        {"type": "content_block_start", "index": 1, "content_block": {"type": "redacted_thinking", "data": "OPAQUE"}},
        {"type": "content_block_start", "index": 2, "content_block": {"type": "text", "text": ""}},
        {"type": "content_block_delta", "index": 2, "delta": {"type": "text_delta", "text": "Looking."}},
        {"type": "content_block_start", "index": 3, "content_block": {"type": "tool_use", "id": "tu1", "name": "live_connect", "input": {}}},
        {"type": "content_block_delta", "index": 3, "delta": {"type": "input_json_delta", "partial_json": "{\"a\":"}},
        {"type": "content_block_delta", "index": 3, "delta": {"type": "input_json_delta", "partial_json": " 1}"}},
        {"type": "message_stop"},
    ]
    BLOCKS = [
        {"type": "thinking", "thinking": "Need the track list.", "signature": "SIG=="},
        {"type": "redacted_thinking", "data": "OPAQUE"},
        {"type": "text", "text": "Looking."},
        {"type": "tool_use", "id": "tu1", "name": "live_connect", "input": {"a": 1}},
    ]

    def test_stream_returns_the_blocks_to_send_back(self):
        think, blocks = [], []
        with patch("urllib.request.urlopen", return_value=FakeResponse(self.EVENTS)):
            content, calls = genius_client._stream_round_anthropic("https://api.anthropic.com/v1/messages", "k", {}, on_thinking=think.append, out_blocks=blocks)
        self.assertEqual((content, "".join(think)), ("Looking.", "Need the track list."))
        self.assertEqual(calls, [{"type": "function_call", "call_id": "tu1", "name": "live_connect", "arguments": "{\"a\": 1}"}])
        self.assertEqual(blocks, self.BLOCKS)

    def ask(self, settings, rounds):
        """Run one ask; `rounds` are per-round (blocks, content, tool_calls). Returns the payloads sent."""
        sent, state = [], {"n": 0}

        def fake_stream(endpoint, api_key, payload, **kwargs):
            sent.append(json.loads(json.dumps(payload)))
            blocks, content, calls = rounds[min(state["n"], len(rounds) - 1)]
            state["n"] += 1
            if "out_blocks" in kwargs:
                kwargs["out_blocks"].extend(blocks)
            return content, calls

        with patch.object(genius_client, "_stream_round_anthropic", side_effect=fake_stream), \
             patch.object(genius_client, "call_live_tool", return_value="connected"):
            reply = genius_client._ask_genius_anthropic(settings, [{"role": "user", "content": "hi"}], "unknown")
        return reply, sent

    TOOL_ROUND = (BLOCKS, "Looking.", [{"call_id": "tu1", "name": "live_connect", "arguments": "{\"a\": 1}"}])

    def test_tool_round_sends_the_thinking_blocks_back_unchanged(self):
        settings = {"api_key": "sk-ant-x", "model": "claude-opus-5-5"}
        reply, sent = self.ask(settings, [self.TOOL_ROUND, ([], "All set.", [])])
        self.assertEqual(reply, "All set.")
        self.assertEqual(sent[0]["thinking"], {"type": "adaptive", "display": "summarized"})
        self.assertEqual(sent[0]["max_tokens"], 4096)
        self.assertEqual(sent[1]["messages"][1], {"role": "assistant", "content": self.BLOCKS})
        self.assertEqual(sent[1]["messages"][2]["content"][0], {"type": "tool_result", "tool_use_id": "tu1", "content": "connected"})

    def test_budget_models_get_room_for_the_budget(self):
        _, sent = self.ask({"api_key": "sk-ant-x", "model": "claude-haiku-4-5"}, [([], "ok", [])])
        self.assertEqual(sent[0]["thinking"], {"type": "enabled", "budget_tokens": genius_client.ANTHROPIC_THINKING_BUDGET})
        self.assertEqual(sent[0]["max_tokens"], 4096 + genius_client.ANTHROPIC_THINKING_BUDGET)

    def test_show_thinking_off_or_an_older_model_sends_the_request_as_before(self):
        for settings in ({"api_key": "sk-ant-x", "model": "claude-opus-5-5", "show_thinking": False},
                         {"api_key": "sk-ant-x", "model": "claude-3-5-sonnet-latest"}):
            reply, sent = self.ask(settings, [self.TOOL_ROUND, ([], "All set.", [])])
            self.assertNotIn("thinking", sent[0])
            self.assertNotIn("tool_choice", sent[0])
            self.assertEqual(sent[0]["max_tokens"], 4096)
            self.assertEqual([b["type"] for b in sent[1]["messages"][1]["content"]], ["text", "tool_use"])

    def test_final_round_turns_tools_off_without_removing_them_when_thinking(self):
        settings = {"api_key": "sk-ant-x", "model": "claude-opus-5-5"}
        with patch.object(genius_client, "MAX_TOOL_LOOPS", 2):
            sent, state = [], {"n": 0}

            def fake_stream(endpoint, api_key, payload, **kwargs):
                sent.append(json.loads(json.dumps(payload)))
                state["n"] += 1
                if payload.get("tool_choice") == {"type": "none"}:
                    return "Summary.", []
                kwargs["out_blocks"].extend(self.BLOCKS)
                return self.TOOL_ROUND[1], self.TOOL_ROUND[2]

            with patch.object(genius_client, "_stream_round_anthropic", side_effect=fake_stream), \
                 patch.object(genius_client, "call_live_tool", return_value="connected"):
                self.assertEqual(genius_client._ask_genius_anthropic(settings, [{"role": "user", "content": "hi"}], "unknown"), "Summary.")
        self.assertEqual(sent[-1]["tool_choice"], {"type": "none"})
        self.assertEqual(sent[-1]["tools"], sent[0]["tools"])

    def test_a_refused_thinking_field_is_retried_without_it(self):
        sent = []

        def fake_stream(endpoint, api_key, payload, **kwargs):
            sent.append(json.loads(json.dumps(payload)))
            if "thinking" in payload:
                raise RuntimeError("Anthropic API 400: thinking: Extra inputs are not permitted")
            return "ok", []

        with patch.object(genius_client, "_stream_round_anthropic", side_effect=fake_stream):
            reply = genius_client._ask_genius_anthropic({"api_key": "sk-ant-x", "model": "claude-opus-5-5"}, [{"role": "user", "content": "hi"}], "unknown")
        self.assertEqual(reply, "ok")
        self.assertEqual(("thinking" in sent[0], "thinking" in sent[1], sent[1]["max_tokens"]), (True, False, 4096))


if __name__ == "__main__":
    unittest.main()
