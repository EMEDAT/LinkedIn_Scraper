LinkedIn Scraper
A Flask-based LinkedIn scraper to extract publicly available profile, company, and comment data. Uses BeautifulSoup for scraping and Firebase for data storage.

Table of Contents
Features
Installation
Setup
Usage
Profile Scraping
Company Scraping
Comment Scraping
Exporting Data
API Documentation
Endpoints
Compliance
Features
Scrape LinkedIn profiles: Name, title, location, and more.
Scrape company details: Specialties, size, and more.
Extract comments from LinkedIn posts using post URLs and cookies.
Store data in Firebase or export as CSV.
Validate email addresses and apply GDPR compliance measures.
Installation
Clone the repository and install the required dependencies:

bash
Copy code
git clone https://github.com/your-repo/LinkedIn_Scraper.git
cd LinkedIn_Scraper/backend
pip install -r requirements.txt
Setup
Create a .env file and add the following variables:
plaintext
Copy code
OPENAI_API_KEY=your_openai_api_key
FIREBASE_CREDENTIALS_PATH=path_to_firebase_key.json
Configure your Firebase project and download the firebase_key.json.
Usage
Profile Scraping
To scrape a LinkedIn profile:

python
Copy code
import requests

url = "http://localhost:5000/search"
payload = {
    "query": "Find software engineers in San Francisco",
    "filters": {"location": "San Francisco"}
}
response = requests.post(url, json=payload)
print(response.json())
Company Scraping
To fetch company details:

python
Copy code
payload = {"query": "Find tech companies in California"}
response = requests.post(url, json=payload)
Comment Scraping
To scrape comments:

python
Copy code
payload = {
    "url": "https://www.linkedin.com/posts/example-post-url",
    "cookies": "your_linkedin_cookies"
}
response = requests.post("http://localhost:5000/comments", json=payload)
Exporting Data
Save results to a CSV file:

python
Copy code
payload = {"export_csv": True}
response = requests.post(url, json=payload)
API Documentation
Endpoints
POST /search
Process a query and fetch LinkedIn profiles.

Request:

json
Copy code
{
    "query": "Find marketing directors in New York",
    "filters": {"industry": "Technology"}
}
Response:

json
Copy code
{
    "profiles": [
        {
            "name": "Jane Doe",
            "title": "Marketing Director",
            "company": "TechCorp",
            "location": "New York",
            "url": "https://www.linkedin.com/in/jane-doe"
        }
    ]
}
POST /comments
Scrape comments from a LinkedIn post.

Compliance
This scraper adheres to GDPR and CCPA guidelines:

Data is stored securely with limited retention periods.
Email addresses are hashed for privacy.