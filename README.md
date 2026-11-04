# UpdatyMeow 🐱

### Every update on your Linux machine. One window.

Inspired by [UpdatyMe](https://github.com/DanielFiller30/UpdatyMe) for macOS, **UpdatyMeow** brings the unified, single-window update experience to the Linux desktop.

APT, Flatpak, Snap, Python packages, global NPM tools, and developer runtimes — UpdatyMeow discovers what you have installed, tells you what's outdated, and updates it when *you* say so.

---

## ✨ Features

- 🔍 **One Unified Inventory**: Scans across your entire system in parallel:
  - **System**: Debian/Ubuntu APT packages & firmware
  - **Apps**: Flatpaks and Snaps
  - **Packages**: Global `npm` and Python `pip` packages
  - **Runtimes**: Node.js, Python, uv, Rust
- 🛡️ **You Stay in Control**:
  - Transparent command previews for every update
  - Copy command to clipboard with one click
  - Live streamed output in an update console
- 📌 **Pin & Favorite**:
  - Pin packages to suppress update alerts
  - Star favorite packages for rapid access
- ⚡ **Update One or All**:
  - Update selected packages or hit **Update All**
- 🕒 **History**:
  - Tracks update runs with timestamps, versions, and execution logs
- 💻 **CLI & GUI Modes**:
  - Launch full desktop GUI or run `updatymeow --check` in terminal / cron scripts

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- PyQt5 (`sudo apt install python3-pyqt5`)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/emacholdt/updatymeow.git
cd updatymeow

# Run GUI
./run.py

# Or run terminal check
./run.py --check
```

### Install Desktop Launcher

```bash
mkdir -p ~/.local/share/applications
cp updatymeow.desktop ~/.local/share/applications/
```

---

## 🧪 Testing

UpdatyMeow is built with Test-Driven Development (TDD) using standard library `unittest`:

```bash
python3 -m unittest discover tests
```

---

## 📄 License

MIT License. Inspired by [Daniel Filler's UpdatyMe](https://github.com/DanielFiller30/UpdatyMe).
