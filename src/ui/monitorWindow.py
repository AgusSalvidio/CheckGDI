import time
import tkinter as tk

from src.ui.palette import BG_DARK, BG_CARD, FG_HEADER, FG_MUTED, FG_EMPTY
from src.ui import cards
from src.ui.settingsDialog import SettingsDialog
from src.core.process import Process
from src.core.processChecker import ProcessChecker

DEMO_STEP = 0.02  # fraction of gdiMax the simulated needle advances per tick
DEMO_INTERVAL_MS = 120
BARS_VIEW_MINSIZE = (280, 100)
GAUGE_VIEW_MINSIZE = (300, 300)  # square, so it doesn't fight the single-gauge square enforcement


class MonitorWindow(tk.Tk):
    def __init__(self, context) -> None:
        super().__init__()
        self._context = context
        self._checker = ProcessChecker.workingWith(context)
        self._afterId: str | None = None
        self._demoMode = False
        self._demoPct = 0.0
        self._demoDirection = 1

        self.title("GDI Monitor")
        self.attributes("-topmost", True)
        self.resizable(True, True)
        self.minsize(*BARS_VIEW_MINSIZE)
        self.configure(bg=BG_DARK)

        self._aspectLocked = False
        self._resizeGuard = False

        self._settingsDialog = SettingsDialog(
            self, self._context, onChange=self._refresh,
            getDemoMode=lambda: self._demoMode, setDemoMode=self._setDemoMode,
        )

        self._buildUI()
        self.bind("<Configure>", self._onConfigure)
        self.after(0, self._refresh)

    # ── UI construction ───────────────────────────────────────────────────────

    def _buildUI(self) -> None:
        header = tk.Frame(self, bg=BG_DARK)
        header.pack(fill="x")

        tk.Label(
            header,
            text="GDI Monitor",
            bg=BG_DARK, fg=FG_HEADER,
            font=("Consolas", 11, "bold"),
            anchor="w", pady=8, padx=12,
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            header, text="⚙", command=self._settingsDialog.open,
            bg=BG_DARK, fg=FG_MUTED, activebackground=BG_CARD, activeforeground=FG_HEADER,
            font=("Consolas", 11), relief="flat", bd=0, padx=10, cursor="hand2",
        ).pack(side="right", padx=(0, 8))

        self._body = tk.Frame(self, bg=BG_DARK)
        self._body.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        self._footer = tk.Label(
            self, text="",
            bg=BG_DARK, fg=FG_EMPTY,
            font=("Consolas", 8),
            anchor="e", padx=10, pady=4,
        )
        self._footer.pack(fill="x")

    def _setDemoMode(self, enabled: bool) -> None:
        self._demoMode = enabled
        self._demoPct = 0.0
        self._demoDirection = 1
        self._refresh()

    def _renderProcess(self, process: Process, count: int) -> None:
        if self._context.viewStyle() == "gauge":
            self.minsize(*GAUGE_VIEW_MINSIZE)
            cards.renderGaugeCard(self._body, process, count, self._context)
        else:
            self.minsize(*BARS_VIEW_MINSIZE)
            cards.renderBarCard(self._body, process, count, self._context)

    def _applyAspectLock(self, singleGauge: bool) -> None:
        """Keeps the window square while a single round gauge is shown, so resizing it
        doesn't create empty space around the (always circular) dial. Tk's wm_aspect is
        not honored by the Windows window manager, so this is enforced manually by
        clamping the window to a square on every resize — see _onConfigure(). Bars view
        and multi-process gauge layouts resize freely."""
        wasLocked = self._aspectLocked
        self._aspectLocked = singleGauge
        if singleGauge and not wasLocked:
            self.update_idletasks()
            self._squareTo(min(self.winfo_width(), self.winfo_height()))

    def _onConfigure(self, event: tk.Event) -> None:
        if event.widget is not self or not self._aspectLocked or self._resizeGuard:
            return
        if event.width == event.height:
            return
        self.after_idle(self._squareTo, min(event.width, event.height))

    def _squareTo(self, size: int) -> None:
        self._resizeGuard = True
        self.geometry(f"{size}x{size}")
        self.after_idle(self._clearResizeGuard)

    def _clearResizeGuard(self) -> None:
        self._resizeGuard = False

    # ── Refresh loop ──────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        if self._afterId is not None:
            self.after_cancel(self._afterId)
            self._afterId = None

        for widget in self._body.winfo_children():
            widget.destroy()

        results = self._demoResults() if self._demoMode else self._checker.checkAll()
        self._applyAspectLock(len(results) == 1 and self._context.viewStyle() == "gauge")

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

        if self._demoMode:
            self._footer.config(text="modo de prueba · valores simulados")
            self._afterId = self.after(DEMO_INTERVAL_MS, self._refresh)
        else:
            self._footer.config(
                text=f"updated {time.strftime('%H:%M:%S')}  ·  every {self._context.pollInterval()}s"
            )
            self._afterId = self.after(self._context.pollInterval() * 1000, self._refresh)

    def _demoResults(self) -> list[tuple[Process, int]]:
        self._demoPct += DEMO_STEP * self._demoDirection
        if self._demoPct >= 1.0:
            self._demoPct = 1.0
            self._demoDirection = -1
        elif self._demoPct <= 0.0:
            self._demoPct = 0.0
            self._demoDirection = 1

        fakeProcess = Process.composedOf(name="demo.exe", pid=0, exe="demo.exe", description="Vista previa (simulado)")
        count = int(self._context.gdiMax() * self._demoPct)
        return [(fakeProcess, count)]
