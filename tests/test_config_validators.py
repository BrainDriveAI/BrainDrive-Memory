# tests/test_config_validators.py
import sys
import importlib
import pytest
from unittest.mock import patch, MagicMock
from pydantic import SecretStr, HttpUrl
from typing import Dict, Any

# Import from correct module paths
from app.config.app_env import CriticalConfigError, app_env
from app.config.core_validator import validate_core_configuration
from app.config.feature_validator import validate_feature_configuration
from app.config.validator import validate_configuration, ConfigError


class TestCoreValidator:
    """Test cases for core configuration validation."""
    
    def setup_valid_core_env(self, monkeypatch):
        """Helper to set a baseline valid core configuration."""
        # LLM Provider - OpenAI
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'openai')
        monkeypatch.setattr(app_env, 'OPENAI_API_KEY', SecretStr('test-openai-key'))
        monkeypatch.setattr(app_env, 'OPENAI_LLM_MODEL', 'gpt-4.1')
        monkeypatch.setattr(app_env, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        
        # Embedding Provider - Pinecone
        monkeypatch.setattr(app_env, 'EMBEDDING_PROVIDER', 'pinecone')
        monkeypatch.setattr(app_env, 'PINECONE_API_KEY', SecretStr('test-pinecone-key'))
        monkeypatch.setattr(app_env, 'PINECONE_ENVIRONMENT', 'test-env')
        monkeypatch.setattr(app_env, 'PINECONE_EMBEDDING_MODEL', 'multilingual-e5-large')
        
        # Neo4j (required)
        monkeypatch.setattr(app_env, 'NEO4J_URL', 'neo4j+s://test.databases.neo4j.io')
        monkeypatch.setattr(app_env, 'NEO4J_USER', 'neo4j')
        monkeypatch.setattr(app_env, 'NEO4J_PWD', SecretStr('test-neo4j-pwd'))
        monkeypatch.setattr(app_env, 'NEO4J_DATABASE', 'neo4j')
        
        # Features disabled by default
        monkeypatch.setattr(app_env, 'ENABLE_AUTH', False)
        monkeypatch.setattr(app_env, 'ENABLE_FILE_UPLOAD', False)

    def test_valid_core_configuration(self, monkeypatch):
        """Test that valid core configuration passes validation."""
        self.setup_valid_core_env(monkeypatch)
        issues = validate_core_configuration()
        assert issues == []

    # LLM Provider Tests
    def test_openai_provider_missing_api_key(self, monkeypatch):
        """Test OpenAI provider with missing API key."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'openai')
        monkeypatch.setattr(app_env, 'OPENAI_API_KEY', None)
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('OpenAI provider selected but OPENAI_API_KEY is missing.' in issue['message'] 
                  for issue in issues)

    def test_ollama_provider_missing_model(self, monkeypatch):
        """Test Ollama provider with missing model."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'ollama')
        monkeypatch.setattr(app_env, 'OLLAMA_LLM_MODEL', None)
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('Ollama provider selected but OLLAMA_LLM_MODEL is missing.' in issue['message']
                  for issue in issues)

    def test_groq_provider_missing_credentials(self, monkeypatch):
        """Test Groq provider with missing credentials."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'groq')
        monkeypatch.setattr(app_env, 'GROQ_API_KEY', None)
        monkeypatch.setattr(app_env, 'GROQ_LLM_MODEL', None)
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('Groq provider selected but missing:' in issue['message']
                  for issue in issues)

    def test_togetherai_provider_missing_credentials(self, monkeypatch):
        """Test TogetherAI provider with missing credentials."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'togetherai')
        # Note: The field name should be TOGETHER_AI_API_KEY based on your app_env
        monkeypatch.setattr(app_env, 'TOGETHER_AI_API_KEY', None)
        monkeypatch.setattr(app_env, 'TOGETHER_AI_LLM_MODEL', None)
        
        issues = validate_core_configuration()
        assert len(issues) > 0

    def test_openrouter_provider_missing_credentials(self, monkeypatch):
        """Test OpenRouter provider with missing credentials."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'openrouter')
        monkeypatch.setattr(app_env, 'OPENROUTER_API_KEY', None)
        monkeypatch.setattr(app_env, 'OPENROUTER_LLM_MODEL', None)
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('OpenRouter provider selected but missing:' in issue['message']
                  for issue in issues)

    def test_cloud_run_gemma_provider_missing_config(self, monkeypatch):
        """Test Cloud Run Gemma provider with missing configuration."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'cloud_run_gemma')
        monkeypatch.setattr(app_env, 'GEMMA_SERVICE_URL', None)
        monkeypatch.setattr(app_env, 'GEMMA_API_KEY', None)
        monkeypatch.setattr(app_env, 'GEMMA_SERVICE_ACCOUNT_PATH', None)
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('Cloud Run Gemma provider selected but required configuration is missing.' in issue['message']
                  for issue in issues)

    def test_unknown_llm_provider(self, monkeypatch):
        """Test unknown LLM provider."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'unknown_provider')
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('Unknown LLM provider' in issue['message']
                  for issue in issues)

    # Neo4j Tests
    def test_neo4j_missing_all_config(self, monkeypatch):
        """Test Neo4j with all configuration missing."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'NEO4J_URL', '')
        monkeypatch.setattr(app_env, 'NEO4J_USER', '')
        monkeypatch.setattr(app_env, 'NEO4J_PWD', SecretStr(''))
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('Neo4j configuration incomplete.' in issue['message']
                  for issue in issues)

    def test_neo4j_missing_partial_config(self, monkeypatch):
        """Test Neo4j with partial configuration missing."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'NEO4J_URL', '')  # Missing URL only
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('Neo4j configuration incomplete.' in issue['message']
                  for issue in issues)

    # Embedding Provider Tests
    def test_openai_embedding_provider_missing_key(self, monkeypatch):
        """Test OpenAI embedding provider with missing API key."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'EMBEDDING_PROVIDER', 'openai')
        monkeypatch.setattr(app_env, 'OPENAI_API_KEY', None)
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('OpenAI embedding provider selected but' in issue['message']
                  for issue in issues)

    def test_pinecone_embedding_provider_missing_config(self, monkeypatch):
        """Test Pinecone embedding provider with missing configuration."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'EMBEDDING_PROVIDER', 'pinecone')
        monkeypatch.setattr(app_env, 'PINECONE_API_KEY', None)
        monkeypatch.setattr(app_env, 'PINECONE_EMBEDDING_MODEL', None)
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('Pinecone embedding provider selected but missing:' in issue['message']
                  for issue in issues)

    def test_ollama_embedding_provider_missing_config(self, monkeypatch):
        """Test Ollama embedding provider with missing configuration."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'EMBEDDING_PROVIDER', 'ollama')
        monkeypatch.setattr(app_env, 'OLLAMA_BASE_URL', None)
        monkeypatch.setattr(app_env, 'OLLAMA_EMBEDDING_MODEL', None)
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('Ollama embedding provider selected but' in issue['message']
                  for issue in issues)

    def test_unknown_embedding_provider(self, monkeypatch):
        """Test unknown embedding provider."""
        self.setup_valid_core_env(monkeypatch)
        monkeypatch.setattr(app_env, 'EMBEDDING_PROVIDER', 'unknown_embedding')
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('Unknown embedding provider' in issue['message']
                  for issue in issues)


class TestFeatureValidator:
    """Test cases for feature configuration validation."""
    
    def setup_valid_feature_env(self, monkeypatch):
        """Helper to set valid feature configuration."""
        # Disable features by default
        monkeypatch.setattr(app_env, 'ENABLE_AUTH', False)
        monkeypatch.setattr(app_env, 'ENABLE_FILE_UPLOAD', False)

    def test_valid_feature_configuration_disabled(self, monkeypatch):
        """Test that valid feature configuration (features disabled) passes validation."""
        self.setup_valid_feature_env(monkeypatch)
        issues = validate_feature_configuration()
        assert issues == []

    def test_auth_enabled_with_valid_config(self, monkeypatch):
        """Test auth enabled with valid configuration."""
        self.setup_valid_feature_env(monkeypatch)
        monkeypatch.setattr(app_env, 'ENABLE_AUTH', True)
        monkeypatch.setattr(app_env, 'GOOGLE_CLIENT_ID', 'test-client-id')
        monkeypatch.setattr(app_env, 'GOOGLE_CLIENT_SECRET', SecretStr('test-client-secret'))
        monkeypatch.setattr(app_env, 'REDIRECT_URI', HttpUrl('https://example.com/callback'))
        
        issues = validate_feature_configuration()
        assert issues == []

    def test_auth_enabled_missing_config(self, monkeypatch):
        """Test auth enabled with missing configuration."""
        self.setup_valid_feature_env(monkeypatch)
        monkeypatch.setattr(app_env, 'ENABLE_AUTH', True)
        monkeypatch.setattr(app_env, 'GOOGLE_CLIENT_ID', None)
        monkeypatch.setattr(app_env, 'GOOGLE_CLIENT_SECRET', None)
        monkeypatch.setattr(app_env, 'REDIRECT_URI', None)
        
        issues = validate_feature_configuration()
        assert len(issues) > 0
        assert any('Authentication settings incomplete.' in issue['message']
                  for issue in issues)

    def test_file_upload_enabled_with_valid_config(self, monkeypatch):
        """Test file upload enabled with valid configuration."""
        self.setup_valid_feature_env(monkeypatch)
        monkeypatch.setattr(app_env, 'ENABLE_FILE_UPLOAD', True)
        monkeypatch.setattr(app_env, 'GCS_BUCKET_NAME', 'test-bucket')
        monkeypatch.setattr(app_env, 'LLM_SHERPA_API_URL', HttpUrl('http://localhost:5010/api/parseDocument'))
        
        issues = validate_feature_configuration()
        assert issues == []

    def test_file_upload_enabled_missing_config(self, monkeypatch):
        """Test file upload enabled with missing configuration."""
        self.setup_valid_feature_env(monkeypatch)
        monkeypatch.setattr(app_env, 'ENABLE_FILE_UPLOAD', True)
        monkeypatch.setattr(app_env, 'GCS_BUCKET_NAME', None)
        monkeypatch.setattr(app_env, 'LLM_SHERPA_API_URL', None)
        
        issues = validate_feature_configuration()
        assert len(issues) > 0
        assert any('File upload settings incomplete.' in issue['message']
                  for issue in issues)

    def test_auth_enabled_partial_missing_config(self, monkeypatch):
        """Test auth enabled with partial missing configuration."""
        self.setup_valid_feature_env(monkeypatch)
        monkeypatch.setattr(app_env, 'ENABLE_AUTH', True)
        monkeypatch.setattr(app_env, 'GOOGLE_CLIENT_ID', 'test-client-id')
        monkeypatch.setattr(app_env, 'GOOGLE_CLIENT_SECRET', None)  # Missing this
        monkeypatch.setattr(app_env, 'REDIRECT_URI', HttpUrl('https://example.com/callback'))
        
        issues = validate_feature_configuration()
        assert len(issues) > 0
        assert any('Authentication settings incomplete.' in issue['message']
                  for issue in issues)


class TestIntegratedValidator:
    """Test cases for the integrated validation function."""
    
    def setup_minimal_valid_env(self, monkeypatch):
        """Setup minimal valid environment for all tests."""
        # LLM Provider - OpenAI
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'openai')
        monkeypatch.setattr(app_env, 'OPENAI_API_KEY', SecretStr('test-openai-key'))
        monkeypatch.setattr(app_env, 'OPENAI_LLM_MODEL', 'gpt-4.1')
        
        # Embedding Provider - OpenAI (reuse same key)
        monkeypatch.setattr(app_env, 'EMBEDDING_PROVIDER', 'openai')
        monkeypatch.setattr(app_env, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        
        # Neo4j
        monkeypatch.setattr(app_env, 'NEO4J_URL', 'neo4j+s://test.databases.neo4j.io')
        monkeypatch.setattr(app_env, 'NEO4J_USER', 'neo4j')
        monkeypatch.setattr(app_env, 'NEO4J_PWD', SecretStr('test-neo4j-pwd'))
        
        # Features disabled
        monkeypatch.setattr(app_env, 'ENABLE_AUTH', False)
        monkeypatch.setattr(app_env, 'ENABLE_FILE_UPLOAD', False)

    def test_validate_configuration_success(self, monkeypatch):
        """Test that valid configuration passes integrated validation."""
        self.setup_minimal_valid_env(monkeypatch)
        # Should not raise any exception
        validate_configuration()

    def test_validate_configuration_raises_config_error(self, monkeypatch):
        """Test that invalid configuration raises ConfigError."""
        self.setup_minimal_valid_env(monkeypatch)
        
        # Introduce multiple issues
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'groq')
        monkeypatch.setattr(app_env, 'GROQ_API_KEY', None)
        monkeypatch.setattr(app_env, 'GROQ_LLM_MODEL', None)
        
        monkeypatch.setattr(app_env, 'ENABLE_AUTH', True)
        monkeypatch.setattr(app_env, 'GOOGLE_CLIENT_ID', None)
        
        with pytest.raises(ConfigError) as exc_info:
            validate_configuration()
        
        # Check that ConfigError has issues attribute
        assert hasattr(exc_info.value, 'issues')
        assert len(exc_info.value.issues) > 0
        
        # Check that both core and feature issues are present
        messages = [issue['message'] for issue in exc_info.value.issues]
        assert any('Groq provider selected but missing:' in msg for msg in messages)
        assert any('Authentication settings incomplete.' in msg for msg in messages)

    def test_validate_configuration_multiple_core_issues(self, monkeypatch):
        """Test configuration with multiple core issues."""
        self.setup_minimal_valid_env(monkeypatch)
        
        # Break LLM provider
        monkeypatch.setattr(app_env, 'OPENAI_API_KEY', None)
        # Break Neo4j
        monkeypatch.setattr(app_env, 'NEO4J_URL', '')
        # Break embedding provider
        monkeypatch.setattr(app_env, 'EMBEDDING_PROVIDER', 'pinecone')
        monkeypatch.setattr(app_env, 'PINECONE_API_KEY', None)
        
        with pytest.raises(ConfigError) as exc_info:
            validate_configuration()
        
        # Should have multiple issues
        assert len(exc_info.value.issues) >= 3  # At least one for each broken component


