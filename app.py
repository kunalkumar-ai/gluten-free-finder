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
