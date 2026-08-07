import math
from dataclasses import dataclass
import tkinter as tk

from src.ui.palette import (
    GAUGE_FACE, GAUGE_BEZEL_OUTER, GAUGE_BEZEL_INNER,
    GAUGE_TICK, GAUGE_NUMBER, GAUGE_HUB, GAUGE_HUB_RING,
    GAUGE_NEEDLE, GAUGE_NEEDLE_TAIL, GAUGE_NEEDLE_ACCENT, GAUGE_REDZONE, GAUGE_YELLOWZONE,
    GAUGE_RETRO_FACE, GAUGE_RETRO_BEZEL, GAUGE_RETRO_TICK, GAUGE_RETRO_NUMBER, GAUGE_RETRO_NEEDLE,
    GAUGE_VEGLIA_FACE, GAUGE_VEGLIA_BEZEL, GAUGE_VEGLIA_TICK, GAUGE_VEGLIA_NUMBER, GAUGE_VEGLIA_NEEDLE,
    GAUGE_FERRARI_FACE, GAUGE_FERRARI_TICK, GAUGE_FERRARI_NUMBER, GAUGE_FERRARI_NEEDLE,
    GAUGE_ASTON_FACE, GAUGE_ASTON_BEZEL_LIGHT, GAUGE_ASTON_BEZEL_DARK, GAUGE_ASTON_TICK,
    GAUGE_ASTON_NUMBER, GAUGE_ASTON_NEEDLE,
    GAUGE_JDM_BG, GAUGE_JDM_BAR_LIT, GAUGE_JDM_BAR_UNLIT, GAUGE_JDM_NUMBER,
    GAUGE_TELEMETRY_BG, GAUGE_TELEMETRY_BAR_LOW, GAUGE_TELEMETRY_BAR_MID, GAUGE_TELEMETRY_BAR_HIGH,
    GAUGE_TELEMETRY_BAR_UNLIT, GAUGE_TELEMETRY_LED_ON, GAUGE_TELEMETRY_LED_OFF, GAUGE_TELEMETRY_NUMBER,
    GAUGE_DIGITAL_BG, GAUGE_DIGITAL_TRACK, GAUGE_DIGITAL_LABEL,
    COLOR_GREEN, COLOR_YELLOW, COLOR_RED,
)

# Sweep goes clockwise from bottom-left (135°) through the top to bottom-right (405°=45°),
# matching a classic automotive RPM dial.
ANGLE_START = 135.0
ANGLE_SWEEP = 270.0


# ── Geometry helpers ─────────────────────────────────────────────────────────────

def _point(cx: float, cy: float, radius: float, angleDeg: float) -> tuple[float, float]:
    rad = math.radians(angleDeg)
    return cx + radius * math.cos(rad), cy + radius * math.sin(rad)


def _angleFor(pct: float, angleStart: float = ANGLE_START, angleSweep: float = ANGLE_SWEEP) -> float:
    return angleStart + max(0.0, min(pct, 1.0)) * angleSweep


def _hexToRgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _drawArcBand(canvas: tk.Canvas, cx: float, cy: float, radius: float, width: float,
                  startPct: float, endPct: float, color: str, steps: int = 24) -> None:
    if endPct <= startPct:
        return
    a0, a1 = _angleFor(startPct), _angleFor(endPct)
    points = [_point(cx, cy, radius, a0 + (a1 - a0) * i / steps) for i in range(steps + 1)]
    flat = [coord for point in points for coord in point]
    canvas.create_line(*flat, width=width, fill=color, capstyle="round", joinstyle="round")


def _drawMetalBezel(canvas: tk.Canvas, cx: float, cy: float, outerRadius: float, innerRadius: float,
                      lightColor: str, darkColor: str, rings: int = 14) -> None:
    """Concentric shrinking rings interpolated between two tones — fakes a brushed-metal bezel.
    The highlight is pushed toward the outer rim and a crisp dark seam is added where the
    bezel meets the face, so it reads as a defined ring instead of a soft, undefined haze."""
    lr, lg, lb = _hexToRgb(lightColor)
    dr, dg, db = _hexToRgb(darkColor)
    for i in range(rings):
        t = i / (rings - 1)
        eased = t ** 1.6
        r = outerRadius - (outerRadius - innerRadius) * t
        color = "#%02x%02x%02x" % (
            int(lr + (dr - lr) * eased), int(lg + (dg - lg) * eased), int(lb + (db - lb) * eased),
        )
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")

    seamWidth = max(1, round(innerRadius * 0.012))
    seamColor = "#%02x%02x%02x" % (int(dr * 0.45), int(dg * 0.45), int(db * 0.45))
    canvas.create_oval(
        cx - innerRadius, cy - innerRadius, cx + innerRadius, cy + innerRadius,
        outline=seamColor, width=seamWidth,
    )



