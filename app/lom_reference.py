"""Offline truth table of the Live Object Model surface.

Parses the runtime-introspected Live 12.3.6 LOM reference
(``B:\\DATABASES\\Music_Audio\\Ableton_Live\\LiveAPI_LOM\\markdown\\general``)
into ``lom_surface.json`` -- one entry per class, one per member, with
``kind`` / ``type`` / ``settable`` / ``listenable``. ``test_lom_surface.py``
uses that file to catch a bridge action that references a member which does
not exist on any LOM class, or writes one that is read-only, *before* the
action ships. The JSON is committed so the check runs without drive B:.

Usage:
    python lom_reference.py --regenerate [--source DIR]
    python lom_reference.py --lookup Song loop_start
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SOURCE = Path(r"B:\DATABASES\Music_Audio\Ableton_Live\LiveAPI_LOM\markdown\general")
SURFACE_PATH = Path(__file__).with_name("lom_surface.json")
SOURCE_LIVE_VERSION = "12.3.6"

_CLASS_RE = re.compile(r"^### (\w+)\s*$")
_MEMBER_RE = re.compile(r"^##### (\w+)\s*$")
_SECTION_RE = re.compile(r"^#### (Properties|Methods)\s*$")
_FENCE_RE = re.compile(r"^```")


def _scalar(block, key):
    m = re.search(r"^%s:\s*(.+?)\s*$" % re.escape(key), block, re.M)
    return m.group(1).strip("'\"") if m else None


def _bool(block, key):
    v = _scalar(block, key)
    if v is None:
        return None
    return v.lower() == "true"


def _yaml_blocks(lines):
    """Yield (heading_line_index, yaml_text) for every ```yaml fence."""
    i = 0
    while i < len(lines):
        if lines[i].strip() == "```yaml":
            j = i + 1
            while j < len(lines) and not _FENCE_RE.match(lines[j]):
                j += 1
            yield i, "\n".join(lines[i + 1:j])
            i = j
        i += 1


def parse_markdown(text):
    """Return {class_name: {member_name: {...}}} for one reference file."""
    lines = text.splitlines()
    classes = {}
    current = None
    member = None
    for idx, line in enumerate(lines):
        m = _CLASS_RE.match(line)
        if m:
            current = m.group(1)
            classes.setdefault(current, {})
            member = None
            continue
        m = _MEMBER_RE.match(line)
        if m and current:
            member = m.group(1)
            # the yaml fence follows the heading after one blank line
            j = idx + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip() == "```yaml":
                k = j + 1
                while k < len(lines) and not _FENCE_RE.match(lines[k]):
                    k += 1
                block = "\n".join(lines[j + 1:k])
                kind = _scalar(block, "kind")
                entry = {"kind": kind}
                if kind == "property":
                    entry["type"] = _scalar(block, "type")
                    entry["settable"] = bool(_bool(block, "settable"))
                    entry["listenable"] = bool(_bool(block, "listenable"))
                elif kind == "method":
                    sig = re.search(r"^signature:\s*(.+?)(?=^\w+:|\Z)", block, re.M | re.S)
                    if sig:
                        entry["signature"] = re.sub(r"\s+", " ", sig.group(1)).strip().strip("'")
                classes[current][member] = entry
    return {k: v for k, v in classes.items() if v}


def build_surface(source):
    source = Path(source)
    if not source.is_dir():
        raise SystemExit("LOM reference folder not found: %s" % source)
    surface = {}
    for md in sorted(source.glob("*.md")):
        for cls, members in parse_markdown(md.read_text(encoding="utf-8")).items():
            surface.setdefault(cls, {}).update(members)
    return surface


def regenerate(source=DEFAULT_SOURCE, out=SURFACE_PATH):
    surface = build_surface(source)
    payload = {
        "_meta": {
            "source_live_version": SOURCE_LIVE_VERSION,
            "source": str(source),
            "note": "Runtime-introspected reference. Repo targets Live 12.3+, so members "
                    "added in later builds (e.g. SimplerDevice.replace_sample, 12.4+) "
                    "are absent here and must be listed in test_lom_surface.VERSION_GAP.",
            "class_count": len(surface),
            "member_count": sum(len(v) for v in surface.values()),
        },
        "classes": surface,
    }
    Path(out).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return payload["_meta"]


def load_surface(path=SURFACE_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))["classes"]


def member_index(surface=None):
    """{member_name: [(class_name, entry), ...]} across every class."""
    surface = surface or load_surface()
    index = {}
    for cls, members in surface.items():
        for name, entry in members.items():
            index.setdefault(name, []).append((cls, entry))
    return index


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--regenerate", action="store_true", help="rebuild lom_surface.json from drive B:")
    ap.add_argument("--source", default=str(DEFAULT_SOURCE))
    ap.add_argument("--lookup", nargs="+", metavar=("CLASS", "MEMBER"))
    args = ap.parse_args(argv)
    if args.regenerate:
        print(json.dumps(regenerate(args.source), indent=1))
        return 0
    if args.lookup:
        surface = load_surface()
        cls = args.lookup[0]
        if len(args.lookup) == 1:
            print(json.dumps(surface.get(cls), indent=1))
        else:
            print(json.dumps(surface.get(cls, {}).get(args.lookup[1]), indent=1))
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
