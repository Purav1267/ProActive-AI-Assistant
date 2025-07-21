# tools/Google Search.py (Mock Version for troubleshooting)
def search(queries: list) -> list:
    """
    Mocks a Google search.
    """
    print(f"(MOCK) Google Search for: {queries}")
    results_list = []
    for query in queries:
        # Provide a very basic mock response for date queries
        if "datetime" in query.lower() or "date" in query.lower():
            results_list.append({
                "queries": [{"search_term": query}],
                "results": [{"title": "Mock Date Result", "snippet": f"The date for '{query}' is 2025-07-22T20:00:00Z. (MOCK)"}]
            })
        else:
            results_list.append({
                "queries": [{"search_term": query}],
                "results": [{"title": "Mock Search Result", "snippet": f"This is a mock search result for: {query}. (MOCK)"}]
            })
    return results_list

if __name__ == '__main__':
    print(search(["current date and time", "tomorrow's date"]))