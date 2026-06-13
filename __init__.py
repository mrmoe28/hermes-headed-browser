"""Headed Desktop Browser Automation Plugin — you see every move.

Registers 6 tools that launch/control a visible Chrome window on the user's
Cinnamon X11 desktop via pyautogui + xdotool.
"""

from __future__ import annotations

from .tools import (
    BROWSER_SCHEMA,
    CLICK_SCHEMA,
    HIGHLIGHT_SCHEMA,
    MOUSE_MOVE_SCHEMA,
    SCROLL_SCHEMA,
    SCREENSHOT_SCHEMA,
    TYPE_SCHEMA,
    check_headed_browser_available,
    handle_desktop_browser,
    handle_desktop_click,
    handle_desktop_highlight,
    handle_desktop_mouse_move,
    handle_desktop_scroll,
    handle_desktop_screenshot,
    handle_desktop_type,
)

_TOOLS = (
    ("desktop_screenshot",  SCREENSHOT_SCHEMA,   handle_desktop_screenshot,  "[IMG]"),
    ("desktop_click",       CLICK_SCHEMA,        handle_desktop_click,       "[CLK]"),
    ("desktop_type",        TYPE_SCHEMA,         handle_desktop_type,        "[TYP]"),
    ("desktop_scroll",      SCROLL_SCHEMA,       handle_desktop_scroll,      "[SCR]"),
    ("desktop_browser",     BROWSER_SCHEMA,      handle_desktop_browser,     "[BRW]"),
    ("desktop_mouse_move",  MOUSE_MOVE_SCHEMA,   handle_desktop_mouse_move,  "[MOV]"),
    ("desktop_highlight",   HIGHLIGHT_SCHEMA,    handle_desktop_highlight,   "[HLG]"),
)


def register(ctx) -> None:
    """Register all headed-browser tools."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="desktop_browser",
            schema=schema,
            handler=handler,
            check_fn=check_headed_browser_available,
            emoji=emoji,
        )
