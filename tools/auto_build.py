import re
import logging
from pathlib import Path
from duckduckgo_search import DDGS
from langchain.tools import tool
from langchain_ollama import ChatOllama

TOOLS_DIR = Path(__file__).parent
MODEL = "qwen3:8b"

CODE_PROMPT = """\
You are writing a Python function body for a local AI assistant tool.

Task to implement: {task}

Relevant search results about APIs and approaches:
{search_context}

Write ONLY the raw Python function body lines. No def line, no decorator, no explanation.

Rules:
- The function takes `query: str` as input and MUST return a str
- Use the `requests` library for any HTTP calls (already imported at module level)
- Return a clean, readable string the user can hear spoken aloud
- Wrap all logic in try/except and return an error string on failure
- No browser, no GUI, no subprocess — HTTP requests only
- Indent every line with exactly 4 spaces

Output ONLY the function body. Nothing else."""


@tool("auto_build_tool")
def auto_build_tool(task: str) -> str:
    """
    Use this when no existing tool can handle what the user asked for.
    Searches online for a free Python API approach, generates working code,
    saves it as a new tool, and hot-reloads it so it is immediately available.
    After this tool returns, the new tool is active — call it to complete the task.
    Input: a short description of the capability needed.
    """
    logging.info(f"auto_build_tool: researching '{task}'")

    # Step 1: Search for implementation approach
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                f"python free API {task} requests example no auth key",
                max_results=3,
            ))
    except Exception as e:
        return f"Search failed: {e}"

    if not results:
        return "Could not find online guidance for this task."

    search_context = "\n\n".join([
        f"Title: {r['title']}\nURL: {r['href']}\nSummary: {r.get('body', 'N/A')}"
        for r in results
    ])

    # Step 2: Ask LLM to generate code body from search results
    try:
        llm = ChatOllama(model=MODEL, reasoning=False)
        response = llm.invoke(CODE_PROMPT.format(task=task, search_context=search_context))
        code_body = response.content.strip()
    except Exception as e:
        return f"Code generation failed: {e}"

    # Strip markdown fences if present
    if "```" in code_body:
        code_body = re.sub(r"```(?:python)?\n?", "", code_body).strip()

    # Step 3: Safety check
    from tools.self_modify import BLOCKED_PATTERNS, TOOL_TEMPLATE
    for pattern in BLOCKED_PATTERNS:
        if pattern in code_body:
            return f"Generated code blocked — contains disallowed pattern '{pattern}'."

    # Step 4: Build file
    func_name = re.sub(r"[^\w]", "_", task.lower()[:30].strip())
    func_name = re.sub(r"_+", "_", func_name).strip("_")

    indented_lines = [
        ("        " + line) if line.strip() else ""
        for line in code_body.strip().splitlines()
    ]
    indented_body = "\n".join(indented_lines)

    if not indented_body.strip():
        return "Code generation returned empty output."

    content = TOOL_TEMPLATE.format(
        name=func_name,
        func_name=func_name,
        description=f"Auto-built tool for: {task}",
        indented_body=indented_body,
    )

    output_path = TOOLS_DIR / f"{func_name}.py"
    try:
        output_path.write_text(content, encoding="utf-8")
        logging.info(f"auto_build_tool: saved {output_path.name}")
    except Exception as e:
        return f"Failed to save tool file: {e}"

    # Step 5: Hot-reload — triggers rebuild_agent in main.py
    try:
        from friday.tool_manager import reload_tools
        reload_tools()
    except Exception as e:
        return f"Tool saved but reload failed: {e}"

    return f"Built and loaded '{func_name}'. Tool is active."
