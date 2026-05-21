#!/usr/bin/env python3
"""Generate diagram 28 — Prompt Cache Flow (prefix match, layout, cost)."""

import json
import os

OUT = "/data/dev/demo/llm-ops-v1/course/diagrams/excalidraw/28-prompt-cache-flow.excalidraw"

_sc = 10000


def ns():
    global _sc
    _sc += 1
    return _sc


def rect(id, x, y, w, h, stroke, fill, sw=2, ss="solid", rounded=True):
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
        "roughness": 1,
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


def text(id, x, y, w, h, txt, fs, color, align="left", va="top"):
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
        "fontFamily": 1,
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


def arrow(id, x1, y1, x2, y2, color="#34495E", label=""):
    e = {
        "type": "arrow",
        "id": id,
        "x": x1,
        "y": y1,
        "width": x2 - x1,
        "height": y2 - y1,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
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
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": "arrow",
    }
    return e


E = []

# ── TITLE ─────────────────────────────────────────────────────────────────────
E.append(text("t1", 60, 20, 900, 36, "28 — Prompt Cache Flow", 28, "#1B2631", "left"))
E.append(text("t2", 60, 58, 600, 20, "Session 1 Blocco 3 + Module 5 LLM Ops · 2026", 14, "#818586"))

# ── SECTION 1: PROMPT LAYOUT (left column) ─────────────────────────────────
E.append(text("s1h", 60, 100, 400, 24, "① Layout ottimale per il caching", 16, "#008080"))
LAYERS = [
    ("#008080", "#E0F2F1", "TOOLS (definizioni tool)", "statico — mai cambiare"),
    (
        "#008080",
        "#E0F2F1",
        "SYSTEM PROMPT (CLAUDE.md / istruzioni)",
        "statico — breakpoint esplicito qui",
    ),
    ("#2471A3", "#EBF5FB", "SESSION CONTEXT (memoria, worktree)", "semi-statico — auto-caching"),
    ("#7D6608", "#FEFDE7", "MESSAGES (conversazione)", "dinamico — cresce ad ogni turno"),
]
LY = 130
for i, (stroke, fill, lbl, note) in enumerate(LAYERS):
    E.append(rect(f"l{i}", 60, LY + i * 62, 420, 50, stroke, fill, sw=2))
    E.append(text(f"lt{i}", 72, LY + i * 62 + 8, 300, 20, lbl, 13, "#1B2631"))
    E.append(text(f"ln{i}", 72, LY + i * 62 + 28, 400, 16, note, 11, "#818586"))

E.append(
    text("la", 200, LY + 4 * 62 + 4, 140, 18, "↑ Statico   Dinamico ↓", 11, "#999999", "center")
)
E.append(
    text(
        "lb",
        60,
        LY + 4 * 62 + 24,
        420,
        14,
        "Regola: breakpoint sull'ultimo blocco IDENTICO tra richieste",
        11,
        "#C0392B",
    )
)

# ── SECTION 2: CACHE FLOW (center column) ──────────────────────────────────
CX = 560
E.append(text("s2h", CX, 100, 400, 24, "② Prefix Match — Cache Hit/Miss/Write", 16, "#008080"))

# Request box
E.append(rect("rq", CX, 130, 340, 44, "#34495E", "#F2F3F4", sw=2))
E.append(
    text(
        "rqt",
        CX + 10,
        144,
        320,
        20,
        "API Request  (system + tools + messages)",
        12,
        "#34495E",
        "center",
    )
)

# Hash compute
E.append(arrow("a1", CX + 170, 174, CX + 170, 210, "#34495E"))
E.append(rect("hsh", CX + 60, 210, 220, 36, "#6D28D9", "#EDE9FE"))
E.append(text("hsht", CX + 70, 220, 200, 20, "Compute prefix hash", 12, "#6D28D9", "center"))

# Cache lookup
E.append(arrow("a2", CX + 170, 246, CX + 170, 280, "#34495E"))
E.append(rect("lk", CX + 60, 280, 220, 36, "#D0A215", "#FFFDE7"))
E.append(
    text("lkt", CX + 70, 290, 200, 20, "Cache lookup (20-block window)", 12, "#7D6608", "center")
)

