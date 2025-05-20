# Import necessary libraries
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Function to call Google Places API (Text Search) ---
def find_gluten_free_restaurants_places_api(city_name, api_key, dedicated_only=True):
    """
    Searches for gluten-free restaurants in a given city using Google Places API.
    If dedicated_only is True, it will try to find restaurants that are more likely to be fully gluten-free.
    """
    if not api_key:
        print("Google Places API key is missing. Cannot perform search.")
        return None

    if dedicated_only:
        query = f"dedicated gluten-free restaurants in {city_name}"
        print(f"\n🔍 Searching Google Places for (dedicated focus): \"{query}\"...")
    else:
        query = f"gluten-free restaurants in {city_name}"
        print(f"\n🔍 Searching Google Places for: \"{query}\"...")

    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        places_data = response.json()

        if places_data.get("status") == "OK":
            restaurants = []
            for place in places_data.get("results", []):
                restaurants.append({
                    "name": place.get("name"),
                    "address": place.get("formatted_address"),
                    "rating": place.get("rating", "N/A"),
                    "user_ratings_total": place.get("user_ratings_total", 0)
                })
            print(f"✅ Found {len(restaurants)} potential restaurants via Places API.")
            return restaurants
        elif places_data.get("status") == "ZERO_RESULTS":
            print(f"✅ Places API returned ZERO_RESULTS for \"{query}\". No restaurants found matching this specific criteria.")
            return []
        else:
            print(f"⚠️ Places API returned status: {places_data.get('status')}")
            if places_data.get("error_message"):
                print(f"   Error message: {places_data.get('error_message')}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Google Places API: {e}")
        return None
    except json.JSONDecodeError:
        print("❌ Error decoding JSON response from Places API.")
        return None

# --- Function to call Gemini API ---
def get_gemini_description(restaurants_list, city_name, api_key, searched_dedicated=True):
    """
    Generates a description of gluten-free options using Gemini API, using up to the top 20 restaurants.
    Instructs Gemini to sort its output by dedicated status first, then others, and include review counts in brackets.
    """
    if not api_key:
        print("Gemini API key is missing. Cannot generate description.")
        return None
    if not GEMINI_API_KEY:
        print("Gemini API key is not available.")
        return "Gemini API key not available."

    search_focus = "dedicated gluten-free" if searched_dedicated else "gluten-free options"

    if restaurants_list:
        restaurant_details_for_prompt = []
        for r in restaurants_list[:20]: 
            detail = f"Name: {r['name']}, Address: {r['address']}, Rating: {r['rating']} (Reviews: {r['user_ratings_total']})"
            restaurant_details_for_prompt.append(detail)
        
        restaurant_block = "\n".join([f"- {detail}" for detail in restaurant_details_for_prompt])

        prompt = (
            f"You are an assistant helping find gluten-free dining. I searched for '{search_focus}' restaurants in {city_name}. "
            f"The following list contains potential places, initially sorted by the number of user reviews (highest first) for your reference:\n"
            f"{restaurant_block}\n\n"
            f"Please re-list these restaurants as a single, continuous numbered list. "
            f"IMPORTANT SORTING FOR YOUR OUTPUT: First, list all restaurants you classify as 'dedicated gluten-free'. After those, list all other restaurants (those classified as 'offers gluten-free options' or 'status unclear, verify with restaurant'). "
            f"For each restaurant in your output list: include its name, then in brackets your classification (e.g., '[dedicated gluten-free]', '[offers gluten-free options]', or '[status unclear, verify with restaurant]'), and then in separate brackets the original review count from the input list (e.g., '[Reviews: {r['user_ratings_total']}]'). "
            f"Base your 'dedicated gluten-free' classification on whether the original search was for 'dedicated gluten-free' AND the restaurant name sounds explicitly gluten-free (e.g., 'GF Bakery', '100% Gluten-Free'). Otherwise, classify as 'offers gluten-free options' or 'status unclear, verify with restaurant' if the name gives no clear clue. "
            f"Do not add any extra conversational lines before or after your numbered list. "
            f"After the list, provide a very brief, separate, single-paragraph advisory note: "
            f"'Reminder: Always call restaurants directly to confirm their current gluten-free practices, menu, and cross-contamination protocols, especially if you have celiac disease or severe sensitivities. Information can change.'"
        )
    else:
        prompt = (
            f"You are an assistant helping find gluten-free dining. "
            f"I searched for '{search_focus}' restaurants in {city_name}, but no specific places were found by the Google Places API matching that criteria.\n"
            f"Please provide some general advice and tips for finding '{search_focus}' food in {city_name}, in a concise paragraph. "
            f"Then, in a separate, single-paragraph advisory note, emphasize the importance of always verifying with restaurants directly about their gluten-free safety protocols, especially when looking for dedicated facilities."
        )

    print("\n🤖 Asking Gemini to sort by dedicated status and format with review counts in brackets...")

    gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(gemini_api_url, headers=headers, json=payload)
        response.raise_for_status()
        gemini_data = response.json()

        if gemini_data.get("candidates") and \
           gemini_data["candidates"][0].get("content") and \
           gemini_data["candidates"][0]["content"].get("parts"):
            generated_text = gemini_data["candidates"][0]["content"]["parts"][0].get("text")
            print("✅ Gemini provided a response.")
            return generated_text.strip() 
        elif gemini_data.get("promptFeedback") and gemini_data["promptFeedback"].get("blockReason"):
            reason = gemini_data["promptFeedback"]["blockReason"]
            safety_ratings = gemini_data["promptFeedback"].get("safetyRatings", [])
            print(f"⚠️ Gemini API blocked the prompt. Reason: {reason}")
            print(f"   Safety Ratings: {safety_ratings}")
            return f"Gemini API blocked the prompt due to: {reason}."
        else:
            print("⚠️ Gemini API returned an unexpected response structure.")
            print(json.dumps(gemini_data, indent=2))
            return "Could not retrieve a valid description from Gemini."

    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Gemini API: {e}")
        try:
            error_content = response.json()
            print("   Error details from Gemini:", json.dumps(error_content, indent=2))
            if error_content.get("error", {}).get("message"):
                 return f"Error from Gemini API: {error_content['error']['message']}"
        except:
            pass
        return "An error occurred while communicating with Gemini."
    except json.JSONDecodeError:
        print("❌ Error decoding JSON response from Gemini API.")
        return "Error decoding Gemini's response."

