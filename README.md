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
