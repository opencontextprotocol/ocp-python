# OCP Python Library

Context-aware HTTP client framework for AI agents.

## Installation

```bash
pip install ocp-agent
# or with poetry
poetry add ocp-agent
```

## Quick Start

```python
from ocp_agent import OCPAgent

# Create an OCP agent
agent = OCPAgent(
    agent_type="api_explorer",
    user="your-username",
    workspace="my-project",
    agent_goal="Explore GitHub API"
)

# Register an API from the registry (fast lookup)
github_api = agent.register_api("github")

# Or register from OpenAPI specification URL
# github_api = agent.register_api(
#     name="github",
#     spec_url="https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json"
# )

# List available tools
tools = agent.list_tools("github")
print(f"Found {len(tools)} GitHub API tools")

# Call a tool
result = agent.call_tool(
    tool_name="usersGetAuthenticated",
    api_name="github"
)
print(result)
```

## API Registration & Authentication

The `register_api()` method supports multiple patterns:

```python
# 1. Registry lookup - fastest, uses community registry
github_api = agent.register_api("github")

# 2. Registry lookup with authentication
github_api = agent.register_api(
    name="github",
    headers={"Authorization": "token ghp_your_token_here"}
)

# 3. Registry lookup with base URL override (e.g., GitHub Enterprise)
ghe_api = agent.register_api(
    name="github",
    base_url="https://github.company.com/api/v3",
    headers={"Authorization": "token ghp_enterprise_token"}
)

# 4. Direct OpenAPI spec URL
api = agent.register_api(
    name="my-api",
    spec_url="https://api.example.com/openapi.json"
)

# 5. Direct OpenAPI spec with base URL override and authentication
api = agent.register_api(
    name="my-api",
    spec_url="https://api.example.com/openapi.json",
    base_url="https://staging-api.example.com",  # Override for testing
    headers={"X-API-Key": "your_api_key_here"}
)

# 6. Local OpenAPI file (JSON or YAML)
api = agent.register_api(
    name="local-api",
    spec_url="file:///path/to/openapi.yaml",
    base_url="http://localhost:8000"
)

# Headers are automatically included in all tool calls
result = agent.call_tool("usersGetAuthenticated", api_name="github")
```

## Core Components

- **OCPAgent**: Main agent class with API discovery and tool invocation
- **AgentContext**: Context management with persistent conversation tracking
- **OCPHTTPClient**: Context-aware HTTP client wrapper
- **OCPSchemaDiscovery**: OpenAPI specification parsing and tool extraction
- **Headers**: OCP context encoding/decoding for HTTP headers
- **Validation**: JSON schema validation for context objects

## API Reference

### OCPAgent

```python
agent = OCPAgent(agent_type, user=None, workspace=None, agent_goal=None, registry_url=None, enable_cache=True)
agent.register_api(name, spec_url=None, base_url=None, headers=None)
agent.list_tools(api_name=None)
agent.call_tool(tool_name, parameters=None, api_name=None)
```

### AgentContext

```python
context = AgentContext(agent_type, user=None, workspace=None)
context.add_interaction(action, api_endpoint, result)
context.update_goal(new_goal)
context.to_dict()
```

### HTTP Client

```python
from ocp_agent import OCPHTTPClient, AgentContext

# Create context
context = AgentContext(
    agent_type="api_client",
    user="username",
    workspace="project"
)

# Create OCP-aware HTTP client
client = OCPHTTPClient(context, base_url="https://api.example.com")

# Make requests with automatic OCP context headers
response = client.get("/endpoint")
```

## Development

```bash
# Clone repository
git clone https://github.com/opencontextprotocol/ocp-python.git
cd ocp-python

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src/ocp --cov-report=term-missing

# Run specific test file
poetry run pytest tests/test_context.py -v
```

## Project Structure

```
src/ocp_agent/
├── __init__.py          # Public API exports
├── agent.py             # OCPAgent class
├── context.py           # AgentContext class  
├── http_client.py       # HTTP client wrappers
├── headers.py           # Header encoding/decoding
├── schema_discovery.py  # OpenAPI parsing
├── registry.py          # Registry client
├── storage.py           # Local storage and caching
├── validation.py        # JSON schema validation
└── errors.py            # Error classes

tests/
├── test_agent.py        # OCPAgent tests
├── test_context.py      # AgentContext tests
├── test_http_client.py  # HTTP client tests
├── test_headers.py      # Header tests
├── test_schema_discovery.py # Schema parsing tests
├── test_registry.py     # Registry tests
├── test_storage.py      # Storage tests
├── test_validation.py   # Validation tests
└── conftest.py          # Test fixtures
```

## License

MIT License - see LICENSE file.