"""
OCP Schema Discovery

Provides automatic API discovery and tool generation from OpenAPI specifications,
enabling context-aware API interactions with zero infrastructure requirements.
"""

import json
import re
import requests
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import urljoin

from .errors import SchemaDiscoveryError

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_SPEC_TIMEOUT = 30
DEFAULT_API_TITLE = 'Unknown API'
DEFAULT_API_VERSION = '1.0.0'
SUPPORTED_HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete']

@dataclass
class OCPTool:
    """Represents a discovered API tool/endpoint"""
    name: str
    description: str
    method: str
    path: str
    parameters: Dict[str, Any]
    response_schema: Optional[Dict[str, Any]]
    operation_id: Optional[str] = None
    tags: Optional[List[str]] = None

@dataclass 
class OCPAPISpec:
    """Represents a parsed OpenAPI specification"""
    base_url: str
    title: str
    version: str
    description: str
    tools: List[OCPTool]
    raw_spec: Dict[str, Any]
    name: Optional[str] = None

class OCPSchemaDiscovery:
    """
    Automatic API discovery and tool generation from OpenAPI specifications.
    
    This enables automatic API discovery while maintaining OCP's zero-infrastructure
    approach by parsing OpenAPI specs directly.
    """
    
    def __init__(self):
        self.cached_specs: Dict[str, OCPAPISpec] = {}
    
    def discover_api(self, spec_url: str, base_url: Optional[str] = None, include_resources: Optional[List[str]] = None, path_prefix: Optional[str] = None) -> OCPAPISpec:
        """
        Discover API capabilities from OpenAPI specification.
        
        Args:
            spec_url: URL to OpenAPI specification (JSON or YAML)
            base_url: Optional override for API base URL
            include_resources: Optional list of resource names to filter tools by (case-insensitive, first resource segment matching)
            path_prefix: Optional path prefix to strip before filtering (e.g., '/v1', '/api/v2')
            
        Returns:
            OCPAPISpec with discovered tools and capabilities
        """
        # Check cache first
        if spec_url in self.cached_specs:
            return self.cached_specs[spec_url]

        try:
            # Fetch and parse OpenAPI spec
            spec_data = self._fetch_spec(spec_url)
            parsed_spec = self._parse_openapi_spec(spec_data, base_url)
            
            # Cache for future use
            self.cached_specs[spec_url] = parsed_spec
            
            # Apply resource filtering if specified (only on newly parsed specs)
            if include_resources:
                filtered_tools = self._filter_tools_by_resources(parsed_spec.tools, include_resources, path_prefix)
                return OCPAPISpec(
                    base_url=parsed_spec.base_url,
                    title=parsed_spec.title,
                    version=parsed_spec.version,
                    description=parsed_spec.description,
                    tools=filtered_tools,
                    raw_spec=parsed_spec.raw_spec
                )
            
            return parsed_spec
        except Exception as e:
            if isinstance(e, SchemaDiscoveryError):
                raise
            raise SchemaDiscoveryError(f"Failed to discover API: {e}")
    
    def _fetch_spec(self, spec_url: str) -> Dict[str, Any]:
        """Fetch OpenAPI specification from URL"""
        try:
            response = requests.get(spec_url, timeout=DEFAULT_SPEC_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise SchemaDiscoveryError(f"Failed to fetch OpenAPI spec from {spec_url}: {e}")
    
    def _resolve_refs(
        self, 
        obj: Any, 
        root: Optional[Dict[str, Any]] = None, 
        resolution_stack: Optional[List[str]] = None,
        memo: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Recursively resolve $ref references in OpenAPI spec
        
        Args:
            obj: Current object being processed (dict, list, or primitive)
            root: Root spec document for looking up references
            resolution_stack: Stack of refs currently being resolved (for circular detection)
            memo: Memoization cache for already-resolved refs
        
        Returns:
            Object with all resolvable $refs replaced by their definitions
        """
        # Initialize on first call
        if root is None:
            root = obj
        if resolution_stack is None:
            resolution_stack = []
        if memo is None:
            memo = {}
        
        # Handle dict objects
        if isinstance(obj, dict):
            # Check if this is a $ref
            if '$ref' in obj and len(obj) == 1:
                ref_path = obj['$ref']
                
                # Only handle internal refs (start with #/)
                if not ref_path.startswith('#/'):
                    return obj
                
                # Check memo cache first
                if ref_path in memo:
                    return memo[ref_path]
                
                # Check for circular reference
                if ref_path in resolution_stack:
                    # Return a placeholder to break the cycle
                    placeholder = {'type': 'object', 'description': 'Circular reference'}
                    memo[ref_path] = placeholder
                    return placeholder
                
                # Resolve the reference
                try:
                    resolved = self._lookup_ref(root, ref_path)
                    if resolved is not None:
                        # Recursively resolve the resolved object with updated stack
                        new_stack = resolution_stack + [ref_path]
                        result = self._resolve_refs(resolved, root, new_stack, memo)
                        memo[ref_path] = result
                        return result
                except Exception:
                    # If lookup fails, return a placeholder
                    placeholder = {'type': 'object', 'description': 'Unresolved reference'}
                    memo[ref_path] = placeholder
                    return placeholder
                
                return obj
            
            # Not a $ref, recursively process all values
            return {k: self._resolve_refs(v, root, resolution_stack, memo) for k, v in obj.items()}
        
        # Handle list objects
        elif isinstance(obj, list):
            return [self._resolve_refs(item, root, resolution_stack, memo) for item in obj]
        
        # Primitives pass through unchanged
        return obj
    
    def _lookup_ref(self, root: Dict[str, Any], ref_path: str) -> Any:
        """Look up a reference path in the spec document
        
        Args:
            root: Root spec document
            ref_path: Reference path like '#/components/schemas/User'
        
        Returns:
            The referenced object, or None if not found
        """
        # Remove the leading '#/' and split by '/'
        if not ref_path.startswith('#/'):
            return None
        
        path_parts = ref_path[2:].split('/')
        
        # Navigate through the spec
        current = root
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _parse_openapi_spec(self, spec_data: Dict[str, Any], base_url_override: Optional[str] = None) -> OCPAPISpec:
        """Parse OpenAPI specification into OCP tools"""
        
        # Extract basic info
        info = spec_data.get('info', {})
        title = info.get('title', DEFAULT_API_TITLE)
        version = info.get('version', DEFAULT_API_VERSION)
        description = info.get('description', '')
        
        # Determine base URL
        base_url = base_url_override
        if not base_url:
            servers = spec_data.get('servers', [])
            if servers:
                base_url = servers[0].get('url', '')
            else:
                base_url = ''
        
        # Create memoization cache for $ref resolution
        memo_cache = {}
        
        # Parse paths into tools
        tools = []
        paths = spec_data.get('paths', {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in SUPPORTED_HTTP_METHODS:
                    tool = self._create_tool_from_operation(
                        path, method.upper(), operation, spec_data, memo_cache
                    )
                    if tool:
                        tools.append(tool)
        
        return OCPAPISpec(
            base_url=base_url,
            title=title,
            version=version,
            description=description,
            tools=tools,
            raw_spec=spec_data
        )
    
    def _normalize_tool_name(self, name: str) -> str:
        """Normalize tool name to camelCase, removing special characters.
        
        Converts various naming patterns to consistent camelCase:
        - 'meta/root' → 'metaRoot'
        - 'repos/disable-vulnerability-alerts' → 'reposDisableVulnerabilityAlerts'
        - 'admin_apps_approve' → 'adminAppsApprove'
        - 'FetchAccount' → 'fetchAccount'
        - 'v2010/Accounts' → 'v2010Accounts'
        - 'get_users_list' → 'getUsersList'
        - 'SMS/send' → 'smsSend'
        """
        # Handle empty or None names
        if not name:
            return name
            
        # First, split PascalCase/camelCase words (e.g., "FetchAccount" -> "Fetch Account")
        # Insert space before uppercase letters that follow lowercase letters or digits
        pascal_split = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', name)
        
        # Replace separators (/, _, -, .) with spaces for processing
        # Also handle multiple consecutive separators like //
        normalized = re.sub(r'[/_.-]+', ' ', pascal_split)
        
        # Split into words and filter out empty strings
        words = [word for word in normalized.split() if word]
        
        if not words:
            return name
            
        # Convert to camelCase: first word lowercase, rest capitalize
        camel_case_words = [words[0].lower()]
        for word in words[1:]:
            camel_case_words.append(word.capitalize())
                
        return ''.join(camel_case_words)
    
    def _is_valid_tool_name(self, name: str) -> bool:
        """Check if a normalized tool name is valid.
        
        A valid tool name must:
        - Not be empty
        - Not consist only of special characters
        - Start with a letter
        - Contain at least one alphanumeric character
        """
        if not name:
            return False
            
        # Must start with a letter
        if not name[0].isalpha():
            return False
            
        # Must contain at least one alphanumeric character
        if not any(c.isalnum() for c in name):
            return False
            
        return True
    
    def _create_tool_from_operation(self, path: str, method: str, operation: Dict[str, Any], spec_data: Dict[str, Any], memo_cache: Dict[str, Any]) -> Optional[OCPTool]:
        """Create OCP tool from OpenAPI operation"""
        
        # Generate tool name with proper validation and fallback logic
        operation_id = operation.get('operationId')
        tool_name = None
        
        # Try operationId first
        if operation_id:
            normalized_name = self._normalize_tool_name(operation_id)
            if self._is_valid_tool_name(normalized_name):
                tool_name = normalized_name
        
        # If operationId failed, try fallback naming
        if not tool_name:
            # Generate name from path and method
            clean_path = path.replace('/', '_').replace('{', '').replace('}', '')
            fallback_name = f"{method.lower()}{clean_path}"
            normalized_fallback = self._normalize_tool_name(fallback_name)
            if self._is_valid_tool_name(normalized_fallback):
                tool_name = normalized_fallback
        
        # If we can't generate a valid tool name, skip this operation
        if not tool_name:
            logger.warning(f"Skipping operation {method} {path}: unable to generate valid tool name")
            return None
        
        # Get description
        description = operation.get('summary', '') or operation.get('description', '')
        if not description:
            description = "No description provided"
        
        # Parse parameters
        parameters = self._parse_parameters(operation.get('parameters', []), spec_data, memo_cache)
        
        # Add request body parameters for POST/PUT/PATCH
        if method in ['POST', 'PUT', 'PATCH'] and 'requestBody' in operation:
            body_params = self._parse_request_body(operation['requestBody'], spec_data, memo_cache)
            parameters.update(body_params)
        
        # Parse response schema
        response_schema = self._parse_responses(operation.get('responses', {}), spec_data, memo_cache)
        
        # Get tags
        tags = operation.get('tags', [])
        
        return OCPTool(
            name=tool_name,
            description=description,
            method=method,
            path=path,
            parameters=parameters,
            response_schema=response_schema,
            operation_id=operation_id,
            tags=tags
        )
    
    def _parse_parameters(self, parameters: List[Dict[str, Any]], spec_data: Dict[str, Any], memo_cache: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenAPI parameters into tool parameter schema"""
        parsed_params = {}
        
        for param in parameters:
            name = param.get('name')
            if not name:
                continue
            
            param_schema = {
                'description': param.get('description', ''),
                'required': param.get('required', False),
                'location': param.get('in', 'query'),  # query, path, header, cookie
                'type': 'string'  # Default type
            }
            
            # Extract type from schema
            schema = param.get('schema', {})
            if schema:
                # Resolve any $refs in the parameter schema
                schema = self._resolve_refs(schema, spec_data, [], memo_cache)
                param_schema['type'] = schema.get('type', 'string')
                if 'enum' in schema:
                    param_schema['enum'] = schema['enum']
                if 'format' in schema:
                    param_schema['format'] = schema['format']
            
            parsed_params[name] = param_schema
        
        return parsed_params
    
    def _parse_request_body(self, request_body: Dict[str, Any], spec_data: Dict[str, Any], memo_cache: Dict[str, Any]) -> Dict[str, Any]:
        """Parse request body into parameters"""
        parameters = {}
        
        content = request_body.get('content', {})
        
        # Look for JSON content first
        json_content = content.get('application/json', {})
        if json_content and 'schema' in json_content:
            schema = json_content['schema']
            
            # Resolve any $refs in the request body schema
            schema = self._resolve_refs(schema, spec_data, [], memo_cache)
            
            # Handle object schemas
            if schema.get('type') == 'object':
                properties = schema.get('properties', {})
                required_fields = schema.get('required', [])
                
                for prop_name, prop_schema in properties.items():
                    parameters[prop_name] = {
                        'description': prop_schema.get('description', ''),
                        'required': prop_name in required_fields,
                        'location': 'body',
                        'type': prop_schema.get('type', 'string')
                    }
                    
                    if 'enum' in prop_schema:
                        parameters[prop_name]['enum'] = prop_schema['enum']
        
        return parameters
    
    def _parse_responses(self, responses: Dict[str, Any], spec_data: Dict[str, Any], memo_cache: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse response schemas"""
        # Look for successful response (200, 201, etc.)
        for status_code, response in responses.items():
            if str(status_code).startswith('2'):  # 2xx success codes
                content = response.get('content', {})
                json_content = content.get('application/json', {})
                
                if json_content and 'schema' in json_content:
                    schema = json_content['schema']
                    # Resolve any $refs in the response schema
                    return self._resolve_refs(schema, spec_data, [], memo_cache)
        
        return None
    
    def _filter_tools_by_resources(self, tools: List[OCPTool], include_resources: List[str], path_prefix: Optional[str] = None) -> List[OCPTool]:
        """Filter tools to only include those whose first resource segment matches include_resources"""
        if not include_resources:
            return tools
        
        # Normalize resource names to lowercase for case-insensitive matching
        normalized_resources = [resource.lower() for resource in include_resources]
        
        filtered_tools = []
        for tool in tools:
            path = tool.path
            
            # Strip path prefix if provided
            if path_prefix:
                prefix_lower = path_prefix.lower()
                path_lower = path.lower()
                if path_lower.startswith(prefix_lower):
                    path = path[len(path_prefix):]
            
            # Extract path segments by splitting on both '/' and '.'
            path_lower = path.lower()
            # Replace dots with slashes for uniform splitting
            path_normalized = path_lower.replace('.', '/')
            # Split by '/' and filter out empty segments and parameter placeholders
            segments = [seg for seg in path_normalized.split('/') if seg and not seg.startswith('{')]
            
            # Check if the first segment matches any of the include_resources
            if segments and segments[0] in normalized_resources:
                filtered_tools.append(tool)
        
        return filtered_tools
    
    def get_tools_by_tag(self, api_spec: OCPAPISpec, tag: str) -> List[OCPTool]:
        """Get tools filtered by tag"""
        return [tool for tool in api_spec.tools if tag in (tool.tags or [])]
    
    def search_tools(self, api_spec: OCPAPISpec, query: str) -> List[OCPTool]:
        """Search tools by name or description"""
        query_lower = query.lower()
        matches = []
        
        for tool in api_spec.tools:
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower()):
                matches.append(tool)
        
        return matches
    
    def generate_tool_documentation(self, tool: OCPTool) -> str:
        """Generate human-readable documentation for a tool"""
        doc_lines = [
            f"## {tool.name}",
            f"**Method:** {tool.method}",
            f"**Path:** {tool.path}",
            f"**Description:** {tool.description}",
            ""
        ]
        
        if tool.parameters:
            doc_lines.append("### Parameters:")
            for param_name, param_info in tool.parameters.items():
                required = " (required)" if param_info.get('required') else " (optional)"
                location = f" [{param_info.get('location', 'query')}]"
                doc_lines.append(f"- **{param_name}**{required}{location}: {param_info.get('description', '')}")
            doc_lines.append("")
        
        if tool.tags:
            doc_lines.append(f"**Tags:** {', '.join(tool.tags)}")
            doc_lines.append("")
        
        return "\n".join(doc_lines)
    
    def clear_cache(self):
        """Clear cached API specifications"""
        self.cached_specs.clear()