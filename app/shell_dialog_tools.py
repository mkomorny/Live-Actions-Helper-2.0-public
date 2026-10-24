"""The three webview-dialog tools in the shell: Arrangement Helper, BBenCut, Breakdowns.

Ported 1:1 from helper.py (`_open_webview_tool*`, `_*_context`, `_run_breakdowns`, `_run_bbencut`,
`_run_arrangement_helper`) with the Tk-only parts replaced:

  * the dialog is a native window opened through `shell_dialogs.DialogHost` (never edited or re-themed --
    the user's standing decision: Breakdowns keeps its design and its own theme picker);
  * messagebox.askyesno  -> `confirm(title, message)`, called on a worker thread with NO lock held;
  * messagebox errors    -> the tool's result box + the console (state "error").

Everything that blocks (the arrangement scan, plan calls, ffmpeg renders, native confirms) runs on a
worker thread; the model lock is only ever held for short state reads and writes.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Callable

import settings_store
import shell_dialogs
from bbencut import bake_render as bbencut_bake_render
from bbencut import ffmpeg_util as bbencut_ffmpeg_util
from bbencut import roll_render as bbencut_roll_render

DIALOG_TOOLS = ("arrangement-helper", "bbencut", "breakdowns")
AH_CAP = 80                    # matches the bridge's own check inside computeArrangementPlan
AH_WAIT_S = 20.0
BBENCUT_WAIT_S = 60.0


def _spawn(fn: Callable[[], None]) -> None:
    threading.Thread(target=fn, daemon=True, name="dialog-tool").start()


def _beats(sig: str) -> int:
    if "/" in sig:
        try:
            return max(1, int(sig.split("/", 1)[0]))
        except ValueError:
            pass
    return 4


def _tempo(bpm: Any) -> float | None:
    try:
        return float(bpm)
    except (TypeError, ValueError):
        return None


class DialogTools:
    def __init__(
        self,
        model: Any,
        host: Any,
        confirm: Callable[[str, str], bool],
        spawn: Callable[[Callable[[], None]], None] = _spawn,
    ) -> None:
        self._m = model
        self._host = host
        self._confirm = confirm
        self._spawn = spawn
        self._scan: dict[str, Any] | None = None     # Arrangement Helper: consumed once by its context
        self._closing = False

    def shutdown(self) -> None:
        """The app is closing: close any open dialog, and let its "cancelled" result die quietly. Without
        this the result would emit page events into a window that is already being disposed."""
        self._closing = True
        if self._host is not None:
            self._host.close_all()

    # -- opening -------------------------------------------------------------------

    def open(self, tool: dict[str, Any], name: str) -> dict[str, Any]:
        """Start opening `tool`'s dialog. Returns at once; the window opens on a worker."""
        m = self._m
        tool_id = str(tool["id"])
        with m._lock:
            if tool_id == "arrangement-helper" and not m._connected:
                msg = "⚠  Bridge offline — start Live and drop the bridge device."
                m._finish_run(tool_id, "error", msg)
                return {"ok": False, "message": msg}
            if self._host is None:
                msg = "⚠  Dialog windows are not available here."
                m._finish_run(tool_id, "error", msg)
                return {"ok": False, "message": msg}
            if self._host.is_open(tool_id):
                self._host.open(tool_id, name, "", lambda _p: None)     # raises the one that is open
                return {"ok": True, "message": "%s is already open — brought to the front." % name}
            msg = "Opening %s…" % name
            m._finish_run(tool_id, "running", msg)
        self._spawn(lambda: self._open_worker(tool, name))
        return {"ok": True, "message": msg}

    def _open_worker(self, tool: dict[str, Any], name: str) -> None:
        m = self._m
        tool_id = str(tool["id"])
        try:
            if tool_id == "arrangement-helper":
                with m._lock:
                    m._finish_run(tool_id, "running", "Scanning the Set for an existing arrangement…")
                    candidate = self._default_section_track(self._ctx_arrangement(None))
                scan: dict[str, Any] = {}
                if candidate:
                    result = m._bridge.call_live("arrangement_scan", {"trackPath": candidate})
                    if result.get("ok"):
                        scan = result
                    else:
                        reason = str(result.get("message") or result.get("error") or "scan failed")
                        m.log("Arrangement Helper: scan failed (%s) -- opening in create mode." % reason)
                self._scan = {"trackPath": candidate, "scan": scan}
            html = self._html(tool)
            if not html:
                raise RuntimeError("Could not load the %s dialog HTML file." % name)
            with m._lock:
                m._finish_run(tool_id, "running", str(tool.get("dialogStatus") or "%s is open in its own dialog window." % name))
            self._host.open(tool_id, name, html, lambda payload: self._on_result(tool, name, payload))
            m.log("%s dialog opened." % name)
        except Exception as exc:
            with m._lock:
                m._finish_run(tool_id, "error", "⚠  Could not open the %s dialog: %s" % (name, exc))
            m.log("%s dialog error: %s" % (name, exc))

    def _html(self, tool: dict[str, Any]) -> str:
        path = Path(str(tool.get("_path") or "")) / str(tool.get("dialog") or "ui/dialog.html")
        if not path.is_file():
            return ""
        with self._m._lock:
            ctx = self._context(str(tool.get("id") or ""))
        return path.read_text(encoding="utf-8").replace("__CTX_JSON__", shell_dialogs.embed_json(ctx))

    # -- what each dialog is handed (__CTX_JSON__) -----------------------------------

    def _context(self, tool_id: str) -> dict[str, Any]:
        if tool_id == "breakdowns":
            return self._ctx_breakdowns()
        if tool_id == "bbencut":
            return self._ctx_bbencut()
        if tool_id == "arrangement-helper":
            return self._ctx_arrangement(self._scan)
        return {}

    def _time(self) -> tuple[int, float | None]:
        s = self._m._set
        return _beats(str(s.get("sig") or "4/4")), _tempo(s.get("bpm"))

    def _ctx_breakdowns(self) -> dict[str, Any]:
        m = self._m
        names = [str(t.get("name") or t.get("key") or "track") for t in m.selected_tracks()]
        beats, tempo = self._time()
        return {
            "source": "MidiTrack",
            "hasClip": bool(names),
            "clipName": ", ".join(names) if names else "tick a MIDI track",
            "beatsPerBar": beats,
            "tempo": tempo,
            "spec": {
                "genre": "melodicHouse", "technique": "ghostGroove", "context": "groove", "lengthBars": 1,
                "beatsPerBar": beats, "intensity": 0.6, "density": 0.6, "swing": 0,
                "humTiming": 0.3, "humVel": 0.3, "seed": 1,
            },
            "availableTargets": ["newClip", "replace", "append", "newTrack", "playhead"],
            "noteCount": 0,
        }

    def _ctx_bbencut(self) -> dict[str, Any]:
        # No Arrangement-clip read support yet (Step 4 of the BBenCut plan) -- honest static defaults.
        _bar, tempo = self._time()
        return {"hasClip": False, "totalLengthBeats": 16.0, "loopLengthBeats": 4.0, "tempo": tempo}

    def _ctx_arrangement(self, cache: dict[str, Any] | None) -> dict[str, Any]:
        """isEditing / sections / scanCount / nextId come from a real arrangement_scan reply when one is
        cached; otherwise the honest create-mode defaults. The cache is consumed here so a later call
        cannot reuse stale edit-mode data."""
        if cache is not None and cache is self._scan:
            self._scan = None
        scan = (cache or {}).get("scan") or {}
        scan_ok = bool(scan.get("ok"))
        beats, tempo = self._time()
        m = self._m
        tracks = [
            {
                "path": str(t.get("path") or ""),
                "name": str(t.get("name") or t.get("key") or "track"),
                "kind": str(t.get("kind") or "audio").lower(),
                "ticked": t.get("key") in m._targets,
            }
            for t in m._tracks
        ]
        stored = (m._settings.get("tool_prefs") or {}).get("arrangement-helper", {})
        ctx: dict[str, Any] = {
            "isEditing": bool(scan_ok and scan.get("isEditing")),
            "sections": (scan.get("sections") or []) if scan_ok else [],
            "nextId": int(scan.get("nextId") or 0) if scan_ok else 0,
            "scanCount": int(scan.get("scanCount") or 0) if scan_ok else 0,
            "beatsPerBar": beats,
            "tempo": tempo,
            "tracks": tracks,
            "lastSectionTrackPath": str((cache or {}).get("trackPath") or "") or str(stored.get("sectionTrackPath") or ""),
        }
        if scan_ok and scan.get("startBar") is not None:
            ctx["startBar"] = scan.get("startBar")
        if scan_ok and scan.get("truncated"):
            ctx["truncated"] = True
        return ctx

    @staticmethod
    def _default_section_track(ctx: dict[str, Any]) -> str:
        """Mirrors dialog.html's own defaultSectionTrackPath() so the pre-open scan targets the track the
        dialog shows selected: last persisted (if still a MIDI track) -> one named "Arrangement" -> the
        first ticked MIDI track -> the first MIDI track. Keep both in sync if either changes."""
        midi = [t for t in (ctx.get("tracks") or []) if t.get("kind") == "midi"]
        if not midi:
            return ""
        last = str(ctx.get("lastSectionTrackPath") or "")
        if last and any(t.get("path") == last for t in midi):
            return last
        for t in midi:
            if str(t.get("name") or "").strip().lower() == "arrangement":
                return str(t["path"])
        for t in midi:
            if t.get("ticked"):
                return str(t["path"])
        return str(midi[0]["path"])

    # -- what a dialog sends back ----------------------------------------------------

    def _on_result(self, tool: dict[str, Any], name: str, payload: Any) -> None:
        """Called by the window host on whatever thread closed the dialog -- so hand off at once."""
        self._spawn(lambda: self._handle_result(tool, name, payload))

    def _handle_result(self, tool: dict[str, Any], name: str, payload: Any) -> None:
        m = self._m
        tool_id = str(tool["id"])
        if self._closing:
            return
        data: Any = payload
        if isinstance(payload, str) and payload != "":
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                self._fail(tool_id, "Webview tool sent an invalid payload.")
                return
        if not isinstance(data, dict):                # closed / cancelled: nothing was written
            with m._lock:
                if m._pending_run != tool_id:
                    m._finish_run(tool_id, "idle", "Dialog closed — nothing was written.")
            m.log("%s dialog closed." % name)
            return
        try:
            if tool_id == "breakdowns":
                self._run_breakdowns(name, data)
            elif tool_id == "bbencut":
                self._run_bbencut(name, data)
            elif tool_id == "arrangement-helper":
                self._run_arrangement_helper(name, data)
        except Exception as exc:                      # never let a handler bug leave the tool "running"
            self._fail(tool_id, "%s failed unexpectedly: %s" % (name, exc))

    def _fail(self, tool_id: str, message: str) -> None:
        with self._m._lock:
            self._m._finish_run(tool_id, "error", "⚠  " + message)
        self._m.log("✗ " + message)

    def _cancelled(self, tool_id: str, name: str) -> None:
        with self._m._lock:
            self._m._finish_run(tool_id, "idle", "Cancelled — nothing was written.")
        self._m.log("%s: cancelled by user." % name)

    def _targets_payload(self) -> list[dict[str, Any]]:
        return [
            {"key": t.get("key"), "index": t.get("index"), "kind": t.get("kind"), "path": t.get("path")}
            for t in self._m.selected_tracks()
        ]

    # -- Breakdowns ----------------------------------------------------------------------

    def _run_breakdowns(self, name: str, request: dict[str, Any]) -> None:
        m = self._m
        with m._lock:
            targets = self._targets_payload()
        if not targets:
            self._fail("breakdowns", "Select at least one track on the left first.")
            return
        notes = request.get("notes") or []
        if not notes:
            self._fail("breakdowns", "No notes generated to insert.")
            return
        payload = {
            "tracks": targets,
            "fields": {
                "target": str(request.get("target") or "newClip"),
                "lengthBeats": request.get("lengthBeats") or 4,
                "name": str(request.get("name") or "Breakdowns"),
                "notes": notes,
            },
        }
        f = payload["fields"]
        with m._lock:
            m._dispatch_run(
                "breakdowns", name, payload,
                "Inserted fill '%s' (%d notes) as %s on %d track(s)." % (f["name"], len(notes), f["target"], len(targets)),
                "Inserting fill '%s' on %d track(s)…" % (f["name"], len(targets)),
            )

    # -- BBenCut -------------------------------------------------------------------------

    def _run_bbencut(self, name: str, request: dict[str, Any]) -> None:
        """Send the computed cut sequence to the bridge's runBbencut job (it resolves the real source clip
        from Live's Detail View selection and places non-roll slices as Arrangement clips). Two safety
        gates come first: a blocking "N individual undo steps" confirmation, and BAKE_THRESHOLD -- above
        it the run is baked into ONE wav and placed as a single clip, or refused if the source is warped.
        See docs/plans/bbencut-step5-roll-rendering.md and bbencut-step6-bake-and-safety.md."""
        m = self._m
        with m._lock:
            targets = self._targets_payload()
            track_name = self._first_selected_name()
            settings = dict(m._settings)
            bridge = m._bridge
        if not targets:
            self._fail("bbencut", "Tick the source audio track on the left first.")
            return
        fields = {
            "algorithm": request.get("algorithm"),
            "params": request.get("params") or {},
            "totalLengthBeats": request.get("totalLengthBeats"),
            "loopLengthBeats": request.get("loopLengthBeats"),
            "slices": request.get("slices") or [],
            "rollGroups": request.get("rollGroups") or [],
        }
        payload = {"tracks": targets, "fields": fields}
        track_name = track_name or "the ticked track"
        track_path = str(targets[0].get("path") or "")
        roll_groups = fields["rollGroups"]
        total_count = len(fields["slices"])           # slicer.ts gives one entry per placement (clip or roll placeholder)
        threshold = bbencut_bake_render.BAKE_THRESHOLD

        def send_and_log() -> None:
            with m._lock:
                m._dispatch_run(
                    "bbencut", name, payload,
                    "BBenCut: sent %d slice(s) for %s to the bridge for placement." % (len(fields["slices"]), fields["algorithm"]),
                    "Placing %d slice(s) in the Arrangement…" % len(fields["slices"]),
                    BBENCUT_WAIT_S,
                )

        def placement_message(count: int, roll_count: int) -> str:
            roll_clause = ", including %d rendered roll group(s)" % roll_count if roll_count else ""
            return (
                "This will place %d Arrangement clip(s) on %s%s.\n\n"
                "Each clip is a separate action — this is %d individual undo steps, "
                "not one atomic action.\n\nContinue?" % (count, track_name, roll_clause, count)
            )

        if total_count <= threshold and not roll_groups:
            if not self._confirm("BBenCut — Confirm Placement", placement_message(total_count, 0)):
                self._cancelled("bbencut", name)
                return
            send_and_log()
            return

        # Past here we need warping / tempo / sampleFile off the source clip -- to decide bake-vs-refuse or to
        # render roll groups -- so fetch it once (bbencut_source is a blocking OSC call; we are on a worker).
        m.log("BBenCut: checking source clip…")
        info = bridge.call_live("bbencut_source", {"trackPath": track_path})
        if not info.get("ok"):
            err = str(info.get("error") or "unknown error")
            self._fail("bbencut", "BBenCut — run refused: could not read the source clip (%s). Nothing was placed." % err)
            return

        sample_file = str(info.get("sampleFile") or "")
        tempo = float(info.get("tempo") or 0)
        warping = bool(info.get("warping"))
        ffmpeg = bbencut_ffmpeg_util.resolve_ffmpeg(settings)
        ffprobe = bbencut_ffmpeg_util.resolve_ffprobe(settings)

        if total_count > threshold:
            if warping:
                self._fail(
                    "bbencut",
                    "BBenCut — run refused: %d clips exceeds the %d-clip safety threshold, and baking to a single file "
                    "needs an unwarped source clip (the one in Detail View is warped). Turn off warping on the source "
                    "clip, or reduce the run below %d clips, and try again. Nothing was placed." % (total_count, threshold, threshold),
                )
                return
            if not self._confirm(
                "BBenCut — Confirm Bake",
                "This run would place %d clips, above the %d-clip safety threshold. BBenCut will "
                "bake the full sequence into one audio file instead and place it as a single "
                "Arrangement clip — one undo step, not %d.\n\nContinue?" % (total_count, threshold, total_count),
            ):
                self._cancelled("bbencut", name)
                return
            m.log("BBenCut: baking %d clips into one file…" % total_count)
            bake = bbencut_bake_render.render_full_bake(
                ffmpeg, ffprobe, settings_store.samples_dir(settings) / "BBenCut Bakes",
                sample_file, tempo, warping, fields["slices"], roll_groups,
            )
            if not bake.get("ok"):
                self._fail("bbencut", "BBenCut — bake failed: could not bake this run (%s)." % bake.get("reason"))
                return
            total_length = fields.get("totalLengthBeats") or 0
            fields["slices"] = [{
                "arrangementStartTime": 0,
                "duration": total_length,
                "filePath": bake["path"],
                "loopSettings": {"looping": False, "startMarker": 0, "endMarker": total_length, "loopStart": 0, "loopEnd": total_length},
            }]
            fields["rollGroups"] = []
            send_and_log()
            return

        # Under the threshold, with roll groups: dry-run confirm, then render.
        if not self._confirm("BBenCut — Confirm Placement", placement_message(total_count, len(roll_groups))):
            self._cancelled("bbencut", name)
            return
        m.log("BBenCut: rendering %d roll group(s)…" % len(roll_groups))
        try:
            result = bbencut_roll_render.render_roll_groups(
                ffmpeg, ffprobe, settings_store.samples_dir(settings) / "BBenCut Rolls",
                sample_file, tempo, warping, roll_groups,
            )
            for idx, path in result["rendered"].items():
                sentinel = "__ROLL_GROUP_%d__" % idx
                for slice_ in fields["slices"]:
                    if slice_.get("filePath") == sentinel:
                        slice_["filePath"] = path
            skipped = result["skipped"]
            if skipped:
                reasons = "; ".join("#%s: %s" % (s["index"], s["reason"]) for s in skipped)
                m.log("BBenCut: rendered %d roll group(s), %d not rendered -- %s" % (len(result["rendered"]), len(skipped), reasons))
            else:
                m.log("BBenCut: rendered %d roll group(s)." % len(result["rendered"]))
        except Exception as exc:                      # never take the run down for a render failure
            m.log("✗ BBenCut: roll rendering failed unexpectedly (%s)." % exc)
        send_and_log()

    def _first_selected_name(self) -> str:
        picked = self._m.selected_tracks()
        return str((picked[0].get("name") or picked[0].get("key")) if picked else "")

    # -- Arrangement Helper ----------------------------------------------------------------

    def _run_arrangement_helper(self, name: str, request: dict[str, Any]) -> None:
        """The two-call sequence: arrangement_plan (read-only, real numbers) -> confirm -> execute."""
        m = self._m
        section_track_path = str(request.get("sectionTrackPath") or "")
        with m._lock:
            if not section_track_path:
                m._finish_run("arrangement-helper", "idle", "No section track chosen — nothing to plan.")
                m.log("Arrangement Helper: no section track chosen -- nothing to plan.")
                return
            m._save_prefs("arrangement-helper", {"sectionTrackPath": section_track_path})
            ticked_paths = [
                str(t.get("path") or "") for t in m._tracks
                if t.get("key") in m._targets and t.get("path") and str(t.get("path")) != section_track_path
            ]
            beats, _tempo_unused = self._time()
            bridge = m._bridge
        remap_all_tracks = bool(request.get("remapAllTracks"))
        plan_fields = {
            "sections": request.get("sections") or [],
            "createLocators": bool(request.get("createLocators")),
            "remapAllTracks": remap_all_tracks,
            "renameTrack": bool(request.get("renameTrack")),
            "sectionTrackPath": section_track_path,
            "scanCount": int(request.get("scanCount") or 0),
            "isEditing": bool(request.get("isEditing")),   # the dialog echoes the flag arrangement_scan seeded it with
            "beatsPerBar": beats,
            "tickedTrackPaths": ticked_paths,
        }
        plan = bridge.call_live("arrangement_plan", plan_fields)
        if not plan.get("ok"):
            reason = str(plan.get("message") or plan.get("error") or "unknown error")
            self._fail("arrangement-helper", "Arrangement Helper: plan refused -- %s" % reason)
            return

        write_count = int(plan.get("writeCount") or 0)
        moved = int(plan.get("moved") or 0)
        section_count = int(plan.get("sectionCount") or 0)
        # The cap is checked with the plan's own numbers BEFORE any confirm, i.e. before the user says yes.
        if write_count > AH_CAP:
            self._fail(
                "arrangement-helper",
                "Arrangement Helper — run refused: %d write operations exceeds the %d-operation safety cap. "
                "Nothing was written." % (write_count, AH_CAP),
            )
            return

        undo_steps = int(plan.get("undoStepCount") or 0)
        move_line = " and moves %d existing clip(s) on remap track(s)" % moved if moved > 0 else ""
        if not self._confirm(
            "Arrangement Helper — Confirm",
            "This creates %d section clip(s)%s, as %d individual undo step(s).\n\n"
            "This cannot be undone in one step -- save your Set first. A failure partway "
            "through this run can leave temporary clips behind that won't be auto-removed."
            "\n\nContinue?" % (section_count, move_line, undo_steps),
        ):
            self._cancelled("arrangement-helper", name)
            return
        if remap_all_tracks:
            if not self._confirm(
                "Arrangement Helper — Whole Project",
                "Whole Project is on -- this also affects all %d eligible track(s), not just "
                "ticked ones.\n\nContinue?" % int(plan.get("remapTrackCount") or 0),
            ):
                self._cancelled("arrangement-helper", name)
                return

        exec_fields = dict(plan_fields)
        exec_fields["fingerprint"] = plan.get("fingerprint") or {}
        with m._lock:
            m._dispatch_run(
                "arrangement-helper", name, {"fields": exec_fields},
                "Arrangement Helper: sent %d section(s)%s to the bridge for execution." % (section_count, move_line),
                "Writing %d section(s)%s…" % (section_count, move_line),
                AH_WAIT_S,
            )
