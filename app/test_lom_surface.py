"""LOM truth-table check for the bridge JS.

Extracts every literal member name passed to ``.get("x")`` / ``.set("x")`` /
``.call("x")`` / ``.getcount("x")`` / ``palSetChecked(obj, "x", ...)`` in
``bridge/live-actions-pal.js`` and ``bridge/live-actions-bridge.js`` and fails
if a name exists on *no* class in ``lom_surface.json`` (the Live 12.3.6
runtime-introspected reference), or if a written name is read-only on every
class that has it.

Deliberately name-based, not path-resolved: the bridge builds LOM paths by
string concatenation, so resolving the owning class per call site is
unreliable. Name-existence is the weaker check, but it has no false-negative
risk from a path it could not resolve.

Every exception below needs a one-line justification. An exception that stops
being needed (the bridge no longer references it) also fails, so the lists
cannot rot into a silent blanket allowance.
"""
import re
import unittest
from pathlib import Path

import lom_reference

BRIDGE_DIR = Path(__file__).resolve().parent.parent / "bridge"
BRIDGE_FILES = ("live-actions-pal.js", "live-actions-bridge.js")

# Real members that are newer than the 12.3.6 reference the surface was built from.
VERSION_GAP = {
    "replace_sample": "SimplerDevice.replace_sample is Live 12.4+ (APP-DETAILS.txt); palAssignPadSample reports the failure honestly on older builds",
}

# Members kept on purpose behind a working primary call, or recorded defects
# awaiting the probe (docs/lom-capability-matrix.json) before any action is taken.
# v1.0.39 audit: recorded, NOT removed -- the probe settles absent vs
# absent-from-the-reference before a later pass acts (plan Part A3).
KNOWN_ABSENT = {
    "capture_scene": "fallback that only runs if capture_and_insert_scene throws (pal.js palCreateScene)",
    "fade_in_start": "live_set_clip_fades: not on Clip in 12.3.6 reference; audit finding, probe 4 decides",
    "fade_in_end": "live_set_clip_fades: not on Clip in 12.3.6 reference; audit finding, probe 4 decides",
    "fade_out_start": "live_set_clip_fades: not on Clip in 12.3.6 reference; audit finding, probe 4 decides",
    "fade_out_end": "live_set_clip_fades: not on Clip in 12.3.6 reference; audit finding, probe 4 decides",
    "follow_action_a": "live_set/get_clip_follow_action: not on Clip in 12.3.6 reference; audit finding, probe 4 decides",
    "follow_action_b": "live_set/get_clip_follow_action: not on Clip in 12.3.6 reference; audit finding, probe 4 decides",
    "follow_action_chance": "live_set/get_clip_follow_action: not on Clip in 12.3.6 reference; audit finding, probe 4 decides",
    "follow_action_enabled": "live_set/get_clip_follow_action: not on Clip in 12.3.6 reference; audit finding, probe 4 decides",
    "follow_action_time": "live_set/get_clip_follow_action: not on Clip in 12.3.6 reference; audit finding, probe 4 decides",
    "rename_macro": "palMapRackMagnitude: on no class; code already verifies by re-reading the macro name; probe 5 decides",
    "macro_map": "palMapRackMagnitude: on no class; code already admits no read-back can confirm it; probe 5 decides",
    "clear_range": "palSetClipAutomation: Envelope has delete_events_in_range, not clear_range -- audit finding, fix in a later pass after probe 3",
    "is_showing_on_surface": "palFocusView open_plugin_window: on no class in 12.3.6 reference; audit finding, later pass",
}

# Written names that the reference marks settable: false everywhere.
KNOWN_READONLY_WRITES = {
    "is_active": "palUpdateDevice device.set('is_active'): Device.is_active is read-only (the writable switch is the 'Device On' parameter) -- audit finding, later pass",
    "visible_macro_count": "palMapRackMagnitude: read-only; the code re-reads it and falls back to RackDevice.add_macro",
}

_LITERAL = r'"([A-Za-z_]\w*)"'
_CALL_RES = {
    "get": re.compile(r"\.get\(\s*" + _LITERAL),
    "set": re.compile(r"\.set\(\s*" + _LITERAL),
    "call": re.compile(r"\.call\(\s*" + _LITERAL),
    "getcount": re.compile(r"\.getcount\(\s*" + _LITERAL),
}
_SET_CHECKED_RE = re.compile(r"palSetChecked\(\s*[\w.]+\s*,\s*" + _LITERAL)


def strip_js_comments(src):
    """Remove // and /* */ comments, leaving string literals untouched."""
    out = []
    i, n = 0, len(src)
    quote = None
    while i < n:
        c = src[i]
        if quote:
            if c == "\n":  # JS strings cannot span lines: a stray quote (regex literal etc.)
                quote = None
                out.append(c)
                i += 1
                continue
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "\"'":
            quote = c
            out.append(c)
        elif c == "/" and src[i:i + 2] == "//":
            while i < n and src[i] != "\n":
                i += 1
            continue
        elif c == "/" and src[i:i + 2] == "/*":
            end = src.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        else:
            out.append(c)
        i += 1
    return "".join(out)


