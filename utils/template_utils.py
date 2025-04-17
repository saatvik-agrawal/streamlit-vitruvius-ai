# utils/template_utils.py
import os
import yaml
import re
from typing import List, Dict, Any

def load_all_templates(template_dir: str = "templates") -> List[Dict[str, Any]]:
    """Load all template YAML files from the templates directory."""
    templates = []
    for filename in os.listdir(template_dir):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            file_path = os.path.join(template_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    template = yaml.safe_load(file)
                    templates.append(template)
            except Exception as e:
                print(f"Error loading template {filename}: {e}")
    return templates

def get_template_by_id(template_id: str, template_dir: str = "templates") -> Dict[str, Any]:
    """Get a specific template by its ID."""
    templates = load_all_templates(template_dir)
    for template in templates:
        if template.get("id") == template_id:
            return template
    return None

def fill_template(template: Dict[str, Any], variables: Dict[str, str]) -> str:
    """Fill a template with user-provided variables."""
    content = template.get("content", "")
    
    # Replace all variables in the content
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        content = content.replace(placeholder, value)
    
    # Find any remaining placeholders that weren't filled
    remaining_placeholders = re.findall(r'{{([^}]+)}}', content)
    
    # If there are remaining placeholders, add them to the variables dict with empty strings
    if remaining_placeholders:
        for placeholder in remaining_placeholders:
            content = content.replace("{{" + placeholder + "}}", "")
    
    return content

def extract_template_variables(template: Dict[str, Any]) -> List[str]:
    """Extract all variable placeholders from a template."""
    content = template.get("content", "")
    placeholders = re.findall(r'{{([^}]+)}}', content)
    return list(set(placeholders))  # Remove duplicates

def filter_templates_by_dimensions(templates: List[Dict[str, Any]], 
                                 scale: str = None, 
                                 engagement: str = None) -> List[Dict[str, Any]]:
    """Filter templates based on scale and engagement levels."""
    if not scale and not engagement:
        return templates
    
    filtered_templates = []
    
    for template in templates:
        dimensions = template.get("dimensions", {})
        
        # Check if template matches scale criteria
        if scale:
            template_scale = dimensions.get("scale")
            # Handle case where scale is a list or a string
            if isinstance(template_scale, list) and scale in template_scale:
                scale_match = True
            elif template_scale == scale:
                scale_match = True
            else:
                scale_match = False
        else:
            scale_match = True
            
        # Check if template matches engagement criteria
        if engagement:
            template_engagement = dimensions.get("engagement")
            # Handle case where engagement is a list or a string
            if isinstance(template_engagement, list) and engagement in template_engagement:
                engagement_match = True
            elif template_engagement == engagement:
                engagement_match = True
            else:
                engagement_match = False
        else:
            engagement_match = True
            
        # Include template if it matches both criteria
        if scale_match and engagement_match:
            filtered_templates.append(template)
            
    return filtered_templates