from enum import Enum, auto

class FridayState(Enum):
    IDLE = auto()
    WAKE = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    SEARCHING = auto()
    READING = auto()
    PLANNING = auto()
    TYPING = auto()
    EXECUTING = auto()
    ERROR = auto()
    SUCCESS = auto()

STATE_META = {
    FridayState.IDLE: {
        "color": "#3A3A5C",
        "label": "Say Hey FRIDAY..."
    },
    FridayState.WAKE: {
        "color": "#00FFCC",
        "label": "Yes?"
    },
    FridayState.LISTENING: {
        "color": "#00B4FF",
        "label": "Listening..."
    },
    FridayState.THINKING: {
        "color": "#FF9F40",
        "label": "Thinking..."
    },
    FridayState.SPEAKING: {
        "color": "#A050FF",
        "label": "FRIDAY speaking"
    },
    FridayState.SEARCHING: {
        "color": "#00E5FF",
        "label": "Searching the web..."
    },
    FridayState.READING: {
        "color": "#00FF88",
        "label": "Reading page..."
    },
    FridayState.PLANNING: {
        "color": "#FFD700",
        "label": "Planning your day..."
    },
    FridayState.TYPING: {
        "color": "#E0E0E0",
        "label": "Writing..."
    },
    FridayState.EXECUTING: {
        "color": "#4CAF50",
        "label": "Executing..."
    },
    FridayState.ERROR: {
        "color": "#FF3B30",
        "label": "Error"
    },
    FridayState.SUCCESS: {
        "color": "#34C759",
        "label": "Success"
    }
}
