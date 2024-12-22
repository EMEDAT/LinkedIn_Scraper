from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set the OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def process_query(query):
    """
    Interpret natural language queries and convert them into LinkedIn search parameters.
    Returns a dictionary of search parameters.
    """
    system_prompt = """
    Convert natural language queries into LinkedIn search parameters. Return ONLY a JSON object with these keys:
    - keywords: Main search terms
    - title: Job titles or positions
    - company: Company names
    - location: Geographic locations
    - industry: Industry sectors
    
    Example Input: "Find marketing directors in California working at tech startups"
    Example Output: {
        "title": "Marketing Director",
        "location": "California",
        "industry": "Technology",
        "company": "",
        "keywords": "marketing director"
    }
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        max_tokens=150,
        temperature=0.3
    )
    
    # Parse the response into a dictionary
    import json
    try:
        # Get the response content and parse it as JSON
        processed_query = response.choices[0].message.content.strip()
        return json.loads(processed_query)
    except json.JSONDecodeError:
        # If parsing fails, return a basic structured query
        return {
            "keywords": query,
            "title": "",
            "location": "",
            "industry": "",
            "company": ""
        }

def build_linkedin_url(query_params):
    """
    Convert processed query parameters into a LinkedIn search URL.
    """
    base_url = "https://www.linkedin.com/search/results/people/?"
    params = []
    
    if query_params.get("keywords"):
        params.append(f"keywords={query_params['keywords']}")
    if query_params.get("title"):
        params.append(f"title={query_params['title']}")
    if query_params.get("location"):
        params.append(f"location={query_params['location']}")
    if query_params.get("industry"):
        params.append(f"industry={query_params['industry']}")
    if query_params.get("company"):
        params.append(f"company={query_params['company']}")
    
    return base_url + "&".join(params)

def test_query():
    """
    Test function to verify query processing.
    """
    test_queries = [
        "Find software engineers in San Francisco",
        "Marketing directors at Fortune 500 companies in New York",
        "Data scientists with ML experience in Seattle"
    ]
    
    for query in test_queries:
        print(f"\nOriginal query: {query}")
        result = process_query(query)
        print(f"Processed query: {result}")