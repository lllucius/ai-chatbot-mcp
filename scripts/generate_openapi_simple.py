#!/usr/bin/env python3
"""
Simple OpenAPI JSON generation script for AI Chatbot MCP.
Creates OpenAPI specification based on documented API endpoints.
"""

import json
from pathlib import Path

def get_basic_openapi_schema():
    """Generate basic OpenAPI schema with documented endpoints."""
    
    # Base OpenAPI schema structure
    openapi_schema = {
        "openapi": "3.0.2",
        "info": {
            "title": "AI Chatbot MCP API",
            "description": "Advanced AI chatbot backend API with FastMCP integration",
            "version": "0.1.0",
            "x-logo": {
                "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
            }
        },
        "servers": [
            {
                "url": "/",
                "description": "Current server"
            }
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter JWT token"
                }
            },
            "schemas": {
                "APIResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"},
                        "data": {"type": "object"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "UserResponse": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "username": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "is_active": {"type": "boolean"},
                        "is_superuser": {"type": "boolean"},
                        "created_at": {"type": "string", "format": "date-time"}
                    }
                },
                "LoginRequest": {
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string"}
                    }
                },
                "Token": {
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string"},
                        "token_type": {"type": "string"}
                    }
                }
            }
        },
        "paths": {
            # Root endpoints
            "/": {
                "get": {
                    "summary": "Root endpoint",
                    "description": "Root endpoint with basic application information",
                    "responses": {
                        "200": {
                            "description": "Application information",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["Root"]
                }
            },
            "/ping": {
                "get": {
                    "summary": "Health check",
                    "description": "Simple health check endpoint for load balancers",
                    "responses": {
                        "200": {
                            "description": "Health status",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    },
                    "tags": ["Health"]
                }
            },
            
            # Authentication endpoints
            "/api/v1/auth/register": {
                "post": {
                    "summary": "Register new user",
                    "description": "Register a new user account",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "User registered successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["authentication"]
                }
            },
            "/api/v1/auth/login": {
                "post": {
                    "summary": "User login",
                    "description": "Authenticate user and generate JWT access token",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LoginRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Authentication successful",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["authentication"]
                }
            },
            "/api/v1/auth/logout": {
                "post": {
                    "summary": "User logout",
                    "description": "Logout current user session",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Logged out successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["authentication"]
                }
            },
            "/api/v1/auth/refresh": {
                "post": {
                    "summary": "Refresh token",
                    "description": "Refresh JWT access token for session continuation",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Token refreshed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["authentication"]
                }
            },
            "/api/v1/auth/password-reset": {
                "post": {
                    "summary": "Request password reset",
                    "description": "Request password reset through administrative channels (DEPRECATED: Use /api/v1/users/password-reset instead)",
                    "deprecated": True,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Password reset request processed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["authentication"]
                }
            },
            "/api/v1/auth/password-reset/confirm": {
                "post": {
                    "summary": "Confirm password reset",
                    "description": "Confirm password reset through administrative channels (DEPRECATED: Use /api/v1/users/password-reset/confirm instead)",
                    "deprecated": True,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Password reset confirmed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["authentication"]
                }
            },
            
            # Users endpoints
            "/api/v1/users/me": {
                "get": {
                    "summary": "Get current user profile",
                    "description": "Get current user profile with statistics",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "User profile retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["users"]
                },
                "put": {
                    "summary": "Update current user profile",
                    "description": "Update current user profile information",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "User profile updated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["users"]
                }
            },
            "/api/v1/users/me/change-password": {
                "post": {
                    "summary": "Change password",
                    "description": "Change current user password with security verification",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Password changed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["users"]
                }
            },
            "/api/v1/users/password-reset": {
                "post": {
                    "summary": "Request password reset",
                    "description": "Request password reset for user account (consolidated endpoint)",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Password reset request processed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["users"]
                }
            },
            "/api/v1/users/password-reset/confirm": {
                "post": {
                    "summary": "Confirm password reset",
                    "description": "Confirm password reset with token (consolidated endpoint)",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Password reset confirmed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["users"]
                }
            },
            "/api/v1/users/": {
                "get": {
                    "summary": "List users",
                    "description": "List all users with filtering and pagination",
                    "security": [{"bearerAuth": []}],
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "schema": {"type": "integer", "minimum": 1, "default": 1}
                        },
                        {
                            "name": "size",
                            "in": "query",
                            "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Users retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["users"]
                }
            },
            
            # Health endpoints
            "/api/v1/health/": {
                "get": {
                    "summary": "System health check",
                    "description": "Comprehensive system health check",
                    "responses": {
                        "200": {
                            "description": "System health status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["health"]
                }
            },
            "/api/v1/health/database": {
                "get": {
                    "summary": "Database health check",
                    "description": "Check database connectivity and health",
                    "responses": {
                        "200": {
                            "description": "Database health status",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["health"]
                }
            },
            
            # Analytics endpoints
            "/api/v1/analytics/overview": {
                "get": {
                    "summary": "System overview",
                    "description": "Get system overview analytics",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "System overview data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["analytics"]
                }
            },
            "/api/v1/analytics/performance": {
                "get": {
                    "summary": "Performance metrics",
                    "description": "Get performance metrics",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Performance metrics data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["analytics"]
                }
            },
            
            # Document endpoints
            "/api/v1/documents/": {
                "get": {
                    "summary": "List documents",
                    "description": "List documents with filtering and pagination",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Documents list",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["documents"]
                },
                "post": {
                    "summary": "Upload document",
                    "description": "Upload a new document for processing",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Document uploaded successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                                }
                            }
                        }
                    },
                    "tags": ["documents"]
                }
            },
            
            # Additional endpoint categories would be added here...
            # For brevity, including key endpoints that demonstrate the API structure
        },
        
        "tags": [
            {"name": "Root", "description": "Root application endpoints"},
            {"name": "Health", "description": "Health check endpoints"},
            {"name": "authentication", "description": "Authentication and authorization"},
            {"name": "users", "description": "User management operations"},
            {"name": "analytics", "description": "Analytics and reporting"},
            {"name": "documents", "description": "Document management"},
            {"name": "conversations", "description": "Conversation management"},
            {"name": "database", "description": "Database operations"},
            {"name": "mcp", "description": "MCP server management"},
            {"name": "profiles", "description": "LLM parameter profiles"},
            {"name": "prompts", "description": "Prompt management"},
            {"name": "search", "description": "Search functionality"},
            {"name": "tasks", "description": "Background task management"}
        ]
    }
    
    return openapi_schema

def generate_openapi_json(output_path: str = "openapi.json"):
    """Generate OpenAPI JSON file."""
    try:
        openapi_schema = get_basic_openapi_schema()
        
        # Write to JSON file
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        
        print(f"✅ OpenAPI JSON generated successfully: {output_file}")
        print(f"📄 Schema contains {len(openapi_schema.get('paths', {}))} endpoints")
        print(f"🏷️  API Version: {openapi_schema.get('info', {}).get('version', 'unknown')}")
        print(f"📝 Title: {openapi_schema.get('info', {}).get('title', 'unknown')}")
        
        return str(output_file)
        
    except Exception as e:
        print(f"❌ Failed to generate OpenAPI JSON: {e}")
        raise

def print_openapi_info():
    """Print information about OpenAPI endpoints."""
    try:
        openapi_schema = get_basic_openapi_schema()
        
        print("=" * 60)
        print("AI CHATBOT MCP - OPENAPI ENDPOINTS SUMMARY")
        print("=" * 60)
        print()
        
        print("📊 API INFORMATION:")
        print(f"  • Title: {openapi_schema.get('info', {}).get('title', 'unknown')}")
        print(f"  • Version: {openapi_schema.get('info', {}).get('version', 'unknown')}")
        print(f"  • Total Endpoints: {len(openapi_schema.get('paths', {}))}")
        print()
        
        print("🔗 ENDPOINTS BY TAG:")
        
        # Group endpoints by tags
        endpoints_by_tag = {}
        for path, methods in openapi_schema.get('paths', {}).items():
            for method, details in methods.items():
                tags = details.get('tags', ['untagged'])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    endpoints_by_tag[tag].append(f"{method.upper()} {path}")
        
        # Print endpoints grouped by tag
        for tag, endpoints in sorted(endpoints_by_tag.items()):
            print(f"\n{tag.upper()}:")
            for endpoint in sorted(endpoints):
                print(f"  • {endpoint}")
        
        print()
        print("📋 KEY API FEATURES:")
        print("  • JWT Bearer token authentication")
        print("  • Comprehensive user management")
        print("  • Document upload and processing")
        print("  • Real-time analytics and monitoring")
        print("  • Conversation management")
        print("  • Background task processing")
        print()
        
    except Exception as e:
        print(f"❌ Failed to analyze OpenAPI schema: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate OpenAPI JSON for AI Chatbot MCP")
    parser.add_argument(
        "--output", "-o", 
        default="openapi.json",
        help="Output file path (default: openapi.json)"
    )
    parser.add_argument(
        "--info", "-i",
        action="store_true",
        help="Show OpenAPI information without generating file"
    )
    
    args = parser.parse_args()
    
    if args.info:
        print_openapi_info()
    else:
        generate_openapi_json(args.output)