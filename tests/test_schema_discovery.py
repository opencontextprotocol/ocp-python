"""
Tests for OCP schema discovery functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from ocp_agent.schema_discovery import OCPSchemaDiscovery, OCPTool, OCPAPISpec


class TestOCPSchemaDiscovery:
    """Test schema discovery functionality."""
    
    @pytest.fixture
    def discovery(self):
        """Create a schema discovery instance."""
        return OCPSchemaDiscovery()
    
    @pytest.fixture
    def sample_openapi_spec(self):
        """Basic OpenAPI specification without operationIds for testing fallback naming."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "servers": [
                {"url": "https://api.example.com"}
            ],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "description": "Get a list of all users",
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "schema": {"type": "integer"},
                                "required": False
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "List of users",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "name": {"type": "string"},
                                                    "email": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "summary": "Create user",
                        "description": "Create a new user",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        },
                                        "required": ["name", "email"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "User created",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "email": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/users/{id}": {
                    "get": {
                        "summary": "Get user",
                        "description": "Get a specific user by ID",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "schema": {"type": "string"},
                                "required": True
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "User details",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "email": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    @pytest.fixture
    def openapi_spec_with_operation_ids(self):
        """OpenAPI spec with various operationId patterns for testing normalization."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API with Operation IDs",
                "version": "1.0.0"
            },
            "servers": [
                {"url": "https://api.example.com"}
            ],
            "paths": {
                "/meta": {
                    "get": {
                        "operationId": "meta/root",  # GitHub pattern - slash separator
                        "summary": "Get API root",
                        "description": "Get API metadata"
                    }
                },
                "/repos/alerts": {
                    "post": {
                        "operationId": "repos/disable-vulnerability-alerts",  # GitHub pattern - multiple words
                        "summary": "Disable vulnerability alerts",
                        "description": "Disable vulnerability alerts for repository"
                    }
                },
                "/admin/apps": {
                    "put": {
                        "operationId": "admin_apps_approve",  # Slack pattern - underscore separator
                        "summary": "Approve app",
                        "description": "Approve an application"
                    }
                },
                "/accounts": {
                    "get": {
                        "operationId": "FetchAccount",  # Twilio pattern - PascalCase
                        "summary": "Fetch account",
                        "description": "Fetch account details"
                    },
                    "post": {
                        "operationId": "CreateAccount",  # Twilio pattern - PascalCase
                        "summary": "Create account", 
                        "description": "Create new account"
                    }
                },
                "/v2010/accounts": {
                    "get": {
                        "operationId": "v2010/Accounts",  # Version number with slash
                        "summary": "List v2010 accounts",
                        "description": "List accounts from v2010 API"
                    }
                },
                "/sms": {
                    "post": {
                        "operationId": "SMS/send",  # Acronym preservation test
                        "summary": "Send SMS",
                        "description": "Send SMS message"
                    }
                },
                "/users/no-operation-id": {
                    "get": {
                        # No operationId - should use fallback naming
                        "summary": "Get users without operation ID",
                        "description": "Test fallback naming when no operationId present"
                    }
                },
                "/api//double-slash": {
                    "get": {
                        "operationId": "api//users",  # Multiple consecutive separators
                        "summary": "Test double slash",
                        "description": "Test handling of multiple separators"
                    }
                }
            }
        }
    
    @pytest.fixture  
    def openapi_spec_edge_cases(self):
        """OpenAPI spec with edge cases for testing robustness."""
        return {
            "openapi": "3.0.0", 
            "info": {
                "title": "Edge Cases API",
                "version": "1.0.0"
            },
            "servers": [
                {"url": "https://api.example.com"}
            ],
            "paths": {
                "/empty-operation-id": {
                    "get": {
                        "operationId": "",  # Empty operationId
                        "summary": "Empty operation ID test"
                    }
                },
                "/single-char": {
                    "get": {
                        "operationId": "a",  # Single character
                        "summary": "Single character test"
                    }
                },
                "/no-operation-id": {
                    "get": {
                        # No operationId - should use fallback naming
                        "summary": "Missing operationId test"
                    }
                },
                "/mixed-separators": {
                    "get": {
                        "operationId": "api-v1/users_list.all",  # Mixed separator types
                        "summary": "Mixed separators test"
                    }
                },
                "/preserve-acronyms": {
                    "get": {
                        "operationId": "get_API_HTTP_URL",  # Multiple acronyms
                        "summary": "Acronym preservation test"
                    }
                }
            }
        }
    
    def test_parse_openapi_spec(self, discovery, sample_openapi_spec):
        """Test parsing OpenAPI specification."""
        api_spec = discovery._parse_openapi_spec(
            sample_openapi_spec, 
            "https://api.example.com"
        )
        
        assert isinstance(api_spec, OCPAPISpec)
        assert api_spec.title == "Test API"
        assert api_spec.version == "1.0.0"
        assert api_spec.base_url == "https://api.example.com"
        assert len(api_spec.tools) == 3  # GET /users, POST /users, GET /users/{id}
    
    def test_generate_tools_from_spec(self, discovery, sample_openapi_spec):
        """Test tool generation from OpenAPI specification."""
        api_spec = discovery._parse_openapi_spec(
            sample_openapi_spec, 
            "https://api.example.com"
        )
        
        tools = api_spec.tools
        assert len(tools) == 3  # GET /users, POST /users, GET /users/{id}
        
        # Check that we have the expected tools with deterministic names
        tool_names = [t.name for t in tools]
        expected_names = ["getUsers", "postUsers", "getUsersId"]  # camelCase naming
        
        for expected_name in expected_names:
            assert expected_name in tool_names, f"Expected tool name '{expected_name}' not found in {tool_names}"
        
        # Check GET /users tool
        get_users = next((t for t in tools if t.name == "getUsers"), None)
        assert get_users is not None
        assert get_users.method == "GET"
        assert get_users.path == "/users"
        assert get_users.description == "List users"
        assert "limit" in get_users.parameters
        assert get_users.parameters["limit"]["type"] == "integer"
        assert get_users.parameters["limit"]["location"] == "query"
        assert not get_users.parameters["limit"]["required"]
        assert get_users.response_schema is not None
        assert get_users.response_schema["type"] == "array"
    
        # Check POST /users tool
        post_users = next((t for t in tools if t.name == "postUsers"), None)
        assert post_users is not None
        assert post_users.method == "POST"
        assert post_users.path == "/users"
        assert "name" in post_users.parameters
        assert "email" in post_users.parameters
        assert post_users.parameters["name"]["required"]
        assert post_users.parameters["email"]["required"]
        assert post_users.response_schema is not None
        assert post_users.response_schema["type"] == "object"
        
        # Check GET /users/{id} tool
        get_users_id = next((t for t in tools if t.name == "getUsersId"), None)
        assert get_users_id is not None
        assert get_users_id.method == "GET"
        assert get_users_id.path == "/users/{id}"
        assert "id" in get_users_id.parameters
        assert get_users_id.parameters["id"]["required"]
        assert get_users_id.parameters["id"]["location"] == "path"
        assert get_users_id.response_schema is not None
        assert get_users_id.response_schema["type"] == "object"

    def test_normalize_tool_name_slash_separators(self, discovery):
        """Test normalization of operationId with slash separators."""
        assert discovery._normalize_tool_name("meta/root") == "metaRoot"
        assert discovery._normalize_tool_name("repos/disable-vulnerability-alerts") == "reposDisableVulnerabilityAlerts"
        assert discovery._normalize_tool_name("users/list-followers") == "usersListFollowers"
        
    def test_normalize_tool_name_underscore_separators(self, discovery):
        """Test normalization of operationId with underscore separators."""
        assert discovery._normalize_tool_name("admin_apps_approve") == "adminAppsApprove"
        assert discovery._normalize_tool_name("chat_post_message") == "chatPostMessage"
        assert discovery._normalize_tool_name("users_list_all") == "usersListAll"
        
    def test_normalize_tool_name_pascal_case(self, discovery):
        """Test normalization of PascalCase operationIds."""
        assert discovery._normalize_tool_name("FetchAccount") == "fetchAccount"
        assert discovery._normalize_tool_name("CreateAccount") == "createAccount"
        assert discovery._normalize_tool_name("ListAvailablePhoneNumberLocal") == "listAvailablePhoneNumberLocal"
        
    def test_normalize_tool_name_numbers_preserved(self, discovery):
        """Test that numbers are preserved in normalization."""
        assert discovery._normalize_tool_name("v2010/Accounts") == "v2010Accounts"
        assert discovery._normalize_tool_name("api_v2_users") == "apiV2Users"
        assert discovery._normalize_tool_name("get-v3-repos") == "getV3Repos"
        
    def test_normalize_tool_name_acronyms_preserved(self, discovery):
        """Test that acronyms are converted to camelCase."""
        assert discovery._normalize_tool_name("SMS/send") == "smsSend" 
        assert discovery._normalize_tool_name("api/HTTP_request") == "apiHttpRequest"
        assert discovery._normalize_tool_name("get_API_key") == "getApiKey"
        
    def test_normalize_tool_name_fallback_patterns(self, discovery):
        """Test normalization of fallback generated names."""
        assert discovery._normalize_tool_name("get_users") == "getUsers"
        assert discovery._normalize_tool_name("post_users") == "postUsers"
        assert discovery._normalize_tool_name("get_users_id") == "getUsersId"
        assert discovery._normalize_tool_name("delete_repos_issues_comments_id") == "deleteReposIssuesCommentsId"
        
    def test_normalize_tool_name_multiple_separators(self, discovery):
        """Test handling of multiple consecutive separators."""
        assert discovery._normalize_tool_name("api//users") == "apiUsers"
        assert discovery._normalize_tool_name("admin___apps") == "adminApps"
        assert discovery._normalize_tool_name("repos---list") == "reposList"
        assert discovery._normalize_tool_name("api./..users") == "apiUsers"
        
    def test_normalize_tool_name_edge_cases(self, discovery):
        """Test edge cases for normalization."""
        # Empty and None
        assert discovery._normalize_tool_name("") == ""
        assert discovery._normalize_tool_name(None) == None
        
        # Single character  
        assert discovery._normalize_tool_name("a") == "a"
        assert discovery._normalize_tool_name("A") == "a"
        
        # Only separators should return original (but will be caught by validation)
        assert discovery._normalize_tool_name("///") == "///"
        assert discovery._normalize_tool_name("___") == "___"
        
        # Single word
        assert discovery._normalize_tool_name("users") == "users"
        assert discovery._normalize_tool_name("USERS") == "users"
    
    def test_valid_tool_name_validation(self, discovery):
        """Test tool name validation logic."""
        # Valid names
        assert discovery._is_valid_tool_name("metaRoot") == True
        assert discovery._is_valid_tool_name("a") == True
        assert discovery._is_valid_tool_name("test123") == True
        assert discovery._is_valid_tool_name("getUserId") == True
        
        # Invalid names
        assert discovery._is_valid_tool_name("") == False
        assert discovery._is_valid_tool_name("///") == False
        assert discovery._is_valid_tool_name("___") == False
        assert discovery._is_valid_tool_name("123abc") == False  # Starts with number
        assert discovery._is_valid_tool_name("!@#") == False     # Only special chars
    
    def test_operation_id_integration(self, discovery, openapi_spec_with_operation_ids):
        """Test that operationId normalization works in full tool generation flow."""
        api_spec = discovery._parse_openapi_spec(
            openapi_spec_with_operation_ids, 
            "https://api.example.com"
        )
        
        tools = api_spec.tools
        tool_names = [t.name for t in tools]
        
        # Verify normalized operationId names
        expected_names = [
            "metaRoot",                           # meta/root
            "reposDisableVulnerabilityAlerts",    # repos/disable-vulnerability-alerts  
            "adminAppsApprove",                   # admin_apps_approve
            "fetchAccount",                       # FetchAccount
            "createAccount",                      # CreateAccount
            "v2010Accounts",                      # v2010/Accounts
            "smsSend",                            # SMS/send
            "getUsersNoOperationId",              # fallback: get + /users/no-operation-id
            "apiUsers"                            # api//users
        ]
        
        for expected_name in expected_names:
            assert expected_name in tool_names, f"Expected tool name '{expected_name}' not found in {tool_names}"
            
        # Verify specific tools have correct properties
        meta_tool = next((t for t in tools if t.name == "metaRoot"), None)
        assert meta_tool is not None
        assert meta_tool.operation_id == "meta/root"  # Original preserved
        assert meta_tool.method == "GET"
        assert meta_tool.path == "/meta"
        
        # Test acronym preservation
        sms_tool = next((t for t in tools if t.name == "smsSend"), None)
        assert sms_tool is not None
        assert sms_tool.operation_id == "SMS/send"
        
        # Test fallback naming for missing operationId
        fallback_tool = next((t for t in tools if t.name == "getUsersNoOperationId"), None)
        assert fallback_tool is not None
        assert fallback_tool.operation_id is None  # No operationId in spec
        
    def test_edge_cases_integration(self, discovery, openapi_spec_edge_cases):
        """Test edge cases in full tool generation flow."""
        api_spec = discovery._parse_openapi_spec(
            openapi_spec_edge_cases,
            "https://api.example.com"
        )
        
        tools = api_spec.tools
        tool_names = [t.name for t in tools]
        
        expected_tools = [
            "getEmptyOperationId",     # Empty operationId falls back to path
            "a",                       # Single character preserved (valid)
            "getNoOperationId",        # Missing operationId uses path-based naming
            "apiV1UsersListAll",       # Mixed separators normalized
            "getApiHttpUrl"            # Multiple acronyms preserved
        ]
        
        # Check expected tools are present
        for expected_name in expected_tools:
            assert expected_name in tool_names, f"Expected tool name '{expected_name}' not found in {tool_names}"
            
        # Verify total tool count - all 5 operations should create valid tools
        assert len(tools) == 5, f"Expected 5 tools, got {len(tools)}: {tool_names}"
    
    @patch('requests.get')
    def test_discover_api_success(self, mock_get, discovery, sample_openapi_spec):
        """Test successful API discovery."""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json.return_value = sample_openapi_spec
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        api_spec = discovery.discover_api(
            "https://api.example.com/openapi.json"
        )
        
        assert isinstance(api_spec, OCPAPISpec)
        assert api_spec.title == "Test API"
        assert len(api_spec.tools) == 3
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_discover_api_with_base_url_override(self, mock_get, discovery, sample_openapi_spec):
        """Test API discovery with base URL override."""
        mock_response = Mock()
        mock_response.json.return_value = sample_openapi_spec
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        api_spec = discovery.discover_api(
            "https://api.example.com/openapi.json",
            base_url="https://custom.example.com"
        )
        
        assert api_spec.base_url == "https://custom.example.com"
    
    @patch('requests.get')
    def test_discover_api_failure(self, mock_get, discovery):
        """Test API discovery failure handling."""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception, match="Network error"):
            discovery.discover_api("https://api.example.com/openapi.json")
    
    def test_search_tools(self, discovery):
        """Test tool searching functionality."""
        # Create some sample tools
        tools = [
            OCPTool(
                name="list_users",
                description="Get all users from the system",
                method="GET",
                path="/users",
                parameters={},
                response_schema=None
            ),
            OCPTool(
                name="create_user",
                description="Create a new user account",
                method="POST",
                path="/users",
                parameters={},
                response_schema=None
            ),
            OCPTool(
                name="list_orders",
                description="Get customer orders",
                method="GET",
                path="/orders",
                parameters={},
                response_schema=None
            )
        ]
        
        api_spec = OCPAPISpec(
            title="Test API",
            version="1.0.0",
            base_url="https://api.example.com",
            description="A test API for testing purposes",
            tools=tools,
            raw_spec={}
        )
        
        # Test search by name
        user_tools = discovery.search_tools(api_spec, "user")
        assert len(user_tools) == 2
        assert all("user" in tool.name.lower() or "user" in tool.description.lower() 
                  for tool in user_tools)
        
        # Test search by description
        create_tools = discovery.search_tools(api_spec, "create")
        assert len(create_tools) == 1
        assert create_tools[0].name == "create_user"
        
        # Test no matches
        no_matches = discovery.search_tools(api_spec, "nonexistent")
        assert len(no_matches) == 0
    
    def test_generate_tool_documentation(self, discovery):
        """Test tool documentation generation."""
        tool = OCPTool(
            name="create_user",
            description="Create a new user account",
            method="POST",
            path="/users",
            parameters={
                "name": {
                    "type": "string",
                    "description": "User's full name",
                    "required": True,
                    "location": "body"
                },
                "email": {
                    "type": "string", 
                    "description": "User's email address",
                    "required": True,
                    "location": "body"
                },
                "age": {
                    "type": "integer",
                    "description": "User's age",
                    "required": False,
                    "location": "body"
                }
            },
            response_schema=None
        )
        
        doc = discovery.generate_tool_documentation(tool)
        
        assert "create_user" in doc
        assert "Create a new user account" in doc
        assert "POST" in doc
        assert "/users" in doc
        assert "name" in doc
        assert "email" in doc
        assert "age" in doc
        assert "required" in doc.lower()
        assert "optional" in doc.lower()
    
    @patch('ocp_agent.schema_discovery.requests.get')
    def test_discover_api_with_refs(self, mock_get, discovery):
        """Test that $ref references are resolved in response schemas."""
        openapi_spec_with_refs = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/queue": {
                    "post": {
                        "operationId": "updateQueue",
                        "summary": "Update queue",
                        "responses": {
                            "200": {
                                "description": "Queue updated",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Queue"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "Queue": {
                        "type": "object",
                        "properties": {
                            "sid": {"type": "string"},
                            "friendly_name": {"type": "string"},
                            "current_size": {"type": "integer"}
                        }
                    }
                }
            }
        }
        
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json.return_value = openapi_spec_with_refs
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Discover API
        api_spec = discovery.discover_api("https://api.example.com/openapi.json")
        
        # Should have one tool
        assert len(api_spec.tools) == 1
        tool = api_spec.tools[0]
        
        # Verify the $ref was resolved
        assert tool.name == "updateQueue"
        assert tool.response_schema is not None
        assert tool.response_schema.get("type") == "object"
        assert "properties" in tool.response_schema
        assert "sid" in tool.response_schema["properties"]
        assert "friendly_name" in tool.response_schema["properties"]
        assert "current_size" in tool.response_schema["properties"]
        
        # Should NOT contain $ref anymore
        assert "$ref" not in str(tool.response_schema)
    
    @patch('ocp_agent.schema_discovery.requests.get')
    def test_discover_api_with_circular_refs(self, mock_get, discovery):
        """Test that circular $ref references are handled gracefully."""
        openapi_spec_with_circular_refs = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/node": {
                    "get": {
                        "operationId": "getNode",
                        "summary": "Get node",
                        "responses": {
                            "200": {
                                "description": "Node retrieved",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Node"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "Node": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "children": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/Node"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json.return_value = openapi_spec_with_circular_refs
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Should not raise an error
        api_spec = discovery.discover_api("https://api.example.com/openapi.json")
        
        # Should have one tool
        assert len(api_spec.tools) == 1
        tool = api_spec.tools[0]
        
        # Verify the response schema exists and has the expected structure
        assert tool.response_schema is not None
        assert tool.response_schema.get("type") == "object"
        assert "properties" in tool.response_schema
        assert "id" in tool.response_schema["properties"]
        assert "children" in tool.response_schema["properties"]
        
        # The circular ref in children.items should be replaced with a placeholder
        children_schema = tool.response_schema["properties"]["children"]
        assert children_schema.get("type") == "array"
        assert "items" in children_schema
        # The circular ref should be broken with a placeholder
        assert children_schema["items"].get("description") == "Circular reference"
    
    @patch('ocp_agent.schema_discovery.requests.get')
    def test_discover_api_with_polymorphic_keywords(self, mock_get, discovery):
        """Test that $refs inside anyOf/oneOf/allOf pointing to objects are kept unresolved."""
        openapi_spec_with_polymorphic = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/payment": {
                    "get": {
                        "operationId": "getPayment",
                        "summary": "Get payment",
                        "responses": {
                            "200": {
                                "description": "Payment retrieved",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Payment"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "Payment": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "amount": {"type": "integer"},
                            "status": {
                                "anyOf": [
                                    {"type": "string"},
                                    {"type": "integer"}
                                ]
                            },
                            "source": {
                                "anyOf": [
                                    {"$ref": "#/components/schemas/Card"},
                                    {"$ref": "#/components/schemas/BankAccount"},
                                    {"$ref": "#/components/schemas/Wallet"}
                                ]
                            }
                        }
                    },
                    "Card": {
                        "type": "object",
                        "properties": {
                            "brand": {"type": "string"},
                            "last4": {"type": "string"}
                        }
                    },
                    "BankAccount": {
                        "type": "object",
                        "properties": {
                            "routing_number": {"type": "string"},
                            "account_number": {"type": "string"}
                        }
                    },
                    "Wallet": {
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string"},
                            "wallet_id": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json.return_value = openapi_spec_with_polymorphic
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Discover API
        api_spec = discovery.discover_api("https://api.example.com/openapi.json")
        
        # Should have one tool
        assert len(api_spec.tools) == 1
        tool = api_spec.tools[0]
        
        # Verify the response schema exists
        assert tool.response_schema is not None
        assert tool.response_schema.get("type") == "object"
        assert "properties" in tool.response_schema
        
        # Status field with primitive anyOf (string/integer) should be resolved
        status_schema = tool.response_schema["properties"]["status"]
        assert "anyOf" in status_schema
        assert status_schema["anyOf"][0] == {"type": "string"}
        assert status_schema["anyOf"][1] == {"type": "integer"}
        # Should not contain any $refs
        assert "$ref" not in str(status_schema)
        
        # Source field with object $refs in anyOf should keep the refs unresolved
        source_schema = tool.response_schema["properties"]["source"]
        assert "anyOf" in source_schema
        # The $refs to object schemas should be preserved
        assert source_schema["anyOf"][0] == {"$ref": "#/components/schemas/Card"}
        assert source_schema["anyOf"][1] == {"$ref": "#/components/schemas/BankAccount"}
        assert source_schema["anyOf"][2] == {"$ref": "#/components/schemas/Wallet"}


class TestOCPTool:
    """Test OCPTool dataclass."""
    
    def test_tool_creation(self):
        """Test creating an OCPTool instance."""
        tool = OCPTool(
            name="test_tool",
            description="A test tool",
            method="GET",
            path="/test",
            parameters={"param": {"type": "string"}},
            response_schema=None
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.method == "GET"
        assert tool.path == "/test"
        assert tool.parameters["param"]["type"] == "string"


class TestOCPAPISpec:
    """Test OCPAPISpec dataclass."""
    
    def test_api_spec_creation(self):
        """Test creating an OCPAPISpec instance."""
        tools = [
            OCPTool("tool1", "Description 1", "GET", "/path1", {}, None),
            OCPTool("tool2", "Description 2", "POST", "/path2", {}, None)
        ]
        
        api_spec = OCPAPISpec(
            title="Test API",
            version="1.0.0",
            base_url="https://api.example.com",
            description="A test API for testing purposes",
            tools=tools,
            raw_spec={}
        )
        
        assert api_spec.title == "Test API"
        assert api_spec.version == "1.0.0" 
        assert api_spec.base_url == "https://api.example.com"
        assert api_spec.description == "A test API for testing purposes"
        assert len(api_spec.tools) == 2
        assert api_spec.tools[0].name == "tool1"
        assert api_spec.tools[1].name == "tool2"


class TestSwagger2Support:
    """Test Swagger 2.0 specification support."""
    
    @pytest.fixture
    def discovery(self):
        """Create a schema discovery instance."""
        return OCPSchemaDiscovery()
    
    @pytest.fixture
    def swagger2_spec(self):
        """Basic Swagger 2.0 specification."""
        return {
            "swagger": "2.0",
            "info": {
                "title": "Swagger 2.0 API",
                "version": "1.0.0",
                "description": "A test API using Swagger 2.0"
            },
            "host": "api.example.com",
            "basePath": "/v1",
            "schemes": ["https"],
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "summary": "List users",
                        "description": "Get a list of all users",
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "type": "integer",
                                "required": False
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "List of users",
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "operationId": "createUser",
                        "summary": "Create user",
                        "description": "Create a new user",
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"}
                                    },
                                    "required": ["name", "email"]
                                }
                            }
                        ],
                        "responses": {
                            "201": {
                                "description": "User created",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                        "email": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                },
                "/users/{id}": {
                    "get": {
                        "operationId": "getUserById",
                        "summary": "Get user",
                        "description": "Get a specific user by ID",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "type": "string",
                                "required": True
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "User details",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                        "email": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def test_detect_swagger2_version(self, discovery, swagger2_spec):
        """Test that Swagger 2.0 version is correctly detected."""
        version = discovery._detect_spec_version(swagger2_spec)
        assert version == "swagger_2"
    
    def test_swagger2_base_url_extraction(self, discovery, swagger2_spec):
        """Test base URL extraction from Swagger 2.0 (host + basePath + schemes)."""
        discovery._spec_version = "swagger_2"
        base_url = discovery._extract_base_url(swagger2_spec)
        assert base_url == "https://api.example.com/v1"
    
    def test_swagger2_base_url_multiple_schemes(self, discovery):
        """Test base URL extraction with multiple schemes (uses first one)."""
        spec = {
            "swagger": "2.0",
            "host": "api.example.com",
            "basePath": "/api",
            "schemes": ["http", "https"]
        }
        discovery._spec_version = "swagger_2"
        base_url = discovery._extract_base_url(spec)
        assert base_url == "http://api.example.com/api"
    
    def test_swagger2_base_url_no_schemes(self, discovery):
        """Test base URL extraction defaults to https when no schemes."""
        spec = {
            "swagger": "2.0",
            "host": "api.example.com",
            "basePath": "/v2"
        }
        discovery._spec_version = "swagger_2"
        base_url = discovery._extract_base_url(spec)
        assert base_url == "https://api.example.com/v2"
    
    def test_swagger2_response_schema_parsing(self, discovery, swagger2_spec):
        """Test that Swagger 2.0 response schemas are correctly parsed."""
        discovery._spec_version = "swagger_2"
        responses = swagger2_spec["paths"]["/users"]["get"]["responses"]
        
        schema = discovery._parse_responses(responses, swagger2_spec, {})
        
        assert schema is not None
        assert schema["type"] == "array"
        assert "items" in schema
        assert schema["items"]["type"] == "object"
    
    def test_swagger2_body_parameter_parsing(self, discovery, swagger2_spec):
        """Test that Swagger 2.0 body parameters are correctly parsed."""
        discovery._spec_version = "swagger_2"
        post_operation = swagger2_spec["paths"]["/users"]["post"]
        body_param = post_operation["parameters"][0]
        
        params = discovery._parse_swagger2_body_parameter(body_param, swagger2_spec, {})
        
        assert "name" in params
        assert "email" in params
        assert params["name"]["type"] == "string"
        assert params["name"]["required"] == True
        assert params["name"]["location"] == "body"
        assert params["email"]["required"] == True
    
    @patch('ocp_agent.schema_discovery.requests.get')
    def test_discover_swagger2_api(self, mock_get, discovery, swagger2_spec):
        """Test full API discovery with Swagger 2.0 spec."""
        mock_response = Mock()
        mock_response.json.return_value = swagger2_spec
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        api_spec = discovery.discover_api("https://api.example.com/swagger.json")
        
        assert api_spec.title == "Swagger 2.0 API"
        assert api_spec.version == "1.0.0"
        assert api_spec.base_url == "https://api.example.com/v1"
        assert len(api_spec.tools) == 3
        
        # Check GET /users
        get_users = next(t for t in api_spec.tools if t.name == "getUsers")
        assert get_users.method == "GET"
        assert get_users.path == "/users"
        assert "limit" in get_users.parameters
        assert get_users.response_schema is not None
        assert get_users.response_schema["type"] == "array"
        
        # Check POST /users
        post_users = next(t for t in api_spec.tools if t.name == "createUser")
        assert post_users.method == "POST"
        assert post_users.path == "/users"
        assert "name" in post_users.parameters
        assert "email" in post_users.parameters
        assert post_users.parameters["name"]["required"] == True
        assert post_users.response_schema is not None
        
        # Check GET /users/{id}
        get_user = next(t for t in api_spec.tools if t.name == "getUserById")
        assert get_user.method == "GET"
        assert get_user.path == "/users/{id}"
        assert "id" in get_user.parameters
        assert get_user.parameters["id"]["location"] == "path"
        assert get_user.response_schema is not None


class TestResourceFiltering:
    """Test resource-based filtering functionality for discover_api method."""
    
    @pytest.fixture
    def discovery(self):
        """Create a schema discovery instance."""
        return OCPSchemaDiscovery()
    
    @pytest.fixture
    def openapi_spec_with_resources(self):
        """OpenAPI spec with multiple tools having different resource paths."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "GitHub API", "version": "3.0"},
            "servers": [{"url": "https://api.github.com"}],
            "paths": {
                "/repos/{owner}/{repo}": {
                    "get": {
                        "operationId": "repos/get",
                        "summary": "Get a repository",
                        "parameters": [
                            {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                            {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {"200": {"description": "Repository details"}}
                    }
                },
                "/user/repos": {
                    "get": {
                        "operationId": "repos/listForAuthenticatedUser",
                        "summary": "List user repositories",
                        "responses": {"200": {"description": "List of repositories"}}
                    }
                },
                "/repos/{owner}/{repo}/issues": {
                    "get": {
                        "operationId": "issues/listForRepo",
                        "summary": "List repository issues",
                        "parameters": [
                            {"name": "owner", "in": "path", "required": True, "schema": {"type": "string"}},
                            {"name": "repo", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {"200": {"description": "List of issues"}}
                    }
                },
                "/orgs/{org}/members": {
                    "get": {
                        "operationId": "orgs/listMembers",
                        "summary": "List organization members",
                        "parameters": [
                            {"name": "org", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {"200": {"description": "List of members"}}
                    }
                }
            }
        }
    
    @pytest.fixture
    def tools_with_resources(self):
        """Create test tools with different resource paths."""
        return [
            OCPTool(
                name="reposGet",
                description="Get a repository",
                method="GET",
                path="/repos/{owner}/{repo}",
                parameters={},
                response_schema=None,
                operation_id="repos/get",
                tags=["repos"]
            ),
            OCPTool(
                name="reposListForAuthenticatedUser", 
                description="List user repositories",
                method="GET",
                path="/user/repos",
                parameters={},
                response_schema=None,
                operation_id="repos/listForAuthenticatedUser",
                tags=["repos"]
            ),
            OCPTool(
                name="issuesListForRepo",
                description="List repository issues", 
                method="GET",
                path="/repos/{owner}/{repo}/issues",
                parameters={},
                response_schema=None,
                operation_id="issues/listForRepo",
                tags=["issues"]
            ),
            OCPTool(
                name="orgsListMembers",
                description="List organization members",
                method="GET",
                path="/orgs/{org}/members",
                parameters={},
                response_schema=None,
                operation_id="orgs/listMembers",
                tags=["orgs"]
            )
        ]
    
    def test_filter_tools_by_resources_single_resource(self, discovery, tools_with_resources):
        """Test filtering tools by a single resource name."""
        # Filter for repos resources only (first segment matching)
        filtered_tools = discovery._filter_tools_by_resources(tools_with_resources, ["repos"])
        
        assert len(filtered_tools) == 2  # /repos/{owner}/{repo}, /repos/{owner}/{repo}/issues (NOT /user/repos)
        path_set = {tool.path for tool in filtered_tools}
        assert "/repos/{owner}/{repo}" in path_set
        assert "/repos/{owner}/{repo}/issues" in path_set
    
    def test_filter_tools_by_resources_multiple_resources(self, discovery, tools_with_resources):
        """Test filtering tools by multiple resource names."""
        # Filter for both repos and orgs resources (first segment matching)
        filtered_tools = discovery._filter_tools_by_resources(tools_with_resources, ["repos", "orgs"])
        
        assert len(filtered_tools) == 3  # /repos/..., /repos/.../issues, /orgs/... (NOT /user/repos)
    
    def test_filter_tools_by_resources_case_insensitive(self, discovery, tools_with_resources):
        """Test that resource filtering is case-insensitive."""
        # Filter with different case (first segment matching)
        filtered_tools = discovery._filter_tools_by_resources(tools_with_resources, ["REPOS", "Orgs"])
        
        assert len(filtered_tools) == 3
    
    def test_filter_tools_by_resources_no_matches(self, discovery, tools_with_resources):
        """Test filtering tools with resources that don't match any paths."""
        # Filter for resources that don't exist
        filtered_tools = discovery._filter_tools_by_resources(tools_with_resources, ["payments", "customers"])
        
        assert len(filtered_tools) == 0
    
    def test_filter_tools_by_resources_empty_list(self, discovery, tools_with_resources):
        """Test filtering with empty include_resources list returns all tools."""
        # Empty list should return all tools
        filtered_tools = discovery._filter_tools_by_resources(tools_with_resources, [])
        
        assert len(filtered_tools) == 4
        assert filtered_tools == tools_with_resources
    
    def test_filter_tools_by_resources_none(self, discovery, tools_with_resources):
        """Test filtering with None include_resources returns all tools."""
        # None should return all tools
        filtered_tools = discovery._filter_tools_by_resources(tools_with_resources, None)
        
        assert len(filtered_tools) == 4
        assert filtered_tools == tools_with_resources
    
    def test_filter_tools_by_resources_exact_match(self, discovery):
        """Test that only exact segment matches are included, not substring matches."""
        tools = [
            OCPTool(name="listPaymentMethods", description="List payment methods", method="GET", 
                   path="/payment_methods", parameters={}, response_schema=None),
            OCPTool(name="createPaymentIntent", description="Create payment intent", method="POST",
                   path="/payment_intents", parameters={}, response_schema=None),
            OCPTool(name="listPayments", description="List payments", method="GET",
                   path="/payments", parameters={}, response_schema=None)
        ]
        
        # Filter for "payment" should not match any (no exact segment match)
        filtered_tools = discovery._filter_tools_by_resources(tools, ["payment"])
        assert len(filtered_tools) == 0  # "payment" doesn't exactly match any first segment
        
        # Filter for "payments" should match the exact first segment
        filtered_tools = discovery._filter_tools_by_resources(tools, ["payments"])
        assert len(filtered_tools) == 1
        assert filtered_tools[0].path == "/payments"
        
        # Filter for "payment_methods" should match
        filtered_tools = discovery._filter_tools_by_resources(tools, ["payment_methods"])
        assert len(filtered_tools) == 1
        assert filtered_tools[0].path == "/payment_methods"
    
    def test_filter_tools_by_resources_with_dots(self, discovery):
        """Test that dot-separated paths work correctly (e.g., Slack API)."""
        tools = [
            OCPTool(name="conversationsReplies", description="Get conversation replies", method="GET",
                   path="/conversations.replies", parameters={}, response_schema=None),
            OCPTool(name="conversationsHistory", description="Get conversation history", method="GET",
                   path="/conversations.history", parameters={}, response_schema=None),
            OCPTool(name="chatPostMessage", description="Post a message", method="POST",
                   path="/chat.postMessage", parameters={}, response_schema=None)
        ]
        
        # Filter for "conversations" should match both conversation endpoints
        filtered_tools = discovery._filter_tools_by_resources(tools, ["conversations"])
        assert len(filtered_tools) == 2
        assert all("conversations" in tool.path for tool in filtered_tools)
        
        # Filter for "chat" should match the chat endpoint
        filtered_tools = discovery._filter_tools_by_resources(tools, ["chat"])
        assert len(filtered_tools) == 1
        assert filtered_tools[0].path == "/chat.postMessage"
    
    def test_filter_tools_by_resources_no_substring_match(self, discovery):
        """Test that substring matching doesn't work - only exact segment matches."""
        tools = [
            OCPTool(name="listRepos", description="List repos", method="GET",
                   path="/repos/{owner}/{repo}", parameters={}, response_schema=None),
            OCPTool(name="listRepositories", description="List enterprise repositories", method="GET",
                   path="/enterprises/{enterprise}/code-security/configurations/{config_id}/repositories",
                   parameters={}, response_schema=None)
        ]
        
        # Filter for "repos" should match "/repos/{owner}/{repo}"
        # Should NOT match "/enterprises/.../repositories" (repos != repositories)
        filtered_tools = discovery._filter_tools_by_resources(tools, ["repos"])
        assert len(filtered_tools) == 1
        assert filtered_tools[0].path == "/repos/{owner}/{repo}"
        
        # Filter for "repositories" should match the enterprise endpoint (but first segment is "enterprises")
        filtered_tools = discovery._filter_tools_by_resources(tools, ["repositories"])
        assert len(filtered_tools) == 0  # "repositories" is not the first segment
        
        # Filter for "enterprises" should match the enterprise endpoint
        filtered_tools = discovery._filter_tools_by_resources(tools, ["enterprises"])
        assert len(filtered_tools) == 1
        assert "/enterprises" in filtered_tools[0].path
    
    def test_filter_tools_by_resources_with_path_prefix(self, discovery):
        """Test filtering with path_prefix to strip version prefixes."""
        tools = [
            OCPTool(name="listPayments", description="List payments", method="GET",
                   path="/v1/payments", parameters={}, response_schema=None),
            OCPTool(name="createCharge", description="Create charge", method="POST",
                   path="/v1/charges", parameters={}, response_schema=None),
            OCPTool(name="legacyPayment", description="Legacy payment", method="GET",
                   path="/v2/payments", parameters={}, response_schema=None)
        ]
        
        # Filter for "payments" with /v1 prefix
        filtered_tools = discovery._filter_tools_by_resources(tools, ["payments"], path_prefix="/v1")
        assert len(filtered_tools) == 1
        assert filtered_tools[0].path == "/v1/payments"
        
        # Filter for "payments" with /v2 prefix
        filtered_tools = discovery._filter_tools_by_resources(tools, ["payments"], path_prefix="/v2")
        assert len(filtered_tools) == 1
        assert filtered_tools[0].path == "/v2/payments"
        
        # Filter without prefix - no matches (first segment is "v1" or "v2")
        filtered_tools = discovery._filter_tools_by_resources(tools, ["payments"])
        assert len(filtered_tools) == 0
    
    def test_filter_tools_by_resources_first_segment_only(self, discovery):
        """Test that only the first resource segment is matched."""
        tools = [
            OCPTool(name="listRepoIssues", description="List repo issues", method="GET",
                   path="/repos/{owner}/{repo}/issues", parameters={}, response_schema=None),
            OCPTool(name="listUserRepos", description="List user repos", method="GET",
                   path="/user/repos", parameters={}, response_schema=None)
        ]
        
        # Filter for "repos" - should match /repos/... but NOT /user/repos (first segment is "user")
        filtered_tools = discovery._filter_tools_by_resources(tools, ["repos"])
        assert len(filtered_tools) == 1
        assert filtered_tools[0].path == "/repos/{owner}/{repo}/issues"
        
        # Filter for "user" - should match /user/repos
        filtered_tools = discovery._filter_tools_by_resources(tools, ["user"])
        assert len(filtered_tools) == 1
        assert filtered_tools[0].path == "/user/repos"
        
        # Filter for "issues" - should NOT match anything (issues is not first segment)
        filtered_tools = discovery._filter_tools_by_resources(tools, ["issues"])
        assert len(filtered_tools) == 0
    
    @patch('ocp_agent.schema_discovery.requests.get')
    def test_discover_api_with_include_resources(self, mock_get, discovery, openapi_spec_with_resources):
        """Test discover_api method with include_resources parameter."""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json.return_value = openapi_spec_with_resources
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Discover API with only repos resources (first segment matching)
        api_spec = discovery.discover_api(
            "https://api.github.com/openapi.json",
            include_resources=["repos"]
        )
        
        # Should have 2 tools starting with /repos
        assert len(api_spec.tools) == 2
        assert all(tool.path.lower().startswith("/repos") for tool in api_spec.tools)
    
    @patch('ocp_agent.schema_discovery.requests.get')
    def test_discover_api_with_multiple_include_resources(self, mock_get, discovery, openapi_spec_with_resources):
        """Test discover_api method with multiple include_resources."""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json.return_value = openapi_spec_with_resources
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Discover API with repos and orgs resources (first segment matching)
        api_spec = discovery.discover_api(
            "https://api.github.com/openapi.json",
            include_resources=["repos", "orgs"]
        )
        
        # Should have 3 tools (repos, repos/issues, orgs)
        assert len(api_spec.tools) == 3
    
    @patch('ocp_agent.schema_discovery.requests.get')
    def test_discover_api_without_include_resources(self, mock_get, discovery, openapi_spec_with_resources):
        """Test discover_api method without include_resources returns all tools."""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json.return_value = openapi_spec_with_resources
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Discover API without filtering
        api_spec = discovery.discover_api("https://api.github.com/openapi.json")
        
        # Should have all 4 tools
        assert len(api_spec.tools) == 4