class TestAppEnvInitialization:
    """Test cases for app_env module initialization and error handling."""
    
    def test_app_env_validation_error_handling(self, monkeypatch):
        """Test that ValidationError during app_env initialization is properly handled."""
        # Skip this test since the current app_env configuration doesn't require
        # any fields to be mandatory at Pydantic level (they're all Optional)
        # The validation happens at the application level via validators
        pytest.skip("App env fields are Optional with defaults, validation is done by custom validators")
    
    def test_app_env_successful_initialization(self, monkeypatch):
        """Test that app_env initializes successfully with valid configuration."""
        # Set minimum required environment variables
        monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
        monkeypatch.setenv('NEO4J_URL', 'neo4j://localhost:7687')
        monkeypatch.setenv('NEO4J_USER', 'neo4j')
        monkeypatch.setenv('NEO4J_PWD', 'test-password')
        
        # Remove the module from cache to force re-import
        if 'app.config.app_env' in sys.modules:
            del sys.modules['app.config.app_env']
        
        try:
            # This should not raise any exception
            app_env_module = importlib.import_module('app.config.app_env')
            assert hasattr(app_env_module, 'app_env')
            assert app_env_module.app_env is not None
        finally:
            # Clean up
            if 'app.config.app_env' in sys.modules:
                del sys.modules['app.config.app_env']


