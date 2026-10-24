"""Build the Producer Pal Genius user manual PDF.

Writes:
  B:\\Documents\\TRAINING DOCS\\User Manuals\\Other Manuals\\Producer Pal Genius User Manual.pdf
  docs\\Producer Pal Genius User Manual.pdf  (next to this repo)
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

HERE = Path(__file__).resolve().parent.parent
LIVE = Path(
    r"B:\Documents\TRAINING DOCS\User Manuals\Other Manuals"
    r"\Producer Pal Genius User Manual.pdf"
)
REPO = HERE / "docs" / "Producer Pal Genius User Manual.pdf"

GREEN_HEADER = colors.HexColor("#1E4A3A")
GREEN = colors.HexColor("#2C6B52")
GREEN_SOFT = colors.HexColor("#E7F2EA")
BEIGE = colors.HexColor("#EDE6D4")
AMBER = colors.HexColor("#F6E8C8")
AMBER_EDGE = colors.HexColor("#C4A35A")
INK = colors.HexColor("#1A1A1A")
MUTED = colors.HexColor("#4A4A4A")
RULE = colors.HexColor("#D0D0D0")
WHITE = colors.white


def styles():
    base = getSampleStyleSheet()
    s = {
        "kicker": ParagraphStyle(
            "kicker",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=GREEN,
            tracking=1.2,
            spaceAfter=8,
        ),
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=32,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "deck": ParagraphStyle(
            "deck",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=INK,
            spaceAfter=10,
        ),
        "date": ParagraphStyle(
            "date",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=MUTED,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=INK,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=GREEN,
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "plain": ParagraphStyle(
            "plain",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=INK,
            spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=INK,
            leftIndent=12,
        ),
        "cell": ParagraphStyle(
            "cell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=INK,
        ),
        "cellb": ParagraphStyle(
            "cellb",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=INK,
        ),
        "path": ParagraphStyle(
            "path",
            parent=base["Normal"],
            fontName="Courier",
            fontSize=8,
            leading=11,
            textColor=INK,
            spaceAfter=6,
        ),
        "toc": ParagraphStyle(
            "toc",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=INK,
        ),
        "note": ParagraphStyle(
            "note",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=INK,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
        ),
    }
    return s


S = styles()


def P(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return ListFlowable(
        [ListItem(P(i, "bullet"), leftIndent=12, bulletColor=INK) for i in items],
        bulletType="bullet",
        start="•",
        leftIndent=16,
        bulletFontName="Helvetica",
        bulletFontSize=10,
        spaceBefore=0,
        spaceAfter=8,
    )


def numbered(items):
    flow = []
    for n, text in enumerate(items, 1):
        row = Table(
            [[Paragraph(f"<b>{n}</b>", S["plain"]), P(text, "plain")]],
            colWidths=[18, 6.3 * inch],
        )
        row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        flow.append(row)
    flow.append(Spacer(1, 6))
    return flow


def callout(text, kind="note"):
    bg = GREEN_SOFT if kind == "note" else AMBER
    edge = GREEN if kind == "note" else AMBER_EDGE
    label = "Note. " if kind == "note" else "Watch. "
    inner = Paragraph(f"<b>{label}</b>{text}", S["note"])
    box = Table([[inner]], colWidths=[6.5 * inch])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0.6, edge),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return KeepTogether([box, Spacer(1, 10)])


def grid(headers, rows, widths):
    head = [P(h, "cellb") for h in headers]
    body = [[P(c, "cell") for c in row] for row in rows]
    t = Table([head] + body, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BEIGE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return t


def header_footer(canvas, doc):
    w, h = letter
    canvas.saveState()
    if doc.page == 1:
        canvas.setFillColor(GREEN_HEADER)
        canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.75 * inch, 0.45 * inch, "Producer Pal Genius  ·  studio how-to")
    canvas.drawRightString(w - 0.75 * inch, 0.45 * inch, str(doc.page))
    canvas.restoreState()


def story():
    out = []
    out.append(Spacer(1, 18))
    out.append(P("STUDIO HOW-TO", "kicker"))
    out.append(P("Producer Pal Genius", "title"))
    out.append(
        P(
            "How Producer Pal and Genius work together on this PC. Official Pal does the Live Set. "
            "Genius opens the books first — Live, plugins, hardware, and now music theory and production craft.",
            "deck",
        )
    )
    out.append(P("17 August 2026", "date"))
    out.append(
        P(
            "This is not the official producer-pal.org site capture. That filtered archive is still in this "
            "folder as <font face='Courier' size='8'>producer-pal-ai-readable-guide.pdf</font>.",
            "plain",
        )
    )
    out.append(P("Contents", "h2"))
    for item in [
        "What this book is",
        "What Producer Pal is",
        "What Genius is",
        "How the knowledgebase improves Pal's results",
        "How Genius works",
        "The pieces on this PC",
        "Daily start",
        "How to talk to Genius",
        "Device tabs",
        "What Pal can and cannot do",
        "Genius Live API",
        "After a Pal update",
        "If something fails",
        "Sources",
    ]:
        out.append(P(item, "toc"))
    out.append(PageBreak())

    out.append(P("What this book is", "h1"))
    out.append(
        P(
            "This book is the daily how-to for the setup you actually run: official Producer Pal, the Genius "
            "library method, the Main-tab <b>Genius Live API</b> toggle, and Producer Pal Local so "
            "<b>Open Chat UI</b> opens Grok or Claude instead of Chrome."
        )
    )
    out.append(
        P(
            "Use it to start the device, talk to it, and know what Pal will do versus what you still do by hand. "
            "It also explains why the studio library exists: Pal is a pair of hands. The books are the ears and the theory."
        )
    )

    out.append(P("What Producer Pal is", "h1"))
    out.append(
        P(
            "Producer Pal is a free, open-source Ableton MCP (Model Context Protocol) server packaged as a Max "
            "for Live device. It is made by Adam Murray. Official site: https://producer-pal.org/"
        )
    )
    out.append(
        P(
            "You describe what you want. The AI reads and edits the open Live Set through specialized tools. There "
            "are 21 tools on by default. Direct Live API and Chat UI subagents are extra and off until you turn them on."
        )
    )
    out.append(
        P(
            "Pal is not a DAW and not a replacement for learning Live. It controls the Set you already have open."
        )
    )
    out.append(P("Official requirements:", "plain"))
    out.append(
        bullets(
            [
                "Ableton Live 12.3+ with Max for Live. Live 12.4+ is recommended. Some library tools error below 12.4.",
                "Use the Max bundled with Live unless you have a documented standalone reason.",
                "Drop <font face='Courier' size='8'>Producer_Pal.amxd</font> on a <b>MIDI</b> track in every setup.",
                "Default server port is <b>3350</b>. Default timeout is <b>30 seconds</b>.",
            ]
        )
    )
    out.append(P("On this PC the live device is:", "plain"))
    out.append(
        P(
            "A:\\User Library\\Presets\\MIDI Effects\\Max MIDI Effect\\Producer_Pal.amxd",
            "path",
        )
    )
    out.append(
        P(
            "That file is official Pal v2.1.0 plus the Genius Main-tab toggle. It is not a from-scratch rewrite."
        )
    )

    out.append(P("What Genius is", "h1"))
    out.append(
        P(
            "Genius is not a second product and not a second copy of Pal. It is a working method plus a small "
            "device patch. Genius is a <b>music-theory-aware producer</b>: it reads this studio's books before Pal "
            "touches the Set."
        )
    )
    out.append(
        bullets(
            [
                "A Grok skill and agent named <b>Producer Pal Genius</b>. They force the model to open official studio books before it changes the Set.",
                "A studio library index at <font face='Courier' size='8'>B:\\Documents\\TRAINING DOCS\\INDEX.md</font>. That file names 1–3 books per topic. It does not contain the PDFs.",
                "Child indexes for Live 12, Launchkey, music theory, production / DJ, sound design, drums, audio-effect DSP, and music-only User Manuals.",
                "A <b>Genius Live API</b> toggle on the device <b>Main</b> tab. That toggle is the same flag as Setup → <b>Direct Live API</b>. Off by default. On exposes the raw <font face='Courier' size='8'>ppal-live-api</font> tool.",
            ]
        )
    )
    out.append(
        P(
            "A companion installer, <b>Producer Pal Local</b>, remaps <b>Open Chat UI</b> so it opens Grok Build or Claude Desktop instead of Chrome."
        )
    )
    out.append(
        P(
            "Official Pal stays GPL-3.0 and is not shipped inside the Genius or Local repos. Those add-ons are MIT."
        )
    )

    out.append(
        KeepTogether(
            [
                P("How the knowledgebase improves Pal's results", "h1"),
                P(
                    "Pal is good at tracks, clips, native devices, and routing. It does not know Dorian from Phrygian, "
                    "Ozone's Maximizer from Live's Limiter, or that it cannot add a VST. Without books, the model fills "
                    "those gaps from general training data. It invents knob names, guesses scale degrees, and asks Pal "
                    "to do work Pal cannot do. The result looks confident and is often wrong."
                ),
            ]
        )
    )
    out.append(
        P(
            "The knowledgebase is the fix. Genius does not dump hundreds of PDFs into the chat. It reads "
            "<font face='Courier' size='8'>INDEX.md</font>, follows <b>Decide first</b> to one child index, "
            "and opens only the 1–3 books that match the ask. Pal then does the native half of that job. "
            "That is why Genius results are tighter than Pal alone."
        )
    )

    out.append(P("What the library actually changes", "h2"))
    out.append(
        grid(
            ["Without the books", "With the Genius library"],
            [
                [
                    "The model guesses a scale, a progression, or a 'pro' mix move from memory.",
                    "It opens the theory or production sheet, cites it, and Pal writes MIDI or devices that match the book.",
                ],
                [
                    "It invents VST parameter names and tries to add Ozone, Wider, or Massive.",
                    "It opens that plugin's manual, tells you the real controls, and Pal builds only the native half (return, Limiter, clip).",
                ],
                [
                    "It treats every ask as a Live-set edit — including 'what is Lydian?'",
                    "Decide first sends theory, mix, genre, and hardware asks to the right index. Pal is used only when the Set is involved.",
                ],
                [
                    "It may open Windows or AI product docs that happen to sit under User Manuals.",
                    "Music-only filter: Ableton, Novation, plugin books, MIDI Services. Claude / Windows-dev docs stay closed on a music ask.",
                ],
                [
                    "A vague 'make a dark bass' yields a generic minor riff.",
                    "Theory + dubstep / bass production books name the scale and the role. Pal programs the clip. The VST bass stays a cited handoff.",
                ],
            ],
            [3.2 * inch, 3.3 * inch],
        )
    )
    out.append(Spacer(1, 8))

    out.append(P("Why 1–3 books beat the whole folder", "h2"))
    out.append(
        P(
            "The Music Production tree and the music User Manuals are large on purpose. If Genius loaded them all, "
            "the useful page would drown. The indexes are the knowledgebase: a routing table, not a paste of every PDF. "
            "The model then actually reads the Dorian sheet, the Ozone chapter, or Live 15 (tuning / scale) instead of "
            "skimming a thousand filenames."
        )
    )

    out.append(P("How that shows up in the Set", "h2"))
    out.append(
        P(
            "Theory is not decoration. When you ask for an 8-bar D Dorian progression, Genius opens the Dorian and "
            "progression books plus Live chapters 10 (MIDI) and 15 (scale). Pal can then write notes that belong in "
            "that mode and set the Set scale. Same path for a house drum pattern (drum + production indexes + Drum Rack) "
            "or a Launchkey split (Zones guide + template). Pal still cannot add a VST, hear audio, or draw a fade. "
            "The books make those limits honest instead of silent failures."
        )
    )
    out.append(
        KeepTogether(
            [
                P("Child indexes Genius uses after <b>Decide first</b>:", "plain"),
                grid(
                    ["Ask is about", "Child index"],
                    [
                        [
                            "Scales, keys, modes, chords, intervals, harmony, rhythm, form",
                            "Music Production\\Music Theory\\INDEX.md",
                        ],
                        [
                            "Arrangement, mix, genre, EDM, DJ, finishing, songwriting",
                            "Music Production\\Production_DJing\\INDEX.md",
                        ],
                        [
                            "Oscillators, filters, ADSR, synthesis, frequency map",
                            "Music Production\\Sound Design\\INDEX.md",
                        ],
                        [
                            "Finger drumming, drum pads, drum MIDI, MPE",
                            "Music Production\\Drum course\\INDEX.md",
                        ],
                        [
                            "How an effect works (pitch shift, vocoder, BBD)",
                            "Music Production\\Audio Analysis_Editing\\INDEX.md",
                        ],
                        [
                            "Live how-to",
                            "User Manuals\\Ableton\\Ableton Live 12 Standard Manual\\INDEX.md",
                        ],
                        ["Launchkey MK4 61", "User Manuals\\Novation\\INDEX.md"],
                        ["Which music manuals to open or skip", "User Manuals\\INDEX.md"],
                    ],
                    [3.2 * inch, 3.3 * inch],
                ),
            ]
        )
    )
    out.append(Spacer(1, 8))
    out.append(
        P(
            "If a title is missing, add a row to the master index or drop the PDF in Other Manuals / plugin manuals "
            "and tell Genius the path once. The library only improves results for books it can find."
        )
    )

    out.append(P("How Genius works", "h1"))
    out.append(
        P(
            "Pal does the Live Set. The books say how Live, the plugins, and the music actually work."
        )
    )
    out.append(
        P(
            "That is the whole idea. Pal is not a substitute for the Live manual, an Ozone book, a Launchkey chapter, "
            "or a Dorian sheet. Genius makes the AI read those books first, then use Pal only for the native half."
        )
    )

    out.append(P("The loop", "h2"))
    out.append(P("When you ask a how-to or give a directive, Genius does this:", "plain"))
    out.extend(
        numbered(
            [
                "If the ask touches the Live Set, connect with <font face='Courier' size='8'>ppal-connect</font> first.",
                "Read <font face='Courier' size='8'>B:\\Documents\\TRAINING DOCS\\INDEX.md</font>. Follow <b>Decide first</b>. Do not dump the whole TRAINING DOCS tree into context.",
                "Open only the 1–3 books the index names. Cite product plus chapter or section (or theory book plus topic).",
                "If the index has no row, search Music Production and the music User Manuals first, then the rest of TRAINING DOCS and <font face='Courier' size='8'>A:\\Plugin Documentation_Uninstallers</font> for <font face='Courier' size='8'>*.pdf</font> / <font face='Courier' size='8'>*.md</font>. Skip uninstallers, binaries, presets, and non-music Windows / AI docs.",
                "Inside Live, use Pal <font face='Courier' size='8'>ppal-*</font> tools. Pal can build tracks, returns, sends, clips, routing, library search, and <b>native</b> Live devices — including MIDI clips in a named key or scale.",
                "Pal cannot add a VST/AU, turn unmapped VST knobs, trigger stem separation, or write automation / clip envelopes. Do the native half, then hand the rest back to you with a citation.",
                "Leave <font face='Courier' size='8'>ppal-live-api</font> off unless you turned on <b>Genius Live API</b> or asked for raw Live API.",
                "Treat <font face='Courier' size='8'>ppal-context</font> as production habits, not manuals.",
            ]
        )
    )

    out.append(P("Question versus directive", "h2"))
    out.append(
        bullets(
            [
                "<b>Question</b> (“how does Wider work?” / “what is Dorian?”) — open the book, answer, cite it. Do not edit the Set.",
                "<b>Directive</b> (“put Wider on the sides” / “8-bar D Dorian clip”) — open the book plus the Live chapters, Pal does the native half, you drop the VST or finish the part Pal cannot touch.",
            ]
        )
    )

    out.append(
        KeepTogether(
            [
                P("Worked examples", "h2"),
                P(
                    "<b>“Separate the vocal and put it in a return with Ozone-style limiting.”</b> Genius opens Live chapters 22, 17, "
                    "and 18, the Ozone 12 guide, and the native Limiter in Live chapter 28. Pal makes the return and adds "
                    "Live's Limiter. Stem split and real Ozone stay a cited handoff. Pal cannot separate stems or add the VST."
                ),
            ]
        )
    )
    out.append(
        P(
            "<b>“SPAN on the master, Wider on the sides.”</b> Genius opens those two plugin books. Pal cannot add the "
            "VSTs. You drop them. Genius tells you what the books say about the controls."
        )
    )
    out.append(
        P(
            "<b>“Launchkey Zones: bass on the keys, pads stay in Live.”</b> Genius opens the Launchkey Zones chapter, "
            "DAW-control notes, and the LK4-Zones-Template set. Pal cannot write the custom mode on the hardware."
        )
    )
    out.append(
        P(
            "<b>“8-bar D Dorian progression in a MIDI clip.”</b> Genius opens the Music Theory index (Dorian + progressions) "
            "plus Live chapters 10 and 15. Pal writes the clip in that mode. That is the knowledgebase changing the MIDI, "
            "not just the prose."
        )
    )
    out.append(
        P(
            "<b>“Dark dubstep bass — what scale, then program it.”</b> Genius opens the theory scale lookup and the "
            "dubstep production books, then Pal writes the MIDI. A third-party bass synth stays a cited handoff."
        )
    )

    out.append(P("What Genius does not do", "h2"))
    out.append(
        bullets(
            [
                "It does not invent VST parameter names or pretend Pal can drive an unmapped plugin.",
                "It does not listen to audio. Pal can place, gain, pitch, and warp audio clips. It cannot transcribe, detect key from a waveform, or audio-to-MIDI.",
                "It does not write arrangement automation or clip envelopes. Pal can set a static volume. It cannot draw a fade.",
                "It does not search the web first when a local book exists.",
                "It does not load the entire Music Production or User Manuals trees. The index is the knowledgebase; the PDFs stay on disk until named.",
            ]
        )
    )

    out.append(P("The pieces on this PC", "h1"))
    out.append(
        P(
            "These are the files this studio actually uses. Prefer the live device on A:, not a Downloads copy.",
            "plain",
        )
    )
    out.append(
        grid(
            ["Piece", "What it is", "Where it lives"],
            [
                [
                    "Live device",
                    "Official Pal v2.1.0 plus Genius toggle",
                    "A:\\User Library\\Presets\\MIDI Effects\\Max MIDI Effect\\Producer_Pal.amxd",
                ],
                [
                    "Official backup",
                    "Untouched v2.1.0",
                    "Producer_Pal.amxd.official-2.1.0.bak next to the device",
                ],
                [
                    "Earlier Genius patch",
                    "Previous toggle build",
                    "Producer_Pal.amxd.genius-toggle.bak next to the device",
                ],
                [
                    "Claude Desktop extension",
                    "Official .mcpb, not the Ableton device",
                    "C:\\Users\\<you>\\Downloads\\Producer Pal\\Producer_Pal.mcpb",
                ],
                [
                    "Genius repo",
                    "Skill, agent, indexes, patch script, this manual",
                    "C:\\Users\\<you>\\My Apps\\producer-pal-genius",
                ],
                [
                    "Installed Grok skill",
                    "What Grok actually runs",
                    "%USERPROFILE%\\.grok\\skills\\producer-pal-genius",
                ],
                [
                    "Producer Pal Local",
                    "Open Chat UI → Grok or Claude",
                    "C:\\Users\\<you>\\My Apps\\producer-pal-local",
                ],
                [
                    "Studio index",
                    "First file Genius reads (Decide first)",
                    "B:\\Documents\\TRAINING DOCS\\INDEX.md",
                ],
                [
                    "Music Production books",
                    "Theory, production, sound design, drums, DSP",
                    "B:\\Documents\\TRAINING DOCS\\Music Production\\",
                ],
                [
                    "Music User Manuals",
                    "Ableton, Novation, plugin books; AI/Windows skipped",
                    "B:\\Documents\\TRAINING DOCS\\User Manuals\\INDEX.md",
                ],
                [
                    "Official Pal capture",
                    "Filtered site docs, no Genius",
                    "producer-pal-ai-readable-guide.pdf in this folder",
                ],
            ],
            [1.45 * inch, 2.15 * inch, 2.9 * inch],
        )
    )

    out.append(P("Daily start", "h1"))
    out.append(P("Do this every time you want Pal or Genius to touch a Set.", "plain"))
    out.extend(
        numbered(
            [
                "Open Ableton Live 12 with the Max bundled with Live.",
                "Create or select a <b>MIDI</b> track.",
                "Drop <b>Producer Pal</b> from the User Library (or drag <font face='Courier' size='8'>Producer_Pal.amxd</font>) onto that track.",
                "Wait until the Main tab status bar reads <b>Producer Pal Running</b> (green). If it says <b>Stopped</b>, open <b>Setup</b> and click <b>Start</b>. If it says <b>Error</b> (red), open the Max window from the device three-dot menu before you try a client.",
                "Confirm <b>Port</b> is 3350 unless you already changed every client to match a different port.",
                "Start the AI: click <b>Open Chat UI</b> (on this PC that launches <b>Producer Pal Local</b>, not Chrome), or use the Producer Pal Local shortcut, or in Grok start <b>Producer Pal Genius</b> / <font face='Courier' size='8'>/producer-pal-genius</font>.",
                "Say <b>connect to Ableton</b> before any other Pal work.",
                "Then ask the job. Genius reads the index, opens the books, and Pal does only what Pal can do.",
            ]
        )
    )
    out.append(
        callout(
            "A connect reply is a status line: Live version, set name, tempo, key, track and scene counts. "
            "Genius does not edit the Set in the first greeting unless you asked for a change."
        )
    )

    out.append(P("How to talk to Genius", "h1"))
    out.append(
        P("Lead with the outcome. Name the plugin, the key, or the hardware when it matters.", "plain")
    )
    out.append(P("Good", "h2"))
    out.append(
        bullets(
            [
                "“Connect to Ableton.”",
                "“Make a return called Vocal FX and put Live's Limiter on it.”",
                "“How does Ozone 12's Maximizer work? Don't change the Set.”",
                "“Build a MIDI clip in barbeat on track 2, eight bars, C minor.”",
                "“Write an 8-bar D Dorian progression.”",
                "“Dark dubstep bass — what scale, then program it.”",
                "“Turn Genius Live API on, then read the selected track's devices.”",
            ]
        )
    )
    out.append(P("Weak", "h2"))
    out.append(
        bullets(
            [
                "“Make it sound pro.” (no book, no target)",
                "“Listen to the vocal and write MIDI.” (Pal cannot hear audio)",
                "“Add Ozone and automate the threshold.” (cannot add the VST; cannot write automation)",
            ]
        )
    )
    out.append(
        P(
            "If Live is not reachable, Genius will say so. Open Live, drop the device, wait for <b>Running</b>, then say connect again."
        )
    )

    out.append(P("Device tabs", "h1"))
    out.append(P("Current chrome is <b>Main</b>, <b>Context</b>, and <b>Setup</b>.", "plain"))
    out.append(P("Main", "h2"))
    out.append(P("The Main tab is the status face of the device.", "plain"))
    out.append(
        bullets(
            [
                "Status bar: <b>Running</b> (green), <b>Stopped</b> (black), <b>Error</b> (red).",
                "Version string on the device (this studio installed 2.1.0).",
                "<b>Docs</b> opens the official site.",
                "<b>Open Chat UI</b> opens Producer Pal Local on this PC (patched). Stock Pal would open the browser Chat UI at http://localhost:3350/chat.",
                "<b>Genius Live API</b> toggle (the patch). Same flag as Setup → Direct Live API. Off by default.",
            ]
        )
    )
    out.append(P("Context", "h2"))
    out.append(
        P(
            "Project notes live in this device. They die if you delete the device from the Set. Clear the text to stop "
            "the AI reading project context. Disable the Context tool to stop writes. "
            "<font face='Courier' size='8'>ppal-context</font> is for production habits, not manuals."
        )
    )
    out.append(P("Setup", "h2"))
    out.append(
        bullets(
            [
                "<b>Server:</b> Start / Stop, port 3350, timeout 30 sec.",
                "If you change the port, every client must follow (<font face='Courier' size='8'>MCP_SERVER_ORIGIN</font> or the device URL).",
                "Device-wide notation (barbeat, midi-json, stark) and <b>Small Model Mode</b> live here.",
                "<b>Sample Folder</b> appears first in library search.",
                "<b>Direct Live API</b> is the same flag as <b>Genius Live API</b> on Main.",
                "Debug flags stay off for daily use unless you are diagnosing.",
            ]
        )
    )

    out.append(P("What Pal can and cannot do", "h1"))
    out.append(
        P(
            "Official Pal documents these groups: tracks and mixing; MIDI clips with text notation and transforms; "
            "audio clip <i>management</i> (not listening); Arrangement (place, move, split, duplicate, locators, take "
            "lanes); Session (scenes, capture playing, scene tempo/signature); native devices and racks; library "
            "search (Live 12.4+); playback; project settings; context and memory."
        )
    )
    out.append(
        grid(
            ["Pal can", "Pal cannot"],
            [
                ["Connect, summarize the Set, call 21 default tools", "Run without the device Running"],
                ["Tracks, returns, sends, mixer static values", "Add a VST/AU to a track"],
                ["Native Live devices and racks", "Turn unmapped third-party knobs"],
                [
                    "MIDI clips in the documented notations, including in a named key / scale from the theory books",
                    "Listen, analyze, or transcribe audio",
                ],
                [
                    "Place / gain / pitch / warp audio clips; load Simpler and Drum Rack samples",
                    "Audio-to-MIDI; detect key or tempo from a waveform",
                ],
                ["Library search (Live 12.4+)", "Write arrangement automation or clip envelopes"],
                ["Playback and project settings", "Trigger stem separation"],
                [
                    "ppal-live-api only when Genius Live API / Direct Live API is on",
                    "Invent a Live API path you did not ask for",
                ],
            ],
            [3.25 * inch, 3.25 * inch],
        )
    )
    out.append(Spacer(1, 8))
    out.append(
        P(
            "Third-party plugins: Pal can <font face='Courier' size='8'>listPlugins</font> and open a plugin window if the plugin is already on a track. It "
            "cannot instantiate the VST. Those limits are design boundaries, not bugs."
        )
    )

    out.append(P("Genius Live API", "h1"))
    out.append(
        P(
            "<b>Genius Live API</b> sits on the Main tab. It is the same Live parameter as Setup → <b>Direct Live API</b> "
            "(<font face='Courier' size='8'>direct-live-api</font> / <font face='Courier' size='8'>liveApiEnabled</font>)."
        )
    )
    out.append(
        bullets(
            [
                "<b>Off (default).</b> Daily Genius. Specialized Pal tools only.",
                "<b>On.</b> Exposes <font face='Courier' size='8'>ppal-live-api</font>. The AI can read or modify Live Set properties the specialized tools do not cover.",
            ]
        )
    )
    out.append(
        P(
            "Turn it on only when the specialized tools are not enough, or when you explicitly ask for raw Live API. "
            "Turn it off when you are done."
        )
    )
    out.append(P("The patch script is:", "plain"))
    out.append(
        P(
            "C:\\Users\\<you>\\My Apps\\producer-pal-genius\\scripts\\patch-genius-live-api.py",
            "path",
        )
    )
    out.append(
        P(
            "It injects the toggle into the frozen <font face='Courier' size='8'>tab-main.maxpat</font> inside "
            "<font face='Courier' size='8'>Producer_Pal.amxd</font> and writes "
            "<font face='Courier' size='8'>Producer_Pal.amxd.genius-toggle.bak</font> before changing the live file."
        )
    )
    out.append(
        callout(
            "After you run the script, remove Producer Pal from the track and drop it on again so Live loads the new chrome.",
            "watch",
        )
    )

    out.append(P("After a Pal update", "h1"))
    out.append(
        P(
            "An official Pal update overwrites <font face='Courier' size='8'>Producer_Pal.amxd</font>. Two things come back to stock: the "
            "<b>Genius Live API</b> toggle disappears, and <b>Open Chat UI</b> opens Chrome again."
        )
    )
    out.append(P("Fix, in order:", "plain"))
    out.extend(
        numbered(
            [
                "Confirm the new official device is the one in the User Library.",
                "From <font face='Courier' size='8'>C:\\Users\\<you>\\My Apps\\producer-pal-genius</font> run <font face='Courier' size='8'>python .\\scripts\\patch-genius-live-api.py</font>.",
                "From <font face='Courier' size='8'>C:\\Users\\<you>\\My Apps\\producer-pal-local</font> run <font face='Courier' size='8'>.\\install.ps1 -NonInteractive</font> to restore the Local button wiring.",
                "In Live, remove the device and drop it on again. Wait for <b>Running</b>.",
            ]
        )
    )
    out.append(
        P(
            "If an update goes badly, the untouched official copy is "
            "<font face='Courier' size='8'>Producer_Pal.amxd.official-2.1.0.bak</font> next to the device. That filename will be stale after you install a newer official version. Make a new "
            "<font face='Courier' size='8'>.official-*.bak</font> before you patch the next release."
        )
    )

    out.append(P("If something fails", "h1"))
    out.append(
        P(
            "<b>Device not Running.</b> Open Setup → <b>Start</b>. Port 3350. If the bar is red, three-dot menu → Open Max Window."
        )
    )
    out.append(
        P(
            "<b>Connect fails.</b> Live must be open, the device on a MIDI track, status green. Start a new conversation "
            "after you enable tools. Restart the AI app if tools were just added."
        )
    )
    out.append(
        P(
            "<b>Grok has no official Pal page.</b> Use Other MCP (<font face='Courier' size='8'>npx -y producer-pal</font>) or Producer Pal Local, which "
            "already wires that MCP. Portable Agent Skill and REST on port 3350 are also valid."
        )
    )
    out.append(
        P(
            "<b>Stale tools after you change device settings.</b> Some clients cache tool definitions. Fully quit the AI app, "
            "or toggle the extension off and on."
        )
    )
    out.append(
        P(
            "<b>Genius cites nothing / guesses a plugin or a scale.</b> The index missed that title. Add a row to "
            "<font face='Courier' size='8'>B:\\Documents\\TRAINING DOCS\\INDEX.md</font> or the matching child index, or drop the PDF in Other Manuals / plugin manuals / Music Theory and tell Genius the path once."
        )
    )
    out.append(
        P(
            "<b>You asked Pal to hear audio or draw automation.</b> That is a limit, not a broken install. Do that part in Live."
        )
    )

    out.append(P("Sources", "h1"))
    out.append(
        bullets(
            [
                "Official Pal: https://producer-pal.org/ and the filtered capture <font face='Courier' size='8'>producer-pal-ai-readable-guide.pdf</font> in this folder",
                "Genius repo: <font face='Courier' size='8'>C:\\Users\\<you>\\My Apps\\producer-pal-genius</font>",
                "Local launcher: <font face='Courier' size='8'>C:\\Users\\<you>\\My Apps\\producer-pal-local</font>",
                "Studio index: <font face='Courier' size='8'>B:\\Documents\\TRAINING DOCS\\INDEX.md</font>",
                "Live device: <font face='Courier' size='8'>A:\\User Library\\Presets\\MIDI Effects\\Max MIDI Effect\\Producer_Pal.amxd</font>",
            ]
        )
    )
    return out


def build(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="Producer Pal Genius User Manual",
        author="Studio how-to",
        subject="How Producer Pal and Genius work on this PC",
        creator="Producer Pal Genius",
    )
    doc.build(story(), onFirstPage=header_footer, onLaterPages=header_footer)


def main() -> None:
    build(LIVE)
    build(REPO)
    print("wrote", LIVE)
    print("wrote", REPO)


if __name__ == "__main__":
    main()
