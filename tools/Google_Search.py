# tools/Google_Search.py
# This script provides a mock implementation of a Google Search tool.
# It is intended for local testing and debugging without making actual API calls.

def search(queries: list) -> list:
    """
    Simulates a Google search by returning predefined, mock results.
    This function is designed to be a placeholder for a real search API, allowing
    the agent's logic to be tested in isolation.

    It provides a basic, hardcoded response for queries related to dates and times
    to assist in testing the agent's natural language date understanding.

    Args:
        queries: A list of search strings.

    Returns:
        A list of dictionaries, where each dictionary represents the mock
        search results for a corresponding query.
    """
    print(f"--- MOCK Google Search Executed for: {queries} ---")
    results_list = []
    for query in queries:
        # A simple heuristic to provide a somewhat relevant mock response for date-related queries.
        if "datetime" in query.lower() or "date" in query.lower():
            results_list.append({
                "queries": [{"search_term": query}],
                "results": [{
                    "title": "Mock Date Result",
                    "snippet": f"The mock date for '{query}' is 2025-07-22T20:00:00Z."
                }]
            })
        else:
            # Generic response for any other query.
            results_list.append({
                "queries": [{"search_term": query}],
                "results": [{
                    "title": "Mock Search Result",
                    "snippet": f"This is a mock search result for the query: '{query}'."
                }]
            })
    return results_list

# --- Standalone Test Block ---
if __name__ == '__main__':
    # This demonstrates how the mock search function can be called directly.
    print("--- Testing Mock Google Search ---")
    test_results = search(["current date and time", "best restaurants in Hyderabad"])
    import json
    print(json.dumps(test_results, indent=2))