# utils/query_processor.py
from huggingface_hub import InferenceClient
import json
import os
from dotenv import load_dotenv

load_dotenv()

def preprocess_query(user_query: str):
    """
    Process user query using a Hugging Face model to improve retrieval.
    Uses free Hugging Face inference API.
    
    Returns:
        tuple: (processed_query, entities)
    """
    # Initialize the Hugging Face Inference client (no API key needed for free tier)
    client = InferenceClient(token=os.getenv("HUGGINGFACE_API_KEY"))
    
    # Using a smaller open model that's available for free inference
    model_id = "gpt2" 
    
    prompt = f"""
    Task: Improve this restaurant search query for database retrieval.
    
    Original query: "{user_query}"
    
    1. Rewrite the query to be more specific.
    2. Identify key entities (restaurants, dishes, cuisine types).
    3. List related terms that could improve search.
    
    Format your response as JSON with keys:
    - processed_query
    - entities
    - expansion_terms
    """
    
    try:
        # Use the Hugging Face text generation API
        response = client.text_generation(
            prompt,
            model=model_id,
            max_new_tokens=256,
            temperature=0.1
        )
        
        # Try to extract JSON from the response
        # The response might not be perfectly formatted JSON
        response_text = response.strip()
        
        # Find JSON-like content between braces
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                expanded_query = f"{user_query} {parsed.get('processed_query', '')} {' '.join(parsed.get('expansion_terms', []))}"
                return expanded_query, parsed.get('entities', {})
            except json.JSONDecodeError:
                pass
        
        # If JSON parsing fails, try rule-based extraction
        # Simple keyword extraction fallback
        keywords = extract_keywords_from_query(user_query)
        return f"{user_query} {' '.join(keywords)}", {}
        
    except Exception as e:
        print(f"Query preprocessing failed: {e}, using original query")
        return user_query, {}

def extract_keywords_from_query(query):
    """Simple keyword extraction fallback if the model fails"""
    # List of food-related terms to look for
    food_terms = ["spicy", "sweet", "sour", "vegetarian", "vegan", "non-veg", 
                 "appetizer", "main course", "dessert", "breakfast", "lunch", "dinner"]
    
    # List of cuisine types
    cuisines = ["indian", "chinese", "italian", "mexican", "thai", "japanese"]
    
    # Extract words that match our lists or are capitalized (potential restaurant/dish names)
    words = query.lower().split()
    extracted = []
    
    for word in words:
        if word in food_terms or word in cuisines or word[0].isupper():
            extracted.append(word)
    
    return extracted