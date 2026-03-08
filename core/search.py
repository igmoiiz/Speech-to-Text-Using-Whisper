# core/search.py — Advanced Web Search Logic

import time
import random
from ddgs import DDGS

def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for general info with multiple time-limit fallbacks. 
    Returns: Title | URL | Snippet
    """
    print(f"  🔍 Global Search: {query}")
    results_list = []
    
    # Attempt normal search then news-specific search for 'latest' queries
    search_types = ["text", "news"] if any(x in query.lower() for x in ["latest", "news", "today", "current", "update"]) else ["text"]

    for stype in search_types:
        try:
            with DDGS() as ddgs:
                # Try Day -> Week -> Month fallbacks for maximum relevance
                for tlimit in ["d", "w", "m"]:
                    if stype == "text":
                        res = list(ddgs.text(query, max_results=max_results, timelimit=tlimit))
                    else:
                        res = list(ddgs.news(query, max_results=max_results, timelimit=tlimit))
                    
                    if res:
                        for r in res:
                            title   = r.get("title", "No Title")
                            snippet = r.get("body", r.get("snippet", ""))
                            link    = r.get("href", r.get("link", r.get("url", "")))
                            results_list.append(f"TITLE: {title}\nURL: {link}\nCONTENT: {snippet}\n---")
                        break # Found something, exit tlimit loop
                        
            if results_list: break # Found in this search type, exit stype loop
        except Exception as e:
            print(f"  Search ({stype}) encountered an issue: {e}")
            continue

    return "\n".join(results_list).strip() if results_list else "I've scanned the live web and found no concrete pinpoint data on that topic yet, Sir."

def news_search(query: str, max_results: int = 5) -> str:
    """Targeted search for latest news reports with fallback."""
    print(f"  🗞️ News Pulse: {query}")
    try:
        with DDGS() as ddgs:
            results = []
            for tlimit in ["d", "w", "m"]:
                results = list(ddgs.news(query, max_results=max_results, timelimit=tlimit))
                if results: break
            
            if not results:
                return "The current news cycles are quiet on that front, Sir."

            output = []
            for r in results:
                title   = r.get("title", "No Title")
                source  = r.get("source", "Unknown Source")
                date    = r.get("date", "Recently")
                url     = r.get("url", r.get("link", r.get("href", "#")))
                output.append(f"SOURCE: {source} | {title} ({date})\nURL: {url}\n---")
            
            return "\n".join(output).strip()
    except Exception as e:
        return f"News pulse failed: {e}"

