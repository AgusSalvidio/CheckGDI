import time
import tkinter as tk

from src.ui.palette import BG_DARK, BG_CARD, FG_HEADER, FG_MUTED, FG_EMPTY
from src.ui import cards
from src.ui.settingsDialog import SettingsDialog
from src.core.process import Process
from src.core.processChecker import ProcessChecker

DEMO_STEP = 0.02  # fraction of gdiMax the simulated needle advances per tick
DEMO_INTERVAL_MS = 120
HOLD_INTERVAL_MS = 60
GEOMETRY_SAVE_DELAY_MS = 600
BARS_VIEW_MINSIZE = (280, 100)
GAUGE_VIEW_MINSIZE = (140, 140)  # square, so it doesn't fight the single-gauge square enforcement
HOLD_STEP = 0.03  # fraction of gdiMax the held-rev simulation advances per tick while held
HOLD_DECAY_STEP = 0.015  # fraction of gdiMax the held-rev simulation falls per tick after release


class MonitorWindow(tk.Tk):
    def __init__(self, context) -> None:
        super().__init__()
        self._context = context
        self._checker = ProcessChecker.workingWith(context)
        self._afterId: str | None = None
        self._demoMode = False
        self._demoPct = 0.0
        self._demoDirection = 1
        self._holdRevActive = False
        self._holdRevPressed = False
        self._holdRevPct = 0.0
        self._fixedSimActive = False
        self._fixedSimValue = 0
        self._geometrySaveAfterId: str | None = None

        self.title("GDI Monitor")
        self.attributes("-topmost", True)
        self.resizable(True, True)
        self.minsize(*BARS_VIEW_MINSIZE)
        self.configure(bg=BG_DARK)

        self._aspectLocked = False
        self._resizeGuard = False
        self._compactMode = False

        self._settingsDialog = SettingsDialog(
            self, self._context, onChange=self._refresh,
            getDemoMode=lambda: self._demoMode, setDemoMode=self._setDemoMode,
            startHoldRev=self._startHoldRev, stopHoldRev=self._stopHoldRev,
            getFixedSim=lambda: (self._fixedSimActive, self._fixedSimValue), setFixedSim=self._setFixedSim,
        )

        self._buildUI()
        savedGeometry = self._context.windowGeometry()
        if savedGeometry:
            self.geometry(savedGeometry)
        self.bind("<Configure>", self._onConfigure)
        self.protocol("WM_DELETE_WINDOW", self._onClose)
        self.after(0, self._refresh)

    # ── UI construction ───────────────────────────────────────────────────────

    def _buildUI(self) -> None:
        self._header = tk.Frame(self, bg=BG_DARK)
        self._header.pack(fill="x")

        tk.Label(
            self._header,
            text="GDI Monitor",
            bg=BG_DARK, fg=FG_HEADER,
            font=("Consolas", 11, "bold"),
            anchor="w", pady=8, padx=12,
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            self._header, text="⚙", command=self._settingsDialog.open,
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

        # Floating gear used instead of the header in compact mode, so it costs no layout space.
        self._overlayGear = tk.Button(
            self, text="⚙", command=self._settingsDialog.open,
            bg=BG_DARK, fg=FG_MUTED, activebackground=BG_CARD, activeforeground=FG_HEADER,
            font=("Consolas", 9), relief="flat", bd=0, padx=4, pady=1, cursor="hand2",
        )

    def _setCompactMode(self, compact: bool) -> None:
        """Compact mode drops the title bar/footer/card header so a single round gauge
        can fill almost the entire window, keeping only a tiny floating gear button."""
        if compact == self._compactMode:
            return
        self._compactMode = compact
        if compact:
            self._header.pack_forget()
            self._footer.pack_forget()
            self._body.pack_configure(padx=1, pady=1)
            self._overlayGear.place(relx=1.0, rely=0.0, x=-2, y=2, anchor="ne")
            self._overlayGear.lift()
        else:
            self._overlayGear.place_forget()
            self._body.pack_configure(padx=10, pady=(0, 4))
            self._header.pack(fill="x")
            self._footer.pack(fill="x")

    def _setDemoMode(self, enabled: bool) -> None:
        self._demoMode = enabled
        self._demoPct = 0.0
        self._demoDirection = 1
        self._refresh()

    def _startHoldRev(self) -> None:
        """Simulates holding the throttle down: RPM climbs while pressed and, once
        released, keeps ticking on its own until it decays back down to zero."""
        self._holdRevPressed = True
        if not self._holdRevActive:
            self._holdRevActive = True
            self._holdRevPct = 0.0
            self._refresh()

    def _stopHoldRev(self) -> None:
        self._holdRevPressed = False

    def _setFixedSim(self, active: bool, value: int) -> None:
        self._fixedSimActive = active
        self._fixedSimValue = value
        self._refresh()

    def _renderProcess(self, process: Process, count: int, compact: bool) -> None:
        if self._context.viewStyle() == "gauge":
            self.minsize(*GAUGE_VIEW_MINSIZE)
            cards.renderGaugeCard(self._body, process, count, self._context, compact=compact)
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
        if event.widget is not self:
            return
        self._scheduleGeometrySave()
        if not self._aspectLocked or self._resizeGuard:
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

    def _scheduleGeometrySave(self) -> None:
        if self._geometrySaveAfterId is not None:
            self.after_cancel(self._geometrySaveAfterId)
        self._geometrySaveAfterId = self.after(GEOMETRY_SAVE_DELAY_MS, self._saveGeometry)

    def _saveGeometry(self) -> None:
        self._geometrySaveAfterId = None
        self._context.setWindowGeometry(self.geometry())

    def _onClose(self) -> None:
        if self._geometrySaveAfterId is not None:
            self.after_cancel(self._geometrySaveAfterId)
            self._geometrySaveAfterId = None
        self._saveGeometry()
        self.destroy()

    # ── Refresh loop ──────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        if self._afterId is not None:
            self.after_cancel(self._afterId)
            self._afterId = None

        for widget in self._body.winfo_children():
            widget.destroy()

        if self._holdRevActive:
            results = self._holdRevResults()
        elif self._fixedSimActive:
            results = self._fixedSimResults()
        elif self._demoMode:
            results = self._demoResults()
        else:
            results = self._checker.checkAll()
        singleGauge = len(results) == 1 and self._context.viewStyle() == "gauge"
        self._applyAspectLock(singleGauge)
        self._setCompactMode(singleGauge)

        if not results:
            tk.Label(
                self._body,
                text="No process found",
                bg=BG_DARK, fg=FG_EMPTY,
                font=("Consolas", 10), pady=12,
            ).pack()
        else:
            for process, count in results:
                self._renderProcess(process, count, singleGauge)

        if self._holdRevActive:
            self._footer.config(text="modo de prueba · mantené presionado para acelerar")
            self._afterId = self.after(HOLD_INTERVAL_MS, self._refresh)
        elif self._fixedSimActive:
            self._footer.config(text="modo de prueba · valor fijo simulado")
            self._afterId = None
        elif self._demoMode:
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

    def _holdRevResults(self) -> list[tuple[Process, int]]:
        step = HOLD_STEP if self._holdRevPressed else -HOLD_DECAY_STEP
        self._holdRevPct = max(0.0, min(1.0, self._holdRevPct + step))
        if not self._holdRevPressed and self._holdRevPct <= 0.0:
            self._holdRevActive = False

        fakeProcess = Process.composedOf(name="demo.exe", pid=0, exe="demo.exe", description="Vista previa (simulado)")
        count = int(self._context.gdiMax() * self._holdRevPct)
        return [(fakeProcess, count)]

    def _fixedSimResults(self) -> list[tuple[Process, int]]:
        fakeProcess = Process.composedOf(name="demo.exe", pid=0, exe="demo.exe", description="Vista previa (simulado)")
        return [(fakeProcess, self._fixedSimValue)]
