"""
Schema Validation - JSON schema validation for OCP context objects.

Validates agent contexts against the OCP specification schemas.
"""

import json
from typing import Dict, Any, Optional, List
from importlib import resources

from jsonschema import validate, ValidationError

from .context import AgentContext


def _load_schema() -> Dict[str, Any]:
    """Load OCP context schema from braided specification file."""
    schema_data = resources.files(__package__).joinpath("schemas/ocp-context.json").read_text()
    return json.loads(schema_data)


# Load schema from braided specification repo
OCP_CONTEXT_SCHEMA = _load_schema()


class ValidationResult:
    """Result of schema validation.
    
    Provides validation status and error details for OCP context validation.
    Supports boolean conversion for simple valid/invalid checks.
    
    Attributes:
        valid: True if validation passed, False otherwise
        errors: List of validation error messages
    """
    
    def __init__(self, valid: bool, errors: Optional[List[str]] = None):
        self.valid = valid
        self.errors = errors or []
    
    def __bool__(self) -> bool:
        return self.valid
    
    def __str__(self) -> str:
        if self.valid:
            return "Valid OCP context"
        return f"Invalid OCP context: {'; '.join(self.errors)}"


def validate_context(context: AgentContext) -> ValidationResult:
    """
    Validate an AgentContext against the OCP schema.
    
    Args:
        context: AgentContext to validate
        
    Returns:
        ValidationResult with validation status and errors
    """
    try:
        context_dict = context.to_dict()
        validate(context_dict, OCP_CONTEXT_SCHEMA)
        return ValidationResult(True)
    
    except ValidationError as e:
        return ValidationResult(False, [str(e)])
    except Exception as e:
        return ValidationResult(False, [f"Validation error: {str(e)}"])


def validate_context_dict(context_dict: Dict[str, Any]) -> ValidationResult:
    """Validate a context dictionary against the OCP schema.
    
    Args:
        context_dict: Context data as dictionary to validate
        
    Returns:
        ValidationResult with validation status and any error messages
    """
    try:
        validate(context_dict, OCP_CONTEXT_SCHEMA)
        return ValidationResult(True)
    
    except ValidationError as e:
        return ValidationResult(False, [str(e)])
    except Exception as e:
        return ValidationResult(False, [f"Validation error: {str(e)}"])




def get_schema() -> Dict[str, Any]:
    """Get the OCP context JSON schema.
    
    Returns:
        Copy of the JSON schema dictionary used for validation
        
    Note:
        Returns a copy to prevent accidental modification of the schema.
    """
    return OCP_CONTEXT_SCHEMA.copy()


def validate_and_fix_context(context: AgentContext) -> tuple[AgentContext, ValidationResult]:
    """Validate context and attempt to fix common issues.
    
    Attempts to automatically repair common validation failures:
    - Adds 'ocp-' prefix to context_id if missing
    - Ensures required collections (session, history, api_specs) exist
    - Initializes collections as empty if they are None or wrong type
    
    Args:
        context: AgentContext to validate and potentially fix
        
    Returns:
        Tuple of (fixed_context, validation_result)
        - fixed_context: New AgentContext with repairs applied
        - validation_result: Final validation status after fixes
        
    Note:
        Original context is not modified; returns a new instance.
    """
    # Make a copy to avoid modifying original
    fixed_context = AgentContext.from_dict(context.to_dict())
    
    # Fix common issues
    if not fixed_context.context_id.startswith("ocp-"):
        fixed_context.context_id = f"ocp-{fixed_context.context_id}"
    
    # Ensure required collections exist
    if not isinstance(fixed_context.session, dict):
        fixed_context.session = {}
    
    if not isinstance(fixed_context.history, list):
        fixed_context.history = []
    
    if not isinstance(fixed_context.api_specs, dict):
        fixed_context.api_specs = {}
    
    # Validate the fixed context
    result = validate_context(fixed_context)
    
    return fixed_context, result