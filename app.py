from flask import Flask, render_template, jsonify, request
import google.generativeai as genai
import os
import dotenv
import json 
import traceback 

from find_places import find_gluten_free_restaurants_places_api, get_gemini_description

dotenv.load_dotenv()

app = Flask(__name__)

GEMINI_API_KEY_FROM_ENV = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY_FROM_ENV:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY_FROM_ENV)
gemini_model = genai.GenerativeModel(model_name='gemini-2.0-flash')

GOOGLE_PLACES_API_KEY_FROM_ENV = os.getenv('GOOGLE_PLACES_API_KEY')
if not GOOGLE_PLACES_API_KEY_FROM_ENV:
    raise ValueError("GOOGLE_PLACES_API_KEY not found in environment variables.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/news')
def news():
    example_news_articles = [
        {"title": "Example News 1", "content": "Content for news 1...", "date": "2025-05-21"},
        {"title": "Example News 2", "content": "Content for news 2...", "date": "2025-05-20"}
    ]
    return render_template('news.html', articles=example_news_articles)

@app.route('/apps')
def apps():
    return render_template('apps.html')

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

@app.route('/check-product', methods=['POST'])
def check_product():
    data = request.get_json()
    if not data or 'barcode' not in data:
        return jsonify({"error": "Barcode not provided"}), 400
    barcode = data.get('barcode')
    
    try:
        current_generation_config = genai.types.GenerationConfig(temperature=0.2) 
        prompt = f"""Given this product barcode: {barcode}
        1. Is this product gluten-free? Yes/No/Cannot Determine
        2. What is the product name? (If known)
        3. What is the brand? (If known)
        4. Provide a brief suggestion for gluten-free alternatives if not gluten-free or if status is 'Cannot Determine'.
        
        Respond ONLY in JSON format like this:
        {{
            "isGlutenFree": "Yes" | "No" | "Cannot Determine",
            "productName": "string or null",
            "brand": "string or null",
            "suggestion": "string or null"
        }}
        If you cannot find information for the barcode, respond with "Cannot Determine" for isGlutenFree and null for other fields.
        """
        
        response = gemini_model.generate_content(prompt, generation_config=current_generation_config)
        result_text = response.text
        
        try:
            if result_text.strip().startswith("```json"):
                result_text = result_text.strip()[7:-3].strip()
            elif result_text.strip().startswith("```"):
                 result_text = result_text.strip()[3:-3].strip()

            result_dict = json.loads(result_text)
            return jsonify(result_dict)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError from Gemini response in /check-product: {e}")
            print(f"Problematic Gemini response text: {result_text}")
            return jsonify({
                "isGlutenFree": "Cannot Determine",
                "productName": None,
                "brand": None,
                "suggestion": "Could not reliably determine product status from barcode. Please check ingredients manually."
            }), 200 
    except Exception as e:
        print(f"Error in /check-product: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/get-news')
def get_news_api(): 
    try:
        example_news_articles = [
            {"id": 1, "title": "Understanding Gluten Sensitivity", "summary": "Learn the difference...", "date": "2025-05-20"},
            {"id": 2, "title": "New GF Products on the Market", "summary": "Discover exciting new options...", "date": "2025-05-18"}
        ]
        return jsonify({"articles": example_news_articles})
    except Exception as e:
        print(f"Error in /get-news: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get-restaurants') # Endpoint name can remain, or be changed to /get-establishments
def get_restaurants_route():
    try:
        city = request.args.get('city')
        # The 'type_' from frontend will now be 'restaurants_cafes' or 'bakeries'
        type_ = request.args.get('type', 'restaurants_cafes') # Default to restaurants_cafes
        
        if not city:
            return jsonify({"error": "Please provide a city name"}), 400
            
        print(f"Received request for city: {city}, type: {type_}")

        places_list = find_gluten_free_restaurants_places_api(
            city, 
            GOOGLE_PLACES_API_KEY_FROM_ENV,
            type_=type_ 
        )
        
        if not places_list: 
            print(f"No establishments found for {type_} in {city} by Google Places API.")
            description = get_gemini_description(
                [], 
                city, 
                GEMINI_API_KEY_FROM_ENV,
                type_=type_
            )
            return jsonify({"result": description, "raw_data": []})

        # REMOVED: Sorting by review count
        # places_list.sort(key=get_review_count, reverse=True) 
        # print(f"ℹ️ Places list (not sorted by review count). Top {min(len(places_list), 20)} will be sent to Gemini.")
        print(f"ℹ️ Found {len(places_list)} places. Up to {min(len(places_list), 20)} will be sent to Gemini as is (order from Places API).")
        
        description = get_gemini_description(
            places_list, # Pass the unsorted list (or as Google returned it)
            city, 
            GEMINI_API_KEY_FROM_ENV,
            type_=type_
        )
        
        if not description or description.strip() == "" or description.startswith("Error:") or "Gemini API blocked" in description:
            print(f"\n❌ Gemini returned an empty or error description for city: {city}, type: {type_}. Description: '{description}'")
            fallback_message = f"Could not retrieve a detailed summary for {type_} in {city}. Please try again."
            if "No " in description and " found matching the criteria" in description:
                 fallback_message = description
            return jsonify({"result": fallback_message, "raw_data": places_list if places_list else []})
            
        return jsonify({
            "result": description,
            "raw_data": places_list # Send the original list from Places API for potential frontend use
        })
    except Exception as e:
        print(f"Critical error in /get-restaurants route: {e}")
        traceback.print_exc()
        return jsonify({"error": "An unexpected server error occurred. Please try again later."}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5007))
    flask_debug_env = os.environ.get('FLASK_DEBUG', 'True') 
    debug_mode = flask_debug_env.lower() not in ['false', '0', 'no']
    
    print(f"Starting Flask app on http://0.0.0.0:{port}/ with debug mode: {debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
