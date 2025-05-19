from flask import Flask, render_template, jsonify, request
import google.generativeai as genai
import os
import dotenv
from prompts import get_restaurants_prompt

dotenv.load_dotenv()

app = Flask(__name__)

# Configure the API key
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("API key not found in environment variables. Make sure to set GEMINI_API_KEY in your .env file")

genai.configure(api_key=api_key)
generation_config = genai.types.GenerationConfig(temperature=0.4) # Example temperature value

#model = genai.GenerativeModel('gemini-2.0-flash')
model = genai.GenerativeModel(model_name='gemini-2.0-flash',
                                generation_config=generation_config)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/get-news')
def get_news():
    try:
        # This is a placeholder - in a real application you would fetch actual news articles
        # For now, we'll return some sample data
        news_articles = [
            {
                "title": "New Gluten-Free Bakery Opens in Downtown",
                "date": "May 19, 2025",
                "content": "A new dedicated gluten-free bakery has opened its doors in downtown, offering a wide variety of breads, pastries, and custom orders."
            },
            {
                "title": "Gluten-Free Festival Returns This Weekend",
                "date": "May 18, 2025",
                "content": "The annual Gluten-Free Festival is back this weekend with over 50 vendors showcasing their gluten-free products and dishes."
            },
            {
                "title": "New Study Shows Benefits of Gluten-Free Diet",
                "date": "May 17, 2025",
                "content": "A recent study published in the Journal of Nutrition highlights the health benefits of maintaining a gluten-free diet for those with celiac disease."
            }
        ]
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
        
        # Get the prompt from prompts.py
        prompt = get_restaurants_prompt(city, type_)
        
        response = model.generate_content(prompt)
        return jsonify({"content": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5007))
    debug = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug)
