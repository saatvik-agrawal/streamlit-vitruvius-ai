# utils/llm_utils.py
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import Google Generative AI
try:
    import google.generativeai as genai
    HAVE_GENAI = True
except ImportError:
    print("Google Generative AI package not found. Run 'pip install google-generativeai'")
    HAVE_GENAI = False

from utils.template_utils import (
    extract_template_variables,
    fill_template
)

# Set up the Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")  # Get from .env file

# Configure the API if we have a key
if GEMINI_API_KEY and HAVE_GENAI:
    genai.configure(api_key=GEMINI_API_KEY)

def initialize_llm():
    """Initialize Gemini API connection."""
    if not HAVE_GENAI:
        print("Google Generative AI package not installed.")
        return None
        
    if not GEMINI_API_KEY:
        print("No Gemini API key found in .env file.")
        return None
    
    try:
        # Create a simple test to verify connection - using the newest model
        model = genai.GenerativeModel('gemini-2.0-flash')  # Updated to the latest model
        response = model.generate_content("Hello")
        print("Gemini API connected successfully!")
        
        # Create a wrapper function to match our expected interface
        def gemini_wrapper(prompt, max_length=512):
            try:
                response = model.generate_content(prompt, generation_config={
                    "max_output_tokens": max_length,
                    "temperature": 0.2  # Lower temperature for more consistent outputs
                })
                # Format to match our expected format
                return [{"generated_text": response.text}]
            except Exception as e:
                print(f"Error generating content: {e}")
                # Return empty text on error
                return [{"generated_text": ""}]
        
        return gemini_wrapper
    except Exception as e:
        print(f"Error initializing Gemini API: {e}")
        return None

def recommend_templates(user_description: str, templates: List[Dict[str, Any]], llm) -> List[Dict[str, Any]]:
    """Use the LLM to recommend templates based on the user's description."""
    if not llm:
        # Fallback to keyword matching if LLM isn't available
        return keyword_based_recommendations(user_description, templates)
    
    # Create a prompt that asks the LLM to recommend templates
    template_summaries = []
    for i, template in enumerate(templates):
        summary = f"Template {i+1}: {template['name']} - {template['description']}"
        template_summaries.append(summary)
    
    template_text = "\n".join(template_summaries)
    
    prompt = f"""Based on the following user description:
"{user_description}"

Please recommend the most suitable templates from this list:
{template_text}

Return the template numbers separated by commas (e.g., "1,3,5").
"""
    
    # Generate recommendations using the LLM
    try:
        response = llm(prompt, max_length=50)[0]["generated_text"]
        print(f"Raw recommendation response: {response}")
        
        # Extract the recommended template numbers
        recommended_indices = [int(idx.strip()) - 1 for idx in response.split(",") if idx.strip().isdigit()]
        # Return the recommended templates
        recommended_templates = [templates[idx] for idx in recommended_indices if 0 <= idx < len(templates)]
        
        # If no recommendations were found, fall back to keyword matching
        if not recommended_templates:
            print("No valid template indices found in response, using keyword matching")
            return keyword_based_recommendations(user_description, templates)
        
        return recommended_templates
    except Exception as e:
        print(f"Error getting recommendations from LLM: {e}")
        return keyword_based_recommendations(user_description, templates)