def _drawHub(canvas: tk.Canvas, cx: float, cy: float, faceRadius: float,
              ringColor: str, capColor: str, slotColor: str) -> None:
    hubRadius = faceRadius * 0.1
    canvas.create_oval(
        cx - hubRadius, cy - hubRadius, cx + hubRadius, cy + hubRadius,
        fill=ringColor, outline="",
    )
    screwRadius = hubRadius * 0.55
    canvas.create_oval(
        cx - screwRadius, cy - screwRadius, cx + screwRadius, cy + screwRadius,
        fill=capColor, outline="",
    )
    canvas.create_line(cx - screwRadius * 0.7, cy, cx + screwRadius * 0.7, cy, fill=slotColor, width=1)


def _zoneColor(count: int, warnThreshold: int, criticalThreshold: int) -> str:
    if count >= criticalThreshold:
        return COLOR_RED
    if count >= warnThreshold:
        return COLOR_YELLOW
    return COLOR_GREEN


def _tickZoneColor(value: float, baseColor: str, warnThreshold: int | None, criticalThreshold: int | None,
                     zoneMode: str, warnColor: str, criticalColor: str, accentColor: str) -> str:
    """Picks a tick's color: two-tone warn/critical scheme ("multicolor"), or every single
    tick across the whole face in one accent tone ("mono", BMW-style single-color dial)."""
    if zoneMode == "mono":
        return accentColor
    if warnThreshold is None:
        return baseColor
    if value >= criticalThreshold:
        return criticalColor
    if value >= warnThreshold:
        return warnColor
    return baseColor