def bridge_sources():
    return {name: strip_js_comments((BRIDGE_DIR / name).read_text(encoding="utf-8")) for name in BRIDGE_FILES}


def referenced_members(sources=None):
    """{'get'|'set'|'call'|'getcount'|'write': {name, ...}} across the bridge."""
    sources = sources or bridge_sources()
    found = {k: set() for k in list(_CALL_RES) + ["write"]}
    for text in sources.values():
        for op, rx in _CALL_RES.items():
            found[op].update(rx.findall(text))
        found["write"].update(_SET_CHECKED_RE.findall(text))
    found["write"].update(found["set"])
    return found


class LomSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.surface = lom_reference.load_surface()
        cls.index = lom_reference.member_index(cls.surface)
        cls.refs = referenced_members()

    def test_surface_is_populated(self):
        self.assertGreaterEqual(len(self.surface), 40)
        self.assertIn("loop_start", self.index)
        self.assertTrue(any(e.get("settable") for _, e in self.index["loop_start"]))

    def test_every_referenced_member_exists_on_some_class(self):
        allowed = set(VERSION_GAP) | set(KNOWN_ABSENT)
        missing = {}
        for op in ("get", "set", "call", "getcount", "write"):
            for name in self.refs[op]:
                if name not in self.index and name not in allowed:
                    missing.setdefault(name, []).append(op)
        self.assertFalse(
            missing,
            "Bridge references LOM members that exist on no class in the Live 12.3.6 "
            "reference (add to VERSION_GAP/KNOWN_ABSENT with a justification only if "
            "intentional): %r" % missing,
        )

    def test_written_members_are_settable_somewhere(self):
        readonly = {}
        for name in self.refs["write"]:
            if name in self.index and name not in KNOWN_READONLY_WRITES:
                if not any(e.get("settable") for _, e in self.index[name]):
                    readonly[name] = [c for c, _ in self.index[name]]
        self.assertFalse(readonly, "Bridge writes members the reference marks read-only: %r" % readonly)

    def test_allowlists_are_justified_and_still_needed(self):
        every_ref = set().union(*self.refs.values())
        for label, table in (("VERSION_GAP", VERSION_GAP), ("KNOWN_ABSENT", KNOWN_ABSENT),
                             ("KNOWN_READONLY_WRITES", KNOWN_READONLY_WRITES)):
            for name, why in table.items():
                self.assertTrue(len(why.strip()) > 10, "%s[%r] needs a justification" % (label, name))
        stale = [n for n in list(VERSION_GAP) + list(KNOWN_ABSENT) if n not in every_ref]
        self.assertFalse(stale, "Allowlist entries the bridge no longer references (remove them): %r" % stale)
        stale_ro = [n for n in KNOWN_READONLY_WRITES if n not in self.refs["write"]]
        self.assertFalse(stale_ro, "KNOWN_READONLY_WRITES entries no longer written (remove them): %r" % stale_ro)

    def test_allowlisted_absent_members_really_are_absent(self):
        # A member that now exists in the reference should leave the allowlist.
        present = [n for n in KNOWN_ABSENT if n in self.index]
        self.assertFalse(present, "Now in the reference -- remove from KNOWN_ABSENT: %r" % present)

    def test_v1_0_39_new_members_are_verified_settable(self):
        """The members the v1.0.39 actions write must be settable per the reference."""
        expected = {
            ("Song", "loop"), ("Song", "loop_start"), ("Song", "loop_length"),
            ("Song", "groove_amount"), ("Song", "nudge_down"), ("Song", "nudge_up"),
            ("Song", "swing_amount"), ("Song", "appointed_device"),
            ("Song", "session_automation_record"), ("DeviceParameter", "display_value"),
        }
        for cls, name in expected:
            entry = self.surface.get(cls, {}).get(name)
            self.assertIsNotNone(entry, "%s.%s missing from reference" % (cls, name))
            self.assertTrue(entry.get("settable"), "%s.%s is not settable" % (cls, name))

    def test_read_only_members_stay_read_only(self):
        """Guard the four setters the plan proved impossible against being 'added' later."""
        for cls, name in (("Song", "exclusive_arm"), ("Song", "exclusive_solo"),
                          ("Song", "count_in_duration"), ("Song", "tuning_system")):
            entry = self.surface.get(cls, {}).get(name)
            self.assertIsNotNone(entry, "%s.%s missing" % (cls, name))
            self.assertFalse(entry.get("settable"), "%s.%s unexpectedly settable" % (cls, name))


if __name__ == "__main__":
    unittest.main()
