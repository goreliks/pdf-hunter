import json
from typing import Any, Dict

def serialize_state_safely(state: Dict[str, Any]) -> str:
    """
    Safely serialize orchestrator state to JSON string, handling:
    - Pydantic models via model_dump()
    - Missing/None fields
    - Complex nested structures
    - Non-serializable objects
    """
    def make_serializable(obj):
        # Handle Pydantic models
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        # Handle dictionaries recursively
        elif isinstance(obj, dict):
            return {
                k: make_serializable(v) 
                for k, v in obj.items() 
                if k != 'mcp_playwright_session'  # Exclude non-serializable sessions
            }
        # Handle lists recursively
        elif isinstance(obj, list):
            return [make_serializable(item) for item in obj]
        # Handle primitives and fallback
        else:
            try:
                json.dumps(obj)  # Test if serializable
                return obj
            except (TypeError, ValueError):
                return str(obj)  # Convert to string as fallback
    
    serializable_data = make_serializable(state)
    # return json.dumps(serializable_data, indent=2, ensure_ascii=False)
    return serializable_data
