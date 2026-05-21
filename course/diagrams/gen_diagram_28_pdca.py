#!/usr/bin/env python3
"""Diagram 28 — Registry PDCA: Skill Lifecycle nel nostro stack."""

import json
import os

OUT = (
    "/data/dev/demo/llm-ops-v1/course/diagrams/excalidraw/"
    "28-registry-pdca-skill-lifecycle.excalidraw"
)

_sc = 10000


def ns():
    global _sc
    _sc += 1
    return _sc


def rect(id, x, y, w, h, stroke, fill, sw=2, ss="solid", rn=0, rounded=True):
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
        "roughness": rn if (rn := 0) is not None else 1,
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


def arrow(id, x1, y1, x2, y2, color="#34495E", sw=2, ss="solid", bi=False):
    return {
        "type": "arrow",
        "id": id,
        "x": x1,
        "y": y1,
        "width": abs(x2 - x1),
        "height": abs(y2 - y1),
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
        "startArrowhead": "arrow" if bi else None,
        "endArrowhead": "arrow",
    }


def code_box(id, x, y, w, lines):
    """Dark code snippet box."""
    lh = 20
    pad = 12
    h = pad * 2 + len(lines) * lh
    elems = [rect(id + "_bg", x, y, w, h, "#1E293B", "#1E293B", sw=0, rounded=True)]
    for i, ln in enumerate(lines):
        col = "#22C55E" if ln.startswith("#") else ("#94A3B8" if ln.startswith("  ") else "#F8FAFC")
        elems.append(
            text(
                id + f"_l{i}",
                x + pad,
                y + pad + i * lh,
                w - pad * 2,
                lh,
                ln,
                12,
                col,
                "left",
                "top",
                3,
            )
        )
    return elems, h


