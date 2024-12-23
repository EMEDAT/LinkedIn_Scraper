from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper.linkedin_profile_scraper import scrape_linkedin_profiles
from scraper.linkedin_comment_scraper import scrape_comments_from_post
from ai.query_processor import process_query
from database.firebase_client import save_to_firebase  # Replace with your database implementation
from scraper.utils import export_to_csv, ensure_gdpr_compliance
import logging
from werkzeug.serving import WSGIRequestHandler
from functools import wraps
import time

# Increase the timeout for the WSGI server
WSGIRequestHandler.timeout = 300  # 5 minutes timeout

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def handle_timeout(timeout_seconds):
    """Decorator to handle timeouts for routes"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            while time.time() - start_time < timeout_seconds:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    if "timeout" in str(e).lower():
                        if time.time() - start_time < timeout_seconds:
                            logger.warning("Request timed out, retrying...")
                            time.sleep(2)  # Wait before retry
                            continue
                    logger.error(f"Error in route: {str(e)}")
                    return jsonify({
                        'status': 'error',
                        'error': str(e),
                        'message': 'An error occurred while processing your request'
                    }), 500
            return jsonify({
                'status': 'error',
                'error': 'Operation timed out',
                'message': 'The request took too long to complete'
            }), 504
        return wrapper
    return decorator

@app.route('/')
def home():
    return jsonify({
        'status': 'success',
        'message': 'Welcome to LinkedIn Scraper API!',
        'version': '1.0'
    })

@app.route('/search', methods=['POST'])
@handle_timeout(300)  # 5 minutes timeout
def search_profiles():
    """
    Endpoint to process user query and fetch relevant LinkedIn profiles.
    """
    try:
        data = request.json
        logger.info(f"Received search request with data: {data}")

        # Validate required fields
        query = data.get('query')
        filters = data.get('filters', {})
        cookies = data.get('cookies')
        
        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Missing required field',
                'message': 'Query is required'
            }), 400
        if not cookies:
            return jsonify({
                'status': 'error',
                'error': 'Missing required field',
                'message': 'LinkedIn cookies are required'
            }), 400
        
        # AI Processing
        logger.info(f"Processing query: {query}")
        query_params = process_query(query)
        logger.info(f"Processed query params: {query_params}")
        
        # LinkedIn Scraping with progress tracking
        logger.info("Starting LinkedIn scraping")
        profiles = scrape_linkedin_profiles(query_params, cookies, filters)
        logger.info(f"Found {len(profiles)} profiles")
        
        if not profiles:
            return jsonify({
                'status': 'warning',
                'message': 'No profiles found matching your criteria',
                'profile_count': 0,
                'profiles': []
            })
        
        # Apply GDPR compliance
        compliant_profiles = [ensure_gdpr_compliance(profile) for profile in profiles]
        
        # Save to Firebase
        try:
            save_to_firebase(compliant_profiles)
            logger.info("Successfully saved profiles to Firebase")
        except Exception as e:
            logger.error(f"Failed to save to Firebase: {str(e)}")
            # Continue execution even if Firebase save fails
        
        # Export to CSV if requested
        if data.get('export_csv'):
            try:
                filename = f'linkedin_profiles_{int(time.time())}.csv'
                export_to_csv(compliant_profiles, filename)
                logger.info(f"Successfully exported profiles to {filename}")
            except Exception as e:
                logger.error(f"Failed to export CSV: {str(e)}")
                # Continue execution even if CSV export fails
        
        return jsonify({
            'status': 'success',
            'message': 'Successfully retrieved profiles',
            'profile_count': len(compliant_profiles),
            'profiles': compliant_profiles,
            'query_params': query_params  # Return processed query params for reference
        })
        
    except Exception as e:
        logger.error(f"Error in search_profiles: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'An error occurred while processing your request'
        }), 500


@app.route('/comments', methods=['POST'])
@handle_timeout(420)  # 7 minutes timeout
def scrape_comments():
    """
    Endpoint to scrape LinkedIn comments with improved error handling.
    """
    try:
        data = request.json
        url = data.get('url')
        cookies = data.get('cookies')
        
        # Validate input
        if not url or not cookies:
            return jsonify({
                'status': 'error',
                'error': 'Missing required fields',
                'message': 'URL and cookies are required'
            }), 400

        # Validate URL format
        if not url.startswith('https://www.linkedin.com/'):
            return jsonify({
                'status': 'error',
                'error': 'Invalid URL',
                'message': 'Please provide a valid LinkedIn URL'
            }), 400

        # Call the scraper function
        logger.info(f"Starting comment scraping for URL: {url}")
        comments = scrape_comments_from_post(url, cookies)
        
        if not comments:
            return jsonify({
                'status': 'warning',
                'message': 'No comments found for this post',
                'comment_count': 0,
                'comments': []
            })
        
        return jsonify({
            'status': 'success',
            'message': 'Successfully retrieved comments',
            'comment_count': len(comments),
            'comments': comments,
            'url': url
        })

    except Exception as e:
        logger.error(f"Error in scrape_comments: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'An error occurred while scraping comments'
        }), 500


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'status': 'error',
        'error': 'Not Found',
        'message': 'The requested URL was not found on the server'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    app.run(debug=True)