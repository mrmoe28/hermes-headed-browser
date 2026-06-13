#!/usr/bin/env bash
# Hermes Headed Browser Plugin — One-Command Installer
# https://github.com/mrmoe28/hermes-headed-browser
#
# Usage: curl -fsSL .../install.sh | bash

set -euo pipefail

REPO_URL="https://github.com/mrmoe28/hermes-headed-browser.git"
PLUGIN_DIR="$HOME/.hermes/plugins/headed_browser"
PLUGINS_DIR="$HOME/.hermes/plugins/plugins"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ──────────────────────────────────────────────────────────────
# 1. Check for Linux + X11
# ──────────────────────────────────────────────────────────────
log_info "Checking environment..."

if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    log_error "This plugin requires Linux. Detected: $OSTYPE"
    exit 1
fi

if [[ -z "${DISPLAY:-}" ]]; then
    log_warn "DISPLAY not set. Trying :0..."
    export DISPLAY=:0
fi

if ! xset q &>/dev/null; then
    log_warn "No X11 session detected on $DISPLAY. Plugin will not work without a GUI."
fi

# ──────────────────────────────────────────────────────────────
# 2. Install system packages
# ──────────────────────────────────────────────────────────────
log_info "Checking system dependencies..."

NEEDS_APT=false
for pkg in xdotool wmctrl; do
    if ! command -v "$pkg" &>/dev/null; then
        NEEDS_APT=true
        break
    fi
done

# Check for at least one screenshot backend
HAS_SCREENSHOT=false
for cmd in scrot gnome-screenshot maim; do
    if command -v "$cmd" &>/dev/null; then
        HAS_SCREENSHOT=true
        log_info "Screenshot backend found: $cmd"
        break
    fi
done

if [[ "$NEEDS_APT" == true || "$HAS_SCREENSHOT" == false ]]; then
    if command -v apt-get &>/dev/null; then
        log_info "Installing missing packages via apt..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq xdotool wmctrl scrot || {
            log_warn "scrot failed, trying gnome-screenshot..."
            sudo apt-get install -y -qq gnome-screenshot || {
                log_warn "gnome-screenshot failed, trying maim..."
                sudo apt-get install -y -qq maim
            }
        }
    else
        log_error "apt-get not found. Please install manually: xdotool, wmctrl, scrot (or gnome-screenshot, or maim)"
        exit 1
    fi
else
    log_info "System packages already installed"
fi

# ──────────────────────────────────────────────────────────────
# 3. Install Python dependency
# ──────────────────────────────────────────────────────────────
log_info "Checking Python dependencies..."

if ! python3 -c "import pyautogui" 2>/dev/null; then
    log_info "Installing pyautogui..."
    pip3 install --user pyautogui || pip install --user pyautogui || {
        log_error "Failed to install pyautogui. Try: pip3 install pyautogui"
        exit 1
    }
else
    log_info "pyautogui already installed"
fi

# ──────────────────────────────────────────────────────────────
# 4. Install Chrome if missing
# ──────────────────────────────────────────────────────────────
if ! command -v google-chrome &>/dev/null && ! command -v chromium-browser &>/dev/null && ! command -v chromium &>/dev/null; then
    log_info "Chrome/Chromium not found. Installing Google Chrome..."
    if command -v apt-get &>/dev/null; then
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add - 2>/dev/null || true
        sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list' 2>/dev/null || true
        sudo apt-get update -qq
        sudo apt-get install -y -qq google-chrome-stable || {
            log_warn "Google Chrome install failed. Trying Chromium..."
            sudo apt-get install -y -qq chromium-browser || sudo apt-get install -y -qq chromium
        }
    else
        log_warn "Chrome not found and apt not available. Please install Chrome manually."
    fi
else
    log_info "Chrome/Chromium already installed"
fi

# ──────────────────────────────────────────────────────────────
# 5. Clone plugin
# ──────────────────────────────────────────────────────────────
log_info "Installing plugin to $PLUGIN_DIR..."

if [[ -d "$PLUGIN_DIR" ]]; then
    log_warn "Plugin directory already exists. Updating..."
    cd "$PLUGIN_DIR"
    git fetch origin
    git reset --hard origin/master || git reset --hard origin/main || true
else
    mkdir -p "$HOME/.hermes/plugins"
    git clone --depth 1 "$REPO_URL" "$PLUGIN_DIR"
fi

# ──────────────────────────────────────────────────────────────
# 6. Create namespace package init
# ──────────────────────────────────────────────────────────────
mkdir -p "$PLUGINS_DIR"
if [[ ! -f "$PLUGINS_DIR/__init__.py" ]]; then
    log_info "Creating namespace package init..."
    touch "$PLUGINS_DIR/__init__.py"
fi

# ──────────────────────────────────────────────────────────────
# 7. Verify plugin loads
# ──────────────────────────────────────────────────────────────
log_info "Verifying plugin..."

if python3 -c "import sys; sys.path.insert(0, '$HOME/.hermes/plugins'); \
    from headed_browser.tools import check_headed_browser_available; \
    print('ready' if check_headed_browser_available() else 'missing-deps')" 2>/dev/null | grep -q "ready"; then
    log_info "Plugin installed and ready!"
else
    log_warn "Plugin installed but some prerequisites may be missing."
    log_warn "Make sure you're running in a graphical session (X11)."
fi

# ──────────────────────────────────────────────────────────────
# 8. Done
# ──────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Hermes Headed Browser Plugin Installed!  ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Location: $PLUGIN_DIR"
echo ""
echo "Available tools:"
echo "  [BRW] desktop_browser     — Launch visible Chrome"
echo "  [IMG] desktop_screenshot  — Capture screen"
echo "  [MOV] desktop_mouse_move  — Slow cursor glide (2s)"
echo "  [HLG] desktop_highlight   — Attention ring (no click)"
echo "  [CLK] desktop_click       — Move, wiggle, click"
echo "  [TYP] desktop_type        — Type with 30ms/char"
echo "  [SCR] desktop_scroll      — Scroll wheel"
echo ""
echo "Restart Hermes to register the plugin."
echo "Demo: ~/.hermes/plugins/headed_browser/demo.py"
echo ""
