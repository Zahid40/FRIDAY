import importlib.util
import inspect
import sys
import logging
from pathlib import Path
from langchain_core.tools import BaseTool

TOOLS_DIR = Path(__file__).parent.parent / "tools"

_active_tools: list[BaseTool] = []
_reload_callback = None


def register_reload_callback(fn):
    global _reload_callback
    _reload_callback = fn


def _load_module(file: Path):
    module_name = f"tools.{file.stem}"
    if module_name in sys.modules:
        del sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _discover_tools(mod) -> list[BaseTool]:
    tools = []
    if hasattr(mod, "get_tool") and callable(mod.get_tool):
        tools.append(mod.get_tool())
    else:
        for _, obj in inspect.getmembers(mod):
            if isinstance(obj, BaseTool):
                tools.append(obj)
    return tools


def load_all_tools() -> list[BaseTool]:
    global _active_tools
    _active_tools = []
    for file in sorted(TOOLS_DIR.glob("*.py")):
        if file.name.startswith("_"):
            continue
        try:
            mod = _load_module(file)
            found = _discover_tools(mod)
            _active_tools.extend(found)
            logging.info(f"Loaded {len(found)} tool(s) from {file.name}")
        except Exception as e:
            logging.error(f"Failed to load {file.name}: {e}")
    logging.info(f"Total tools loaded: {len(_active_tools)}")
    return list(_active_tools)


def reload_tools() -> list[BaseTool]:
    tools = load_all_tools()
    if _reload_callback:
        _reload_callback(tools)
    return tools


def get_active_tools() -> list[BaseTool]:
    return list(_active_tools)
