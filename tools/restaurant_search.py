import requests
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

if not GOOGLE_PLACES_API_KEY:
    print("Warning: GOOGLE_PLACES_API_KEY not found in .env. Restaurant search will return dummy data.")

def search_restaurants(cuisine: str, location: str, max_results: int = 3) -> list:
    if not GOOGLE_PLACES_API_KEY:
        print("\n(Simulating) Google Places API Key missing. Returning dummy data for restaurant search.")
        return [
            {"name": "Paradise Biryani (Simulated)", "address": "Gachibowli, Hyderabad (Simulated Address)", "rating": "4.1", "cuisine": "Hyderabadi Biryani", "booking_url": "https://example.com/simulated-booking"},
            {"name": "Bawarchi (Simulated)", "address": "RTC Cross Roads, Hyderabad (Simulated Address)", "rating": "4.3", "cuisine": "Hyderabadi, North Indian", "booking_url": "https://example.com/simulated-booking"},
            {"name": "Sarvi (Simulated)", "address": "Banjara Hills, Hyderabad (Simulated Address)", "rating": "4.0", "cuisine": "Hyderabadi, Multi-Cuisine", "booking_url": "https://example.com/simulated-booking"}
        ]

    query = f"{cuisine} restaurants in {location}"
    places_api_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    params = {
        "query": query,
        "key": GOOGLE_PLACES_API_KEY,
        "type": "restaurant"
    }

    print(f"\n(Using Google Places API) Searching for '{cuisine}' restaurants in '{location}'...")

    restaurants_found = []

    try:
        response = requests.get(places_api_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()

        if data.get('status') == 'OK':
            for i, place in enumerate(data.get('results', [])):
                if len(restaurants_found) >= max_results:
                    break
                
                name = place.get('name', 'N/A')
                address = place.get('formatted_address', 'N/A')
                rating = place.get('rating', 'N/A')
                cuisine_hint = ", ".join(place.get('types', [])) 
                
                if cuisine.lower() != 'any' and cuisine.lower() not in cuisine_hint.lower():
                    cuisine_hint = cuisine
                elif not cuisine_hint:
                    cuisine_hint = cuisine

                # --- MODIFIED: Inject specific Google Reserve URL for Chowman ---
                # This is the exact URL you provided for Chowman Gurgaon.
                specific_chowman_google_reserve_url = "https://www.google.com/maps/reserve/v/dine/c/FLzW2pMrpZ4?source=pa&opi=89978449&hl=en-IN&gei=44l_aMD9MZ6VseMP9Py_6Qo&sourceurl=https%3A%2F%2Fwww.google.com%2Fsearch%3Fq%3DChowman%2BGurgaon%26oq%3DChowman%2BGurgaon%26gs_lcrp%3DEgZjaHJvbWUyBggAEEUYOTIGCAEQRRg8MgYIAhBFGD0yBggDEC4YQNIBBzU4MmowajGoAgiwAgE%26sourceid%3Dchrome%26ie%3DUTF-8&ihs=3" 
                
                if "chowman" in name.lower() and "gurgaon" in address.lower():
                    booking_url = specific_chowman_google_reserve_url
                    print(f"(Internal) Injected specific Google Reserve URL for Chowman: {booking_url}")
                else:
                    # Fallback for other restaurants (generic placeholder)
                    booking_url = f"https://example.com/booking/{name.replace(' ', '-').lower()}" 
                
                restaurants_found.append({
                    "name": name,
                    "address": address,
                    "rating": str(rating),
                    "cuisine": cuisine_hint,
                    "booking_url": booking_url # Added booking_url
                })
        elif data.get('status') == 'ZERO_RESULTS':
            print("Google Places API found no results for this query.")
        else:
            print(f"Google Places API Error: {data.get('status')}. Message: {data.get('error_message', 'No error message provided.')}")

        if not restaurants_found:
            print("Google Places API returned no specific restaurant data. Returning dummy data.")
            return [
                {"name": "Paradise Biryani (Simulated)", "address": "Gachibowli, Hyderabad (Simulated Address)", "rating": "4.1", "cuisine": "Hyderabadi Biryani", "booking_url": "https://example.com/simulated-booking"},
                {"name": "Bawarchi (Simulated)", "address": "RTC Cross Roads, Hyderabad (Simulated Address)", "rating": "4.3", "cuisine": "Hyderabadi, North Indian", "booking_url": "https://example.com/simulated-booking"},
                {"name": "Sarvi (Simulated)", "address": "Banjara Hills, Hyderabad (Simulated Address)", "rating": "4.0", "cuisine": "Hyderabadi, Multi-Cuisine", "booking_url": "https://example.com/simulated-booking"}
            ]

        return restaurants_found

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Google Places API: {e}")
        print("Returning dummy data for restaurant search.")
    except Exception as e:
        print(f"An unexpected error occurred during Google Places API call: {e}")
        print("Returning dummy data for restaurant search.")

    return [
        {"name": "Paradise Biryani (Simulated)", "address": "Gachibowli, Hyderabad (Simulated Address)", "rating": "4.1", "cuisine": "Hyderabadi Biryani", "booking_url": "https://example.com/simulated-booking"},
        {"name": "Bawarchi (Simulated)", "address": "RTC Cross Roads, Hyderabad (Simulated Address)", "rating": "4.3", "cuisine": "Hyderabadi, North Indian", "booking_url": "https://example.com/simulated-booking"},
        {"name": "Sarvi (Simulated)", "address": "Banjara Hills, Hyderabad (Simulated Address)", "rating": "4.0", "cuisine": "Hyderabadi, Multi-Cuisine", "booking_url": "https://example.com/simulated-booking"}
    ]

if __name__ == '__main__':
    print("--- Running Restaurant Search Tool Test ---")
    test_cuisine = "North Indian" 
    test_location = "Sector 31, Gurgaon" 
    found_restaurants = search_restaurants(test_cuisine, test_location)

    if found_restaurants and "(Simulated)" not in found_restaurants[0].get('name', ''):
        print("\nSuccessfully Retrieved Real Restaurants (from Google Places API):")
        for r in found_restaurants:
            print(f"- Name: {r['name']}, Address: {r['address']}, Rating: {r['rating']}, Cuisine: {r['cuisine']}, Booking URL: {r.get('booking_url', 'N/A')}")
    else:
        print("\nRestaurant search returned dummy data. Ensure GOOGLE_PLACES_API_KEY is set and Places API is enabled with billing in GCP.")