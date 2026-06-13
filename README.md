# Hermes Headed Browser Plugin 🖱️

A **headed desktop browser automation** plugin for Hermes Agent that lets you — and your users — see every mouse move, click, and keystroke in real-time on a visible Chrome window.

> **Use case:** When the user says "do this for me and test," you can actually launch a visible Chrome window, navigate to their site, fill forms, click buttons, and they watch it happen live.

---

## What You See

- **1–2 second mouse glides** — cursor smoothly animates across screen (not instant jumps)
- **Visual wiggle before click** — cursor does a small attention ring to show target
- **Attention-ring highlights** — circle drawn around elements without clicking
- **Character-by-character typing** — 30ms per keystroke, clearly visible
- **Live screenshots** — before every action so the agent knows where to click

---

## Requirements

| Component | Minimum | Notes |
|-----------|---------|-------|
| OS | Linux | Tested on Ubuntu 22.04+ / Mint / Cinnamon |
| Display | X11 | `DISPLAY=:0` must be set |
| Desktop | Any | Chrome window must be visible on screen |
| Browser | Google Chrome or Chromium | `--no-sandbox` used for reliability |
| Python | 3.10+ | `pyautogui` required |

### System Packages

```bash
sudo apt update
sudo apt install -y xdotool wmctrl scrot
# OR: sudo apt install -y xdotool wmctrl gnome-screenshot
# OR: sudo apt install -y xdotool wmctrl maim
```

> Only **one** screenshot backend needed: `scrot`, `gnome-screenshot`, or `maim`.

### Python Package

```bash
pip install pyautogui
```

---

## One-Command Install ⬇️

```bash
curl -fsSL https://raw.githubusercontent.com/mrmoe28/hermes-headed-browser/master/install.sh | bash
```

That's it. The installer will:
1. Check for required system packages (`xdotool`, `wmctrl`, `scrot`)
2. Install missing deps via `apt` (sudo prompt if needed)
3. Install `pyautogui` via pip
4. Clone the plugin to `~/.hermes/plugins/headed_browser/`
5. Create the `~/.hermes/plugins/plugins/__init__.py` namespace package
6. Verify the plugin loads correctly
7. Print a success message with next steps

**No manual steps required.**

---

## Manual Install (if you prefer)

```bash
# 1. Install system deps
sudo apt install -y xdotool wmctrl scrot

# 2. Install Python dep
pip install pyautogui

# 3. Clone plugin
git clone https://github.com/mrmoe28/hermes-headed-browser.git \
  ~/.hermes/plugins/headed_browser

# 4. Create namespace package init
touch ~/.hermes/plugins/plugins/__init__.py

# 5. Verify
python3 -c "import sys; sys.path.insert(0, '~/.hermes/plugins'); \
  from headed_browser.tools import check_headed_browser_available; \
  print('Ready:', check_headed_browser_available())"
```

---

## Available Tools

| Tool | Emoji | What it does |
|------|-------|--------------|
| `desktop_browser` | [BRW] | Launch or focus visible Chrome on `DISPLAY=:0` |
| `desktop_screenshot` | [IMG] | Capture full-screen screenshot |
| `desktop_mouse_move` | [MOV] | Move cursor to (x, y) — **2 second glide** |
| `desktop_highlight` | [HLG] | Draw attention ring at (x, y) — no click |
| `desktop_click` | [CLK] | Move to (x, y), wiggle, click |
| `desktop_type` | [TYP] | Type text with 30ms/char delay |
| `desktop_scroll` | [SCR] | Scroll wheel up/down |

---

## Demo Script

Save as `demo.py` and run:

```python
import sys
sys.path.insert(0, '~/.hermes/plugins')
from headed_browser.tools import (
    handle_desktop_browser,
    handle_desktop_mouse_move,
    handle_desktop_highlight,
    handle_desktop_click,
    handle_desktop_type,
    handle_desktop_screenshot,
)

# 1. Launch visible Chrome
handle_desktop_browser({'url': 'https://example.com'})

# 2. Take a screenshot to see current state
handle_desktop_screenshot({})

# 3. Move mouse slowly to center (2s glide)
handle_desktop_mouse_move({'x': 960, 'y': 540})

# 4. Highlight a link (attention ring)
handle_desktop_highlight({'x': 500, 'y': 300, 'duration': 1.0})

# 5. Click it
handle_desktop_click({'x': 500, 'y': 300})

# 6. Type in a field
handle_desktop_type({'text': 'Hello world!'})
```

---

## Troubleshooting

### "DISPLAY not set"
```bash
export DISPLAY=:0
echo $DISPLAY
```

### "Screenshot failed — no backend available"
Install at least one of:
```bash
sudo apt install -y scrot        # simplest
# OR: sudo apt install -y gnome-screenshot
# OR: sudo apt install -y maim
```

### Chrome won't launch
```bash
which google-chrome
# If not found, install:
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list'
sudo apt update && sudo apt install -y google-chrome-stable
```

### Plugin not detected by Hermes
Restart Hermes:
```bash
hermes gateway restart  # or restart your terminal session
```

---

## Repo

**GitHub:** `https://github.com/mrmoe28/hermes-headed-browser`

---

## License

MIT — do what you want. Built for EKO Solar Ops by @mrmoe28.
