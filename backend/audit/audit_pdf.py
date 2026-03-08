"""
audit_pdf.py
─────────────
Branded PDF report for the Decision Audit Trail using reportlab canvas API
(direct drawing — avoids Platypus table nesting issues).
"""

from __future__ import annotations
import io
import re
import time
import textwrap
from typing import Any

from reportlab.pdfgen  import canvas
from reportlab.lib     import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# ── Brand palette ─────────────────────────────────────────────────────────
HEX = lambda h: colors.HexColor(h)
C_BG     = HEX("#0c1119")
C_TEAL   = HEX("#00d4ff")
C_GREEN  = HEX("#39d98a")
C_AMBER  = HEX("#ffb340")
C_PURPLE = HEX("#9b5de5")
C_RED    = HEX("#ff3b5c")
C_NAVY   = HEX("#0d2233")
C_BORDER = HEX("#1a3a52")
C_TEXT   = HEX("#c8dcea")
C_MUTED  = HEX("#7aa0be")
C_WHITE  = colors.white

AGENT_COL_MAP = {
    "logistics":   HEX("#00d4ff"),
    "finance":     HEX("#39d98a"),
    "procurement": HEX("#ffb340"),
    "sales":       HEX("#9b5de5"),
    "risk":        HEX("#ff3b5c"),
    "vp":          HEX("#39d98a"),
    "orchestrator":HEX("#00d4ff"),
}

def _agent_color(label: str, fallback: str = "#00d4ff"):
    low = label.lower()
    for k, c in AGENT_COL_MAP.items():
        if k in low:
            return c
    try:
        return HEX(fallback)
    except Exception:
        return C_TEAL

def _safe(text, maxlen=300):
    if not text:
        return ""
    clean = "".join(ch if ord(ch) < 0x2500 else " " for ch in str(text))
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:maxlen]

def _wrap(text, width=90):
    return textwrap.wrap(text, width=width) or [""]

# ── Canvas helpers ─────────────────────────────────────────────────────────

