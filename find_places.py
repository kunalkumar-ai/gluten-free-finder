import requests
import json
import os
import time 
from dotenv import load_dotenv

load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# MODIFIED function signature
def find_gluten_free_restaurants_places_api(city_name, api_key, type_, country_filter=None):
    """
    Searches for gluten-free establishments in a given city and optional country using Google Places API.
    """
    if not api_key:
        print("Google Places API key is missing. Cannot perform search.")
        return [] 

    text_query_base = "" # Base for text query before city/country
    google_api_type_param = None 
    query_location_part = city_name
    
    # NEW: Incorporate country_filter into the query_location_part
    if country_filter and country_filter.strip():
        query_location_part = f"{city_name}, {country_filter.strip()}"
        print(f"ℹ️ Applying country filter: {country_filter.strip()}")

    if type_ == 'restaurants':
        text_query_base = "gluten-free restaurants in"
        google_api_type_param = 'restaurant'
    elif type_ == 'cafes':
        text_query_base = "gluten-free cafes in"
        google_api_type_param = 'cafe'
    elif type_ == 'bakery':
        text_query_base = "gluten-free bakeries in"
        google_api_type_param = 'bakery'
    else: 
        print(f"⚠️ Unexpected type_ value: '{type_}'. Falling back to general search.")
        text_query_base = "gluten-free establishments in"
    
    text_query = f"{text_query_base} {query_location_part}"
    
    print(f"\n🔍 Google Places Search for type: '{type_}' with text query: \"{text_query}\" and API type parameter: '{google_api_type_param}'...")

    all_places = []
    params = {'query': text_query, 'key': api_key}
    if google_api_type_param:
        params['type'] = google_api_type_param
    
    # NEW: Add region parameter if country_filter is a valid 2-letter code (optional enhancement)
    # For now, primary country filtering is via text_query.
    # if country_filter and len(country_filter.strip()) == 2: # Simple check for 2-letter code
    #     params['region'] = country_filter.strip().lower()
    #     print(f"ℹ️ Also using region parameter for API: {params['region']}")


    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    max_pages = 2 

    for page_num in range(max_pages):
        try:
            current_params = params.copy() 
            if page_num > 0 and 'pagetoken' in params:
                current_params = {'pagetoken': params['pagetoken'], 'key': api_key}
                print(f"\n🔍 Fetching page {page_num + 1} from Google Places using pagetoken...")
            elif page_num == 0:
                print(f"\n🔍 Making Google Places API request (Page 1) with params: {current_params}")
            else: 
                print("Error: Attempting to fetch next page without a pagetoken.")
                break

            response = requests.get(url, params=current_params)
            print(f"🔍 Google Places API Response Status Code: {response.status_code} for page {page_num + 1}")
            response.raise_for_status()
            places_data = response.json()

            if places_data.get("status") == "OK":
                page_results = []
                for place_result in places_data.get("results", []):
                    google_types_from_api = place_result.get('types', [])
                    if not isinstance(google_types_from_api, list): 
                        google_types_from_api = []
                    
                    if place_result.get('business_status') == 'OPERATIONAL' and place_result.get('place_id'):
                        page_results.append({
                            "name": place_result.get("name"),
                            "address": place_result.get("formatted_address"),
                            "rating": place_result.get("rating", "N/A"),
                            "user_ratings_total": place_result.get("user_ratings_total", 0),
                            'types': google_types_from_api, 
                            'place_id': place_result.get('place_id'), 
                            'business_status': place_result.get('business_status', ''),
                        })
                all_places.extend(page_results)
                print(f"✅ Page {page_num + 1}: Found {len(page_results)} operational establishments.")

                next_page_token = places_data.get('next_page_token')
                if next_page_token and page_num < max_pages - 1:
                    params['pagetoken'] = next_page_token 
                    params.pop('query', None) 
                    params.pop('type', None)
                    params.pop('region', None) # Also remove region if it was added for pagetoken use
                    print(f"ℹ️ next_page_token found. Waiting briefly before fetching next page...")
                    time.sleep(2)
                else:
                    if not next_page_token: print("ℹ️ No next_page_token found. Ending pagination.")
                    elif page_num >= max_pages -1: print(f"ℹ️ Reached max_pages ({max_pages}). Ending pagination.")
                    break 
            
            elif places_data.get("status") == "ZERO_RESULTS":
                print(f"✅ Places API (Text Search) returned ZERO_RESULTS for page {page_num + 1} with current query.")
                break 
            else:
                print(f"⚠️ Places API (Text Search) returned status: {places_data.get('status')} on page {page_num + 1}")
                if places_data.get("error_message"): print(f"   Error message: {places_data.get('error_message')}")
                break 
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error calling Google Places API (Text Search) on page {page_num + 1}: {e}")
            break 
        except json.JSONDecodeError:
            print(f"❌ Error decoding JSON response from Places API (Text Search) on page {page_num + 1}.")
            break 
            
    count_before_deduplication = len(all_places)
    print(f"\nℹ️ Total items collected before deduplication: {count_before_deduplication}")

    unique_places_dict = {place['place_id']: place for place in all_places if place.get('place_id')}
    final_places_list = list(unique_places_dict.values())
    
    count_after_deduplication = len(final_places_list)
    print(f"✅ Total unique operational establishments found after deduplication by Place ID: {count_after_deduplication}")

    items_removed_count = count_before_deduplication - count_after_deduplication
    print(f"ℹ️ Number of duplicate items removed: {items_removed_count}")

    if not final_places_list:
        print("No operational establishments found by Google Places API after deduplication.")
    # else: # Keep console print minimal if saving to file
        # print("\n--- Unique Results from Google Places API (After Deduplication by Place ID) ---") 
        # for i, place in enumerate(final_places_list):
        #     print(f"  {i+1}. Name: {place.get('name')}, Place ID: {place.get('place_id')}, Address: {place.get('address')}, Types: {place.get('types')}") 
    
    # File saving logic
    file_output_path = "google_places_output.txt" # Renamed for clarity
    if final_places_list or count_before_deduplication > 0 : 
        with open(file_output_path, "w", encoding="utf-8") as f: 
            f.write(f"Search City: {city_name}\n")
            f.write(f"Search Country: {country_filter if country_filter else 'Not specified'}\n")
            f.write(f"Search Type: {type_}\n")
            f.write(f"Effective Text Query: {text_query}\n")
            f.write(f"Google API Type Parameter: {google_api_type_param if google_api_type_param else 'None'}\n\n")
            f.write(f"Total items collected before deduplication: {count_before_deduplication}\n")
            f.write(f"Total unique operational establishments found after deduplication: {count_after_deduplication}\n")
            f.write(f"Number of duplicate items removed: {items_removed_count}\n\n")
            if final_places_list:
                f.write("--- Unique Results from Google Places API (Deduplicated by Place ID) ---\n")
                for i, place in enumerate(final_places_list):
                    f.write(f"  {i+1}. Name: {place.get('name')}\n")
                    f.write(f"     Place ID: {place.get('place_id')}\n")
                    f.write(f"     Address: {place.get('address')}\n")
                    f.write(f"     Types: {place.get('types')}\n")
                    f.write(f"     Rating: {place.get('rating')}\n")
                    f.write(f"     User Ratings Total: {place.get('user_ratings_total')}\n")
                    f.write(f"     Business Status: {place.get('business_status')}\n\n")
            else:
                f.write("No operational establishments to list after deduplication.\n")
        print(f"✅ Google Places API results saved to {file_output_path}")
    else: 
        with open(file_output_path, "w", encoding="utf-8") as f:
            f.write(f"Search City: {city_name}\n")
            f.write(f"Search Country: {country_filter if country_filter else 'Not specified'}\n")
            f.write(f"Search Type: {type_}\n")
            f.write(f"Effective Text Query: {text_query}\n")
            f.write(f"Google API Type Parameter: {google_api_type_param if google_api_type_param else 'None'}\n\n")
            f.write("No operational establishments found by Google Places API.\n")
        print(f"✅ No results to save. {file_output_path} created with no results message.")
    
    return final_places_list

