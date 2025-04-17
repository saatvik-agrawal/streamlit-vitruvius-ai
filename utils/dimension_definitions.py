# utils/dimension_definitions.py

ENGAGEMENT_DEFINITIONS = {
    "low": "Methods where participants primarily provide information or feedback but have limited influence on outcomes.",
    "medium": "Methods where participants actively contribute ideas and insights with some collaborative elements.",
    "high": "Methods where participants take significant ownership in co-creating processes and outcomes."
}

SCALE_DEFINITIONS = {
    "small": "Intimate sessions with 5-15 participants, requiring minimal facilitation.",
    "medium": "Larger groups of 15-50 people that still allow for meaningful interaction.",
    "large": "Events involving 50+ participants, requiring substantial planning and logistics."
}

def get_scale_options():
    return list(SCALE_DEFINITIONS.keys())

def get_engagement_options():
    return list(ENGAGEMENT_DEFINITIONS.keys())

def get_scale_definition(scale):
    return SCALE_DEFINITIONS.get(scale, "")

def get_engagement_definition(engagement):
    return ENGAGEMENT_DEFINITIONS.get(engagement, "")