def line_e(id, x1, y1, x2, y2, color="#E0E0E0", sw=1, ss="solid"):
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
E.append(
    text(
        "t1",
        40,
        18,
        1400,
        36,
        "Registry PDCA — Skill Lifecycle nel Claude Code Stack",
        30,
        "#1B2631",
        "left",
    )
)
E.append(
    text(
        "t2",
        40,
        58,
        900,
        22,
        "Come il nostro sistema gestisce le skill: dal problema al fix permanente, "
        "senza skill irraggiungibili",
        15,
        "#818586",
        "left",
    )
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION A — Anatomia di una Skill (left column, x=40..480)
# ─────────────────────────────────────────────────────────────────────────────
AX = 40
AY = 100
AW = 430

E.append(text("a_ttl", AX, AY, AW, 28, "Anatomia di una Skill", 20, "#008080", "left"))
E.append(
    text(
        "a_sub",
        AX,
        AY + 30,
        AW,
        20,
        "Ogni skill è un file SKILL.md + codice + test",
        13,
        "#818586",
        "left",
    )
)

# SKILL.md structure box
code_lines_skill = [
    "# ~/.claude/skills/my-skill.md",
    "",
    "---",
    "name: my-skill",
    "description: Quando e perché usarla",
    "triggers:",
    "  - pattern: 'fai X'",
    "  - pattern: 'X please'",
    "status: active   # planned|active|deprecated",
    "pdca: check      # plan|do|check|act",
    "---",
    "",
    "## Steps",
    "1. Verifica precondizioni",
    "2. Esegui task principale",
    "3. Valida output",
]
cb1, h1 = code_box("cb_skill", AX, AY + 60, AW, code_lines_skill)
E.extend(cb1)

# 3 components below
comp_y = AY + 60 + h1 + 16
comps = [
    ("#22C55E", "Tests", "pytest / vitest\nper ogni skill"),
    ("#4385BE", "Triggers", "Pattern in AGENTS.md\nrouting → skill"),
    ("#D0A215", "Registry", "/registry status\nPDCA tracking"),
]
comp_w = (AW - 20) // 3
for i, (col, name, desc) in enumerate(comps):
    cx2 = AX + i * (comp_w + 10)
    E.append(rect(f"comp_{i}", cx2, comp_y, comp_w, 64, col, col + "22", sw=2, rn=0, rounded=True))
    E.append(text(f"comp_n_{i}", cx2 + 8, comp_y + 8, comp_w - 16, 22, name, 14, col, "left"))
    E.append(
        text(f"comp_d_{i}", cx2 + 8, comp_y + 30, comp_w - 16, 30, desc, 11, "#34495E", "left")
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION B — PDCA Cycle (center, x=510..1050)
# ─────────────────────────────────────────────────────────────────────────────
BX = 510
BY = 100
BW = 540

E.append(text("b_ttl", BX, BY, BW, 28, "PDCA — Lifecycle delle Skill", 20, "#1B2631", "center"))
E.append(
    text(
        "b_sub",
        BX,
        BY + 30,
        BW,
        20,
        "4 fasi, loop continuo, nessuna skill lasciata indietro",
        13,
        "#818586",
        "center",
    )
)

# PDCA boxes in 2x2 layout
PBW = 240
PBH = 190
P_GAP = 20
p1x = BX
p1y = BY + 66  # PLAN top-left
p2x = BX + PBW + P_GAP
p2y = BY + 66  # DO top-right
p3x = BX
p3y = BY + 66 + PBH + P_GAP  # CHECK bottom-left
p4x = BX + PBW + P_GAP
p4y = BY + 66 + PBH + P_GAP  # ACT bottom-right

pdca_data = [
    (
        p1x,
        p1y,
        "PLAN",
        "#4385BE",
        "#EBF5FB",
        "Skill identificata\ncome necessaria",
        [
            "Analisi: è davvero nuova?",
            "Frontmatter bozza",
            "Aggiunta al registry\nin stato planned",
        ],
    ),
    (
        p2x,
        p2y,
        "DO",
        "#879A39",
        "#F1F8E9",
        "Implementazione\ne test",
        ["SKILL.md completo", "Codice/script scritto", "Tests che passano", "Trigger in AGENTS.md"],
    ),
    (
        p3x,
        p3y,
        "CHECK",
        "#D0A215",
        "#FFFDE7",
        "Audit periodico\ndella skill",
        ["/registry audit", "Verifica raggiungibilità", "DRY check (duplicati)", "Eval di routing"],
    ),
    (
        p4x,
        p4y,
        "ACT",
        "#008080",
        "#E0F2F1",
        "Decisione\npost-audit",
        ["ACTIVE: skill sana", "DEPRECATE: obsoleta", "MERGE: è duplicato", "FIX: trigger rotto"],
    ),
]

for bx, by, name, stroke, fill, sub, items in pdca_data:
    E.append(rect(f"pb_{name}", bx, by, PBW, PBH, stroke, fill, sw=2, rn=0, rounded=True))
    E.append(rect(f"pbhdr_{name}", bx, by, PBW, 42, stroke, stroke, sw=0, rn=0, rounded=False))
    E.append(text(f"pbname_{name}", bx, by + 10, PBW, 24, name, 18, "#FFFFFF", "center", "top"))
    E.append(text(f"pbsub_{name}", bx + 8, by + 46, PBW - 16, 30, sub, 12, "#34495E", "left"))
    for i, it in enumerate(items):
        E.append(
            text(
                f"pbit_{name}_{i}",
                bx + 8,
                by + 82 + i * 24,
                PBW - 16,
                22,
                f"• {it}",
                11,
                "#555555",
                "left",
            )
        )

# Arrows between PDCA phases (cycle)
arrow_mid_x = BX + PBW + P_GAP // 2
arrow_mid_y = BY + 66 + PBH + P_GAP // 2
# PLAN→DO (right)
E.append(arrow("pa_pd", p1x + PBW, p1y + PBH // 2, p2x, p2y + PBH // 2, "#4385BE", 2, "solid"))
# DO→ACT (down)
E.append(arrow("pa_da", p2x + PBW // 2, p2y + PBH, p4x + PBW // 2, p4y, "#879A39", 2, "solid"))
# ACT→CHECK (left)
E.append(arrow("pa_ac", p4x, p4y + PBH // 2, p3x + PBW, p3y + PBH // 2, "#008080", 2, "solid"))
# CHECK→PLAN (up)
E.append(arrow("pa_cp", p3x + PBW // 2, p3y, p1x + PBW // 2, p1y + PBH, "#D0A215", 2, "solid"))

# Center label in the cycle
cx2 = BX + PBW // 2 + P_GAP // 2
cy2 = BY + 66 + PBH // 2 + P_GAP // 2
E.append(
    text(
        "cycle_lbl",
        BX + PBW // 2 - 30,
        BY + 66 + PBH // 2,
        P_GAP + 60,
        P_GAP,
        "↻",
        22,
        "#AAAAAA",
        "center",
    )
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION C — Dark Skills Problem (right column, x=1090..1540)
# ─────────────────────────────────────────────────────────────────────────────
CX = 1090
CY = 100
CW2 = 440

E.append(text("c_ttl", CX, CY, CW2, 28, "Il Problema Dark Skills", 20, "#D14D41", "left"))
E.append(
    text(
        "c_sub",
        CX,
        CY + 30,
        CW2,
        20,
        "Skill esistenti ma irraggiungibili — common failure mode",
        13,
        "#818586",
        "left",
    )
)

# Before/after comparison
BA_Y = CY + 66
E.append(rect("before_bg", CX, BA_Y, CW2, 130, "#D14D41", "#FFEBEE", sw=2, rn=0, rounded=True))
E.append(text("before_lbl", CX + 12, BA_Y + 8, 100, 22, "PRIMA", 12, "#D14D41", "left"))
E.append(
    text(
        "before_t1",
        CX + 12,
        BA_Y + 30,
        CW2 - 24,
        20,
        "40 skill nel sistema — 6 irraggiungibili",
        13,
        "#D14D41",
        "left",
    )
)
E.append(
    text(
        "before_t2",
        CX + 12,
        BA_Y + 52,
        CW2 - 24,
        18,
        "• Trigger description ambigue",
        12,
        "#888888",
        "left",
    )
)
E.append(
    text(
        "before_t3",
        CX + 12,
        BA_Y + 70,
        CW2 - 24,
        18,
        "• Skill con stessa funzione (duplicati)",
        12,
        "#888888",
        "left",
    )
)
E.append(
    text(
        "before_t4",
        CX + 12,
        BA_Y + 88,
        CW2 - 24,
        18,
        "• Script referenziato ma non esiste",
        12,
        "#888888",
        "left",
    )
)
E.append(
    text(
        "before_t5",
        CX + 12,
        BA_Y + 108,
        CW2 - 24,
        18,
        "= 15% capabilities silently dark",
        12,
        "#D14D41",
        "left",
    )
)

E.append(
    arrow("arrow_ba", CX + CW2 // 2, BA_Y + 130, CX + CW2 // 2, BA_Y + 148, "#008080", 2, "solid")
)

after_y = BA_Y + 152
E.append(rect("after_bg", CX, after_y, CW2, 130, "#008080", "#E0F2F1", sw=2, rn=0, rounded=True))
E.append(text("after_lbl", CX + 12, after_y + 8, 100, 22, "DOPO", 12, "#008080", "left"))
E.append(
    text(
        "after_t1",
        CX + 12,
        after_y + 30,
        CW2 - 24,
        20,
        "/registry audit — weekly automatico",
        13,
        "#008080",
        "left",
    )
)
E.append(
    text(
        "after_t2",
        CX + 12,
        after_y + 52,
        CW2 - 24,
        18,
        "• Ogni skill ha status: planned|active|deprecated",
        12,
        "#555555",
        "left",
    )
)
E.append(
    text(
        "after_t3",
        CX + 12,
        after_y + 70,
        CW2 - 24,
        18,
        "• Trigger unici, nessuna ambiguità",
        12,
        "#555555",
        "left",
    )
)
E.append(
    text(
        "after_t4",
        CX + 12,
        after_y + 88,
        CW2 - 24,
        18,
        "• Script verificati a runtime",
        12,
        "#555555",
        "left",
    )
)
E.append(
    text(
        "after_t5",
        CX + 12,
        after_y + 108,
        CW2 - 24,
        18,
        "= 0% dark skills, 100% raggiungibili",
        12,
        "#008080",
        "left",
    )
)

# /registry command example
cmd_y = after_y + 148
cb2, h2 = code_box(
    "cb_reg",
    CX,
    cmd_y,
    CW2,
    [
        "# /registry audit output",
        "$ claude /registry",
        "",
        "  ACTIVE    42 skills   ✓ reachable",
        "  PLANNED    3 skills   waiting impl",
        "  DARK       0 skills   ← obiettivo",
        "  DEPRECATED 2 skills   archived",
        "",
        "  DRY violations: 0",
        "  Routing conflicts: 0",
    ],
)
E.extend(cb2)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION D — Skillify Loop (bottom, full width)
# ─────────────────────────────────────────────────────────────────────────────
sec_a_bottom = AY + 60 + h1 + 16 + 64 + 20
sec_b_bottom = BY + 66 + PBH * 2 + P_GAP + 20
sec_c_bottom = CY + 66 + 130 + 4 + 130 + 4 + h2 + 20
DY = max(sec_a_bottom, sec_b_bottom, sec_c_bottom) + 40

E.append(line_e("sep_d", 40, DY - 16, 1540, DY - 16, "#EEEEEE", 1))
E.append(
    text(
        "d_ttl",
        40,
        DY,
        600,
        28,
        "Il Loop Skillify — Failure → Fix Permanente",
        20,
        "#1B2631",
        "left",
    )
)
E.append(
    text(
        "d_sub",
        40,
        DY + 30,
        900,
        20,
        "Ogni failure diventa una skill con tests. "
        "Il bug diventa strutturalmente impossibile da ripetere.",
        13,
        "#818586",
        "left",
    )
)

steps_d = [
    ("#D14D41", "FAILURE\nRilevata", "Agent fa qualcosa\ndi sbagliato 2 volte"),
    ("#D0A215", "IDENTIFICA\nPattern", "È deterministico?\nPuò essere fixato con codice?"),
    ("#4385BE", "SKILL.md\n+ Codice", "Scrivi contratto\nScript/tool deterministico"),
    ("#879A39", "TESTS\n+ Trigger", "Unit test + eval\nAGENTS.md trigger"),
    ("#008080", "REGISTRY\nAudit", "/registry check\nDRY, raggiungibilità"),
    ("#1B2631", "PERMANENT\nFix", "Bug strutturalmente\nimpossibile da ripetere"),
]
SW_D = 220
SH_D = 80
SG_D = 14
tot_w = len(steps_d) * (SW_D + SG_D) - SG_D
sx_start = (1540 - tot_w) // 2
for i, (col, name, desc) in enumerate(steps_d):
    sx = sx_start + i * (SW_D + SG_D)
    sy = DY + 66
    E.append(rect(f"sd_{i}", sx, sy, SW_D, SH_D, col, col + "22", sw=2, rn=0, rounded=True))
    E.append(rect(f"sdhdr_{i}", sx, sy, SW_D, 36, col, col, sw=0, rn=0, rounded=False))
    E.append(text(f"sdname_{i}", sx, sy + 4, SW_D, 28, name, 12, "#FFFFFF", "center", "top"))
    E.append(
        text(f"sddesc_{i}", sx + 6, sy + 40, SW_D - 12, 36, desc, 11, "#34495E", "center", "top")
    )
    if i < len(steps_d) - 1:
        ax = sx + SW_D + 2
        ay = sy + SH_D // 2
        E.append(arrow(f"sda_{i}", ax, ay, ax + SG_D + 2, ay, col, 2, "solid"))

E.append(
    text(
        "d_note",
        40,
        DY + 66 + SH_D + 16,
        1460,
        20,
        'Fonte pattern: Gary Tan — "Skillify" (2026) · Nostra implementazione: '
        "hooks + registry PDCA invece di GBrain",
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
    "files": {},
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(diagram, f)
print(f"D28: {len(E)} elements · {os.path.getsize(OUT) // 1024}KB")
