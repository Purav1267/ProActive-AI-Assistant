# tools/restaurant_search.py
# This module provides a function to search for restaurants using the Google Places API.
# It is designed to be used as a tool by the AI assistant to find dining options based on user queries.

import requests
import os
from dotenv import load_dotenv

# --- Configuration ---

# Load environment variables from .env file.
# This is necessary for securely accessing the API key.
load_dotenv()
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# A warning is printed if the API key is not found, as the tool will fall back to dummy data.
if not GOOGLE_PLACES_API_KEY:
    print("Warning: GOOGLE_PLACES_API_KEY not found in .env. The restaurant search tool will return dummy data.")

# --- Core Tool Function ---

def search_restaurants(cuisine: str, location: str, max_results: int = 3) -> list:
    """
    Searches for restaurants using the Google Places Text Search API.
    If the GOOGLE_PLACES_API_KEY is not available or if the API call fails,
    it gracefully falls back to returning a predefined list of dummy restaurants.

    Args:
        cuisine: The type of food or restaurant style (e.g., "Italian", "pizza").
        location: The area to search within (e.g., "downtown", "near Central Park").
        max_results: The maximum number of results to return.

    Returns:
        A list of dictionaries, where each dictionary represents a restaurant.
        Each restaurant has a 'name', 'address', 'rating', and 'cuisine'.
    """
    
    # Fallback mechanism: If the API key is missing, return hardcoded dummy data.
    if not GOOGLE_PLACES_API_KEY:
        print("\n(Simulating) Google Places API key not found. Returning dummy data.")
        return [
            {"name": "Paradise Biryani (Simulated)", "address": "Gachibowli, Hyderabad", "rating": "4.1", "cuisine": "Hyderabadi"},
            {"name": "Bawarchi (Simulated)", "address": "RTC Cross Roads, Hyderabad", "rating": "4.3", "cuisine": "Indian"},
            {"name": "Sarvi (Simulated)", "address": "Banjara Hills, Hyderabad", "rating": "4.0", "cuisine": "Multi-Cuisine"}
        ]

    # Construct the search query and parameters for the Google Places API.
    query = f"{cuisine} restaurants in {location}"
    places_api_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": GOOGLE_PLACES_API_KEY,
        "type": "restaurant"
    }

    print(f"\n--- Searching for '{cuisine}' restaurants in '{location}' via Google Places API... ---")

    try:
        # Make the API request.
        response = requests.get(places_api_url, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx).
        
        data = response.json()
        restaurants_found = []

        # Process the API response.
        if data.get('status') == 'OK':
            for place in data.get('results', []):
                if len(restaurants_found) >= max_results:
                    break
                
                # Extract relevant details for each found place.
                cuisine_hint = ", ".join(t.replace('_', ' ').title() for t in place.get('types', []))
                
                restaurants_found.append({
                    "name": place.get('name', 'N/A'),
                    "address": place.get('formatted_address', 'N/A'),
                    "rating": str(place.get('rating', 'N/A')),
                    "cuisine": cuisine_hint or cuisine # Use API hint or fall back to original query.
                })
        else:
            # Log API errors if the status is not 'OK'.
            print(f"Google Places API Error: {data.get('status')} - {data.get('error_message', 'No message')}")

        # If after a successful API call, no results were parsed, return dummy data.
        if not restaurants_found:
            print("API call succeeded but no restaurants were found. Returning dummy data.")
            return _get_dummy_data()

        return restaurants_found

    except requests.exceptions.RequestException as e:
        # Handle network-related errors.
        print(f"Error connecting to Google Places API: {e}. Returning dummy data.")
        return _get_dummy_data()
    except Exception as e:
        # Handle other unexpected errors.
        print(f"An unexpected error occurred: {e}. Returning dummy data.")
        return _get_dummy_data()

def _get_dummy_data() -> list:
    """Returns a predefined list of simulated restaurant data."""
    return [
        {"name": "Paradise Biryani (Simulated)", "address": "Gachibowli, Hyderabad", "rating": "4.1", "cuisine": "Hyderabadi"},
        {"name": "Bawarchi (Simulated)", "address": "RTC Cross Roads, Hyderabad", "rating": "4.3", "cuisine": "Indian"},
        {"name": "Sarvi (Simulated)", "address": "Banjara Hills, Hyderabad", "rating": "4.0", "cuisine": "Multi-Cuisine"}
    ]

# --- Standalone Test Block ---
if __name__ == '__main__':
    # This block allows for independent testing of the restaurant search tool.
    print("--- Running Restaurant Search Tool Test ---")
    
    test_cuisine = "Hyderabadi biryani"
    test_location = "Gachibowli, Hyderabad" 
    
    found_restaurants = search_restaurants(test_cuisine, test_location)

    if found_restaurants and "(Simulated)" not in found_restaurants[0].get('name', ''):
        print("\nSuccessfully Retrieved Real Restaurants:")
        for r in found_restaurants:
            print(f"- Name: {r['name']}\n  Address: {r['address']}\n  Rating: {r['rating']}\n  Cuisine: {r['cuisine']}\n")
    else:
        print("\nSearch returned dummy data. Please check the following:")
        print("1. Your `.env` file contains a valid `GOOGLE_PLACES_API_KEY`.")
        print("2. The Google Places API is enabled in your Google Cloud project.")
        print("3. Billing is enabled for your Google Cloud project.")