# Hit branch
E.append(arrow("ah", CX + 60, 298, CX - 70, 340, "#4E7A44"))
E.append(rect("hit", CX - 160, 328, 160, 44, "#4E7A44", "#EAFAF1"))
E.append(text("hitt", CX - 150, 338, 140, 20, "CACHE HIT", 13, "#4E7A44", "center"))
E.append(text("hitn", CX - 150, 354, 140, 14, "0.10× costo base", 11, "#4E7A44", "center"))

# Miss branch
E.append(arrow("am", CX + 280, 298, CX + 390, 340, "#C0392B"))
E.append(rect("miss", CX + 382, 328, 160, 44, "#C0392B", "#FDEDEC"))
E.append(text("misst", CX + 392, 338, 140, 20, "CACHE MISS", 13, "#C0392B", "center"))
E.append(text("missn", CX + 392, 354, 140, 14, "1.25× costo base (write)", 11, "#C0392B", "center"))

E.append(text("hl", CX - 20, 308, 60, 14, "HIT", 11, "#4E7A44"))
E.append(text("ml", CX + 305, 308, 60, 14, "MISS", 11, "#C0392B"))

# TTL note
E.append(rect("ttl", CX + 60, 400, 220, 36, "#1B2631", "#F8F9F9"))
E.append(
    text("ttlt", CX + 70, 410, 200, 20, "TTL: 5 min (default) · 1h (2×)", 12, "#1B2631", "center")
)
E.append(arrow("a3h", CX + 110, 372, CX + 110, 400, "#4E7A44"))
E.append(arrow("a3m", CX + 460, 372, CX + 230, 400, "#C0392B"))

# ── SECTION 3: COST TABLE (right bottom) ────────────────────────────────────
TX = 560
TY = 470
E.append(text("s3h", TX, TY, 400, 24, "③ Costo differenziale", 16, "#008080"))
COSTS = [
    ("#4E7A44", "#EAFAF1", "Cache READ", "0.10×  →  90% risparmio"),
    ("#D0A215", "#FFFDE7", "Cache WRITE", "1.25×  →  25% sovraprezzo"),
    ("#34495E", "#F2F3F4", "Uncached", "1.00×  →  baseline"),
]
for i, (stroke, fill, lbl, note) in enumerate(COSTS):
    E.append(rect(f"c{i}", TX, TY + 32 + i * 48, 340, 38, stroke, fill, sw=2))
    E.append(text(f"ctl{i}", TX + 10, TY + 40 + i * 48, 130, 20, lbl, 13, stroke))
    E.append(text(f"ctn{i}", TX + 150, TY + 40 + i * 48, 180, 20, note, 12, "#34495E"))

# ── ANTI-PATTERN CALLOUT ──────────────────────────────────────────────────────
E.append(rect("ap", 60, 440, 420, 128, "#C0392B", "#FDEDEC", sw=2, ss="dashed"))
E.append(text("aph", 72, 450, 396, 20, "⚠️ Anti-pattern che rompono la cache", 13, "#C0392B"))
AP = [
    "Timestamp/data nel system prompt → usare <system-reminder> nei messaggi",
    "Aggiungere/rimuovere tool mid-session → tenerli fissi (EnterPlanMode pattern)",
    "Cambiare modello mid-session → subagenti con contesto proprio",
]
for i, line in enumerate(AP):
    E.append(text(f"ap{i}", 72, 474 + i * 30, 396, 22, f"• {line}", 11, "#34495E"))

# ── FOOTNOTE ─────────────────────────────────────────────────────────────────
E.append(
    text(
        "fn",
        60,
        590,
        900,
        16,
        "Claude Code: Plan Mode = tool (non swap) · <system-reminder> = dynamic update "
        "senza rompere cache · compaction usa stesso prefix del parent",
        11,
        "#BBBBBB",
    )
)

diagram = {
    "type": "excalidraw",
    "version": 2,
    "source": "https://excalidraw.com",
    "elements": E,
    "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
    "files": {},
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(diagram, f)
print(f"✓ {len(E)} elements · {os.path.getsize(OUT) // 1024}KB")
