from langchain.tools import tool
from duckduckgo_search import DDGS

@tool("duckduckgo_search")
def duckduckgo_search_tool(query: str) -> str:
    """
    Perform a web search using DuckDuckGo and return the top result.
    Use this tool when the user asks a question that requires up-to-date information from the internet.
    
    Examples of queries:
    - "Please look up what's the weather like in Paris today?"
    - "Look up the latest tech news"
    - "yes, please search for current AI news"

    Input:
    - A natural language query string.
    """
    with DDGS() as ddgs:
        results = ddgs.text(query, region='wt-wt', safesearch='Moderate', max_results=3)
        results_list = list(results)

    if not results_list:
        return f"No results found for: \"{query}\"."

    output = f"Search results for: \"{query}\"\n\n"
    for r in results_list:
        output += f"Title: {r['title']}\nURL: {r['href']}\nSummary: {r.get('body', 'N/A')}\n\n"
    return output.strip()
