"""
OCP Error Hierarchy

Consistent error handling for the Open Context Protocol library.
Provides specific exception types for different failure scenarios.
"""

from typing import List, Optional


class OCPError(Exception):
    """Base exception for all OCP-related errors."""
    pass


class RegistryUnavailable(OCPError):
    """Registry service is unreachable or returned an error.
    
    Args:
        registry_url: The URL of the unreachable registry
        message: Optional specific error message
    """
    
    def __init__(self, registry_url: str, message: str = None):
        self.registry_url = registry_url
        if message is None:
            full_message = f"Registry unavailable at {registry_url}. Use spec_url for direct discovery."
        else:
            full_message = f"Registry unavailable at {registry_url}: {message}"
        super().__init__(full_message)


class APINotFound(OCPError):
    """API not found in the registry.
    
    Args:
        api_name: The name of the API that was not found
        suggestions: Optional list of similar API names to suggest
    """
    
    def __init__(self, api_name: str, suggestions: Optional[List[str]] = None):
        self.api_name = api_name
        self.suggestions = suggestions or []
        
        message = f"API '{api_name}' not found in registry"
        if suggestions:
            message += f". Did you mean: {', '.join(suggestions[:3])}?"
        super().__init__(message)


class SchemaDiscoveryError(OCPError):
    """OpenAPI schema discovery and parsing errors.
    
    Raised when there are issues fetching, parsing, or processing OpenAPI specifications.
    This includes network errors, malformed JSON/YAML, and invalid schema structures.
    """
    pass


class ValidationError(OCPError):
    """Context or parameter validation errors.
    
    Raised when agent context, API parameters, or response data fails validation.
    This includes missing required fields, type mismatches, and constraint violations.
    """
    pass