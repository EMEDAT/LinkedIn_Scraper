import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
import random
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 3.0):
    """Decorator to implement rate limiting between requests"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(random.uniform(min_delay, max_delay))
            return func(*args, **kwargs)
        return wrapper
    return decorator

def build_linkedin_url(query_params: Dict) -> str:
    """
    Convert processed query parameters into a LinkedIn search URL.
    """
    base_url = "https://www.linkedin.com/search/results/people/?"
    params = []
    
    # Add debugging
    logger.info(f"Building URL with params: {query_params}")
    
    if query_params.get("keywords"):
        params.append(f"keywords={requests.utils.quote(query_params['keywords'])}")
    if query_params.get("title"):
        params.append(f"title={requests.utils.quote(query_params['title'])}")
    if query_params.get("location"):
        params.append(f"location={requests.utils.quote(query_params['location'])}")
    if query_params.get("industry"):
        params.append(f"industry={requests.utils.quote(query_params['industry'])}")
    if query_params.get("company"):
        params.append(f"company={requests.utils.quote(query_params['company'])}")
    
    final_url = base_url + "&".join(params)
    logger.info(f"Generated URL: {final_url}")
    return final_url


@rate_limit_decorator()
def scrape_linkedin_profiles(query_params: Dict, cookies: str = None, filters: Optional[Dict] = None) -> List[Dict]:
    """
    Scrape LinkedIn profiles based on structured query parameters.
    """
    search_url = build_linkedin_url(query_params)
    logger.info(f"Attempting to scrape URL: {search_url}")
    
    # Enhanced headers to better mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'Referer': 'https://www.linkedin.com/',
    }
    
    if cookies:
        # Parse the cookies string and set them properly
        headers['Cookie'] = cookies
        logger.info("Cookies added to headers")
    else:
        logger.warning("No cookies provided")

    try:
        session = requests.Session()
        response = session.get(search_url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response URL: {response.url}")  # Add this line to see if we're being redirected
        
        # Save the HTML response for debugging (temporary)
        with open('linkedin_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.info(f"Response content length: {len(response.text)}")
        
        # Debug HTML content
        if "challenge-form" in response.text:
            logger.error("LinkedIn is showing a challenge form - we need to handle captcha")
        if "sign-in" in response.text:
            logger.error("LinkedIn is redirecting to sign-in page")
            
        profiles = []
        results = soup.select('.reusable-search__result-container')
        logger.info(f"Found {len(results)} profile containers")
        
        for profile in results:
            try:
                name_elem = profile.select_one('.app-aware-link span[aria-hidden="true"]')
                if name_elem:
                    logger.info(f"Found profile: {name_elem.text.strip()}")
                    profile_data = {
                        'name': name_elem.text.strip(),
                        'title': profile.select_one('.entity-result__primary-subtitle').text.strip() if profile.select_one('.entity-result__primary-subtitle') else '',
                        'location': profile.select_one('.entity-result__secondary-subtitle').text.strip() if profile.select_one('.entity-result__secondary-subtitle') else '',
                        'url': f"https://linkedin.com{profile.select_one('.app-aware-link')['href']}" if profile.select_one('.app-aware-link') else '',
                        'collection_date': datetime.now().isoformat(),
                        'data_source': 'LinkedIn Public Profile'
                    }
                    profiles.append(profile_data)
            except AttributeError as e:
                logger.warning(f"Failed to parse profile: {str(e)}")
                continue
        
        if filters:
            profiles = apply_filters(profiles, filters)
            
        return remove_duplicates(profiles)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch LinkedIn profiles: {str(e)}")
        raise

@rate_limit_decorator()
def scrape_comments_from_post(url: str, cookies: str) -> List[Dict]:
    """
    Scrape comments from a LinkedIn post with improved error handling.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.linkedin.com/',
        'Cookie': cookies
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = []

        # Updated selectors for comments
        for comment in soup.select('.comments-post-meta__name-text'):
            try:
                comment_data = {
                    'name': comment.text.strip(),
                    'comment': comment.find_next('.comments-comment-item__main-content').text.strip(),
                    'timestamp': comment.find_next('.comments-comment-item__timestamp').text.strip(),
                    'collection_date': datetime.now().isoformat(),
                    'data_source': 'LinkedIn Comment'
                }
                comments.append(comment_data)
            except AttributeError as e:
                logger.warning(f"Failed to parse comment: {str(e)}")
                continue

        return comments
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch LinkedIn comments: {str(e)}")
        raise

def apply_filters(profiles: List[Dict], filters: Dict) -> List[Dict]:
    """Apply filters to the scraped profiles"""
    filtered_profiles = []
    for profile in profiles:
        matches_all_filters = True
        for key, value in filters.items():
            profile_value = profile.get(key, '').lower()
            filter_value = str(value).lower()
            
            if not (filter_value in profile_value):
                matches_all_filters = False
                break
                
        if matches_all_filters:
            filtered_profiles.append(profile)
            
    return filtered_profiles

def remove_duplicates(profiles: List[Dict]) -> List[Dict]:
    """Remove duplicate profiles based on URL and name"""
    seen = set()
    unique_profiles = []
    
    for profile in profiles:
        profile_key = (profile.get('url', ''), profile.get('name', ''))
        if profile_key not in seen:
            seen.add(profile_key)
            unique_profiles.append(profile)
    
    return unique_profiles