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
def find_gluten_free_restaurants_places_api(city_name, api_key, type_): # type_ is now 'restaurants_cafes' or 'bakeries'
    """
    Searches for gluten-free establishments in a given city using Google Places API.
    The 'type_' parameter guides the query.
    Returns a list of basic place dictionaries or an empty list on error/no results.
    """
    if not api_key:
        print("Google Places API key is missing. Cannot perform search.")
        return [] 

    query = ""
    google_api_type_param = 'establishment' # Default broad type for Places API

    if type_ == 'restaurants_cafes':
        query = f"gluten-free restaurants and cafes in {city_name}"
        # We can try to bias with 'restaurant|cafe' if the API supports it well,
        # or rely on the query string and Gemini's filtering of Google Types.
        # For Text Search, including in query is often effective.
        # No specific 'type' param here, let query string and Gemini handle types.
    elif type_ == 'bakeries':
        query = f"gluten-free bakeries in {city_name}"
        google_api_type_param = 'bakery' # Be more specific if possible
    else: # Fallback for any other unexpected type
        query = f"gluten-free establishments in {city_name}"
    
    print(f"\n🔍 Searching Google Places for: \"{query}\" (API type hint: {google_api_type_param})...")

    params = {'query': query, 'key': api_key}
    if google_api_type_param != 'establishment': # Only add type if specific
        params['type'] = google_api_type_param

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    try:
        print(f"\n🔍 Making Google Places API request with params: {params}")
        response = requests.get(url, params=params)
        print(f"\n🔍 Google Places API Response Status Code: {response.status_code}")
        
        response.raise_for_status()
        places_data = response.json()

        if places_data.get("status") == "OK":
            places = []
            for place_result in places_data.get("results", []):
                google_types = place_result.get('types', [])
                if not isinstance(google_types, list): 
                    google_types = []
                places.append({
                    "name": place_result.get("name"),
                    "address": place_result.get("formatted_address"),
                    "rating": place_result.get("rating", "N/A"),
                    "user_ratings_total": place_result.get("user_ratings_total", 0), # Still useful for Gemini if it wants to consider it
                    'types': google_types, 
                    'place_id': place_result.get('place_id'), 
                    'business_status': place_result.get('business_status', ''),
                })
            
            open_places = [p for p in places if p['business_status'] == 'OPERATIONAL' and p['place_id']]
            print(f"✅ Initial search found {len(places)} total, {len(open_places)} are operational with place_id.")
            return open_places

        elif places_data.get("status") == "ZERO_RESULTS":
            print(f"✅ Places API (Text Search) returned ZERO_RESULTS for \"{query}\".")
            return []
        else:
            print(f"⚠️ Places API (Text Search) returned status: {places_data.get('status')}")
            if places_data.get("error_message"):
                print(f"   Error message: {places_data.get('error_message')}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Google Places API (Text Search): {e}")
        return []
    except json.JSONDecodeError:
        print("❌ Error decoding JSON response from Places API (Text Search).")
        return []

