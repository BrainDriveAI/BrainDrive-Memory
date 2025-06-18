from typing import List, Dict
from app.config.app_env import app_env


def validate_feature_configuration() -> List[Dict[str, str]]:
    """
    Validate optional feature configurations.
    Returns a list of issue dicts; empty if valid.
    """
    issues: List[Dict[str, str]] = []

    # Authentication feature
    if app_env.ENABLE_AUTH:
        missing = [key for key in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "REDIRECT_URI") if not getattr(app_env, key)]
        if missing:
            issues.append({
                "message": "Authentication settings incomplete.",
                "details": f"Missing: {', '.join(missing)}.",
                "fix": "Add GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and REDIRECT_URI to your .env file."
            })

    # File upload feature
    if app_env.ENABLE_FILE_UPLOAD:
        missing = [key for key in ("GCS_BUCKET_NAME", "LLM_SHERPA_API_URL") if not getattr(app_env, key)]
        if missing:
            issues.append({
                "message": "File upload settings incomplete.",
                "details": f"Missing: {', '.join(missing)}.",
                "fix": "Add GCS_BUCKET_NAME and LLM_SHERPA_API_URL to your .env file."
            })

    return issues