def keyword_based_recommendations(user_description: str, templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fallback method using keyword matching for template recommendations."""
    user_words = set(user_description.lower().split())
    scored_templates = []
    
    for template in templates:
        score = 0
        
        # Check name and description for matches
        text_to_match = f"{template['name']} {template['description']}".lower()
        
        # Add keywords if available
        if 'keywords' in template:
            text_to_match += " " + " ".join(template['keywords']).lower()
        
        # Simple word matching for score
        for word in user_words:
            if len(word) > 3 and word in text_to_match:  # Only match meaningful words
                score += 1
        
        scored_templates.append((template, score))
    
    # Sort by score descending and return top 3
    scored_templates.sort(key=lambda x: x[1], reverse=True)
    return [t[0] for t in scored_templates[:3]]

def adjust_template_to_use_case(template: Dict[str, Any], user_description: str, 
                               variables: Dict[str, str], llm) -> Dict[str, str]:
    """Use the LLM to suggest values for template variables based on the user's description."""
    if not llm:
        return variables
    
    # Extract the variables that need to be filled
    needed_vars = [var for var in variables.keys() if not variables[var]]
    
    if not needed_vars:
        return variables
    
    # Create a prompt for the LLM to fill in the variables
    vars_text = "\n".join([f"- {var}" for var in needed_vars])
    
    prompt = f"""Based on this user description:
"{user_description}"

And for this template:
"{template['name']} - {template['description']}"

Please suggest appropriate values for these template variables:
{vars_text}

Format your response as:
variable_name: suggested value
"""
    
    try:
        response = llm(prompt, max_length=512)[0]["generated_text"]
        
        # Parse the response to extract variable values
        for line in response.strip().split("\n"):
            if ":" in line:
                var_name, var_value = line.split(":", 1)
                var_name = var_name.strip()
                var_value = var_value.strip()
                
                if var_name in needed_vars:
                    variables[var_name] = var_value
        
        return variables
    except Exception as e:
        print(f"Error adjusting template with LLM: {e}")
        return variables

def refine_output(current_output: str, user_feedback: str, llm):
    """Refine the template output based on user feedback."""
    if not llm:
        return current_output
    
    # Make sure we have a substantial template to work with
    if len(current_output) < 50:
        print("Current template too short, cannot refine")
        return current_output
    
    prompt = f"""IMPORTANT: You are adapting a template based on user feedback. Your job is to return the COMPLETE modified template.

ORIGINAL TEMPLATE:
{current_output}

USER FEEDBACK:
"{user_feedback}"

INSTRUCTIONS:
1. Start by copying the entire original template
2. Make ONLY the specific changes requested in the user feedback
3. Keep ALL sections, headings, and structure exactly the same
4. Do NOT add any commentary, explanations, or "thank you" messages
5. The output should be the COMPLETE template with the requested changes incorporated

OUTPUT THE ENTIRE TEMPLATE WITH CHANGES:
"""
    
    try:
        response = llm(prompt, max_length=2048)[0]["generated_text"]
        print(f"Refinement: Length of original={len(current_output)}, Length of response={len(response)}")
        
        # Basic validation - just check if it's too short
        if len(response) < 100:
            print(f"Response too short ({len(response)} chars), reverting to original")
            return current_output
            
        # Check for common prefixes to remove
        common_prefixes = [
            "Here's the complete template with the requested changes:",
            "Here is the adapted template:",
            "Here is the complete template with your changes:",
            "I've incorporated your feedback. Here's the updated template:"
        ]
        
        for prefix in common_prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].lstrip()
                print(f"Removed prefix: {prefix}")
                break
                
        # No more aggressive splitting that might remove top content
        return response
        
    except Exception as e:
        print(f"Error refining output with LLM: {e}")
        return current_output

def fully_adapt_template(template: Dict[str, Any], user_description: str, llm):
    """Adapt the entire template to the user's specific use case."""
    if not llm:
        # Just return the original template if no LLM is available
        return template.get("content", "")
    
    # Extract the template content
    content = template.get("content", "")
    template_name = template.get("name", "Template")
    
    # Create a prompt for the LLM to adapt the template
    prompt = f"""You are helping to adapt a participatory design template to a specific use case.

USER'S USE CASE DESCRIPTION:
"{user_description}"

ORIGINAL TEMPLATE ({template_name}):
{content}

INSTRUCTIONS:
1. KEEP all section titles and headings EXACTLY the same
2. KEEP all steps and process instructions EXACTLY the same 
3. KEEP all formatting EXACTLY the same
4. ONLY change specific examples to be more relevant to the user's scenario
5. DO NOT add new content or remove existing content
6. DO NOT add any personal commentary or greeting message
7. Start your response with the exact same line as the original template

Return ONLY the adapted template content. 
Do not include any explanatory text before or after the template.
"""
    
    try:
        # Generate the adapted template
        response = llm(prompt, max_length=2048)[0]["generated_text"]
        print(f"Adaptation: Length of original={len(content)}, Length of response={len(response)}")
        
        # Basic validation - just check if it's too short
        if len(response) < 100:
            print(f"Response too short ({len(response)} chars), reverting to original")
            return content
            
        # Check for common prefixes to remove
        common_prefixes = [
            "Here's the adapted template:",
            "Here is the adapted template:",
            "I've adapted the template to your use case:",
            "Here's the template adapted to your scenario:"
        ]
        
        for prefix in common_prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].lstrip()
                print(f"Removed prefix: {prefix}")
                break
                
        # No more aggressive splitting that might remove top content
        return response
        
    except Exception as e:
        print(f"Error adapting template with LLM: {e}")
        # Fall back to original template
        return content