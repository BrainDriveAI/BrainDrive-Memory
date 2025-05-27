from typing import List, Dict
from app.config.core_validator import validate_core_configuration
from app.config.feature_validator import validate_feature_configuration

class ConfigError(Exception):
    """
    Raised when any configuration validation fails.
    Contains the list of issues in .issues attribute.
    """
    def __init__(self, issues: List[Dict[str, str]]):
        super().__init__("Configuration validation failed")
        self.issues = issues


def validate_configuration() -> None:
    """
    Run all configuration validations. Raises ConfigError if any issues found.
    """
    issues: List[Dict[str, str]] = []

    # Core checks
    issues.extend(validate_core_configuration())
    # Feature checks
    issues.extend(validate_feature_configuration())

    if issues:
        raise ConfigError(issues)
    