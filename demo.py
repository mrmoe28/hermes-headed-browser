#!/usr/bin/env python3
"""
Hermes Headed Browser Plugin — Demo Script
Shows the slow, visible mouse movements and attention-ring highlights.
Run this after installing the plugin to see it in action.
"""

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

print("=" * 50)
print("Hermes Headed Browser — Live Demo")
print("=" * 50)
print()

# 1. Launch Chrome
print("[1/6] Launching visible Chrome browser...")
result = handle_desktop_browser({'url': 'https://example.com'})
print(f"   Chrome PID: {result['pid']}, Window: {result['window_id']}")
print(f"   You should SEE the Chrome window appear on your screen now.")
input("   Press Enter when you see Chrome...")
print()

# 2. Screenshot
print("[2/6] Taking a screenshot of the screen...")
result = handle_desktop_screenshot({})
print(f"   Screenshot saved to: {result['path']}")
print()

# 3. Slow mouse move
print("[3/6] Moving mouse to center of screen (2 second glide)...")
print("   WATCH your screen — the cursor will slowly glide to the center.")
handle_desktop_mouse_move({'x': 960, 'y': 540})
print("   Done — cursor should now be at the center.")
print()

# 4. Highlight
print("[4/6] Drawing an attention ring at position (500, 300)...")
print("   WATCH — the cursor will circle around the target without clicking.")
handle_desktop_highlight({'x': 500, 'y': 300, 'duration': 1.0})
print("   Done — attention ring drawn.")
print()

# 5. Click
print("[5/6] Clicking at position (500, 300)...")
print("   WATCH — cursor will glide, wiggle, then click.")
handle_desktop_click({'x': 500, 'y': 300})
print("   Click complete.")
print()

# 6. Type
print("[6/6] Typing 'Hello from Hermes!' (30ms per character)...")
print("   WATCH — you'll see each character appear one by one.")
handle_desktop_type({'text': 'Hello from Hermes!'})
print("   Typing complete.")
print()

print("=" * 50)
print("Demo finished! The plugin is working.")
print("=" * 50)
print()
print("Next steps:")
print("  - Use 'desktop_browser' to launch Chrome from your agent")
print("  - Use 'desktop_screenshot' before deciding where to click")
print("  - Use 'desktop_highlight' to point at things without clicking")
print("  - Use 'desktop_click' with visible mouse movement")
print("  - Use 'desktop_type' for slow, visible text entry")
print()
print("For more info: ~/.hermes/plugins/headed_browser/README.md")