# --- Main Execution ---
if __name__ == "__main__":
    if not GOOGLE_PLACES_API_KEY or not GEMINI_API_KEY:
        print("\nOne or both API keys are missing. Please set them up in environment variables and re-run.")
    else:
        target_city = input("Enter the city name to search for gluten-free restaurants: ")
        
        search_dedicated_gf = True 

        if target_city:
            print(f"Searching for {'dedicated ' if search_dedicated_gf else ''}gluten-free options.")
            # 1. Get restaurants from Places API
            restaurants = find_gluten_free_restaurants_places_api(target_city, GOOGLE_PLACES_API_KEY, dedicated_only=search_dedicated_gf)

            if restaurants is not None:
                # Sort restaurants by user_ratings_total (descending) - this is for the INPUT to Gemini
                if restaurants: 
                    def get_review_count(r):
                        count = r.get('user_ratings_total', 0)
                        if isinstance(count, str) and count.isdigit():
                            return int(count)
                        elif isinstance(count, (int, float)): 
                            return int(count)
                        return 0 
                    
                    restaurants.sort(key=get_review_count, reverse=True)
                    print(f"ℹ️ Restaurants sorted by review count (highest first). Top {min(len(restaurants), 20)} will be sent to Gemini for re-sorting and classification.")

                # 2. Get description from Gemini API (passing the review-sorted list for Gemini to re-sort by dedicated status)
                description = get_gemini_description(restaurants, target_city, GEMINI_API_KEY, searched_dedicated=search_dedicated_gf)

                print("\n--- Gluten-Free Restaurant Summary ---")
                
                if restaurants: # This still refers to the initially fetched and review-sorted list
                    print(f"\n(Direct from Google Places - top {min(len(restaurants), 5)} of review-sorted list shown):")
                    for r in restaurants[:5]: 
                        print(f"  - Name: {r['name']}")
                        print(f"    Address: {r['address']}")
                        print(f"    Rating: {r['rating']} (Total Reviews: {r['user_ratings_total']})")
                        print("-" * 20)
                    if len(restaurants) > 5:
                        print(f"  ...and {len(restaurants)-5} more found by Places API (full review-sorted list up to 20 sent to Gemini).")
                else:
                    print(f"\nNo specific restaurants were listed by the Places API for {target_city} matching the '{'dedicated ' if search_dedicated_gf else ''}gluten-free' criteria.")

                print("\nGemini's Formatted and Re-sorted Advice:")
                print(description)
            else:
                print("\nCould not proceed due to an error with the Places API.")
        else:
            print("No city name entered. Exiting.")

    print("\n--- Script Finished ---")
