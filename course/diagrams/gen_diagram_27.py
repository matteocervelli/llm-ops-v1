#!/usr/bin/env python3
"""Generate diagram 27 — Agent Harness Landscape with embedded screenshots."""

import json, base64, os

SCREENSHOTS = "/data/dev/demo/llm-ops-v1/.playwright-cli/screenshots"
OUT = "/data/dev/demo/llm-ops-v1/course/diagrams/excalidraw/27-agent-harness-landscape.excalidraw"

_sc = 10000


def ns():
    global _sc
    _sc += 1
    return _sc


def dataurl(fname):
    with open(os.path.join(SCREENSHOTS, fname), "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{b64}"


FILES = {
    "fc": {
        "mimeType": "image/png",
        "id": "fc",
        "dataURL": dataurl("claude-code-crop.png"),
        "created": 1716258000000,
        "lastRetrieved": 1716258000000,
    },
    "fh": {
        "mimeType": "image/png",
        "id": "fh",
        "dataURL": dataurl("hermes-crop.png"),
        "created": 1716258000000,
        "lastRetrieved": 1716258000000,
    },
    "fo": {
        "mimeType": "image/png",
        "id": "fo",
        "dataURL": dataurl("openclaw-crop.png"),
        "created": 1716258000000,
        "lastRetrieved": 1716258000000,
    },
    "fp": {
        "mimeType": "image/png",
        "id": "fp",
        "dataURL": dataurl("paperclip-crop.png"),
        "created": 1716258000000,
        "lastRetrieved": 1716258000000,
    },
}


def rect(id, x, y, w, h, stroke, fill, sw=2, ss="solid", rn=1, rounded=True):
    e = {
        "type": "rectangle",
        "id": id,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "strokeColor": stroke,
        "backgroundColor": fill,
        "fillStyle": "solid",
        "strokeWidth": sw,
        "strokeStyle": ss,
        "roughness": rn,
        "opacity": 100,
        "angle": 0,
        "seed": ns(),
        "version": 1,
        "versionNonce": ns(),
        "isDeleted": False,
        "groupIds": [],
        "boundElements": [],
        "link": None,
        "locked": False,
    }
    if rounded:
        e["roundness"] = {"type": 3}
    return e


def text(id, x, y, w, h, txt, fs, color, align="left", va="top", fam=1):
    return {
        "type": "text",
        "id": id,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "text": txt,
        "originalText": txt,
        "fontSize": fs,
        "fontFamily": fam,
        "textAlign": align,
        "verticalAlign": va,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "angle": 0,
        "seed": ns(),
        "version": 1,
        "versionNonce": ns(),
        "isDeleted": False,
        "groupIds": [],
        "boundElements": None,
        "link": None,
        "locked": False,
        "containerId": None,
        "lineHeight": 1.25,
    }


def img(id, x, y, w, h, fid):
    return {
        "type": "image",
        "id": id,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "fileId": fid,
        "status": "saved",
        "scale": [1, 1],
        "strokeColor": "transparent",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "angle": 0,
        "seed": ns(),
        "version": 1,
        "versionNonce": ns(),
        "isDeleted": False,
        "groupIds": [],
        "boundElements": None,
        "link": None,
        "locked": False,
    }


def line(id, x1, y1, x2, y2, color="#C5C5C5", sw=1, ss="solid"):
    return {
        "type": "line",
        "id": id,
        "x": x1,
        "y": y1,
        "width": x2 - x1,
        "height": y2 - y1,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": sw,
        "strokeStyle": ss,
        "roughness": 0,
        "opacity": 100,
        "angle": 0,
        "seed": ns(),
        "version": 1,
        "versionNonce": ns(),
        "isDeleted": False,
        "groupIds": [],
        "boundElements": None,
        "link": None,
        "locked": False,
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": None,
    }


E = []

# ── TITLE ────────────────────────────────────────────────────────────────────
E.append(text("t1", 80, 18, 1200, 38, "Code as Agent Harness — Landscape", 30, "#1B2631", "left"))
E.append(text("t2", 80, 58, 700, 22, "Session 1 · LLM Ops v1 · 2026", 16, "#818586", "left"))

# ── QUADRANT ─────────────────────────────────────────────────────────────────
AX_X = 810
AX_Y = 650
QL = 80
QR = 1600
QT = 95
QB = 1125

E.append(line("ah", QL, AX_Y, QR, AX_Y, "#DDDDDD", 1))
E.append(line("av", AX_X, QT, AX_X, QB, "#DDDDDD", 1))

E.append(text("lt", AX_X + 14, QT - 2, 380, 20, "↑  DEVELOPER-FIRST (CLI / IDE)", 13, "#999999"))
E.append(text("lb", AX_X + 14, QB + 4, 360, 20, "↓  END-USER (Chat / Messaging)", 13, "#999999"))
E.append(text("ll", QL, AX_Y + 9, 180, 20, "← SINGLE AGENT", 13, "#999999"))
E.append(text("lr", QR - 310, AX_Y + 9, 310, 20, "MULTI-AGENT ORCHESTRATION →", 13, "#999999"))

# ── SYSTEM BOX BUILDER ───────────────────────────────────────────────────────
BW = 400
HH = 48
IW = 380
IH = 178
DH = 50
BH = HH + 6 + IH + DH  # BH=282


def sysbox(sl, x, y, name, d1, d2, stroke, fill, fid):
    es = []
    es.append(rect(f"c_{sl}", x, y, BW, BH, stroke, fill, sw=2, rn=0))
    es.append(rect(f"h_{sl}", x, y, BW, HH, stroke, stroke, sw=0, rn=0, rounded=False))
    # Claude Code header slightly thicker
    sw_hdr = 3 if sl == "cc" else 2
    name_x = x + BW // 2 - len(name) * 4  # rough centering
    es.append(
        text(f"ht_{sl}", x + 10, y + 14, BW - 20, HH - 16, name, 16, "#FFFFFF", "center", "top")
    )
    es.append(img(f"i_{sl}", x + 10, y + HH + 6, IW, IH, fid))
    es.append(text(f"d1_{sl}", x + 8, y + HH + 6 + IH + 5, BW - 16, 22, d1, 13, "#34495E"))
    es.append(text(f"d2_{sl}", x + 8, y + HH + 6 + IH + 26, BW - 16, 20, d2, 12, "#818586"))
    return es


# TOP-LEFT: Claude Code
E.extend(
    sysbox(
        "cc",
        110,
        115,
        "Claude Code (il nostro stack)",
        "Skills + Hooks + Rules + Registry PDCA",
        "Defense-in-Depth (6 layers)",
        "#008080",
        "#E0F2F1",
        "fc",
    )
)

# TOP-RIGHT: Paperclip
E.extend(
    sysbox(
        "pp",
        840,
        115,
        "Paperclip (@dotta) — Multi-Agent",
        "Org chart per agent fleet · token budgets",
        "Cross-vendor: Claude + Codex + OpenClaw · 66.8K ★",
        "#1B2631",
        "#F5E6D3",
        "fp",
    )
)

# LEFT MID (straddling axis): Hermes Agent
E.extend(
    sysbox(
        "ha",
        110,
        540,
        "Hermes Agent (Nous Research)",
        "118 skills · autonomous skill_manage · 160K ★",
        "DSPy self-evolution · agentskills.io standard",
        "#6D28D9",
        "#EDE9FE",
        "fh",
    )
)

# BOTTOM-LEFT: OpenClaw
E.extend(
    sysbox(
        "oc",
        110,
        833,
        "OpenClaw (Steinberger) — End-User",
        "Chat-first UX · LLM-agnostic · 247K ★",
        "100+ plugin skills · community marketplace",
        "#DA702C",
        "#FFF3E0",
        "fo",
    )
)

# ── GAP ANALYSIS BOX ─────────────────────────────────────────────────────────
GX, GY, GW, GH = 840, 435, 700, 285
E.append(rect("gbg", GX, GY, GW, GH, "#D0A215", "#FFFDE7", sw=2, rn=0))
E.append(
    text(
        "gtt",
        GX + 14,
        GY + 12,
        GW - 28,
        26,
        "Gap Analysis — Nostro Stack vs Skillify",
        17,
        "#1B2631",
        "left",
    )
)
GA_LINES = [
    ("✅", "Hooks preventivi (bash.py) ≈ constraint strutturali", "#4E7A44"),
    ("✅", "Registry PDCA ≈ check-resolvable (skill dark)", "#4E7A44"),
    ("✅", "Hookify ≈ failure → structural fix permanente", "#4E7A44"),
    ("⚠️", "MANCA: Routing eval — test intent → skill corretta", "#C0392B"),
    ("⚠️", "MANCA: Skill health check periodico automatico", "#C0392B"),
    ("⚠️", "MANCA: DRY audit cross-skill", "#C0392B"),
]
for i, (icon, t, col) in enumerate(GA_LINES):
    E.append(text(f"gl{i}", GX + 14, GY + 48 + i * 37, GW - 28, 26, f"{icon}  {t}", 13, col))

# ── SKILL PDCA CALLOUT ───────────────────────────────────────────────────────
PX, PY, PW, PH = 840, 738, 700, 310
E.append(rect("pbg", PX, PY, PW, PH, "#008080", "#E0F2F1", sw=2, rn=0))
E.append(
    text(
        "ptt",
        PX + 14,
        PY + 12,
        PW - 28,
        26,
        "Registry PDCA — Lifecycle delle Skill",
        17,
        "#008080",
        "left",
    )
)
E.append(
    text(
        "psu",
        PX + 14,
        PY + 40,
        PW - 28,
        20,
        "Risposta al problema Dark Skills (skill irraggiungibili)",
        13,
        "#34495E",
        "left",
    )
)

SW4 = (PW - 44) // 4 - 4  # ~159
STEPS = [
    ("PLAN", "#4385BE", "Skill proposta,\nidentificata nel\nregistry"),
    ("DO", "#879A39", "Implementata,\ntestata,\nregistrata"),
    ("CHECK", "#D0A215", "/registry audit\nraggiungibilità,\nDRY, status"),
    ("ACT", "#008080", "Fix, deprecate\no promote a\nstandard"),
]
for i, (sn, sc, sd) in enumerate(STEPS):
    sx = PX + 22 + i * (SW4 + 8)
    sy = PY + 72
    E.append(rect(f"ps{i}", sx, sy, SW4, 44, sc, sc, sw=0, rn=0, rounded=True))
    E.append(text(f"pst{i}", sx, sy + 13, SW4, 20, sn, 14, "#FFFFFF", "center", "top"))
    E.append(text(f"psd{i}", sx - 2, sy + 50, SW4 + 4, 54, sd, 11, "#34495E", "center", "top"))
    if i < 3:
        E.append(line(f"pa{i}", sx + SW4 + 2, sy + 22, sx + SW4 + 9, sy + 22, "#34495E", 1))

E.append(
    text(
        "pft",
        PX + 14,
        PY + PH - 26,
        PW - 28,
        20,
        "Non basta avere skill — serve un sistema che le tenga vive e raggiungibili",
        12,
        "#818586",
        "left",
    )
)

# ── FOOTNOTE ─────────────────────────────────────────────────────────────────
E.append(
    text(
        "fn",
        QL,
        QB + 15,
        900,
        20,
        "Hermes Agent: posizionato tra i due assi — TUI dev-first + Telegram/Discord end-user",
        12,
        "#BBBBBB",
        "left",
    )
)

diagram = {
    "type": "excalidraw",
    "version": 2,
    "source": "https://excalidraw.com",
    "elements": E,
    "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
    "files": FILES,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(diagram, f)
print(f"✓ {len(E)} elements · {os.path.getsize(OUT) // 1024}KB")
