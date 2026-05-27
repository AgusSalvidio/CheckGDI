import time
import tkinter as tk

from src.ui.palette import BG_DARK, BG_CARD, FG_HEADER, FG_MUTED, FG_EMPTY, BAR_BG, COLOR_GREEN, COLOR_YELLOW, COLOR_RED
from src.core.process import Process
from src.core.processChecker import ProcessChecker


class MonitorWindow(tk.Tk):
    def __init__(self, context) -> None:
        super().__init__()
        self._context = context
        self._checker = ProcessChecker.workingWith(context)

        self.title("GDI Monitor")
        self.attributes("-topmost", True)
        self.resizable(True, True)
        self.minsize(280, 100)
        self.configure(bg=BG_DARK)

        self._buildUI()
        self.after(0, self._refresh)

    # ── UI construction ───────────────────────────────────────────────────────

    def _buildUI(self) -> None:
        tk.Label(
            self,
            text="GDI Monitor",
            bg=BG_DARK, fg=FG_HEADER,
            font=("Consolas", 11, "bold"),
            anchor="w", pady=8, padx=12,
        ).pack(fill="x")

        self._body = tk.Frame(self, bg=BG_DARK)
        self._body.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        self._footer = tk.Label(
            self, text="",
            bg=BG_DARK, fg=FG_EMPTY,
            font=("Consolas", 8),
            anchor="e", padx=10, pady=4,
        )
        self._footer.pack(fill="x")

    def _renderProcess(self, process: Process, count: int) -> None:
        color = self._colorFor(count)
        pct   = min(count / self._context.gdiMax(), 1.0)

        card = tk.Frame(self._body, bg=BG_CARD, padx=10, pady=6)
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

        tk.Label(
            left, text=process.displayName(),
            bg=BG_CARD, fg=FG_HEADER,
            font=("Consolas", 10, "bold"), anchor="w",
        ).pack(anchor="w")

        tk.Label(
            left, text=f"{process.name}  ·  PID  {process.pid}",
            bg=BG_CARD, fg=FG_MUTED,
            font=("Consolas", 8), anchor="w",
        ).pack(anchor="w")

        if self._context.showBar():
            barHeight = 16 if self._context.showPercentage() else 6
            bar = tk.Canvas(card, height=barHeight, highlightthickness=0, bg=BAR_BG)
            bar.pack(fill="x", pady=(4, 0))
            bar.bind("<Configure>", lambda e, b=bar, p=pct, c=color: self._drawBar(b, p, c))

    # ── Refresh loop ──────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        for widget in self._body.winfo_children():
            widget.destroy()

        results = self._checker.checkAll()

        if not results:
            tk.Label(
                self._body,
                text="No process found",
                bg=BG_DARK, fg=FG_EMPTY,
                font=("Consolas", 10), pady=12,
            ).pack()
        else:
            for process, count in results:
                self._renderProcess(process, count)

        self._footer.config(
            text=f"updated {time.strftime('%H:%M:%S')}  ·  every {self._context.pollInterval()}s"
        )
        self.after(self._context.pollInterval() * 1000, self._refresh)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _colorFor(self, count: int) -> str:
        if count >= self._context.gdiCriticalThreshold():
            return COLOR_RED
        if count >= self._context.gdiWarnThreshold():
            return COLOR_YELLOW
        return COLOR_GREEN

    def _drawBar(self, canvas: tk.Canvas, fillPct: float, color: str) -> None:
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        fillW = int(w * fillPct)
        if fillW > 0:
            canvas.create_rectangle(0, 0, fillW, h, fill=color, outline="")
        if self._context.showPercentage():
            label = f"{fillPct * 100:.1f}%"
            cx, cy = w // 2, h // 2
            # Shadow pass for readability over both light fill and dark background
            canvas.create_text(cx + 1, cy + 1, text=label, fill="#1e1e2e", font=("Consolas", 8, "bold"), anchor="center")
            canvas.create_text(cx,     cy,     text=label, fill="#cdd6f4", font=("Consolas", 8, "bold"), anchor="center")
