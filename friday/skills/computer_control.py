from __future__ import annotations

import time
import webbrowser
from typing import Optional

import pyautogui
from langchain.tools import tool
from pydantic import BaseModel, Field

from friday.core.command_executor import URL_MAP, open_application

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class ComputerControlInput(BaseModel):
    action: str = Field(
        description=(
            "Action to perform. Supported values: "
            "'open', 'type', 'press', 'hotkey', 'move_mouse', 'drag_mouse', "
            "'click', 'scroll', 'wait', 'screen_size', 'mouse_position'."
        )
    )
    text: str = Field(
        default="",
        description="Text to type, or comma-separated keys for the hotkey action.",
    )
    app_or_url: str = Field(
        default="",
        description="Application name or website URL for the open action.",
    )
    key: str = Field(
        default="",
        description="Single key name for the press action, for example 'enter' or 'tab'.",
    )
    x: Optional[int] = Field(
        default=None,
        description="Screen X coordinate for mouse actions.",
    )
    y: Optional[int] = Field(
        default=None,
        description="Screen Y coordinate for mouse actions.",
    )
    button: str = Field(
        default="left",
        description="Mouse button to use for click or drag actions: left, right, or middle.",
    )
    clicks: int = Field(
        default=1,
        description="Number of clicks to perform for the click action.",
    )
    scroll_amount: int = Field(
        default=0,
        description="Positive to scroll up, negative to scroll down.",
    )
    seconds: float = Field(
        default=0.0,
        description="How long to wait for the wait action.",
    )
    duration: float = Field(
        default=0.2,
        description="Mouse movement duration in seconds.",
    )
    presses: int = Field(
        default=1,
        description="How many times to press the key for the press action.",
    )
    interval: float = Field(
        default=0.02,
        description="Delay between typed characters or repeated key presses.",
    )


def _normalize_button(button: str) -> str:
    normalized = (button or "left").strip().lower()
    if normalized not in {"left", "right", "middle"}:
        raise ValueError("Mouse button must be left, right, or middle.")
    return normalized


def _require_coordinates(x: Optional[int], y: Optional[int]) -> tuple[int, int]:
    if x is None or y is None:
        raise ValueError("Both x and y coordinates are required for this action.")
    return x, y


def _open_target(app_or_url: str) -> str:
    clean_input = app_or_url.strip()
    if not clean_input:
        return "Open action requires an application name or URL."

    lowered_input = clean_input.lower()
    if lowered_input in URL_MAP:
        url = URL_MAP[lowered_input]
        webbrowser.open(url)
        return f"Opened {url}."

    if (
        lowered_input.startswith("http://")
        or lowered_input.startswith("https://")
        or "www." in lowered_input
        or lowered_input.endswith(".com")
        or lowered_input.endswith(".org")
        or lowered_input.endswith(".net")
    ):
        url = clean_input if "://" in clean_input else f"https://{clean_input}"
        webbrowser.open(url)
        return f"Opened {url}."

    if open_application(clean_input):
        return f"Opened {clean_input}."

    return f"Could not open {clean_input}."


@tool("computer_control", args_schema=ComputerControlInput)
def computer_control(
    action: str,
    text: str = "",
    app_or_url: str = "",
    key: str = "",
    x: Optional[int] = None,
    y: Optional[int] = None,
    button: str = "left",
    clicks: int = 1,
    scroll_amount: int = 0,
    seconds: float = 0.0,
    duration: float = 0.2,
    presses: int = 1,
    interval: float = 0.02,
) -> str:
    """
    Controls the local computer for basic GUI tasks.
    Use this for keyboard and mouse actions such as opening an app or page,
    typing text, pressing keys, using shortcuts, moving or clicking the mouse,
    scrolling, waiting for UI changes, or reading simple screen state.
    Use existing screenshot, OCR, clipboard, and file tools for those specific jobs.
    """
    try:
        normalized_action = action.strip().lower()

        if normalized_action == "open":
            return _open_target(app_or_url)

        if normalized_action == "type":
            if not text:
                return "Type action requires text."
            pyautogui.write(text, interval=max(interval, 0.0))
            return "Typed the requested text."

        if normalized_action == "press":
            normalized_key = key.strip().lower()
            if not normalized_key:
                return "Press action requires a key."
            pyautogui.press(normalized_key, presses=max(presses, 1), interval=max(interval, 0.0))
            return f"Pressed {normalized_key}."

        if normalized_action == "hotkey":
            keys = [item.strip().lower() for item in text.split(",") if item.strip()]
            if not keys:
                return "Hotkey action requires comma-separated keys in the text field."
            pyautogui.hotkey(*keys)
            return f"Sent hotkey {' + '.join(keys)}."

        if normalized_action == "move_mouse":
            target_x, target_y = _require_coordinates(x, y)
            pyautogui.moveTo(target_x, target_y, duration=max(duration, 0.0))
            return f"Moved mouse to {target_x}, {target_y}."

        if normalized_action == "drag_mouse":
            target_x, target_y = _require_coordinates(x, y)
            normalized_button = _normalize_button(button)
            pyautogui.dragTo(target_x, target_y, duration=max(duration, 0.0), button=normalized_button)
            return f"Dragged mouse to {target_x}, {target_y}."

        if normalized_action == "click":
            normalized_button = _normalize_button(button)
            if x is not None and y is not None:
                pyautogui.click(x=x, y=y, clicks=max(clicks, 1), button=normalized_button)
                return f"Clicked at {x}, {y}."
            pyautogui.click(clicks=max(clicks, 1), button=normalized_button)
            return "Clicked at the current mouse position."

        if normalized_action == "scroll":
            if scroll_amount == 0:
                return "Scroll action requires a non-zero scroll_amount."
            pyautogui.scroll(scroll_amount)
            direction = "up" if scroll_amount > 0 else "down"
            return f"Scrolled {direction}."

        if normalized_action == "wait":
            wait_seconds = max(seconds, 0.0)
            time.sleep(wait_seconds)
            return f"Waited {wait_seconds:.1f} seconds."

        if normalized_action == "screen_size":
            width, height = pyautogui.size()
            return f"Screen size is {width} by {height}."

        if normalized_action == "mouse_position":
            position = pyautogui.position()
            return f"Mouse is at {position.x}, {position.y}."

        return (
            "Unknown action. Supported actions are open, type, press, hotkey, "
            "move_mouse, drag_mouse, click, scroll, wait, screen_size, and mouse_position."
        )
    except Exception as error:
        return f"Computer control failed: {error}"