# --- get_gemini_description function remains as modified in the previous step ---
def get_gemini_description(establishments_list, city_name, api_key, type_): # country_context can be added if needed by Gemini
    if not api_key:
        print("Gemini API key is missing. Cannot generate description.")
        return "Error: Gemini API key missing."

    search_context_info = "The initial search aimed to identify gluten-free options." 

    if establishments_list:
        establishment_details_for_prompt = []
        for r_idx, r_val in enumerate(establishments_list):
            google_types_list = r_val.get('types', [])
            if not isinstance(google_types_list, list):
                google_types_list = []
            types_str = ", ".join(google_types_list)
            detail = (f"Name: {r_val['name']}, Google Types: [{types_str}]")
            establishment_details_for_prompt.append(detail)

        establishment_block_for_gemini = "\n".join([f"- {detail}" for detail in establishment_details_for_prompt])
        
        type_filtering_instructions = ""
        # --- Instructions as defined in previous response ---
        if type_ == 'restaurants':
            type_filtering_instructions = (
                "The user is looking for 'restaurants'.\n"
                "An establishment is a match if its Google Types array primarily indicates it's a restaurant.\n"
                "- Strongest match: Google Types includes 'restaurant'.\n"
                "- Acceptable: If 'restaurant' is present, it's okay if types also include 'cafe', 'bar', or 'food'.\n"
                "- Caution: If Google Types includes 'bakery' but NOT 'restaurant', it is likely NOT a restaurant for this list.\n"
                "- Fallback: If 'restaurant' is not in Google Types, consider the establishment's 'Name'. If the name clearly indicates a full-service restaurant, then it can be included.\n"
                "- Regional Language: Also, be aware that the establishment's name might use regional language equivalents for 'restaurant' (e.g., 'Gasthaus', 'Wirtshaus', 'Pizzeria', 'Trattoria', 'Restaurante') or other terms strongly indicating a full-service dining place. Consider these as positive indicators for classifying it as a restaurant, especially if Google Types are ambiguous.\n"
                "- Exclude: Do not include establishments that are solely bakeries, dedicated cafes (unless they operate like a full restaurant), or general food stores unless they fit the criteria above."
            )
        elif type_ == 'cafes':
            type_filtering_instructions = (
                "The user is looking for 'cafes'.\n"
                "An establishment is a match if its Google Types array primarily indicates it's a cafe.\n"
                "- Strongest match: Google Types includes 'cafe'.\n"
                "- Acceptable: If 'cafe' is present, it's okay if types also include 'restaurant', 'bakery', or 'food'.\n"
                "- Also consider: If 'cafe' is absent, but Google Types includes 'bakery' AND the establishment's 'Name' suggests a cafe setting, it can be included.\n"
                "- Fallback: If 'cafe' is not in Google Types, but the 'Name' or other types (like 'coffee_shop', 'tea_room') strongly indicate a primary cafe function, it can be included.\n"
                "- Regional Language: Be aware that the establishment's name might use regional language equivalents for 'cafe' (e.g., 'Kaffeehaus', 'Konditorei' when it offers cafe-style service) or terms indicating coffee/tea service. These can be strong positive indicators.\n"
                "- Exclude: Do not include full-service formal restaurants that do not have a clear cafe component, or standalone bakeries/stores with no cafe service."
            )
        elif type_ == 'bakery':
            type_filtering_instructions = (
                "The user is looking for 'bakery' establishments.\n"
                "An establishment is a match if its Google Types array indicates it's primarily a bakery.\n"
                "- Strongest match: Google Types includes 'bakery'.\n"
                "- Acceptable and Common: If 'bakery' is present, it is perfectly fine and expected if its Google Types also include 'cafe', 'store', or 'food'.\n"
                "- Regional Language: Be aware that the establishment's name might use regional language equivalents for 'bakery' (e.g., 'Bäckerei', 'boulangerie', 'panadería'). Consider these as strong positive indicators for classifying it as a bakery.\n"
                "- Exclude: If 'bakery' is NOT in Google Types, do not include the establishment unless other information provided (like an explicit '100% bakery' in the name or strong regional language indicators) makes it absolutely certain. Prioritize the 'bakery' type tag."
            )
        else:
            type_filtering_instructions = "Please identify relevant establishments based on general gluten-free criteria."

        prompt = (
            f"You are an expert assistant helping users find specific types of gluten-free establishments in {city_name}. {search_context_info}\n" # City name is still useful for general context for Gemini
            # If you pass country_context to this function, you could add: (Country: {country_context})
            f"The user has specifically requested establishments of type: '{type_}'.\n\n"
            f"Here is a list of potential establishments. Each item includes its 'Name' and its 'Google Types' array:\n"
            f"{establishment_block_for_gemini}\n\n"
            f"Your task is to carefully review this list and apply the following filtering rules to identify establishments that best match the user's request for '{type_}':\n"
            f"--- Filtering Rules for '{type_}' ---\n"
            f"{type_filtering_instructions}\n"
            f"--- End of Filtering Rules ---\n\n"
            f"After applying these rules, present ONLY THE NAMES and addresses of the matching establishments as a simple numbered list. For example:\n"
            f"1. [Name of Establishment 1]\n"
            f"2. [Name of Establishment 2]\n"
            f"DO NOT include any other information in your list output, such as Google Types, or any introductory/concluding remarks, explanations, or advisory notes.\n"
            f"If, after applying the filtering rules, no establishments from the provided list match the user's request for '{type_}', return ONLY the message: 'No {type_} found matching your criteria in {city_name}.'"
        )
    else: 
        prompt = (
            f"You are an assistant helping find gluten-free dining.\n"
            f"The user is looking for '{type_}' in {city_name}.\n"
            f"The initial search by Google Places API found no establishments.\n"
            f"Please return ONLY the message: 'No {type_} found matching your criteria in {city_name}.' Do not add any other text."
        )

    print(f"\n🤖 Asking Gemini for type '{type_}' with detailed filtering instructions...")
    gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "top_p": 0.95, "max_output_tokens": 2000 }
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(gemini_api_url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        gemini_data = response.json()
        if gemini_data.get("candidates") and gemini_data["candidates"][0].get("content") and \
           gemini_data["candidates"][0]["content"].get("parts") and \
           gemini_data["candidates"][0]["content"]["parts"][0].get("text"):
            generated_text = gemini_data["candidates"][0]["content"]["parts"][0].get("text")
            print("✅ Gemini provided a response.")
            return generated_text.strip()
        elif gemini_data.get("promptFeedback") and gemini_data["promptFeedback"].get("blockReason"):
            reason = gemini_data["promptFeedback"]["blockReason"]
            safety_ratings = gemini_data["promptFeedback"].get("safetyRatings", [])
            print(f"⚠️ Gemini API blocked the prompt. Reason: {reason}. SafetyRatings: {safety_ratings}")
            return f"Gemini API blocked the prompt (Reason: {reason}). Please refine your search or contact support if this persists."
        else:
            print(f"⚠️ Gemini API returned an unexpected response structure for {type_} in {city_name}.")
            return f"Error: Gemini returned an unexpected response for {city_name} ({type_})."
    except requests.exceptions.Timeout:
        print(f"❌ Timeout error calling Gemini API for {type_} in {city_name}.")
        return f"Error: The request to Gemini API timed out for {city_name} ({type_}). Please try again."
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Gemini API for {type_} in {city_name}: {e}")
        return f"Error: Could not connect to Gemini API for {city_name} ({type_})."
    except json.JSONDecodeError:
        print(f"❌ Error decoding JSON response from Gemini API for {type_} in {city_name}.")
        return f"Error: Could not decode Gemini's response for {city_name} ({type_})."

# --- Main Execution (for testing this file directly) ---
if __name__ == "__main__":
    if not GOOGLE_PLACES_API_KEY or not GEMINI_API_KEY:
        print("\nAPI keys missing. Please set them in .env or directly for testing.")
    else:
        target_city = input("Enter city: ").strip()
        target_country = input("Enter country (e.g., Germany, US - leave blank if not needed): ").strip()
        
        valid_types = ['restaurants', 'cafes', 'bakery']
        test_type_input_prompt = f"Enter type ({', '.join(valid_types)}, default: restaurants): "
        selected_test_type = input(test_type_input_prompt).lower().strip() or 'restaurants'

        if selected_test_type not in valid_types:
            print(f"Invalid type. Defaulting to 'restaurants'.")
            selected_test_type = 'restaurants'

        if target_city:
            print(f"\n--- Test: City='{target_city}', Country='{target_country if target_country else 'N/A'}', Type='{selected_test_type}' ---")
            
            places_from_google = find_gluten_free_restaurants_places_api(
                target_city,
                GOOGLE_PLACES_API_KEY,
                type_=selected_test_type,
                country_filter=target_country if target_country else None # Pass country or None
            )

            if places_from_google is not None:
                print(f"\n--- Calling Gemini with {len(places_from_google)} places ---")
                gemini_output = get_gemini_description(
                    places_from_google,
                    target_city, # City name still useful for Gemini's general context
                    GEMINI_API_KEY,
                    type_=selected_test_type
                    # country_context=target_country if target_country else None # Optional: pass to Gemini if its prompt is updated
                )
                print("\n--- Gemini's Output ---")
                print(gemini_output)
            else:
                print("\nPlaces API returned None. Skipping Gemini.")
        else:
            print("No city entered.")
    print("\n--- Script Test Finished ---")