class TestConfigErrorClass:
    """Test cases for the ConfigError exception class."""
    
    def test_config_error_initialization(self):
        """Test ConfigError initialization with issues."""
        test_issues = [
            {'message': 'Test issue 1', 'details': 'Details 1', 'fix': 'Fix 1'},
            {'message': 'Test issue 2', 'details': 'Details 2', 'fix': 'Fix 2'}
        ]
        
        error = ConfigError(test_issues)
        
        assert str(error) == "Configuration validation failed"
        assert error.issues == test_issues
        assert len(error.issues) == 2

    def test_config_error_empty_issues(self):
        """Test ConfigError with empty issues list."""
        error = ConfigError([])
        assert error.issues == []
        assert str(error) == "Configuration validation failed"


# Fixtures for common test data
@pytest.fixture
def valid_openai_config():
    """Fixture providing valid OpenAI configuration."""
    return {
        'LLM_PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key',
        'OPENAI_LLM_MODEL': 'gpt-4.1',
        'EMBEDDING_PROVIDER': 'openai',
        'OPENAI_EMBEDDING_MODEL': 'text-embedding-3-small'
    }

@pytest.fixture
def valid_neo4j_config():
    """Fixture providing valid Neo4j configuration."""
    return {
        'NEO4J_URL': 'neo4j+s://test.databases.neo4j.io',
        'NEO4J_USER': 'neo4j',
        'NEO4J_PWD': 'test-password',
        'NEO4J_DATABASE': 'neo4j'
    }


