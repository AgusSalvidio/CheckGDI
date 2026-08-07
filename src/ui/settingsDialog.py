"""Owns the "Visual settings" popup window: a compact left-nav / right-content layout
with tabs (Vista, Perfiles, Diseño, Aguja, Zonas, Pruebas). Kept separate from
MonitorWindow so the main window class only has to deal with orchestration, not the
whole settings-UI tree."""

import tkinter as tk
from typing import Callable

from src.ui.palette import BG_DARK, BG_CARD, BAR_BG, FG_HEADER, FG_MUTED, COLOR_RED
from src.ui.widgets import addDropdown, addColorPickerRow, addSliderRow, addFontPickerRow
from src.ui import gaugeColors

FIXED_SIM_RESOLUTION = 10

NAV_WIDTH = 128
CONTENT_WIDTH = 300
POPUP_HEIGHT = 420
SIDE_GAP = 14


class SettingsDialog:
    def __init__(self, owner: tk.Tk, context, onChange: Callable[[], None],
                 getDemoMode: Callable[[], bool], setDemoMode: Callable[[bool], None],
                 startHoldRev: Callable[[], None], stopHoldRev: Callable[[], None],
                 getFixedSim: Callable[[], tuple[bool, int]], setFixedSim: Callable[[bool, int], None]) -> None:
        self._owner = owner
        self._context = context
        self._onChange = onChange
        self._getDemoMode = getDemoMode
        self._setDemoMode = setDemoMode
        self._startHoldRev = startHoldRev
        self._stopHoldRev = stopHoldRev
        self._getFixedSim = getFixedSim
        self._setFixedSim = setFixedSim
        self._window: tk.Toplevel | None = None
        self._navButtons: dict[str, tk.Button] = {}
        self._tabFrames: dict[str, tk.Frame] = {}
        self._activeTab = "vista"

    def isOpen(self) -> bool:
        return self._window is not None and self._window.winfo_exists()

    def open(self) -> None:
        if self.isOpen():
            self._positionBesideOwner(self._window)
            self._window.lift()
            return
        self._context.beginEditSession()
        self._build()

    def reopen(self) -> None:
        """Destroys and rebuilds the popup — used after a change (e.g. profile switch)
        that alters which controls/values should be shown. Keeps whichever tab was open
        and does NOT touch the edit session (still uncommitted until Guardar/Cancelar)."""
        self._onChange()
        if self.isOpen():
            self._window.destroy()
        self._window = None
        self._build()

    def _commit(self) -> None:
        self._context.commitEditSession()
        self._onChange()
        self._closeWindow()

    def _cancel(self) -> None:
        self._context.cancelEditSession()
        self._onChange()
        self._closeWindow()

    def _closeWindow(self) -> None:
        if self.isOpen():
            self._window.destroy()
        self._window = None

    # ── Placement ─────────────────────────────────────────────────────────────

    def _positionBesideOwner(self, popup: tk.Toplevel) -> None:
        """Anchors the popup to the right of the main window (or to the left if there
        isn't enough room on the right), so it always sits beside it rather than landing
        wherever it last happened to be."""
        popup.update_idletasks()
        ownerX, ownerY = self._owner.winfo_x(), self._owner.winfo_y()
        ownerW = self._owner.winfo_width()
        popupW = popup.winfo_reqwidth()
        screenW = popup.winfo_screenwidth()

        x = ownerX + ownerW + SIDE_GAP
        if x + popupW > screenW:
            x = max(ownerX - popupW - SIDE_GAP, 0)
        y = ownerY
        popup.geometry(f"+{x}+{y}")

    # ── Construction ──────────────────────────────────────────────────────────

    def _buildFooter(self, popup: tk.Toplevel) -> None:
        tk.Frame(popup, bg=BAR_BG, height=1).pack(side="bottom", fill="x")
        footer = tk.Frame(popup, bg=BG_DARK)
        footer.pack(side="bottom", fill="x")

        tk.Button(
            footer, text="Guardar", command=self._commit, bg="#3a5c3a", fg=FG_HEADER,
            activebackground="#446b44", activeforeground=FG_HEADER, font=("Consolas", 9, "bold"),
            relief="flat", padx=14, pady=4, cursor="hand2",
        ).pack(side="right", padx=(6, 14), pady=8)
        tk.Button(
            footer, text="Cancelar", command=self._cancel, bg=BG_CARD, fg=FG_MUTED,
            activebackground=BG_CARD, activeforeground=FG_HEADER, font=("Consolas", 9),
            relief="flat", padx=14, pady=4, cursor="hand2",
        ).pack(side="right", pady=8)

    def _build(self) -> None:
        context = self._context
        popup = tk.Toplevel(self._owner, bg=BG_DARK)
        self._window = popup
        self._navButtons = {}
        self._tabFrames = {}
        popup.title("Configuración")
        popup.attributes("-topmost", True)
        popup.resizable(False, False)
        popup.transient(self._owner)
        popup.protocol("WM_DELETE_WINDOW", self._cancel)

        tk.Label(
            popup, text="Configuración", bg=BG_DARK, fg=FG_HEADER,
            font=("Consolas", 12, "bold"), anchor="w", padx=14, pady=10,
        ).pack(fill="x")
        tk.Frame(popup, bg=BAR_BG, height=1).pack(fill="x")

        self._buildFooter(popup)

        body = tk.Frame(popup, bg=BG_DARK)
        body.pack(fill="both", expand=True)

        nav = tk.Frame(body, bg=BG_CARD, width=NAV_WIDTH)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)

        content = tk.Frame(body, bg=BG_DARK, width=CONTENT_WIDTH, height=POPUP_HEIGHT)
        content.pack(side="left", fill="both", expand=True)
        content.pack_propagate(False)

        viewVar = tk.StringVar(value=context.viewStyle())
        gaugeVar = tk.StringVar(value=context.gaugeStyle())
        needleVar = tk.StringVar(value=context.needleStyle())
        zoneVar = tk.StringVar(value=context.zoneMode())

        def gaugeTabsEnabled() -> bool:
            return viewVar.get() == "gauge"

        def updateGaugeTabsState() -> None:
            state = "normal" if gaugeTabsEnabled() else "disabled"
            for key in ("perfiles", "diseno", "aguja", "zonas"):
                self._navButtons[key].configure(state=state)
            if not gaugeTabsEnabled() and self._activeTab in ("perfiles", "diseno", "aguja", "zonas"):
                self._showTab("vista")

        def applyView() -> None:
            context.setViewStyle(viewVar.get())
            updateGaugeTabsState()
            self._onChange()

        def applyGauge() -> None:
            context.setGaugeStyle(gaugeVar.get())
            self._onChange()

        def applyNeedle() -> None:
            context.setNeedleStyle(needleVar.get())
            self._onChange()

        def applyZoneMode() -> None:
            context.setZoneMode(zoneVar.get())
            self._onChange()

        vistaFrame = tk.Frame(content, bg=BG_DARK)
        self._sectionTitle(vistaFrame, "Vista")
        addDropdown(vistaFrame, viewVar, (("bars", "Barras"), ("gauge", "Aguja (RPM)")), applyView)

        perfilesFrame = tk.Frame(content, bg=BG_DARK)
        self._buildProfilesTab(perfilesFrame)

        disenoFrame = tk.Frame(content, bg=BG_DARK)
        self._sectionTitle(disenoFrame, "Diseño del tacómetro")
        addDropdown(
            disenoFrame, gaugeVar,
            (
                ("classic", "Clásico"), ("retro", "Retro"),
                ("veglia", "Veglia"), ("ferrari", "Italiano"),
                ("aston", "Británico"), ("jdm", "JDM"), ("telemetry", "Telemetría"),
                ("digital", "Digital"),
            ),
            applyGauge,
        )
        addColorPickerRow(
            disenoFrame, "Dial", lambda: gaugeColors.resolvedDialColor(context),
            context.dialColor, context.setDialColor, self._onChange, popup,
        )
        addColorPickerRow(
            disenoFrame, "Números", lambda: gaugeColors.resolvedNumberColor(context),
            context.numberColor, context.setNumberColor, self._onChange, popup,
        )
        addFontPickerRow(
            disenoFrame, "Fuente", context.fontFamily, context.setFontFamily, self._onChange,
        )

        agujaFrame = tk.Frame(content, bg=BG_DARK)
        self._sectionTitle(agujaFrame, "Aguja")
        addDropdown(
            agujaFrame, needleVar,
            (("classic", "Clásica"), ("sport", "Deportiva"), ("twin", "Doble riel"), ("line", "Línea"), ("slim", "Fina (moto)")),
            applyNeedle,
        )
        addColorPickerRow(
            agujaFrame, "Color", lambda: gaugeColors.resolvedNeedleColor(context),
            context.needleColor, context.setNeedleColor, self._onChange, popup,
        )
        addSliderRow(agujaFrame, "Grosor", context.needleThickness, context.setNeedleThickness, self._onChange)

        zonasFrame = tk.Frame(content, bg=BG_DARK)
        self._sectionTitle(zonasFrame, "Zonas de color")
        addDropdown(zonasFrame, zoneVar, (("multicolor", "Multicolor"), ("mono", "Monocromo")), applyZoneMode)
        addColorPickerRow(
            zonasFrame, "Acento monocromo", lambda: gaugeColors.resolvedAccentColor(context),
            context.accentColor, context.setAccentColor, self._onChange, popup,
        )

        pruebasFrame = tk.Frame(content, bg=BG_DARK)
        self._buildTestsTab(pruebasFrame)

        self._tabFrames = {
            "vista": vistaFrame, "perfiles": perfilesFrame, "diseno": disenoFrame,
            "aguja": agujaFrame, "zonas": zonasFrame, "pruebas": pruebasFrame,
        }

        for key, label in (
            ("vista", "Vista"), ("perfiles", "Perfiles"), ("diseno", "Diseño"),
            ("aguja", "Aguja"), ("zonas", "Zonas"), ("pruebas", "Pruebas"),
        ):
            self._addNavButton(nav, key, label)

        updateGaugeTabsState()
        self._showTab(self._activeTab if gaugeTabsEnabled() or self._activeTab == "vista" else "vista")

        self._positionBesideOwner(popup)

    def _sectionTitle(self, parent: tk.Frame, title: str) -> None:
        tk.Label(
            parent, text=title, bg=BG_DARK, fg=FG_HEADER,
            font=("Consolas", 10, "bold"), anchor="w", padx=14,
        ).pack(fill="x", pady=(2, 8))

    def _addNavButton(self, nav: tk.Frame, key: str, label: str) -> None:
        button = tk.Button(
            nav, text=label, command=lambda: self._showTab(key),
            bg=BG_CARD, fg=FG_MUTED, activebackground=BAR_BG, activeforeground=FG_HEADER,
            disabledforeground="#4a4d5e", font=("Consolas", 9), relief="flat", bd=0,
            anchor="w", padx=14, pady=8, cursor="hand2",
        )
        button.pack(fill="x")
        self._navButtons[key] = button

    def _showTab(self, key: str) -> None:
        self._activeTab = key
        for tabKey, frame in self._tabFrames.items():
            frame.pack_forget()
        self._tabFrames[key].pack(fill="both", expand=True, padx=(4, 10), pady=10)
        for navKey, button in self._navButtons.items():
            button.configure(bg=(BAR_BG if navKey == key else BG_CARD), fg=(FG_HEADER if navKey == key else FG_MUTED))

    def _buildProfilesTab(self, parent: tk.Frame) -> None:
        context = self._context
        self._sectionTitle(parent, "Perfiles")

        profileVar = tk.StringVar(value=context.activeProfile())

        def applyProfile() -> None:
            context.setActiveProfile(profileVar.get())
            self.reopen()

        addDropdown(
            parent, profileVar,
            [(name, name) for name in context.profileNames()],
            applyProfile,
        )

        tk.Label(
            parent, text="Renombrar perfil actual", bg=BG_DARK, fg=FG_MUTED,
            font=("Consolas", 8), anchor="w", padx=14,
        ).pack(fill="x", pady=(10, 2))

        renameRow = tk.Frame(parent, bg=BG_DARK)
        renameRow.pack(fill="x", padx=14, pady=(0, 2))

        renameVar = tk.StringVar(value=context.activeProfile())
        tk.Entry(
            renameRow, textvariable=renameVar, bg=BG_CARD, fg=FG_HEADER, insertbackground=FG_HEADER,
            relief="flat", font=("Consolas", 9),
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        renameWarningLabel = tk.Label(
            parent, text="Ya existe un perfil con ese nombre",
            bg=BG_DARK, fg=COLOR_RED, font=("Consolas", 8), anchor="w", padx=14,
        )

        def renameActiveProfile() -> None:
            newName = renameVar.get().strip()
            if not newName or newName == context.activeProfile():
                return
            if newName in context.profileNames():
                renameWarningLabel.pack(fill="x", pady=(0, 4), after=renameRow)
                return
            context.renameProfile(context.activeProfile(), newName)
            self.reopen()

        tk.Button(
            renameRow, text="✎ Renombrar", command=renameActiveProfile, bg=BG_CARD, fg=FG_HEADER,
            activebackground=BG_CARD, activeforeground=FG_HEADER, font=("Consolas", 9),
            relief="flat", padx=8,
        ).pack(side="left")

        tk.Label(
            parent, text="Nuevo perfil a partir del actual", bg=BG_DARK, fg=FG_MUTED,
            font=("Consolas", 8), anchor="w", padx=14,
        ).pack(fill="x", pady=(10, 2))

        newProfileRow = tk.Frame(parent, bg=BG_DARK)
        newProfileRow.pack(fill="x", padx=14, pady=(0, 2))

        nameVar = tk.StringVar()
        tk.Entry(
            newProfileRow, textvariable=nameVar, bg=BG_CARD, fg=FG_HEADER, insertbackground=FG_HEADER,
            relief="flat", font=("Consolas", 9),
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        warningLabel = tk.Label(
            parent, text="Ya existe un perfil con ese nombre",
            bg=BG_DARK, fg=COLOR_RED, font=("Consolas", 8), anchor="w", padx=14,
        )

        def saveAsNewProfile() -> None:
            name = nameVar.get().strip()
            if not name:
                return
            if name in context.profileNames():
                warningLabel.pack(fill="x", pady=(0, 4), after=newProfileRow)
                return
            context.createProfile(name)
            self.reopen()

        tk.Button(
            newProfileRow, text="Crear", command=saveAsNewProfile, bg=BG_CARD, fg=FG_HEADER,
            activebackground=BG_CARD, activeforeground=FG_HEADER, font=("Consolas", 9),
            relief="flat", padx=8,
        ).pack(side="left")

        def deleteActiveProfile() -> None:
            context.deleteProfile(context.activeProfile())
            self.reopen()

        deleteBtn = tk.Button(
            parent, text="Eliminar perfil actual", command=deleteActiveProfile, bg=BG_CARD, fg=FG_HEADER,
            activebackground=BG_CARD, activeforeground=FG_HEADER, font=("Consolas", 9),
            relief="flat", padx=8,
        )
        deleteBtn.pack(anchor="w", padx=14, pady=(12, 6))
        if len(context.profileNames()) <= 1:
            deleteBtn.configure(state="disabled")

    def _buildTestsTab(self, parent: tk.Frame) -> None:
        self._sectionTitle(parent, "Pruebas")
        demoVar = tk.BooleanVar(value=self._getDemoMode())

        def applyDemo() -> None:
            self._setDemoMode(demoVar.get())

        tk.Checkbutton(
            parent, text="Simular valores (barrido automático)", variable=demoVar, command=applyDemo,
            bg=BG_DARK, fg=FG_HEADER, selectcolor=BG_CARD, activebackground=BG_DARK,
            activeforeground=FG_HEADER, font=("Consolas", 9), anchor="w", padx=14,
            highlightthickness=0,
        ).pack(fill="x")

        holdBtn = tk.Button(
            parent, text="Mantener para aumentar GDIs", bg=BG_CARD, fg=FG_HEADER,
            activebackground=BG_CARD, activeforeground=FG_HEADER, font=("Consolas", 9),
            relief="flat", padx=8, pady=6,
        )
        holdBtn.pack(fill="x", padx=14, pady=(10, 6))
        holdBtn.bind("<ButtonPress-1>", lambda e: self._startHoldRev())
        holdBtn.bind("<ButtonRelease-1>", lambda e: self._stopHoldRev())

        fixedActive, fixedValue = self._getFixedSim()
        fixedActiveVar = tk.BooleanVar(value=fixedActive)
        fixedValueVar = tk.IntVar(value=fixedValue)

        def applyFixed(_=None) -> None:
            self._setFixedSim(fixedActiveVar.get(), fixedValueVar.get())

        tk.Checkbutton(
            parent, text="Fijar en un valor", variable=fixedActiveVar, command=applyFixed,
            bg=BG_DARK, fg=FG_HEADER, selectcolor=BG_CARD, activebackground=BG_DARK,
            activeforeground=FG_HEADER, font=("Consolas", 9), anchor="w", padx=14,
            highlightthickness=0,
        ).pack(fill="x", pady=(12, 0))

        fixedRow = tk.Frame(parent, bg=BG_DARK)
        fixedRow.pack(fill="x", padx=14)
        tk.Scale(
            fixedRow, from_=0, to=self._context.gdiMax(), resolution=FIXED_SIM_RESOLUTION,
            orient="horizontal", variable=fixedValueVar, command=applyFixed,
            bg=BG_DARK, fg=FG_HEADER, troughcolor=BG_CARD, highlightthickness=0,
            activebackground=BG_CARD, font=("Consolas", 8), showvalue=True,
        ).pack(fill="x")