def _drawTicksAndNumbers(canvas: tk.Canvas, cx: float, cy: float, faceRadius: float, gdiMax: int,
                           tickColor: str, numberColor: str, fontFamily: str, thin: bool = False,
                           warnThreshold: int | None = None, criticalThreshold: int | None = None,
                           zoneMode: str = "multicolor", warnColor: str = "", criticalColor: str = "",
                           accentColor: str = "", angleStart: float = ANGLE_START,
                           angleSweep: float = ANGLE_SWEEP) -> None:
    majorStep = max(gdiMax // 10, 1)
    minorDivisions = 10  # each minor tick is 1/10th of a major step (100 GDIs when major = 1000)
    majorWidth = 2 if thin else 3
    tick = 0
    while tick <= gdiMax:
        pct = tick / gdiMax
        angle = _angleFor(pct, angleStart, angleSweep)
        color = _tickZoneColor(tick, tickColor, warnThreshold, criticalThreshold, zoneMode, warnColor, criticalColor, accentColor)
        outer = _point(cx, cy, faceRadius * 0.98, angle)
        inner = _point(cx, cy, faceRadius * 0.86, angle)
        canvas.create_line(*outer, *inner, width=majorWidth, fill=color)

        labelPoint = _point(cx, cy, faceRadius * 0.75, angle)
        canvas.create_text(
            *labelPoint, text=str(tick // 1000),
            fill=numberColor, font=(fontFamily, max(int(faceRadius * 0.15), 8), "bold"), anchor="center",
        )

        if tick < gdiMax:
            for m in range(1, minorDivisions):
                minorValue = tick + majorStep * m / minorDivisions
                minorPct = minorValue / gdiMax
                mAngle = _angleFor(minorPct, angleStart, angleSweep)
                mColor = _tickZoneColor(minorValue, tickColor, warnThreshold, criticalThreshold, zoneMode, warnColor, criticalColor, accentColor)
                mOuter = _point(cx, cy, faceRadius * 0.98, mAngle)
                mInner = _point(cx, cy, faceRadius * 0.92, mAngle)
                canvas.create_line(*mOuter, *mInner, width=1, fill=mColor)

        tick += majorStep


# ── Needle styles ────────────────────────────────────────────────────────────────

def _drawNeedleClassic(canvas: tk.Canvas, cx: float, cy: float, angleDeg: float, length: float,
                         needleColor: str, tailColor: str, thickness: float = 1.0) -> None:
    """Tapered dagger blade with a counterweight tail — traditional analog tachometer needle."""
    tipX, tipY = _point(cx, cy, length, angleDeg)
    baseWidth = length * 0.032 * thickness
    perp = math.radians(angleDeg + 90)
    dx, dy = math.cos(perp) * baseWidth, math.sin(perp) * baseWidth

    canvas.create_polygon(
        cx + dx, cy + dy, tipX, tipY, cx - dx, cy - dy,
        fill=needleColor, outline="",
    )
    tailX, tailY = _point(cx, cy, length * 0.16, angleDeg + 180)
    canvas.create_line(cx, cy, tailX, tailY, width=baseWidth * 1.4, fill=tailColor, capstyle="round")


def _drawNeedleSport(canvas: tk.Canvas, cx: float, cy: float, angleDeg: float, length: float,
                      needleColor: str, tailColor: str, accentColor: str, thickness: float = 1.0) -> None:
    """Two-tone racing blade: a flat parallel shaft with a bright wedge tip and a racing stripe."""
    shaftStart, shaftEnd = length * 0.1, length * 0.66
    halfWidth = length * 0.026 * thickness
    perp = math.radians(angleDeg + 90)
    dx, dy = math.cos(perp) * halfWidth, math.sin(perp) * halfWidth

    shaftBase = _point(cx, cy, shaftStart, angleDeg)
    shaftTip = _point(cx, cy, shaftEnd, angleDeg)
    canvas.create_polygon(
        shaftBase[0] + dx, shaftBase[1] + dy, shaftTip[0] + dx, shaftTip[1] + dy,
        shaftTip[0] - dx, shaftTip[1] - dy, shaftBase[0] - dx, shaftBase[1] - dy,
        fill=needleColor, outline="",
    )
    canvas.create_line(*shaftBase, *shaftTip, width=1, fill=GAUGE_NUMBER)

    tip = _point(cx, cy, length, angleDeg)
    canvas.create_polygon(
        shaftTip[0] + dx, shaftTip[1] + dy, tip[0], tip[1], shaftTip[0] - dx, shaftTip[1] - dy,
        fill=accentColor, outline="",
    )


def _drawNeedleTwin(canvas: tk.Canvas, cx: float, cy: float, angleDeg: float, length: float,
                     needleColor: str, tailColor: str, accentColor: str, thickness: float = 1.0) -> None:
    """Slim double-rail pointer that converges to a small diamond tip — modern instrument look."""
    railOffset = length * 0.05 * thickness
    baseRadius = length * 0.14
    perp = math.radians(angleDeg + 90)
    dx, dy = math.cos(perp) * railOffset, math.sin(perp) * railOffset
    lineWidth = max(1, round(2 * thickness))

    base = _point(cx, cy, baseRadius, angleDeg)
    tip = _point(cx, cy, length, angleDeg)
    canvas.create_line(base[0] + dx, base[1] + dy, tip[0], tip[1], width=lineWidth, fill=needleColor, capstyle="round")
    canvas.create_line(base[0] - dx, base[1] - dy, tip[0], tip[1], width=lineWidth, fill=needleColor, capstyle="round")

    diamond = length * 0.03 * thickness
    back = _point(cx, cy, length - diamond, angleDeg)
    dTipX, dTipY = math.cos(perp) * diamond, math.sin(perp) * diamond
    canvas.create_polygon(
        back[0] + dTipX, back[1] + dTipY, tip[0], tip[1], back[0] - dTipX, back[1] - dTipY,
        fill=accentColor, outline="",
    )


def _drawNeedleLine(canvas: tk.Canvas, cx: float, cy: float, angleDeg: float, length: float,
                     needleColor: str, tailColor: str, accentColor: str, thickness: float = 1.0) -> None:
    """Minimalist flat pointer: a thin line ending in a small accent dot."""
    tipX, tipY = _point(cx, cy, length, angleDeg)
    lineWidth = max(1, round(2 * thickness))
    canvas.create_line(cx, cy, tipX, tipY, width=lineWidth, fill=needleColor, capstyle="round")
    dotRadius = length * 0.045 * thickness
    canvas.create_oval(
        tipX - dotRadius, tipY - dotRadius, tipX + dotRadius, tipY + dotRadius,
        fill=accentColor, outline="",
    )


def _drawNeedleSlim(canvas: tk.Canvas, cx: float, cy: float, angleDeg: float, length: float,
                     needleColor: str, tailColor: str, accentColor: str, thickness: float = 1.0) -> None:
    """Slender tapered blade with no counterweight tail — inspired by compact motorcycle-
    cluster tachometers (thin, high-contrast needle over a plain round hub)."""
    tipX, tipY = _point(cx, cy, length, angleDeg)
    baseWidth = length * 0.018 * thickness
    perp = math.radians(angleDeg + 90)
    dx, dy = math.cos(perp) * baseWidth, math.sin(perp) * baseWidth
    baseX, baseY = _point(cx, cy, length * 0.06, angleDeg + 180)
    canvas.create_polygon(
        baseX + dx, baseY + dy, tipX, tipY, baseX - dx, baseY - dy,
        fill=needleColor, outline="",
    )


# Every needle drawer shares the same signature, so adding a new style is a one-line addition.
_NEEDLE_DRAWERS = {
    "classic": _drawNeedleClassic,
    "sport": _drawNeedleSport,
    "twin": _drawNeedleTwin,
    "line": _drawNeedleLine,
    "slim": _drawNeedleSlim,
}


def _drawNeedle(canvas: tk.Canvas, cx: float, cy: float, angleDeg: float, length: float,
                 style: str, needleColor: str, tailColor: str, accentColor: str, thickness: float = 1.0) -> None:
    drawer = _NEEDLE_DRAWERS.get(style, _drawNeedleClassic)
    if drawer is _drawNeedleClassic:
        drawer(canvas, cx, cy, angleDeg, length, needleColor, tailColor, thickness)
    else:
        drawer(canvas, cx, cy, angleDeg, length, needleColor, tailColor, accentColor, thickness)


# ── Analog gauge styles (classic / retro share one renderer, driven by a spec) ──────

@dataclass(frozen=True)
class AnalogGaugeSpec:
    """Every visual constant that differs between analog gauge styles (classic, retro, …).
    Adding a brand-new analog style is just adding one more entry to ANALOG_GAUGE_SPECS."""
    bezelLight: str
    bezelDark: str
    bezelRings: int
    faceRadiusRatio: float
    faceColor: str
    innerRingColor: str | None      # retro draws a thin ring just inside the face; classic doesn't
    tickColor: str
    numberColor: str
    fontFamily: str
    thinTicks: bool
    needleColor: str
    needleTailColor: str
    needleLengthRatio: float
    hubRingColor: str
    hubCapColor: str
    labelText: str
    labelYRatio: float
    labelFontRatio: float
    numberFontRatio: float = 0.13
    angleStart: float = ANGLE_START  # where the minimum value sits (0°=3 o'clock, clockwise)
    angleSweep: float = ANGLE_SWEEP  # total arc from minimum to maximum value


ANALOG_GAUGE_SPECS: dict[str, AnalogGaugeSpec] = {
    "classic": AnalogGaugeSpec(
        bezelLight=GAUGE_BEZEL_OUTER, bezelDark=GAUGE_BEZEL_INNER, bezelRings=14,
        faceRadiusRatio=0.95, faceColor=GAUGE_FACE, innerRingColor=None,
        tickColor=GAUGE_TICK, numberColor=GAUGE_NUMBER, fontFamily="Consolas", thinTicks=False,
        needleColor=GAUGE_NEEDLE, needleTailColor=GAUGE_NEEDLE_TAIL, needleLengthRatio=0.98,
        hubRingColor=GAUGE_HUB_RING, hubCapColor=GAUGE_HUB,
        labelText="GDI\nx1000", labelYRatio=0.26, labelFontRatio=0.09, numberFontRatio=0.13,
    ),
    "retro": AnalogGaugeSpec(
        bezelLight="#f2ecd8", bezelDark=GAUGE_RETRO_BEZEL, bezelRings=10,
        faceRadiusRatio=0.95, faceColor=GAUGE_RETRO_FACE, innerRingColor=GAUGE_RETRO_TICK,
        tickColor=GAUGE_RETRO_TICK, numberColor=GAUGE_RETRO_NUMBER, fontFamily="Georgia", thinTicks=True,
        needleColor=GAUGE_RETRO_NEEDLE, needleTailColor=GAUGE_RETRO_TICK, needleLengthRatio=0.98,
        hubRingColor=GAUGE_RETRO_BEZEL, hubCapColor=GAUGE_RETRO_TICK,
        labelText="GDI x1000", labelYRatio=0.24, labelFontRatio=0.08, numberFontRatio=0.12,
    ),
    "veglia": AnalogGaugeSpec(
        bezelLight=GAUGE_VEGLIA_BEZEL, bezelDark=GAUGE_BEZEL_INNER, bezelRings=14,
        faceRadiusRatio=0.95, faceColor=GAUGE_VEGLIA_FACE, innerRingColor=GAUGE_VEGLIA_TICK,
        tickColor=GAUGE_VEGLIA_TICK, numberColor=GAUGE_VEGLIA_NUMBER, fontFamily="Bahnschrift", thinTicks=True,
        needleColor=GAUGE_VEGLIA_NEEDLE, needleTailColor=GAUGE_VEGLIA_TICK, needleLengthRatio=0.98,
        hubRingColor=GAUGE_VEGLIA_TICK, hubCapColor=GAUGE_HUB,
        labelText="GDI\nx100", labelYRatio=0.30, labelFontRatio=0.075, numberFontRatio=0.12,
        # Same 270° sweep as classic, but rotated so 0 sits at 3 o'clock (gap moves to top-right).
        angleStart=0.0, angleSweep=270.0,
    ),
    "ferrari": AnalogGaugeSpec(
        bezelLight=GAUGE_BEZEL_OUTER, bezelDark=GAUGE_BEZEL_INNER, bezelRings=14,
        faceRadiusRatio=0.95, faceColor=GAUGE_FERRARI_FACE, innerRingColor=None,
        tickColor=GAUGE_FERRARI_TICK, numberColor=GAUGE_FERRARI_NUMBER, fontFamily="Arial Black", thinTicks=False,
        needleColor=GAUGE_FERRARI_NEEDLE, needleTailColor=GAUGE_FERRARI_NEEDLE, needleLengthRatio=0.98,
        hubRingColor=GAUGE_HUB_RING, hubCapColor=GAUGE_HUB,
        labelText="GDI\nx1000", labelYRatio=0.20, labelFontRatio=0.07, numberFontRatio=0.12,
        # Wider sweep than classic, 0 sits exactly at 6 o'clock (dead-bottom).
        angleStart=90.0, angleSweep=280.0,
    ),
    "aston": AnalogGaugeSpec(
        bezelLight=GAUGE_ASTON_BEZEL_LIGHT, bezelDark=GAUGE_ASTON_BEZEL_DARK, bezelRings=14,
        faceRadiusRatio=0.95, faceColor=GAUGE_ASTON_FACE, innerRingColor=GAUGE_ASTON_BEZEL_DARK,
        tickColor=GAUGE_ASTON_TICK, numberColor=GAUGE_ASTON_NUMBER, fontFamily="Trebuchet MS", thinTicks=True,
        needleColor=GAUGE_ASTON_NEEDLE, needleTailColor=GAUGE_ASTON_NEEDLE, needleLengthRatio=0.98,
        hubRingColor=GAUGE_ASTON_BEZEL_LIGHT, hubCapColor="#1c1c1e",
        labelText="RPM\nX1000", labelYRatio=0.28, labelFontRatio=0.065, numberFontRatio=0.12,
        # Reference dial sweeps counter-clockwise (numbers increase to the left of the gap).
        angleStart=135.0, angleSweep=-270.0,
    ),
}
_DEFAULT_ANALOG_STYLE = "classic"


def _analogSpec(gaugeStyle: str) -> AnalogGaugeSpec:
    return ANALOG_GAUGE_SPECS.get(gaugeStyle, ANALOG_GAUGE_SPECS[_DEFAULT_ANALOG_STYLE])


def defaultNeedleColor(gaugeStyle: str) -> str:
    return _analogSpec(gaugeStyle).needleColor


def defaultNumberColor(gaugeStyle: str) -> str:
    if gaugeStyle == "jdm":
        return GAUGE_JDM_NUMBER
    if gaugeStyle == "telemetry":
        return GAUGE_TELEMETRY_NUMBER
    return _analogSpec(gaugeStyle).numberColor


def defaultDialColor(gaugeStyle: str) -> str:
    if gaugeStyle == "digital":
        return GAUGE_DIGITAL_BG
    if gaugeStyle == "jdm":
        return GAUGE_JDM_BG
    if gaugeStyle == "telemetry":
        return GAUGE_TELEMETRY_BG
    return _analogSpec(gaugeStyle).faceColor


def defaultFontFamily(gaugeStyle: str) -> str:
    if gaugeStyle in ("digital", "jdm", "telemetry"):
        return "Consolas"
    return _analogSpec(gaugeStyle).fontFamily


def _drawAnalog(canvas: tk.Canvas, cx: float, cy: float, radius: float, count: int, gdiMax: int,
                 warnThreshold: int, criticalThreshold: int, needleStyle: str, needleColor: str,
                 zoneMode: str, accentColor: str, numberColor: str, dialColor: str,
                 needleThickness: float, fontFamily: str, spec: AnalogGaugeSpec) -> None:
    """Shared renderer for every analog (needle-based) gauge style, parametrized by `spec`."""
    faceRadius = radius * spec.faceRadiusRatio
    # Bezel's inner edge must reach the face radius exactly, or a gap of canvas background shows through.
    _drawMetalBezel(canvas, cx, cy, radius, faceRadius, spec.bezelLight, spec.bezelDark, rings=spec.bezelRings)
    effectiveDial = spec.faceColor if dialColor == "auto" else dialColor
    canvas.create_oval(
        cx - faceRadius, cy - faceRadius, cx + faceRadius, cy + faceRadius,
        fill=effectiveDial, outline="",
    )
    if spec.innerRingColor:
        innerRing = faceRadius * 0.97
        canvas.create_oval(
            cx - innerRing, cy - innerRing, cx + innerRing, cy + innerRing,
            outline=spec.innerRingColor, width=1,
        )

    effectiveNeedle = spec.needleColor if needleColor == "auto" else needleColor
    effectiveAccent = effectiveNeedle if accentColor == "auto" else accentColor
    effectiveNumber = spec.numberColor if numberColor == "auto" else numberColor
    effectiveFont = spec.fontFamily if fontFamily == "auto" else fontFamily
    _drawTicksAndNumbers(
        canvas, cx, cy, faceRadius, gdiMax, spec.tickColor, effectiveNumber, effectiveFont, thin=spec.thinTicks,
        warnThreshold=warnThreshold, criticalThreshold=criticalThreshold, zoneMode=zoneMode,
        warnColor=GAUGE_YELLOWZONE, criticalColor=GAUGE_REDZONE, accentColor=effectiveAccent,
        angleStart=spec.angleStart, angleSweep=spec.angleSweep,
    )

    canvas.create_text(
        cx, cy - faceRadius * spec.labelYRatio,
        text=spec.labelText, justify="center",
        fill=effectiveNumber, font=(effectiveFont, max(int(faceRadius * spec.labelFontRatio), 7), "bold"), anchor="center",
    )

    # Drawn before the needle so the needle passes in front of it, not on top.
    canvas.create_text(
        cx, cy + faceRadius * 0.45,
        text=str(count),
        fill=effectiveNumber, font=(effectiveFont, max(int(faceRadius * spec.numberFontRatio), 8), "bold"), anchor="center",
    )

    pct = min(count / gdiMax, 1.0)
    _drawNeedle(
        canvas, cx, cy, _angleFor(pct, spec.angleStart, spec.angleSweep), faceRadius * spec.needleLengthRatio,
        needleStyle, effectiveNeedle, spec.needleTailColor, effectiveAccent, needleThickness,
    )
    _drawHub(canvas, cx, cy, faceRadius, spec.hubRingColor, spec.hubCapColor, effectiveDial)


def _drawJdmBar(canvas: tk.Canvas, cx: float, cy: float, halfWidth: float, halfHeight: float,
                  count: int, gdiMax: int, warnThreshold: int, criticalThreshold: int,
                  numberColor: str, dialColor: str, needleColor: str, accentColor: str,
                  zoneMode: str, fontFamily: str) -> None:
    """JDM-cluster bar tachometer: a straight horizontal bar of stacked segments that fills
    from left to right as the count rises — no arc, no needle, no curvature."""
    effectiveDial = GAUGE_JDM_BG if dialColor == "auto" else dialColor
    effectiveNumber = GAUGE_JDM_NUMBER if numberColor == "auto" else numberColor
    effectiveNeedle = defaultNeedleColor("jdm") if needleColor == "auto" else needleColor
    effectiveAccent = effectiveNeedle if accentColor == "auto" else accentColor
    effectiveFont = "Consolas" if fontFamily == "auto" else fontFamily
    scale = min(halfWidth, halfHeight)
    canvas.create_rectangle(
        cx - halfWidth, cy - halfHeight, cx + halfWidth, cy + halfHeight, fill=effectiveDial, outline="",
    )

    pct = min(count / gdiMax, 1.0)
    warnPct = warnThreshold / gdiMax if warnThreshold else None
    criticalPct = criticalThreshold / gdiMax if criticalThreshold else None

    barLeft = cx - halfWidth * 0.85
    barRight = cx + halfWidth * 0.85
    barTop = cy - halfHeight * 0.55
    barBottom = cy - halfHeight * 0.05
    barWidthTotal = barRight - barLeft

    segments = 30
    gap = max(barWidthTotal / segments * 0.12, 1)
    for i in range(segments):
        segPct0 = i / segments
        segPct1 = (i + 1) / segments
        segLeft = barLeft + segPct0 * barWidthTotal
        segRight = barLeft + segPct1 * barWidthTotal
        if segPct0 < pct:
            if zoneMode == "mono":
                color = effectiveAccent
            elif criticalPct is not None and segPct0 >= criticalPct:
                color = GAUGE_REDZONE
            elif warnPct is not None and segPct0 >= warnPct:
                color = GAUGE_YELLOWZONE
            else:
                color = GAUGE_JDM_BAR_LIT
        else:
            color = GAUGE_JDM_BAR_UNLIT
        canvas.create_rectangle(segLeft + gap, barTop, segRight - gap, barBottom, fill=color, outline="")

    majorStep = max(gdiMax // 9, 1)
    labelY = barBottom + halfHeight * 0.12
    tick = 0
    while tick <= gdiMax:
        tickPct = tick / gdiMax
        labelX = barLeft + tickPct * barWidthTotal
        canvas.create_text(
            labelX, labelY, text=str(tick // 1000), fill=effectiveNumber,
            font=(effectiveFont, max(int(scale * 0.16), 8), "bold"), anchor="n",
        )
        tick += majorStep

    canvas.create_text(
        cx, cy + halfHeight * 0.55, text=str(count), fill=effectiveNumber,
        font=(effectiveFont, max(int(scale * 0.32), 10), "bold"), anchor="center",
    )
    canvas.create_text(
        cx, cy + halfHeight * 0.85, text="GDI x1000", fill=effectiveNumber,
        font=(effectiveFont, max(int(scale * 0.11), 7)), anchor="center",
    )


def _blendRgb(colorA: str, colorB: str, t: float) -> str:
    ar, ag, ab = _hexToRgb(colorA)
    br, bg, bb = _hexToRgb(colorB)
    t = max(0.0, min(t, 1.0))
    return "#%02x%02x%02x" % (int(ar + (br - ar) * t), int(ag + (bg - ag) * t), int(ab + (bb - ab) * t))


def _drawTelemetryBar(canvas: tk.Canvas, cx: float, cy: float, halfWidth: float, halfHeight: float,
                        count: int, gdiMax: int, warnThreshold: int, criticalThreshold: int,
                        numberColor: str, dialColor: str, needleColor: str, accentColor: str,
                        zoneMode: str, fontFamily: str) -> None:
    """Sim-racing telemetry HUD: a row of shift-light LEDs above a gradient bar-graph
    (cool colors at low values, warm near the redline) with a big digital readout below."""
    effectiveDial = GAUGE_TELEMETRY_BG if dialColor == "auto" else dialColor
    effectiveNumber = GAUGE_TELEMETRY_NUMBER if numberColor == "auto" else numberColor
    effectiveNeedle = defaultNeedleColor("telemetry") if needleColor == "auto" else needleColor
    effectiveAccent = effectiveNeedle if accentColor == "auto" else accentColor
    effectiveFont = "Consolas" if fontFamily == "auto" else fontFamily
    mono = zoneMode == "mono"
    scale = min(halfWidth, halfHeight)
    canvas.create_rectangle(
        cx - halfWidth, cy - halfHeight, cx + halfWidth, cy + halfHeight, fill=effectiveDial, outline="",
    )

    pct = min(count / gdiMax, 1.0)
    warnPct = warnThreshold / gdiMax if warnThreshold else 0.6
    criticalPct = criticalThreshold / gdiMax if criticalThreshold else 0.85

    # Shift-light LED row across the top, lighting up left-to-right as the value climbs.
    ledCount = 8
    ledY = cy - halfHeight * 0.72
    ledRadius = scale * 0.09
    ledSpan = halfWidth * 1.7
    litLeds = round(pct * ledCount)
    ledOnColor = effectiveAccent if mono else GAUGE_TELEMETRY_LED_ON
    for i in range(ledCount):
        ledX = cx - ledSpan / 2 + ledSpan * (i + 0.5) / ledCount
        color = ledOnColor if i < litLeds else GAUGE_TELEMETRY_LED_OFF
        canvas.create_oval(
            ledX - ledRadius, ledY - ledRadius, ledX + ledRadius, ledY + ledRadius, fill=color, outline="",
        )

    # Gradient bar-graph: each segment's height grows progressively left to right. In mono
    # mode it's a single-hue gradient (dim-to-bright accent); otherwise the usual cool-to-warm scheme.
    barBottom = cy + halfHeight * 0.02
    maxBarHeight = halfHeight * 0.42
    barLeft, barRight = cx - halfWidth * 0.9, cx + halfWidth * 0.9
    segments = 60
    segWidth = (barRight - barLeft) / segments
    for i in range(segments):
        segPct = (i + 0.5) / segments
        barHeight = maxBarHeight * (0.12 + 0.88 * segPct)
        if segPct <= pct:
            if mono:
                color = _blendRgb("#000000", effectiveAccent, 0.35 + 0.65 * segPct)
            elif segPct >= criticalPct:
                color = _blendRgb(GAUGE_TELEMETRY_BAR_MID, GAUGE_TELEMETRY_BAR_HIGH, (segPct - criticalPct) / max(1 - criticalPct, 0.01))
            elif segPct >= warnPct:
                color = _blendRgb(GAUGE_TELEMETRY_BAR_LOW, GAUGE_TELEMETRY_BAR_MID, (segPct - warnPct) / max(criticalPct - warnPct, 0.01))
            else:
                color = _blendRgb(GAUGE_TELEMETRY_BAR_LOW, GAUGE_TELEMETRY_BAR_MID, segPct / max(warnPct, 0.01))
        else:
            color = GAUGE_TELEMETRY_BAR_UNLIT
        x0 = barLeft + i * segWidth
        canvas.create_rectangle(x0, barBottom - barHeight, x0 + segWidth * 0.7, barBottom, fill=color, outline="")

    canvas.create_text(
        cx, cy + halfHeight * 0.42, text=str(count), fill=effectiveNumber,
        font=(effectiveFont, max(int(scale * 0.4), 12), "bold"), anchor="center",
    )
    canvas.create_text(
        cx, cy + halfHeight * 0.78, text="GDI x1000", fill=effectiveNumber,
        font=(effectiveFont, max(int(scale * 0.11), 7)), anchor="center",
    )


def _drawDigital(canvas: tk.Canvas, cx: float, cy: float, radius: float, count: int, gdiMax: int,
                   warnThreshold: int, criticalThreshold: int, dialColor: str, fontFamily: str) -> None:
    """Modern LCD-cluster progress ring: no needle, just a colored arc and a big digital readout."""
    effectiveDial = GAUGE_DIGITAL_BG if dialColor == "auto" else dialColor
    effectiveFont = "Consolas" if fontFamily == "auto" else fontFamily
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=effectiveDial, outline="")

    ringRadius = radius * 0.82
    ringWidth = radius * 0.13
    _drawArcBand(canvas, cx, cy, ringRadius, ringWidth, 0.0, 1.0, GAUGE_DIGITAL_TRACK)

    pct = min(count / gdiMax, 1.0)
    color = _zoneColor(count, warnThreshold, criticalThreshold)
    _drawArcBand(canvas, cx, cy, ringRadius, ringWidth, 0.0, max(pct, 0.006), color)

    # End-of-scale reference ticks at 0 / 25 / 50 / 75 / 100 %
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        angle = _angleFor(fraction)
        outer = _point(cx, cy, ringRadius + ringWidth * 0.7, angle)
        inner = _point(cx, cy, ringRadius - ringWidth * 0.7, angle)
        canvas.create_line(*outer, *inner, width=2, fill=effectiveDial)

    canvas.create_text(
        cx, cy - radius * 0.18,
        text="GDI",
        fill=GAUGE_DIGITAL_LABEL, font=(effectiveFont, max(int(radius * 0.09), 7), "bold"), anchor="center",
    )
    canvas.create_text(
        cx, cy + radius * 0.08,
        text=str(count),
        fill=color, font=(effectiveFont, max(int(radius * 0.32), 10), "bold"), anchor="center",
    )
    canvas.create_text(
        cx, cy + radius * 0.38,
        text=f"x1000  ·  {count / 1000:.1f}k / {gdiMax // 1000}k",
        fill=GAUGE_DIGITAL_LABEL, font=(effectiveFont, max(int(radius * 0.07), 7)), anchor="center",
    )


# ── Public entry point ───────────────────────────────────────────────────────────

# Styles that are a wide horizontal band rather than a circular dial — the caller (window
# sizing/aspect-lock code) uses this to avoid forcing a square container for them.
RECTANGULAR_GAUGE_STYLES = {"jdm", "telemetry"}


def isRectangularStyle(gaugeStyle: str) -> bool:
    return gaugeStyle in RECTANGULAR_GAUGE_STYLES


def draw(canvas: tk.Canvas, width: int, height: int, count: int, gdiMax: int,
          warnThreshold: int, criticalThreshold: int, gaugeStyle: str, needleStyle: str,
          needleColor: str = "auto", zoneMode: str = "multicolor", accentColor: str = "auto",
          numberColor: str = "auto", dialColor: str = "auto", needleThickness: float = 1.0,
          fontFamily: str = "auto") -> None:
    if not canvas.winfo_exists():
        return
    canvas.delete("all")
    if width < 20 or height < 20:
        return

    cx, cy = width / 2, height / 2

    if gaugeStyle == "jdm":
        _drawJdmBar(
            canvas, cx, cy, width * 0.47, height * 0.47, count, gdiMax,
            warnThreshold, criticalThreshold, numberColor, dialColor, needleColor, accentColor, zoneMode, fontFamily,
        )
        return
    if gaugeStyle == "telemetry":
        _drawTelemetryBar(
            canvas, cx, cy, width * 0.47, height * 0.47, count, gdiMax,
            warnThreshold, criticalThreshold, numberColor, dialColor, needleColor, accentColor, zoneMode, fontFamily,
        )
        return
    # Always a perfect circle sized to the smaller dimension (never stretched into an
    # ellipse), just with a thinner margin so it fills as much of that dimension as possible.
    radius = min(width, height) * 0.47

    if gaugeStyle == "digital":
        _drawDigital(canvas, cx, cy, radius, count, gdiMax, warnThreshold, criticalThreshold, dialColor, fontFamily)
    else:
        spec = _analogSpec(gaugeStyle)
        _drawAnalog(
            canvas, cx, cy, radius, count, gdiMax, warnThreshold, criticalThreshold, needleStyle,
            needleColor, zoneMode, accentColor, numberColor, dialColor, needleThickness, fontFamily, spec,
        )

