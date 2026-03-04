# core/search.py — Web Search via DDGS

import time
from ddgs import DDGS

def web_search(query: str, max_results: int = 5) -> str:
    """Search the web. Returns formatted string of results."""
    print(f"  🔍 Searching: {query}")
    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query, max_results=max_results,
                    backend="lite", timelimit="d"
                ))
            if not results:
                with DDGS() as ddgs:
                    results = list(ddgs.text(
                        query, max_results=max_results,
                        backend="lite", timelimit="w"
                    ))
            if results:
                return "\n".join(
                    f"{r['title']}: {r['body']}" for r in results
                ).strip()
        except Exception as e:
            print(f"  Search attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    return "No results found."