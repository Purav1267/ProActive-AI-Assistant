import requests
import os
from dotenv import load_dotenv

# Load environment variables (needed here if this module is tested independently, or by main)
load_dotenv()
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

if not GOOGLE_PLACES_API_KEY:
    print("Warning: GOOGLE_PLACES_API_KEY not found in .env. Restaurant search will return dummy data.")

def search_restaurants(cuisine: str, location: str, max_results: int = 3) -> list:
    """
    Searches for restaurants using Google Places Text Search API.
    Args:
        cuisine (str): The type of cuisine (e.g., "Hyderabadi biryani").
        location (str): The general location (e.g., "Hyderabad", "Gachibowli, Hyderabad").
        max_results (int): Maximum number of restaurant results to return.
    Returns:
        list: A list of dictionaries, each containing restaurant 'name', 'address', 'rating', and 'cuisine'.
              Returns dummy data if API key is missing or on API error.
    """
    
    if not GOOGLE_PLACES_API_KEY:
        print("\n(Simulating) Google Places API Key missing. Returning dummy data for restaurant search.")
        return [
            {"name": "Paradise Biryani (Simulated)", "address": "Gachibowli, Hyderabad (Simulated Address)", "rating": "4.1", "cuisine": "Hyderabadi Biryani"},
            {"name": "Bawarchi (Simulated)", "address": "RTC Cross Roads, Hyderabad (Simulated Address)", "rating": "4.3", "cuisine": "Hyderabadi, North Indian"},
            {"name": "Sarvi (Simulated)", "address": "Banjara Hills, Hyderabad (Simulated Address)", "rating": "4.0", "cuisine": "Hyderabadi, Multi-Cuisine"}
        ]

    # Construct the query for Google Places API
    # Combine cuisine and location for a robust search query
    query = f"{cuisine} restaurants in {location}"
    
    # Google Places Text Search API endpoint
    places_api_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    params = {
        "query": query,
        "key": GOOGLE_PLACES_API_KEY,
        "type": "restaurant" # Ensure it searches for restaurants
    }

    print(f"\n(Using Google Places API) Searching for '{cuisine}' restaurants in '{location}'...")

    restaurants_found = []

    try:
        response = requests.get(places_api_url, params=params, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()

        if data.get('status') == 'OK':
            for i, place in enumerate(data.get('results', [])):
                if len(restaurants_found) >= max_results:
                    break
                
                name = place.get('name', 'N/A')
                address = place.get('formatted_address', 'N/A')
                rating = place.get('rating', 'N/A') # Rating is a number, not string
                
                # Google Places API 'types' can give a hint for cuisine, but not precise
                cuisine_hint = ", ".join(place.get('types', [])) 
                if 'food' in cuisine_hint: cuisine_hint = 'Restaurant'
                if 'meal_takeaway' in cuisine_hint: cuisine_hint = 'Takeaway'
                if 'bakery' in cuisine_hint: cuisine_hint = 'Bakery'
                
                # Try to make cuisine more relevant if the original query contained it
                if cuisine.lower() != 'any' and cuisine.lower() not in cuisine_hint.lower():
                    cuisine_hint = cuisine # Prioritize the user's explicit cuisine
                elif not cuisine_hint: # If no hint from API, but user specified
                    cuisine_hint = cuisine


                restaurants_found.append({
                    "name": name,
                    "address": address,
                    "rating": str(rating), # Convert rating to string for consistency with previous output
                    "cuisine": cuisine_hint # This is a broad hint, not specific cuisine
                })
        elif data.get('status') == 'ZERO_RESULTS':
            print("Google Places API found no results for this query.")
        else:
            print(f"Google Places API Error: {data.get('status')}. Message: {data.get('error_message', 'No error message provided.')}")

        if not restaurants_found:
            print("Google Places API returned no specific restaurant data. Returning dummy data.")
            return [
                {"name": "Paradise Biryani (Simulated)", "address": "Gachibowli, Hyderabad (Simulated Address)", "rating": "4.2", "cuisine": "Hyderabadi Biryani"},
                {"name": "Bawarchi (Simulated)", "address": "RTC Cross Roads, Hyderabad (Simulated Address)", "rating": "4.3", "cuisine": "Hyderabadi, North Indian"},
                {"name": "Sarvi (Simulated)", "address": "Banjara Hills, Hyderabad (Simulated Address)", "rating": "4.0", "cuisine": "Hyderabadi, Multi-Cuisine"}
            ]

        return restaurants_found

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Google Places API: {e}")
        print("Returning dummy data for restaurant search.")
    except Exception as e:
        print(f"An unexpected error occurred during Google Places API call: {e}")
        print("Returning dummy data for restaurant search.")

    # Fallback to dummy data if any error occurs
    return [
        {"name": "Paradise Biryani (Simulated)", "address": "Gachibowli, Hyderabad (Simulated Address)", "rating": "4.1", "cuisine": "Hyderabadi Biryani"},
        {"name": "Bawarchi (Simulated)", "address": "RTC Cross Roads, Hyderabad (Simulated Address)", "rating": "4.3", "cuisine": "Hyderabadi, North Indian"},
        {"name": "Sarvi (Simulated)", "address": "Banjara Hills, Hyderabad (Simulated Address)", "rating": "4.0", "cuisine": "Hyderabadi, Multi-Cuisine"}
    ]

# --- Example Usage (for testing this module independently) ---
if __name__ == '__main__':
    print("--- Running Restaurant Search Tool Test ---")
    
    test_cuisine = "Hyderabadi biryani"
    test_location = "Gachibowli, Hyderabad" 
    
    found_restaurants = search_restaurants(test_cuisine, test_location)

    if found_restaurants and "(Simulated)" not in found_restaurants[0].get('name', ''):
        print("\nSuccessfully Retrieved Real Restaurants (from Google Places API):")
        for r in found_restaurants:
            print(f"- Name: {r['name']}, Address: {r['address']}, Rating: {r['rating']}, Cuisine: {r['cuisine']}")
    else:
        print("\nRestaurant search returned dummy data. Ensure GOOGLE_PLACES_API_KEY is set and Places API is enabled with billing in GCP.")