from langchain.tools import tool
from pydantic import BaseModel, Field
from friday.memory.long_term_memory import (
    add_user_fact,
    search_user_facts,
    add_repair_note,
    search_repair_notes,
)

@tool("remember_user_fact")
def remember_user_fact(fact: str) -> str:
    """
    Saves a persistent fact about the user (e.g. name, preferences, studio details).
    Use this tool whenever the user tells you personal details, schedules, or rules to remember.
    Input: the fact statement to remember.
    """
    return add_user_fact(fact)

@tool("recall_user_facts")
def recall_user_facts(query: str) -> str:
    """
    Retrieves saved facts about the user matching a search query.
    Use this tool when the user asks questions about their settings, preferences, or what you know about them.
    Input: search query or keywords to match.
    """
    matched = search_user_facts(query)
    if not matched:
        return f"No facts found matching: {query}"
    return "I remember these facts:\n- " + "\n- ".join(matched)

class RepairNoteInput(BaseModel):
    problem: str = Field(description="Short description of the failure, bug, or stuck state.")
    fix: str = Field(description="Short explanation of what solved it.")
    context: str = Field(default="", description="Optional extra context such as tool name or workflow.")

@tool("remember_repair_note", args_schema=RepairNoteInput)
def remember_repair_note(problem: str, fix: str, context: str = "") -> str:
    """
    Saves a persistent repair note describing a failure pattern and the fix that worked.
    Use this after solving a bug, recovering from a stuck state, or discovering a reliable workaround.
    """
    return add_repair_note(problem, fix, context)

@tool("recall_repair_notes")
def recall_repair_notes(query: str) -> str:
    """
    Retrieves saved repair notes that may help recover from a failure or stuck state.
    Use this before retrying a task that seems familiar or after a tool fails unexpectedly.
    """
    matched = search_repair_notes(query)
    if not matched:
        return f"No repair notes found matching: {query}"

    formatted = []
    for note in matched[:8]:
        line = f"Problem: {note.get('problem', '')}\nFix: {note.get('fix', '')}"
        context = note.get("context", "")
        if context:
            line += f"\nContext: {context}"
        formatted.append(line)
    return "\n\n".join(formatted)
