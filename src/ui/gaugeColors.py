"""Resolves the effective color to draw with when a setting is "auto" — a single source of
truth shared by the gauge card (for actual drawing) and the settings dialog (for swatch
previews), instead of duplicating each gauge style's default colors in multiple places."""

from src.ui import gaugeWidget


def resolvedNeedleColor(context) -> str:
    color = context.needleColor()
    return color if color != "auto" else gaugeWidget.defaultNeedleColor(context.gaugeStyle())


def resolvedAccentColor(context) -> str:
    color = context.accentColor()
    return color if color != "auto" else resolvedNeedleColor(context)


def resolvedNumberColor(context) -> str:
    color = context.numberColor()
    return color if color != "auto" else gaugeWidget.defaultNumberColor(context.gaugeStyle())


def resolvedDialColor(context) -> str:
    color = context.dialColor()
    return color if color != "auto" else gaugeWidget.defaultDialColor(context.gaugeStyle())
