import google.generativeai as genai
import os

# Replace with your actual Gemini API key
API_KEY = "AIzaSyDUn4oYyJv16JWyvzumqljzHaLPxkbBRtQ"

# Configure the API key
genai.configure(api_key=API_KEY)

try:
    # Select the Gemini 2.0 Flash model
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Simple text generation prompt
    prompt = "Find me 4 gluten-free restaurants in Helsinki. Check the reviews. Return only the restaurants' names and addresses, contact details. Present the results in a Markdown table with columns for Restaurant Name, Address, Contact Details. Do not use bold formatting."

    # Generate content
    response = model.generate_content(prompt)
    #print("API Key is likely working with gemini-2.0-flash!")
    print("Response for query:")
    print(response.text)

except Exception as e:
    print(f"There was an error testing the API key with gemini-2.0-flash: {e}")
    print("Please double-check your API key and network connection.")


from flask import Flask, render_template, jsonify
import google.generativeai as genai
import os
import dotenv

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
        # Define the prompt for Munich
        #prompt = """
        #Find me 4 gluten-free restaurants in Munich. Check the reviews. 
        #Return only the restaurants' names and addresses, contact details. 
        #Present the results in a Markdown table with columns for Restaurant Name, Address, Contact Details. 
        #Do not use bold formatting. Also tell me how did you find them? add this information the table.
        #"""
        prompt = """
        Find me 4 dedicated gluten-free restaurants and cafes in Munich.
        Return the restaurants' names, addresses, and contact details.
        Present the results as a Markdown table with columns: "Restaurant Name", "Address", "Contact Details", and "Dedicated Gluten-Free or Separate Menu".
        Ensure each row of the table contains information for a specific restaurant. Do not use bold formatting.
        """
        
        response = model.generate_content(prompt)
        return jsonify({"content": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5006)