# Additional edge case tests
class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_string_vs_none_values(self, monkeypatch):
        """Test that empty strings are treated the same as None for validation."""
        # Setup base valid config
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'openai')
        monkeypatch.setattr(app_env, 'EMBEDDING_PROVIDER', 'openai')
        monkeypatch.setattr(app_env, 'OPENAI_LLM_MODEL', 'gpt-4.1')
        monkeypatch.setattr(app_env, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        monkeypatch.setattr(app_env, 'NEO4J_USER', 'neo4j')
        monkeypatch.setattr(app_env, 'NEO4J_PWD', SecretStr('pwd'))
        monkeypatch.setattr(app_env, 'NEO4J_URL', 'neo4j://localhost')
        
        # Test empty string (should fail validation)
        monkeypatch.setattr(app_env, 'OPENAI_API_KEY', SecretStr(''))
        issues = validate_core_configuration()
        
        # Reset and test None (should also fail validation)
        monkeypatch.setattr(app_env, 'OPENAI_API_KEY', None)
        issues_none = validate_core_configuration()
        
        # Both should produce validation errors
        assert len(issues) > 0
        assert len(issues_none) > 0

    def test_case_sensitivity_in_provider_names(self, monkeypatch):
        """Test that provider names are case sensitive."""
        monkeypatch.setattr(app_env, 'LLM_PROVIDER', 'OpenAI')  # Wrong case
        monkeypatch.setattr(app_env, 'OPENAI_API_KEY', SecretStr('test-key'))
        
        issues = validate_core_configuration()
        assert len(issues) > 0
        assert any('Unknown LLM provider' in issue['message'] for issue in issues)
