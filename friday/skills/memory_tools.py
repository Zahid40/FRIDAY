from langchain.tools import tool
from friday.memory.long_term_memory import add_user_fact, search_user_facts

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
