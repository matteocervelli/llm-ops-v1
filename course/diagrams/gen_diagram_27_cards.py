#!/usr/bin/env python3
"""Diagram 27 (v2) — 4 system cards with pro/cons and real UI screenshots."""

import base64
import json
import os

SS = "/data/dev/demo/llm-ops-v1/.playwright-cli/screenshots"
OUT = "/data/dev/demo/llm-ops-v1/course/diagrams/excalidraw/27-agent-harness-landscape.excalidraw"

_sc = 10000


def ns():
    global _sc
    _sc += 1
    return _sc


def dataurl(f):
    with open(os.path.join(SS, f), "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    return f"data:image/png;base64,{b64}"


FILES = {
    "fc": {
        "mimeType": "image/png",
        "id": "fc",
        "dataURL": dataurl("claude-new.png"),
        "created": 1716258000000,
        "lastRetrieved": 1716258000000,
    },
    "fh": {
        "mimeType": "image/png",
        "id": "fh",
        "dataURL": dataurl("hermes-new.png"),
        "created": 1716258000000,
        "lastRetrieved": 1716258000000,
    },
    "fo": {
        "mimeType": "image/png",
        "id": "fo",
        "dataURL": dataurl("openclaw-new.png"),
        "created": 1716258000000,
        "lastRetrieved": 1716258000000,
    },
    "fp": {
        "mimeType": "image/png",
        "id": "fp",
        "dataURL": dataurl("paperclip-new.png"),
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


def line(id, x1, y1, x2, y2, color="#E0E0E0", sw=1):
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
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": None,
    }


E = []

# ── TITLE ────────────────────────────────────────────────────────────────────
E.append(text("t1", 40, 18, 1100, 36, "Agent Harness Systems — Confronto", 30, "#1B2631", "left"))
E.append(
    text(
        "t2",
        40,
        58,
        800,
        22,
        "Session 1 · LLM Ops v1 · 2026  |  Claude Code · Hermes Agent · OpenClaw · Paperclip",
        15,
        "#818586",
        "left",
    )
)

# ── CARD BUILDER ─────────────────────────────────────────────────────────────
CW = 520
IW = 500
IH = 235
HDR = 50
SEP = 8
COSA = 44
PROSEP = 8
LINE_H = 24
LABEL_H = 20


def card(sl, cx, cy, name, tagline, cosa_fa, pros, contros, stroke, fill, fid):
    es = []
    # shadow / container
    es.append(rect(f"ctr_{sl}", cx, cy, CW, CW + 10, stroke, fill, sw=2, rn=0))
    # header
    es.append(rect(f"hdr_{sl}", cx, cy, CW, HDR, stroke, stroke, sw=0, rn=0, rounded=False))
    es.append(
        text(f"hname_{sl}", cx + 12, cy + 8, CW - 24, HDR - 10, name, 17, "#FFFFFF", "left", "top")
    )
    es.append(
        text(f"htag_{sl}", cx + 12, cy + 28, CW - 24, 18, tagline, 12, "#FFFFFF", "left", "top")
    )
    # screenshot
    iy = cy + HDR + 5
    es.append(img(f"img_{sl}", cx + 10, iy, IW, IH, fid))
    # separator + cosa fa
    sep1y = iy + IH + SEP
    es.append(line(f"sep1_{sl}", cx + 12, sep1y, cx + CW - 12, sep1y, "#E8E8E8"))
    es.append(text(f"cf_lbl_{sl}", cx + 12, sep1y + 6, 70, 16, "COSA FA", 10, "#999999", "left"))
    es.append(text(f"cf_{sl}", cx + 90, sep1y + 5, CW - 102, 20, cosa_fa, 13, "#34495E", "left"))
    # PRO
    pro_y = sep1y + COSA
    es.append(line(f"sep2_{sl}", cx + 12, pro_y, cx + CW - 12, pro_y, "#E8E8E8"))
    es.append(text(f"pro_lbl_{sl}", cx + 12, pro_y + 4, 80, LABEL_H, "PRO", 11, "#4E9A44", "left"))
    for i, p in enumerate(pros):
        es.append(
            text(
                f"pro_{sl}_{i}",
                cx + 12,
                pro_y + LABEL_H + 4 + i * LINE_H,
                CW - 24,
                LINE_H,
                f"+ {p}",
                12,
                "#4E9A44",
                "left",
            )
        )
    # CONTRO
    ctr_y = pro_y + LABEL_H + 4 + len(pros) * LINE_H + 6
    es.append(line(f"sep3_{sl}", cx + 12, ctr_y, cx + CW - 12, ctr_y, "#E8E8E8"))
    es.append(
        text(f"ctr_lbl_{sl}", cx + 12, ctr_y + 4, 80, LABEL_H, "CONTRO", 11, "#C0392B", "left")
    )
    for i, c in enumerate(contros):
        es.append(
            text(
                f"ctr_{sl}_{i}",
                cx + 12,
                ctr_y + LABEL_H + 4 + i * LINE_H,
                CW - 24,
                LINE_H,
                f"- {c}",
                12,
                "#C0392B",
                "left",
            )
        )
    return es


# ── 4 CARDS ──────────────────────────────────────────────────────────────────
GAP = 60
R2 = 560 + GAP  # row2 y offset from first card top

# Row 1
E.extend(
    card(
        "cc",
        40,
        95,
        "Claude Code (il nostro stack)",
        "CLI harness · Developer-First",
        "Harness CLI con skills/hooks/rules/registry — enforcement strutturale, non suggestion",
        [
            "Defense-in-Depth 6 layer (enforcement, non prompt)",
            "Registry PDCA — lifecycle, no dark skill",
            "Hooks preventivi (bash.py exit code, non aggirabile)",
        ],
        [
            "No self-evolution autonoma delle skill",
            "Routing eval mancante (intent→skill non testato)",
            "Single-vendor (legato a Claude/Anthropic)",
        ],
        "#008080",
        "#E0F2F1",
        "fc",
    )
)

E.extend(
    card(
        "pp",
        40 + CW + GAP,
        95,
        "Paperclip (@dotta)",
        "Multi-Agent Orchestrator",
        "Control plane per fleet di agent eterogenei organizzati in una company virtuale",
        [
            "Unico orchestratore cross-vendor (Claude+Codex+OpenClaw)",
            "Token budget + audit trail immutabile per ogni agent",
            "Org chart persistente cross-session con heartbeat",
        ],
        [
            "Orchestrates agenti, non li costruisce",
            "Dipende da agent esterni funzionanti correttamente",
            "Setup complesso (PostgreSQL embedded, Node.js)",
        ],
        "#1B2631",
        "#F5E6D3",
        "fp",
    )
)

# Row 2
E.extend(
    card(
        "ha",
        40,
        95 + R2,
        "Hermes Agent (Nous Research)",
        "Self-Improving Runtime",
        "Agent runtime self-improving: impara dall'esperienza, crea skill autonomamente",
        [
            "Self-evolution autonoma (DSPy/GEPA — ICLR 2026 Oral)",
            "118 skill built-in + skill_manage autonomo",
            "Multi-platform: TUI + Telegram, Discord, WhatsApp",
        ],
        [
            "No eval di routing (skill create ma non testate)",
            "No lifecycle governance (no PDCA, no dark skill check)",
            "Setup complesso per self-hosting (7 backend opzioni)",
        ],
        "#6D28D9",
        "#EDE9FE",
        "fh",
    )
)

E.extend(
    card(
        "oc",
        40 + CW + GAP,
        95 + R2,
        "OpenClaw (Steinberger)",
        "End-User Chat Agent",
        "Agent chat-first per utenti finali, accessibile via messaging app, LLM-agnostic",
        [
            "LLM-agnostic (Claude, GPT, DeepSeek, Gemini)",
            "Zero skill CLI — puro chat, accessibile a tutti",
            "100+ plugin skill + community marketplace",
        ],
        [
            "Rischi sicurezza (data exfiltration trovata da Cisco)",
            "Governance in transizione (fondazione, Steinberger→OpenAI)",
            "Meno adatto a workflow developer complessi",
        ],
        "#DA702C",
        "#FFF3E0",
        "fo",
    )
)

# ── FOOTNOTE ─────────────────────────────────────────────────────────────────
foot_y = 95 + R2 + CW + 20
E.append(
    text(
        "fn",
        40,
        foot_y + 12,
        1100,
        20,
        "Confronto basato su: Hermes Agent v0.9 (Apr 2026) · OpenClaw v1 (2026) · "
        "Paperclip v2026.517 · Claude Code (May 2026)",
        11,
        "#CCCCCC",
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
print(f"D27: {len(E)} elements · {os.path.getsize(OUT) // 1024}KB")
