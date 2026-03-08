# core/search.py — Advanced Web Search Logic

import time
import random
from ddgs import DDGS

def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for general info. 
    Returns: Title | URL | Snippet
    """
    print(f"  🔍 Global Search: {query}")
    results_list = []
    
    # Attempt normal search then news-specific search for 'latest' queries
    search_types = ["text", "news"] if any(x in query.lower() for x in ["latest", "news", "today", "current"]) else ["text"]

    for stype in search_types:
        try:
            with DDGS() as ddgs:
                if stype == "text":
                    res = ddgs.text(query, max_results=max_results, timelimit="d")
                else:
                    res = ddgs.news(query, max_results=max_results, timelimit="d")
                
                for r in res:
                    title   = r.get("title", "No Title")
                    snippet = r.get("body", r.get("snippet", ""))
                    link    = r.get("href", r.get("link", ""))
                    results_list.append(f"TITLE: {title}\nURL: {link}\nCONTENT: {snippet}\n---")
                    
            if results_list: break
        except Exception as e:
            print(f"  Search ({stype}) encountered an issue: {e}")
            continue

    if not results_list:
        # Fallback to wider time limit
        try:
            with DDGS() as ddgs:
                res = ddgs.text(query, max_results=max_results, timelimit="w")
                for r in res:
                    results_list.append(f"TITLE: {r['title']}\nURL: {r['href']}\nCONTENT: {r['body']}\n---")
        except: pass

    return "\n".join(results_list).strip() if results_list else "No relevant information found on the live web, Sir."

def news_search(query: str, max_results: int = 5) -> str:
    """Targeted search for latest news reports."""
    print(f"  🗞️ News Pulse: {query}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results, timelimit="d"))
            if not results:
                results = list(ddgs.news(query, max_results=max_results, timelimit="w"))
            
            output = []
            for r in results:
                title   = r.get("title", "No Title")
                source  = r.get("source", "Unknown Source")
                date    = r.get("date", "Today")
                url     = r.get("url", r.get("link", r.get("href", "#")))
                output.append(f"SOURCE: {source} | {title} ({date})\nURL: {url}\n---")
            
            return "\n".join(output).strip()
    except Exception as e:
        return f"News search failed: {e}"