class PDFPainter:
    def __init__(self, buf):
        self.W, self.H = A4
        self.c   = canvas.Canvas(buf, pagesize=A4)
        self.LM  = 18 * mm     # left margin
        self.RM  = self.W - 18 * mm
        self.CW  = self.RM - self.LM
        self.y   = self.H - 18 * mm   # current y cursor (top-down)
        self.PAGE = 1

    # ── low-level ──────────────────────────────────────────────────────────
    def _set(self, color):
        self.c.setFillColor(color)
        self.c.setStrokeColor(color)

    def rect(self, x, y, w, h, fill=C_NAVY, stroke=C_BORDER, sw=0.5):
        self.c.setFillColor(fill)
        self.c.setStrokeColor(stroke)
        self.c.setLineWidth(sw)
        self.c.rect(x, y, w, h, fill=1, stroke=1)

    def line(self, x1, y1, x2, y2, color=C_BORDER, w=0.5):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(w)
        self.c.line(x1, y1, x2, y2)

    def text(self, x, y, txt, font="Helvetica", size=9, color=C_TEXT):
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        self.c.drawString(x, y, txt)

    def rtext(self, x, y, txt, font="Helvetica", size=9, color=C_TEXT):
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        self.c.drawRightString(x, y, txt)

    def need(self, h, margin=18*mm):
        """Check if we need a new page."""
        if self.y - h < margin:
            self._new_page()

    def _new_page(self):
        self._draw_footer()
        self.c.showPage()
        self.PAGE += 1
        self.y = self.H - 18 * mm
        self._draw_page_header()

    def _draw_footer(self):
        fx = self.LM
        fy = 12 * mm
        self.line(fx, fy + 4, self.RM, fy + 4, C_BORDER, 0.3)
        self.text(fx, fy, "ChainGuardAI  ·  Confidential  ·  AI-generated — verify before execution",
                  size=7, color=C_MUTED)
        self.rtext(self.RM, fy, f"Page {self.PAGE}", size=7, color=C_MUTED)

    def _draw_page_header(self):
        """Compact repeat header on continuation pages."""
        self.rect(self.LM, self.y - 8*mm, self.CW, 8*mm, fill=C_BG, stroke=C_BG)
        self.text(self.LM + 2, self.y - 5.5*mm,
                  "ChainGuardAI — Decision Audit Trail (continued)",
                  font="Helvetica-Bold", size=9, color=C_TEAL)
        self.y -= 10 * mm

    def advance(self, h):
        self.y -= h

    # ── high-level blocks ──────────────────────────────────────────────────
    def draw_header(self, run_id, scenario_str, customer, generated_at):
        H = 22 * mm
        self.rect(self.LM, self.y - H, self.CW, H, fill=C_BG, stroke=C_BG)
        # Brand name
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(C_TEAL)
        self.c.drawString(self.LM + 5, self.y - 10*mm, "ChainGuard")
        tw = self.c.stringWidth("ChainGuard", "Helvetica-Bold", 20)
        self.c.setFillColor(C_WHITE)
        self.c.drawString(self.LM + 5 + tw, self.y - 10*mm, "AI")
        # Right side
        sc_disp = scenario_str.replace("_", " ").title()
        self.rtext(self.RM - 5, self.y - 7*mm, "DECISION AUDIT TRAIL",
                   font="Helvetica-Bold", size=11, color=C_WHITE)
        self.rtext(self.RM - 5, self.y - 12*mm, sc_disp,
                   font="Helvetica", size=9, color=C_MUTED)
        if customer:
            self.rtext(self.RM - 5, self.y - 16.5*mm, f"Customer: {customer}",
                       font="Helvetica", size=8, color=C_MUTED)
        # Teal underline
        self.line(self.LM, self.y - H, self.RM, self.y - H, C_TEAL, 2)
        self.y -= H + 4*mm
        # Sub-header
        self.text(self.LM, self.y,
                  f"Run ID: {run_id}   ·   Generated: {generated_at}",
                  size=8, color=C_MUTED)
        self.y -= 6*mm

    def draw_metrics(self, metrics: list[tuple[str,str]]):
        """Draw a row of metric boxes."""
        N = len(metrics)
        bw = self.CW / N
        bh = 14 * mm
        for i, (lbl, val) in enumerate(metrics):
            x = self.LM + i * bw
            self.rect(x, self.y - bh, bw - 1, bh, fill=C_NAVY, stroke=C_BORDER)
            self.text(x + 5, self.y - 5*mm, lbl.upper(), size=7, color=C_MUTED,
                      font="Helvetica-Bold")
            self.text(x + 5, self.y - 11*mm, val, size=13, color=C_WHITE,
                      font="Helvetica-Bold")
        self.y -= bh + 5*mm

    def draw_section_title(self, title):
        self.text(self.LM, self.y, title, font="Helvetica-Bold", size=10, color=C_TEAL)
        self.y -= 3*mm
        self.line(self.LM, self.y, self.RM, self.y, C_TEAL, 0.5)
        self.y -= 4*mm

    def draw_audit_card(self, item: dict):
        """Draw one audit event card. Returns height used."""
        time_label  = _safe(item.get("time_label") or item.get("time") or "")
        agent_label = _safe(item.get("agent_label") or item.get("agent") or "Unknown")
        description = _safe(item.get("description") or "", 350)
        data        = _safe(item.get("data") or "", 200)
        mem_note    = _safe(item.get("memory_note") or item.get("memory") or "", 200)
        dot_color   = _agent_color(agent_label, item.get("agent_color", "#00d4ff"))

        # Estimate height
        desc_lines = _wrap(description, 88)
        data_lines = _wrap(data, 88) if data else []
        mem_lines  = _wrap(mem_note, 88) if mem_note else []
        LINE_H = 3.8 * mm
        PAD    = 3 * mm
        card_h = PAD + 3.5*mm + len(desc_lines)*LINE_H
        if data_lines: card_h += 1.5*mm + len(data_lines)*LINE_H
        if mem_lines:  card_h += 1.5*mm + len(mem_lines)*LINE_H
        card_h += PAD

        self.need(card_h + 3*mm)

        # Background card
        DOT_W = 4
        cx = self.LM
        cy = self.y - card_h
        self.rect(cx + DOT_W, cy, self.CW - DOT_W, card_h, fill=C_NAVY, stroke=C_BORDER)
        # Coloured left bar
        self.c.setFillColor(dot_color)
        self.c.rect(cx, cy, DOT_W, card_h, fill=1, stroke=0)

        # Text content
        tx = cx + DOT_W + 6
        ty = self.y - PAD

        # Agent label
        self.c.setFont("Helvetica-Bold", 8)
        self.c.setFillColor(dot_color)
        self.c.drawString(tx, ty - 3, agent_label)
        # Time label (right-aligned)
        self.c.setFont("Helvetica", 7)
        self.c.setFillColor(C_MUTED)
        self.c.drawRightString(self.RM - 6, ty - 3, time_label)

        ty -= LINE_H + 1.5*mm

        # Description
        self.c.setFont("Helvetica", 9)
        self.c.setFillColor(C_TEXT)
        for line in desc_lines:
            self.c.drawString(tx, ty, line)
            ty -= LINE_H

        # Tool data
        if data_lines:
            ty -= 1.5*mm
            self.c.setFont("Helvetica-Oblique", 8)
            self.c.setFillColor(C_MUTED)
            for line in data_lines:
                self.c.drawString(tx, ty, line)
                ty -= LINE_H

        # Memory note
        if mem_lines:
            ty -= 1.5*mm
            self.c.setFont("Helvetica-Oblique", 8)
            self.c.setFillColor(C_PURPLE)
            for line in mem_lines:
                self.c.drawString(tx, ty, line)
                ty -= LINE_H

        self.y -= card_h + 2.5*mm


def generate_audit_pdf(run_id, scenario_str, items, run_meta):
    """
    Build branded PDF. Returns raw bytes.
    """
    buf = io.BytesIO()
    p   = PDFPainter(buf)

    generated_at = time.strftime("%d %b %Y  %H:%M UTC", time.gmtime())
    customer     = run_meta.get("customer", "")

    p.draw_header(run_id, scenario_str, customer, generated_at)

    # Metrics
    def _k(v):
        if v is None: return "—"
        n = int(v)
        if n >= 1_000_000: return f"${n/1_000_000:.1f}M"
        if n >= 1_000:     return f"${n//1000}K"
        return f"${n}"

    ci  = run_meta.get("confidence")
    metrics = [
        ("AI Resolution",  str(run_meta.get("resolution_time") or "—")),
        ("Route Cost",     _k(run_meta.get("cost_usd"))),
        ("Cost Saved",     _k(run_meta.get("saved_usd"))),
        ("Confidence",     f"{int(float(ci)*100)}%" if ci is not None else "—"),
        ("Steps",          str(len(items))),
    ]
    p.draw_metrics(metrics)

    p.draw_section_title(f"DECISION AUDIT TIMELINE  ({len(items)} events)")

    if not items:
        p.text(p.LM, p.y, "No audit events recorded for this run.", size=9, color=C_MUTED)
        p.y -= 8*mm
    else:
        for item in items:
            p.draw_audit_card(item)

    p._draw_footer()
    p.c.save()
    return buf.getvalue()
