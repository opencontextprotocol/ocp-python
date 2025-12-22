"""
HTTP Client Enhancement - Make HTTP requests OCP-enabled.

Provides a simple HTTP client that automatically adds OCP context
headers to all requests.
"""

import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from .context import AgentContext
from .headers import create_ocp_headers, extract_context_from_response


class OCPHTTPClient:
    """
    OCP-enabled HTTP client.
    
    Automatically adds OCP context headers to all requests and tracks
    interactions in the agent context.
    """
    
    def __init__(
        self, 
        context: AgentContext,
        auto_update_context: bool = True,
        base_url: Optional[str] = None
    ):
        """
        Initialize OCP HTTP client.
        
        Args:
            context: Agent context to include in requests
            auto_update_context: Whether to automatically update context with interactions
            base_url: Optional base URL for API requests
        """
        self.context = context
        self.auto_update_context = auto_update_context
        self.base_url = base_url.rstrip('/') if base_url else None
        
        # Use requests as our HTTP client
        self.http_client = requests.Session()
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare headers with OCP context."""
        ocp_headers = create_ocp_headers(self.context)
        
        if headers:
            # Merge with existing headers
            merged = headers.copy()
            merged.update(ocp_headers)
            return merged
        
        return ocp_headers
    
    def _log_interaction(self, method: str, url: str, response: Any = None, error: Exception = None) -> None:
        """Log the API interaction in context."""
        if not self.auto_update_context:
            return
        
        # Parse API endpoint
        parsed = urlparse(url)
        endpoint = f"{method.upper()} {parsed.path}"
        
        # Get response status and build result
        status_code = None
        if response and hasattr(response, 'status_code'):
            status_code = response.status_code
        elif response and hasattr(response, 'status'):
            status_code = response.status
            
        # Determine result string
        result = None
        if error:
            result = f"Error: {str(error)}"
        elif status_code:
            result = f"HTTP {status_code}"
        
        # Build detailed metadata like JavaScript implementation
        metadata = {
            "method": method.upper(),
            "url": url,
            "domain": parsed.netloc,
            "success": not error and status_code and 200 <= status_code < 300,
        }
        
        if status_code:
            metadata["status_code"] = status_code
            
        if error:
            metadata["error"] = str(error)
        
        # Add to context history
        self.context.add_interaction(
            action=f"api_call_{method.lower()}",
            api_endpoint=endpoint,
            result=result,
            metadata=metadata
        )
    
    def request(self, method: str, url: str, **kwargs) -> Any:
        """Make an HTTP request with OCP context."""
        # Handle base URL for relative URLs
        if self.base_url and not url.startswith('http'):
            url = f"{self.base_url}{url}"
        
        # Prepare headers
        headers = kwargs.get('headers', {})
        kwargs['headers'] = self._prepare_headers(headers)
        
        try:
            # Make request
            response = self.http_client.request(method, url, **kwargs)
            
            # Log successful interaction
            self._log_interaction(method, url, response)
            
            return response
            
        except Exception as error:
            # Log failed interaction
            self._log_interaction(method, url, error=error)
            
            # Re-raise the exception
            raise
    
    def get(self, url: str, **kwargs) -> Any:
        """Make a GET request with OCP context."""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Any:
        """Make a POST request with OCP context."""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> Any:
        """Make a PUT request with OCP context."""
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Any:
        """Make a DELETE request with OCP context."""
        return self.request('DELETE', url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> Any:
        """Make a PATCH request with OCP context.""" 
        return self.request('PATCH', url, **kwargs)


def _wrap_api(
    base_url: str, 
    context: AgentContext,
    headers: Optional[Dict[str, str]] = None
) -> OCPHTTPClient:
    """
    Create an OCP-enabled client for a specific API (internal use only).
    
    Args:
        base_url: Base URL for the API (e.g., "https://api.github.com")
        context: Agent context to include in requests
        headers: Additional headers to include in all requests
        
    Returns:
        OCP-enabled API client
        
    Example:
        >>> from ocp_agent import AgentContext, wrap_api
        >>> 
        >>> context = AgentContext(agent_type="debug_assistant")
        >>> github = wrap_api(
        ...     "https://api.github.com",
        ...     context,
        ...     headers={"Authorization": "token ghp_your_token"}
        ... )
        >>> issues = github.get("/search/issues", params={"q": "bug"})
    """
    # Create OCP client with base URL
    ocp_client = OCPHTTPClient(context, base_url=base_url)
    
    # Set up additional headers if provided
    if headers:
        ocp_client.http_client.headers.update(headers)
    
    return ocp_client