# --- Function to call Gemini API ---
def get_gemini_description(establishments_list, city_name, api_key, type_): # type_ is 'restaurants_cafes' or 'bakeries'
    """
    Generates a description of gluten-free options using Gemini API.
    Gemini classifies "dedicated" based on name/types and sorts accordingly.
    Review counts are NOT included in the final output.
    """
    if not api_key:
        print("Gemini API key is missing. Cannot generate description.")
        return "Error: Gemini API key missing."

    search_context_info = "The initial search was for general 'gluten-free' establishments."

    if establishments_list: 
        establishment_details_for_prompt = []
        # establishments_list is NOT pre-sorted by review count by app.py anymore
        # We still send up to 20 items for Gemini to process
        for r_idx, r_val in enumerate(establishments_list[:20]): 
            types_str = ", ".join(r_val.get('types', []))
            # REMOVED review count from the detail string sent to Gemini for processing.
            # Gemini will be instructed NOT to include it in its output.
            # We still have user_ratings_total in r_val if Gemini needs it for some internal logic, but it won't be in the prompt detail.
            detail = (f"Name: {r_val['name']}, Address: {r_val['address']}, "
                      f"Rating: {r_val['rating']}, Google Types: [{types_str}]")
            establishment_details_for_prompt.append(detail)
        
        establishment_block_for_gemini = "\n".join([f"- {detail}" for detail in establishment_details_for_prompt])
        
        type_filtering_instructions = ""
        if type_ == 'restaurants_cafes':
            type_filtering_instructions = "A 'restaurant or cafe' should primarily have 'restaurant', 'cafe', 'meal_takeaway', 'meal_delivery', or 'bakery' (if it functions like a cafe) in its Google Types."
        elif type_ == 'bakeries':
            type_filtering_instructions = "A 'bakery' should primarily have 'bakery' in its Google Types. It can sometimes also be a 'cafe' if it's a bakery-cafe."
        
        prompt = (
            f"You are an assistant helping find gluten-free dining. {search_context_info}\n"
            f"I am looking for establishments of type '{type_}' in {city_name}. "
            f"The following list contains potential places. Each item includes its 'Google Types' array from the Google Places API:\n"
            f"{establishment_block_for_gemini}\n\n"
            f"Your task is to re-list ONLY the establishments that strictly match the requested type: '{type_}'. "
            f"Use the 'Google Types' array provided for each establishment to make this determination. {type_filtering_instructions}\n"
            f"If no establishments from the list match the type '{type_}', return ONLY the message: 'No {type_} found matching the criteria in {city_name}.' Do not add any other text or the advisory note in this case.\n\n"
            f"If matching establishments are found, present them as a single, continuous numbered list with the following sorting and formatting:\n"
            f"SORTING: First, list all establishments you classify as 'dedicated gluten-free'. After those, list establishments classified as 'offers gluten-free options'. Finally, list any classified as 'status unclear, verify with restaurant'.\n"
            f"FORMAT for each item in your list:\n"
            f"1. Name of the establishment.\n"
            f"2. In brackets, your classification of its gluten-free status (e.g., '[dedicated gluten-free]', '[offers gluten-free options]', or '[status unclear, verify with restaurant]').\n"
            f"DO NOT include review counts or ratings in your final numbered list output.\n"
            f"Gluten-Free Status Classification Rules (based on the provided name and Google Types):\n"
            f"   - Classify as '[dedicated gluten-free]' ONLY if the establishment's name is EXPLICITLY and CLEARLY indicative of being entirely gluten-free (e.g., '100% Gluten-Free Cafe', 'Totally GF Bakery', 'Celiac Safe Kitchen'). The presence of 'gluten-free' in the name alone is not enough for this category unless it implies exclusivity.\n"
            f"   - Otherwise, classify as '[offers gluten-free options]' if the name or types suggest it's a regular establishment that likely has some gluten-free items.\n"
            f"   - If there's insufficient information from the name or types to make a judgment, classify as '[status unclear, verify with restaurant]'.\n"
            f"Do not add any extra conversational lines before or after your numbered list if establishments are found.\n"
            f"If establishments are listed, then AFTER the list, provide this very brief, separate, single-paragraph advisory note: "
            f"'Reminder: Always call establishments directly to confirm their current gluten-free practices, menu, and cross-contamination protocols, especially if you have celiac disease or severe sensitivities. Information can change.'"
        )
    else: 
        prompt = (
            f"You are an assistant helping find gluten-free dining. "
            f"The initial search was for general 'gluten-free' establishments of type '{type_}' in {city_name}, but no specific places were found by the Google Places API matching that criteria.\n"
            f"Please return ONLY the message: 'No {type_} found matching the criteria in {city_name}.' Do not add any other text or an advisory note."
        )

    print(f"\n🤖 Asking Gemini with type '{type_}' and general search context...")

    gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "top_p": 0.95 }
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
            print(f"⚠️ Gemini API blocked the prompt. Reason: {reason}")
            return f"Gemini API blocked the prompt. Please refine your search or contact support if this persists."
        else:
            print("⚠️ Gemini API returned an unexpected response structure.")
            return f"Error: Gemini returned an unexpected response for {city_name}."

    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Gemini API: {e}")
        return f"Error: Could not connect to Gemini API for {city_name}."
    except json.JSONDecodeError:
        print("❌ Error decoding JSON response from Gemini API.")
        return f"Error: Could not decode Gemini's response for {city_name}."

# --- Main Execution (for testing this file directly) ---
if __name__ == "__main__":
    if not GOOGLE_PLACES_API_KEY or not GEMINI_API_KEY:
        print("\nOne or both API keys are missing. Please set them up in environment variables and re-run.")
    else:
        target_city = input("Enter the city name to search for gluten-free establishments: ")
        test_type = input(f"Enter type for {target_city} (e.g., restaurants_cafes, bakeries, default: restaurants_cafes): ") or 'restaurants_cafes'
        
        if target_city:
            print(f"Searching for general gluten-free options for type '{test_type}'.")
            
            places_list = find_gluten_free_restaurants_places_api(
                target_city, 
                GOOGLE_PLACES_API_KEY,
                type_=test_type
            )

            if places_list: 
                # No longer sorting by review count here before sending to Gemini
                print(f"ℹ️ Found {len(places_list)} places. Top {min(len(places_list), 20)} will be sent to Gemini as is.")

                description = get_gemini_description(
                    places_list, 
                    target_city, 
                    GEMINI_API_KEY, 
                    type_=test_type 
                )

                print("\n--- Gluten-Free Establishment Summary ---")
                # Displaying raw data from Places API is less relevant now as Gemini does the main formatting.
                # We can show a snippet of what was sent to Gemini for debugging if needed.
                print(f"\n(Sample of data sent to Gemini - first {min(len(places_list), 3)} shown):")
                for r_val in places_list[:3]: 
                    print(f"  - Name: {r_val['name']}, Types: {r_val.get('types', [])}")
                
                print("\nGemini's Formatted and Re-sorted Advice:")
                print(description)

            else: 
                print(f"\nNo specific establishments were listed by the Places API for {target_city} matching the 'gluten-free' criteria for type '{test_type}'.")
                description = get_gemini_description(
                    [], target_city, GEMINI_API_KEY, 
                    type_=test_type 
                )
                print("\nGemini's Advice:")
                print(description)
        else:
            print("No city name entered. Exiting.")
    print("\n--- Script Finished ---")
