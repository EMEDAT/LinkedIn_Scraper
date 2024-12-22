import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time
import random
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Helper Functions
def init_selenium_driver() -> webdriver.Chrome:
    """
    Initialize Selenium WebDriver with options and WebDriver Manager.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def login_with_cookie(driver, cookie):
    """
    Log in to LinkedIn using cookies.
    """
    driver.get("https://www.linkedin.com/")
    driver.add_cookie({"name": "li_at", "value": cookie})
    driver.refresh()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "global-nav__primary-link"))
    )

def build_linkedin_url(query_params: Dict) -> str:
    """
    Build LinkedIn search URL from query parameters.
    """
    base_url = "https://www.linkedin.com/search/results/people/?"
    params = [f"{key}={requests.utils.quote(value)}" for key, value in query_params.items() if value]
    return base_url + "&".join(params)

def scrape_linkedin_profiles(query_params: Dict, cookie: str) -> List[Dict]:
    """
    Scrape LinkedIn profiles using Selenium.
    """
    driver = init_selenium_driver()
    try:
        login_with_cookie(driver, cookie)
        search_url = build_linkedin_url(query_params)
        driver.get(search_url)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "reusable-search__result-container"))
        )

        profiles = []
        results = driver.find_elements(By.CLASS_NAME, "reusable-search__result-container")
        for result in results:
            try:
                profiles.append({
                    "name": result.find_element(By.CSS_SELECTOR, ".actor-name").text,
                    "title": result.find_element(By.CSS_SELECTOR, ".subline-level-1").text,
                    "location": result.find_element(By.CSS_SELECTOR, ".subline-level-2").text,
                    "profile_url": result.find_element(By.CSS_SELECTOR, ".app-aware-link").get_attribute("href")
                })
            except Exception as e:
                logger.warning(f"Error parsing profile: {e}")

        return profiles
    finally:
        driver.quit()

def scrape_comments_from_post(post_url: str, cookie: str) -> List[Dict]:
    """
    Scrape comments from a LinkedIn post.
    """
    driver = init_selenium_driver()
    try:
        login_with_cookie(driver, cookie)
        driver.get(post_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "comments-comment-item"))
        )

        comments = []
        results = driver.find_elements(By.CLASS_NAME, "comments-comment-item")
        for comment in results:
            try:
                comments.append({
                    "name": comment.find_element(By.CLASS_NAME, "comments-post-meta__name-text").text,
                    "comment": comment.find_element(By.CLASS_NAME, "comments-comment-item__main-content").text,
                    "timestamp": comment.find_element(By.CLASS_NAME, "comments-comment-item__timestamp").text,
                })
            except Exception as e:
                logger.warning(f"Error parsing comment: {e}")

        return comments
    finally:
        driver.quit()

# API Endpoints
@app.route('/search', methods=['POST'])
def search_profiles():
    try:
        data = request.json
        query = data.get('query')
        cookie = data.get('cookie')

        if not query or not cookie:
            return jsonify({'error': 'Query and LinkedIn cookie are required'}), 400

        profiles = scrape_linkedin_profiles(query, cookie)
        return jsonify({
            'status': 'success',
            'profile_count': len(profiles),
            'profiles': profiles
        })
    except Exception as e:
        logger.error(f"Error in /search: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/comments', methods=['POST'])
def fetch_comments():
    try:
        data = request.json
        post_url = data.get('post_url')
        cookie = data.get('cookie')

        if not post_url or not cookie:
            return jsonify({'error': 'Post URL and LinkedIn cookie are required'}), 400

        comments = scrape_comments_from_post(post_url, cookie)
        return jsonify({
            'status': 'success',
            'comment_count': len(comments),
            'comments': comments
        })
    except Exception as e:
        logger.error(f"Error in /comments: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)