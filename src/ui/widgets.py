"""Small, reusable Tkinter widget builders shared by the settings dialog (and anywhere
else a themed collapsible section / radio group / color picker / slider is needed)."""

import tkinter as tk
from tkinter import colorchooser
from typing import Callable, Iterable

from src.ui.palette import BG_DARK, BG_CARD, FG_HEADER, FG_MUTED


def addCollapsible(parent: tk.Widget, title: str, expanded: bool = False) -> tk.Frame:
    header = tk.Frame(parent, bg=BG_DARK)
    header.pack(fill="x", pady=(10, 0))

    content = tk.Frame(parent, bg=BG_DARK)

    def toggle() -> None:
        if content.winfo_ismapped():
            content.pack_forget()
            toggleBtn.configure(text="▸")
        else:
            content.pack(fill="x", after=header)
            toggleBtn.configure(text="▾")

    toggleBtn = tk.Button(
        header, text=("▾" if expanded else "▸"), command=toggle,
        bg=BG_DARK, fg=FG_MUTED, activebackground=BG_DARK, activeforeground=FG_HEADER,
        font=("Consolas", 9), relief="flat", bd=0, width=2, cursor="hand2",
    )
    toggleBtn.pack(side="left")

    tk.Label(
        header, text=title, bg=BG_DARK, fg=FG_HEADER,
        font=("Consolas", 9, "bold"), anchor="w",
    ).pack(side="left", fill="x", expand=True)

    if expanded:
        content.pack(fill="x", after=header)

    return content


def addRadioGroup(parent: tk.Widget, variable: tk.Variable, options: Iterable[tuple[str, str]],
                   command: Callable[[], None]) -> None:
    for value, label in options:
        tk.Radiobutton(
            parent, text=label, value=value, variable=variable, command=command,
            bg=BG_DARK, fg=FG_HEADER, selectcolor=BG_CARD, activebackground=BG_DARK,
            activeforeground=FG_HEADER, font=("Consolas", 9), anchor="w", padx=16,
            highlightthickness=0,
        ).pack(fill="x")


def addColorPickerRow(parent: tk.Widget, title: str, resolve: Callable[[], str],
                       getRaw: Callable[[], str], setRaw: Callable[[str], None],
                       onChange: Callable[[], None], dialogOwner: tk.Misc) -> None:
    tk.Label(
        parent, text=title, bg=BG_DARK, fg=FG_HEADER,
        font=("Consolas", 9), anchor="w", padx=16,
    ).pack(fill="x", pady=(6, 2))

    row = tk.Frame(parent, bg=BG_DARK)
    row.pack(fill="x", padx=16)

    swatch = tk.Label(row, text="  ", bg=resolve(), relief="solid", borderwidth=1, width=3)
    swatch.pack(side="left", padx=(0, 8))

    def pick() -> None:
        picked = colorchooser.askcolor(color=resolve(), parent=dialogOwner, title=title)
        if picked and picked[1]:
            setRaw(picked[1])
            swatch.configure(bg=picked[1])
            onChange()

    def reset() -> None:
        setRaw("auto")
        swatch.configure(bg=resolve())
        onChange()

    tk.Button(
        row, text="Elegir…", command=pick, bg=BG_CARD, fg=FG_HEADER,
        activebackground=BG_CARD, activeforeground=FG_HEADER, font=("Consolas", 9),
        relief="flat", padx=8,
    ).pack(side="left", padx=(0, 6))
    tk.Button(
        row, text="Auto", command=reset, bg=BG_CARD, fg=FG_HEADER,
        activebackground=BG_CARD, activeforeground=FG_HEADER, font=("Consolas", 9),
        relief="flat", padx=8,
    ).pack(side="left")


def addSliderRow(parent: tk.Widget, title: str, getValue: Callable[[], float],
                  setValue: Callable[[float], None], onChange: Callable[[], None],
                  frm: float = 0.5, to: float = 2.5, resolution: float = 0.1) -> None:
    tk.Label(
        parent, text=title, bg=BG_DARK, fg=FG_HEADER,
        font=("Consolas", 9), anchor="w", padx=16,
    ).pack(fill="x", pady=(6, 0))

    row = tk.Frame(parent, bg=BG_DARK)
    row.pack(fill="x", padx=16)

    var = tk.DoubleVar(value=getValue())

    def onSliderChange(_value) -> None:
        setValue(var.get())
        onChange()

    tk.Scale(
        row, from_=frm, to=to, resolution=resolution, orient="horizontal", variable=var,
        command=onSliderChange, bg=BG_DARK, fg=FG_HEADER, troughcolor=BG_CARD,
        highlightthickness=0, activebackground=BG_CARD, font=("Consolas", 8), showvalue=True,
    ).pack(fill="x")
