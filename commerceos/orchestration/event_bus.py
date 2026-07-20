"""In-process event bus — pub/sub for agent collaboration."""
from typing import Callable
from collections import defaultdict
import logging


class EventBus:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event_type: str, handler: Callable | None = None) -> Callable | None:
        if handler is not None:
            self._listeners[event_type].append(handler)
            return None
        # Decorator mode: return a wrapper that registers the decorated function
        def decorator(fn: Callable) -> Callable:
            self._listeners[event_type].append(fn)
            return fn
        return decorator

    def emit(self, event_type: str, data: dict | None = None) -> None:
        data = data or {}
        for handler in self._listeners.get(event_type, []):
            try:
                handler(data)
            except Exception as e:
                logging.error(f"Event handler error for {event_type}: {e}")

    def remove(self, event_type: str, handler: Callable) -> None:
        self._listeners[event_type] = [h for h in self._listeners[event_type] if h != handler]

    def clear(self) -> None:
        self._listeners.clear()


event_bus = EventBus()
