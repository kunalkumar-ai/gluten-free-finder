from flask import Flask, render_template, jsonify, request
import google.generativeai as genai
import os
import dotenv
from colab_implementation import find_gluten_free_restaurants_places_api, get_gemini_description
from news_data import news_articles

dotenv.load_dotenv()

app = Flask(__name__)

# Configure the API key
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("API key not found in environment variables. Make sure to set GEMINI_API_KEY in your .env file")

genai.configure(api_key=api_key)
generation_config = genai.types.GenerationConfig(temperature=0.2) # Example temperature value

#model = genai.GenerativeModel('gemini-2.0-flash')
model = genai.GenerativeModel(model_name='gemini-2.0-flash',
                                generation_config=generation_config)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/apps')
def apps():
    return render_template('apps.html')

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

@app.route('/check-product', methods=['POST'])
def check_product():
    data = request.get_json()
    barcode = data.get('barcode')
    
    # Use Gemini API to check if product is gluten-free
    try:
        # Example prompt - you might want to adjust this based on your needs
        prompt = f"""Given this product barcode: {barcode}
        1. Is this product gluten-free? Yes/No
        2. What is the product name?
        3. What is the brand?
        4. Provide a suggestion for gluten-free alternatives if not gluten-free.
        
        Respond in JSON format:
        {{
            "isGlutenFree": boolean,
            "productName": string,
            "brand": string,
            "suggestion": string
        }}
        """
        
        response = model.generate_content(prompt, generation_config)
        result = response.text
        
        # Parse the JSON response
        try:
            result_dict = json.loads(result)
            return jsonify(result_dict)
        except json.JSONDecodeError:
            return jsonify({
                "isGlutenFree": False,
                "productName": "Unknown",
                "brand": "Unknown",
                "suggestion": "Could not determine if product is gluten-free. Please check the ingredients manually."
            })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/get-news')
def get_news():
    try:
        # Return the static news articles
        return jsonify({"articles": news_articles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-restaurants')
def get_restaurants():
    try:
        # Get city from query parameter
        city = request.args.get('city')
        type_ = request.args.get('type', 'restaurants')  # Default to restaurants if type not specified
        
        if not city:
            return jsonify({"error": "Please provide a city name"}), 400
            
        # First try to find dedicated gluten-free restaurants
        restaurants = find_gluten_free_restaurants_places_api(city, os.getenv('GOOGLE_PLACES_API_KEY'), dedicated_only=True)
        
        if not restaurants:
            # If no dedicated restaurants found, try regular gluten-free search
            restaurants = find_gluten_free_restaurants_places_api(city, os.getenv('GOOGLE_PLACES_API_KEY'), dedicated_only=False)
            
        if not restaurants:
            return jsonify({"result": "No restaurants found matching the criteria"})
            
        # Get Gemini's formatted description
        description = get_gemini_description(restaurants, city, os.getenv('GEMINI_API_KEY'), searched_dedicated=True)
        
        return jsonify({
            "result": description,
            "raw_data": restaurants  # Include raw restaurant data for debugging
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5007))
    debug = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug)
