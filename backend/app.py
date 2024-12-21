from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper.linkedin_scraper import scrape_linkedin_profiles, scrape_comments_from_post
from ai.query_processor import process_query
from database.firebase_client import save_to_firebase
from scraper.utils import export_to_csv, ensure_gdpr_compliance  # Fixed import path
import logging

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return "Welcome to LinkedIn Scraper API!"

@app.route('/search', methods=['POST'])
def search_profiles():
    """
    Endpoint to process user query and fetch relevant LinkedIn profiles.
    """
    try:
        data = request.json
        query = data.get('query')
        filters = data.get('filters', {})
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # AI Processing
        processed_query = process_query(query)
        
        # LinkedIn Scraping
        profiles = scrape_linkedin_profiles(processed_query, filters)
        
        # Apply GDPR compliance
        compliant_profiles = [ensure_gdpr_compliance(profile) for profile in profiles]
        
        # Save to Firebase
        save_to_firebase(compliant_profiles)
        
        # Export to CSV if requested
        if data.get('export_csv'):
            export_to_csv(compliant_profiles, 'linkedin_profiles.csv')
        
        return jsonify({'profiles': compliant_profiles})
        
    except Exception as e:
        logger.error(f"Error in search_profiles: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/comments', methods=['POST'])
def scrape_comments():
    """
    Endpoint to scrape LinkedIn comments.
    """
    try:
        data = request.json
        url = data.get('url')
        cookies = data.get('cookies')
        
        if not url or not cookies:
            return jsonify({'error': 'URL and cookies are required'}), 400

        # Call the scraper function
        comments = scrape_comments_from_post(url, cookies)
        
        return jsonify({'comments': comments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)