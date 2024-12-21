from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import json
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_query_processor() -> Optional[dict]:
    """
    Test function to verify query processing with OpenAI.
    Returns the processed query as a dictionary if successful, None if failed.
    """
    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not client.api_key:
            logger.error("OpenAI API key not found in environment variables")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        return None

    test_query = "Find LinkedIn profiles of software engineers in San Francisco"
    
    try:
        logger.info(f"Testing query: {test_query}")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
                Convert natural language queries into LinkedIn search parameters.
                Return ONLY a JSON object with these keys:
                - title: Job titles or positions
                - location: Geographic locations
                - keywords: Additional search terms
                - industry: Industry sector
                - company: Company name (if specified)
                
                Example Output:
                {
                    "title": "Software Engineer",
                    "location": "San Francisco",
                    "keywords": "engineer tech",
                    "industry": "Technology",
                    "company": ""
                }
                """},
                {"role": "user", "content": test_query}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        processed_query = response.choices[0].message.content.strip()
        
        # Try to parse the response as JSON
        try:
            query_dict = json.loads(processed_query)
            logger.info("Query processing successful:")
            logger.info(f"Original query: {test_query}")
            logger.info(f"Processed query: {json.dumps(query_dict, indent=2)}")
            return query_dict
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
            logger.error(f"Raw response: {processed_query}")
            return None
            
    except Exception as e:
        logger.error(f"Error during query processing: {str(e)}")
        return None

def run_test_suite():
    """
    Run a suite of tests with different query types
    """
    test_queries = [
        "Find software engineers in San Francisco",
        "Marketing directors at Fortune 500 companies in New York",
        "Data scientists with ML experience in Seattle",
        "Product managers at startups in Austin"
    ]
    
    results = []
    for query in test_queries:
        try:
            logger.info(f"\nTesting query: {query}")
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Convert natural language queries into LinkedIn search parameters as JSON."},
                    {"role": "user", "content": query}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            results.append({
                "original_query": query,
                "processed_result": result
            })
            logger.info(f"Processed result: {result}")
            
        except Exception as e:
            logger.error(f"Failed to process query '{query}': {str(e)}")
            results.append({
                "original_query": query,
                "error": str(e)
            })
    
    return results

if __name__ == "__main__":
    print("Testing single query processor...")
    result = test_query_processor()
    if result:
        print("\nSingle query test successful!")
    
    print("\nRunning test suite...")
    suite_results = run_test_suite()
    print("\nTest suite completed!")