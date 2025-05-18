# Gluten-Free Restaurant Finder

A web application that helps find dedicated gluten-free restaurants and cafes in any city using the Gemini AI API.

## Deployment to Render

1. Create a Render account at https://render.com/
2. Connect your GitHub repository
3. Create a new Web Service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Environment Variables:
     - `GEMINI_API_KEY`: Your Gemini API key
     - `FLASK_DEBUG`: `False`
4. Deploy the application

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API key
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Access the app at http://localhost:5006
