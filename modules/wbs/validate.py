from typing import Dict, Any


def validate_input(event_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validation disabled per requirements: always return ok.
    """
    return {"status": "ok"}

