# CheckGDI

<img src="assets/logos/logo.png" alt="Logo" width="200" height="100">

Real-time GDI object monitor for Windows. Displays a always-on-top window with traffic-light color coding per process, a progress bar, and optional desktop notifications when a critical threshold is reached.

## Quick links 🚀

- [Report a defect](https://github.com/AgusSalvidio/CheckGDI/issues/new?labels=Type%3A+Defect)
- [Request a feature](https://github.com/AgusSalvidio/CheckGDI/issues/new?labels=Type%3A+Feature)

---

## Requirements

- Windows (uses Win32 APIs)
- Python 3.10+

---

## Installation

### 1. Create the virtual environment

```cmd
cd CheckGDI
python -m venv .venv
```

### 2. Activate it

**cmd.exe**
```cmd
.venv\Scripts\activate.bat
```

**PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

> If PowerShell blocks `.ps1` execution, run first:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### 3. Install dependencies

```cmd
pip install -r requirements.txt
```

---

## Configuration

Copy `.env.example` to `.env` and edit as needed:

| Variable                 | Default | Description                                                              |
|--------------------------|---------|--------------------------------------------------------------------------|
| `PROCESS_NAMES`          | `abt`   | Process names to monitor, comma-separated (partial match, case-insensitive) |
| `POLL_INTERVAL`          | `10`    | Seconds between each refresh                                             |
| `GDI_WARN_THRESHOLD`     | `100`   | Count at which the indicator turns yellow                                |
| `GDI_CRITICAL_THRESHOLD` | `300`   | Count at which the indicator turns red                                   |
| `GDI_MAX`                | `10000` | Windows GDI limit per process (used for the progress bar scale)         |
| `NOTIFICATION_ENABLED`   | `true`  | Enable desktop notifications when the critical threshold is reached      |
| `NOTIFICATION_COOLDOWN`  | `60`    | Minimum seconds between notifications for the same PID                  |
| `SHOW_BAR`               | `true`  | Show the progress bar under each process card                            |
| `SHOW_PERCENTAGE`        | `true`  | Show the percentage centered inside the bar (requires `SHOW_BAR=true`)  |
| `VIEW_STYLE`             | `bars`  | Visual style per card: `bars` (progress bar) or `gauge` (RPM-style dial, GDI in thousands) |
| `GAUGE_STYLE`            | `classic` | Tachometer design for the `gauge` view: `classic`, `retro` or `digital`                |
| `NEEDLE_STYLE`           | `classic` | Needle shape for the `classic`/`retro` gauge designs: `classic`, `sport`, `twin` or `line` |
| `NEEDLE_COLOR`           | `auto`  | Needle color override: `auto` (style default) or a hex color like `#ff6600`             |
| `GAUGE_ZONE_MODE`        | `multicolor` | Tick coloring: `multicolor` (yellow/red zones) or `mono` (single accent color, BMW-style) |
| `GAUGE_ACCENT_COLOR`     | `auto`  | Accent color used by every tick when `GAUGE_ZONE_MODE=mono`, independent of `NEEDLE_COLOR` |
| `GAUGE_NUMBER_COLOR`     | `auto`  | Tick number / digit color override: `auto` (style default) or a hex color               |
| `GAUGE_DIAL_COLOR`       | `auto`  | Dial/face background color override: `auto` (style default) or a hex color              |
| `NEEDLE_THICKNESS`       | `1.0`   | Needle thickness multiplier for `classic`/`retro` designs (0.5 thin .. 3.0 thick)        |

To monitor multiple processes, use a comma-separated list:
```
PROCESS_NAMES=abt,hyperspace,bell
```

---

## Usage

With the virtual environment active:

```cmd
python main.py
```

A resizable, always-on-top window opens showing a card per process instance:

- **Description** — human-readable name read from the executable's version resource
- **exe name · PID** — subtitle for identification
- **GDI count** — current value in traffic-light color
- **Progress bar** — proportional to `GDI_MAX`, with optional percentage label
- **Footer** — timestamp of the last refresh and the configured interval

### View styles

Set `VIEW_STYLE=gauge` to switch every card from the progress bar to an automotive tachometer. Pick the full dashboard design with `GAUGE_STYLE`:

| Style     | Look                                                                                   |
|-----------|------------------------------------------------------------------------------------------|
| `classic` | Chrome-bezel analog dial, black face, white numbers — reference BMW-style tachometer     |
| `retro`   | Vintage ivory face, thin bezel, serif numerals — classic '60s car cluster                |
| `digital` | Modern LCD progress ring with a big digital readout, no needle                           |

For `classic`/`retro`, pick the needle look with `NEEDLE_STYLE`:

| Style     | Look                                                            |
|-----------|------------------------------------------------------------------|
| `classic` | Tapered dagger blade with a counterweight tail                   |
| `sport`   | Two-tone racing blade: flat shaft + bright wedge tip              |
| `twin`    | Slim double-rail pointer converging to a small diamond tip        |
| `line`    | Minimalist thin line ending in an accent dot                     |

`VIEW_STYLE`, `GAUGE_STYLE` and `NEEDLE_STYLE` can all be changed live from the ⚙ button in the app, without restarting. That popup is organized into side tabs (Vista, Perfiles, Diseño, Aguja, Zonas, Pruebas) — click a tab on the left to switch sections.

The ⚙ button also lets you independently override, each with its own color picker and "Auto" reset to the style default:

- **Aguja** — the needle color, style and thickness.
- **Diseño** — the tachometer design, plus the dial background and number colors.
- **Zonas** — the multicolor/mono tick mode, plus the mono accent color (decoupled from the needle color).

`GAUGE_ZONE_MODE` switches the tick coloring between `multicolor` (yellow/red zones matching the thresholds) and `mono` (every tick uses the accent color above, regardless of threshold).

Every change in the settings popup is previewed instantly on the gauge but is **not** written to disk until you press **Guardar** — press **Cancelar** (or close the popup) to discard everything done since it was opened and go back to the last saved state.

#### Profiles

All of the gauge design/needle/color settings above belong to a **profile**, shown in the "Perfiles" tab. Selecting a profile previews its whole combination instantly; use "Crear" to save the current combination under a new profile name, and "Eliminar perfil actual" to remove it (at least one profile always remains). None of this is persisted until you press the dialog's **Guardar** button. Profiles are stored locally in `.gdi_monitor_settings.json` (gitignored) and survive restarts.


### Traffic-light colors

| Color  | Meaning                                                    |
|--------|------------------------------------------------------------|
| Green  | GDI count below `GDI_WARN_THRESHOLD`                    |
| Yellow | Between `GDI_WARN_THRESHOLD` and `GDI_CRITICAL_THRESHOLD` |
| Red    | At or above `GDI_CRITICAL_THRESHOLD`                    |

---

## License 📋

- The code is licensed under [MIT](LICENSE).
- The documentation is licensed under [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/).
