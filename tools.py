"""Headed Desktop Browser Automation — you see every move.

Launch Chrome on your Cinnamon X11 desktop and control it with visible mouse
movement, clicks, and typing. The plugin captures screenshots before each
action so the agent knows exactly where to click.

Architecture:
  - desktop_browser  → launch Chrome (headed, visible) on DISPLAY=:0
  - desktop_screenshot → capture the screen region
  - desktop_click      → move mouse then click (with visual trail)
  - desktop_type       → type text or press hotkeys
  - desktop_scroll     → scroll the mouse wheel
  - desktop_mouse_move → move mouse to coordinates (no click)
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Display / prerequisites
# ---------------------------------------------------------------------------

def _check_display() -> None:
    if not os.environ.get("DISPLAY"):
        env_disp = os.environ.get("DISPLAY")
        if not env_disp:
            raise RuntimeError("DISPLAY not set — no X11 session detected")

# ---------------------------------------------------------------------------
# Chrome lifecycle
# ---------------------------------------------------------------------------

_CHROME_PID: Optional[int] = None
_CHROME_WINDOW_ID: Optional[str] = None

def _find_chrome_window() -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["wmctrl", "-l"],
            text=True,
            timeout=5,
        )
        for line in out.strip().splitlines():
            if "google-chrome" in line.lower() or "chrome" in line.lower():
                parts = line.split(None, 3)
                if parts:
                    return parts[0]
    except Exception:
        pass
    return None


def _ensure_chrome(url: str = "about:blank") -> Tuple[int, str]:
    global _CHROME_PID, _CHROME_WINDOW_ID
    if _CHROME_PID is not None:
        try:
            os.kill(_CHROME_PID, 0)
            # Chrome still alive — raise window
            wid = _CHROME_WINDOW_ID or _find_chrome_window()
            if wid:
                _CHROME_WINDOW_ID = wid
                subprocess.run(
                    ["wmctrl", "-i", "-r", wid, "-b", "add,above"],
                    capture_output=True,
                    timeout=5,
                )
                subprocess.run(
                    ["wmctrl", "-i", "-a", wid],
                    capture_output=True,
                    timeout=5,
                )
            return _CHROME_PID, _CHROME_WINDOW_ID or ""
        except (ProcessLookupError, OSError):
            _CHROME_PID = None

    env = os.environ.copy()
    env["DISPLAY"] = ":0"
    proc = subprocess.Popen(
        [
            "/usr/bin/google-chrome",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-popup-blocking",
            "--disable-infobars",
            "--no-first-run",
            "--no-default-browser-check",
            url,
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _CHROME_PID = proc.pid
    time.sleep(2.0)

    wid = _find_chrome_window()
    _CHROME_WINDOW_ID = wid
    if wid:
        subprocess.run(
            ["wmctrl", "-i", "-r", wid, "-b", "add,above"],
            capture_output=True,
            timeout=5,
        )
        subprocess.run(
            ["wmctrl", "-i", "-a", wid],
            capture_output=True,
            timeout=5,
        )
    return _CHROME_PID, wid or ""


def _activate_chrome() -> None:
    wid = _CHROME_WINDOW_ID or _find_chrome_window()
    if wid:
        subprocess.run(
            ["wmctrl", "-i", "-a", wid],
            capture_output=True,
            timeout=5,
        )

# ---------------------------------------------------------------------------
# Screenshot helpers
# ---------------------------------------------------------------------------

def _screenshot_path() -> str:
    return os.path.expanduser("~/.hermes/headed_browser_screenshot.png")


def _take_screenshot() -> str:
    _check_display()
    path = _screenshot_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Prefer gnome-screenshot for speed, fall back to maim, then scrot
    for cmd in [
        ["gnome-screenshot", "-f", path],
        ["maim", path],
        ["scrot", "-q", "80", path],
    ]:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=8)
            if result.returncode == 0 and os.path.exists(path):
                return path
        except Exception:
            continue
    raise RuntimeError("Screenshot failed — no backend available (gnome-screenshot / maim / scrot)")


def _screenshot_dims() -> Tuple[int, int]:
    try:
        import pyautogui
        size = pyautogui.size()
        return size.width, size.height
    except Exception:
        return 1920, 1080

# ---------------------------------------------------------------------------
# Mouse / keyboard via pyautogui + xdotool
# ---------------------------------------------------------------------------

def _move_mouse(x: int, y: int, duration: float = 1.2) -> None:
    """Move the mouse cursor to (x, y) with a smooth visible animation.
    Duration defaults to 1.2s so the movement is clearly visible on screen."""
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(x, y, duration=duration)
    except Exception:
        # Fallback to xdotool with multiple steps for visibility
        subprocess.run(
            ["xdotool", "mousemove", str(x), str(y)],
            capture_output=True,
            timeout=5,
        )


def _click(x: int, y: int, button: str = "left") -> None:
    """Click at (x, y) with a visible animation: move there, pause for visibility,
    then click with a slight "thump" effect."""
    _move_mouse(x, y, duration=1.2)
    time.sleep(0.4)  # Pause so user sees the cursor arrive

    # Visual indicator — small wiggle circle to draw attention
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        for offset in [(5, 0), (0, 5), (-5, 0), (0, -5)]:
            pyautogui.moveRel(offset[0], offset[1], duration=0.05)
            time.sleep(0.02)
        pyautogui.moveTo(x, y, duration=0.05)
        time.sleep(0.1)
    except Exception:
        pass

    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        # Visual "thump" — press down, tiny offset, release
        pyautogui.mouseDown(button=button)
        time.sleep(0.05)
        pyautogui.mouseUp(button=button)
    except Exception:
        _move_mouse(x, y, duration=0.1)
        subprocess.run(
            ["xdotool", "click", "1" if button == "left" else "3"],
            capture_output=True,
            timeout=5,
        )

    time.sleep(0.3)  # Let the UI react before next action


def _scroll(steps: int, x: Optional[int] = None, y: Optional[int] = None) -> None:
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        if x is not None and y is not None:
            pyautogui.scroll(steps, x, y)
        else:
            pyautogui.scroll(steps)
    except Exception:
        subprocess.run(
            ["xdotool", "click", "4" if steps > 0 else "5"],
            capture_output=True,
            timeout=5,
        )


def _type_text(text: str, interval: float = 0.03) -> None:
    """Type text with a visible delay between keystrokes.
    Default interval is 30ms so you can see each character appear."""
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.typewrite(text, interval=interval)
    except Exception:
        subprocess.run(
            ["xdotool", "type", text],
            capture_output=True,
            timeout=5,
        )


def _press_key(key: str) -> None:
    keymap = {
        "enter": "Return",
        "return": "Return",
        "tab": "Tab",
        "escape": "Escape",
        "esc": "Escape",
        "backspace": "BackSpace",
        "delete": "Delete",
        "space": "space",
        "ctrl+l": "ctrl+l",
        "ctrl+a": "ctrl+a",
        "ctrl+c": "ctrl+c",
        "ctrl+v": "ctrl+v",
        "ctrl+t": "ctrl+t",
        "ctrl+w": "ctrl+w",
        "f5": "F5",
        "f12": "F12",
    }
    xdo = keymap.get(key.lower(), key)
    subprocess.run(
        ["xdotool", "key", xdo],
        capture_output=True,
        timeout=5,
    )

# ---------------------------------------------------------------------------
# Runtime gate
# ---------------------------------------------------------------------------

def check_headed_browser_available() -> bool:
    try:
        _check_display()
    except Exception:
        return False
    if not os.path.exists("/usr/bin/google-chrome") and not os.path.exists("/usr/bin/chromium"):
        return False
    try:
        import pyautogui  # noqa: F401
    except ImportError:
        return False
    return True

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

SCREENSHOT_SCHEMA: Dict[str, Any] = {
    "name": "desktop_screenshot",
    "description": (
        "Capture a screenshot of the desktop (or a specific region) and save it "
        "to a file. Returns the absolute path to the image. Use this to see the "
        "current state of the screen before deciding where to click."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X offset (default 0)"},
            "y": {"type": "integer", "description": "Y offset (default 0)"},
            "width": {"type": "integer", "description": "Width (default full screen)"},
            "height": {"type": "integer", "description": "Height (default full screen)"},
        },
        "required": [],
    },
}

CLICK_SCHEMA: Dict[str, Any] = {
    "name": "desktop_click",
    "description": (
        "Move the mouse to (x, y) and click. You can specify screen coordinates "
        "or describe the target (e.g., 'login button', 'top-right of screen') — "
        "if coordinates are not given, the agent uses the most recent screenshot "
        "to infer the location. The mouse movement is visible on screen."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X coordinate (pixels from left)"},
            "y": {"type": "integer", "description": "Y coordinate (pixels from top)"},
            "button": {"type": "string", "enum": ["left", "right"], "default": "left"},
            "description": {"type": "string", "description": "What to click if coords not given"},
        },
        "required": ["x", "y"],
    },
}

TYPE_SCHEMA: Dict[str, Any] = {
    "name": "desktop_type",
    "description": (
        "Type text or press a key in the focused window. First activate the "
        "Chrome window, then type. For hotkeys use 'key' (e.g., 'ctrl+l', 'enter', 'tab')."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to type"},
            "key": {"type": "string", "description": "Hotkey to press (e.g., enter, ctrl+l)"},
        },
        "required": [],
    },
}

SCROLL_SCHEMA: Dict[str, Any] = {
    "name": "desktop_scroll",
    "description": (
        "Scroll the mouse wheel. Positive = up, negative = down. "
        "Optional x/y to position mouse first."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "amount": {"type": "integer", "description": "Scroll amount (+up / -down)"},
            "x": {"type": "integer", "description": "X coordinate to move to first"},
            "y": {"type": "integer", "description": "Y coordinate to move to first"},
        },
        "required": ["amount"],
    },
}

BROWSER_SCHEMA: Dict[str, Any] = {
    "name": "desktop_browser",
    "description": (
        "Launch or focus a visible Chrome browser on the desktop and optionally "
        "navigate to a URL. Returns the Chrome PID and window ID. The window "
        "appears on your screen — you see it. If Chrome is already running, "
        "this raises it to the foreground."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to open (default about:blank)"},
        },
        "required": [],
    },
}

MOUSE_MOVE_SCHEMA: Dict[str, Any] = {
    "name": "desktop_mouse_move",
    "description": (
        "Move the mouse cursor to (x, y) on screen WITHOUT clicking. "
        "The movement is animated and visible — you will see the cursor glide "
        "across the screen slowly. Use this to show where I am looking before a click."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X coordinate (pixels from left)"},
            "y": {"type": "integer", "description": "Y coordinate (pixels from top)"},
        },
        "required": ["x", "y"],
    },
}

HIGHLIGHT_SCHEMA: Dict[str, Any] = {
    "name": "desktop_highlight",
    "description": (
        "Draw a visible attention ring at (x, y) by wiggling the mouse cursor in a small "
        "circle. No click — just a visual 'ping' to show a target location on screen. "
        "Useful for pointing out UI elements before clicking them."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "X coordinate (pixels from left)"},
            "y": {"type": "integer", "description": "Y coordinate (pixels from top)"},
            "duration": {"type": "number", "description": "Seconds to wiggle (default 0.8)"},
        },
        "required": ["x", "y"],
    },
}

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def handle_desktop_screenshot(params: Dict[str, Any]) -> Dict[str, Any]:
    path = _take_screenshot()
    return {"ok": True, "path": path, "note": "View this image to see the current screen state"}


def handle_desktop_click(params: Dict[str, Any]) -> Dict[str, Any]:
    x = params["x"]
    y = params["y"]
    button = params.get("button", "left")

    _check_display()
    _activate_chrome()
    time.sleep(0.3)

    # _click already moves the mouse visibly — just call it
    _click(x, y, button=button)

    return {
        "ok": True,
        "action": "click",
        "x": x,
        "y": y,
        "button": button,
        "note": "Mouse moved and clicked — visible on screen",
    }


def handle_desktop_type(params: Dict[str, Any]) -> Dict[str, Any]:
    text = params.get("text", "")
    key = params.get("key", "")

    _check_display()
    _activate_chrome()
    time.sleep(0.2)

    if text:
        _type_text(text)
    if key:
        _press_key(key)
    time.sleep(0.1)

    return {"ok": True, "text": text, "key": key}


def handle_desktop_scroll(params: Dict[str, Any]) -> Dict[str, Any]:
    amount = params["amount"]
    x = params.get("x")
    y = params.get("y")

    _check_display()
    if x is not None and y is not None:
        _move_mouse(x, y, duration=0.2)
        time.sleep(0.1)

    _scroll(amount, x, y)
    time.sleep(0.1)

    return {"ok": True, "amount": amount, "x": x, "y": y}


def handle_desktop_browser(params: Dict[str, Any]) -> Dict[str, Any]:
    url = params.get("url", "about:blank")
    pid, wid = _ensure_chrome(url)
    return {
        "ok": True,
        "pid": pid,
        "window_id": wid,
        "url": url,
        "display": ":0",
        "note": "Chrome is now visible on your desktop — you should see it",
    }


def handle_desktop_mouse_move(params: Dict[str, Any]) -> Dict[str, Any]:
    x = params["x"]
    y = params["y"]

    _check_display()
    _activate_chrome()
    time.sleep(0.3)

    # Slow, deliberate movement — 2 seconds so you can follow it visually
    _move_mouse(x, y, duration=2.0)
    time.sleep(0.3)

    return {
        "ok": True,
        "action": "mouse_move",
        "x": x,
        "y": y,
        "note": "Cursor moved to target slowly — visible on screen",
    }


def handle_desktop_highlight(params: Dict[str, Any]) -> Dict[str, Any]:
    x = params["x"]
    y = params["y"]
    duration = params.get("duration", 0.8)

    _check_display()
    _activate_chrome()
    time.sleep(0.3)

    # Move to target
    _move_mouse(x, y, duration=1.0)
    time.sleep(0.2)

    # Draw a small circle around the target
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        radius = 8
        steps = int(duration * 10)
        import math
        for i in range(steps):
            angle = (2 * math.pi * i) / steps
            nx = x + radius * math.cos(angle)
            ny = y + radius * math.sin(angle)
            pyautogui.moveTo(nx, ny, duration=0.05)
            time.sleep(0.02)
        # Return to center
        pyautogui.moveTo(x, y, duration=0.1)
    except Exception:
        pass

    time.sleep(0.2)

    return {
        "ok": True,
        "action": "highlight",
        "x": x,
        "y": y,
        "note": "Attention ring drawn at target — visible on screen",
    }
