"""Builds the per-process UI cards shown in the monitor window body: a slim bar-style
card, or a resizable gauge card with its own analog/digital tachometer canvas."""

import tkinter as tk

from src.ui.palette import BG_CARD, FG_HEADER, FG_MUTED, BAR_BG, COLOR_GREEN, COLOR_YELLOW, COLOR_RED
from src.ui import gaugeWidget
from src.core.process import Process

MIN_GAUGE_SIDE = 120


def colorForCount(count: int, warnThreshold: int, criticalThreshold: int) -> str:
    if count >= criticalThreshold:
        return COLOR_RED
    if count >= warnThreshold:
        return COLOR_YELLOW
    return COLOR_GREEN


def _renderCardHeader(card: tk.Widget, process: Process) -> None:
    tk.Label(
        card, text=process.displayName(),
        bg=BG_CARD, fg=FG_HEADER,
        font=("Consolas", 10, "bold"), anchor="w",
    ).pack(anchor="w")

    tk.Label(
        card, text=f"{process.name}  ·  PID  {process.pid}",
        bg=BG_CARD, fg=FG_MUTED,
        font=("Consolas", 8), anchor="w",
    ).pack(anchor="w")


def renderBarCard(body: tk.Widget, process: Process, count: int, context) -> None:
    color = colorForCount(count, context.gdiWarnThreshold(), context.gdiCriticalThreshold())
    pct = min(count / context.gdiMax(), 1.0)

    card = tk.Frame(body, bg=BG_CARD, padx=10, pady=6)
    card.pack(fill="x", pady=3)

    top = tk.Frame(card, bg=BG_CARD)
    top.pack(fill="x")

    # GDI count — packed first so it always keeps its space when resizing
    tk.Label(
        top, text=str(count),
        bg=BG_CARD, fg=color,
        font=("Consolas", 16, "bold"), anchor="e",
    ).pack(side="right", anchor="center")

    left = tk.Frame(top, bg=BG_CARD)
    left.pack(side="left", anchor="w", fill="x", expand=True)
    _renderCardHeader(left, process)

    if context.showBar():
        barHeight = 16 if context.showPercentage() else 6
        bar = tk.Canvas(card, height=barHeight, highlightthickness=0, bg=BAR_BG)
        bar.pack(fill="x", pady=(4, 0))
        bar.bind("<Configure>", lambda e, b=bar, p=pct, c=color: drawBar(b, p, c, context.showPercentage()))


def drawBar(canvas: tk.Canvas, fillPct: float, color: str, showPercentage: bool) -> None:
    if not canvas.winfo_exists():
        return
    canvas.delete("all")
    w, h = canvas.winfo_width(), canvas.winfo_height()
    fillW = int(w * fillPct)
    if fillW > 0:
        canvas.create_rectangle(0, 0, fillW, h, fill=color, outline="")
    if showPercentage:
        label = f"{fillPct * 100:.1f}%"
        cx, cy = w // 2, h // 2
        # Shadow pass for readability over both light fill and dark background
        canvas.create_text(cx + 1, cy + 1, text=label, fill="#1e1e2e", font=("Consolas", 8, "bold"), anchor="center")
        canvas.create_text(cx, cy, text=label, fill="#cdd6f4", font=("Consolas", 8, "bold"), anchor="center")


def renderGaugeCard(body: tk.Widget, process: Process, count: int, context) -> None:
    card = tk.Frame(body, bg=BG_CARD, padx=10, pady=6)
    card.pack(fill="both", expand=True, pady=3)

    _renderCardHeader(card, process)

    gaugeArea = tk.Frame(card, bg=BG_CARD)
    gaugeArea.pack(fill="both", expand=True, pady=(8, 2))

    # relwidth/relheight keep the canvas exactly the size of its container at all times —
    # no manual re-placement needed, so there's no risk of it lagging or going stale.
    gauge = tk.Canvas(gaugeArea, highlightthickness=0, bg=BG_CARD)
    gauge.place(x=0, y=0, relwidth=1, relheight=1)
    gaugeArea.bind("<Configure>", lambda e, g=gauge: _onGaugeAreaResize(g, e, count, context))


def _onGaugeAreaResize(canvas: tk.Canvas, event: "tk.Event", count: int, context) -> None:
    if not canvas.winfo_exists():
        return
    # event.width/height are the container's own dimensions — reliable even mid-resize,
    # unlike querying the canvas's winfo_width()/height() which can lag or ping-pong.
    width = max(event.width, MIN_GAUGE_SIDE)
    height = max(event.height, MIN_GAUGE_SIDE)
    drawGauge(canvas, width, height, count, context)


def drawGauge(canvas: tk.Canvas, width: int, height: int, count: int, context) -> None:
    if not canvas.winfo_exists():
        return
    gaugeWidget.draw(
        canvas, width, height,
        count, context.gdiMax(),
        context.gdiWarnThreshold(), context.gdiCriticalThreshold(),
        context.gaugeStyle(), context.needleStyle(),
        context.needleColor(), context.zoneMode(),
        context.accentColor(), context.numberColor(), context.dialColor(),
        context.needleThickness(),
    )
