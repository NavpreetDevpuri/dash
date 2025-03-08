from flask import Blueprint, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
import os
import json

# Create a blueprint for the Swagger documentation
api_docs_bp = Blueprint('api_docs', __name__)

# Define the Swagger JSON specification
SWAGGER_URL = '/api-docs'  # URL for exposing Swagger UI
API_URL = '/api-docs/swagger.json'  # URL to access the API documentation

# Create Swagger UI blueprint
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Dash API Documentation"
    }
)

def generate_swagger_spec():
    """
    Generate the OpenAPI/Swagger specification as a dictionary
    """
    swagger_spec = {
        "swagger": "2.0",
        "info": {
            "title": "Dash API",
            "description": "API documentation for Dash backend services",
            "version": "1.0.0"
        },
        "host": f"localhost:{os.getenv('PORT', '5000')}",  # Adjust based on your environment
        "basePath": "/",
        "schemes": ["http"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "paths": {
            "/auth/signup": {
                "post": {
                    "tags": ["auth"],
                    "summary": "Create a new user account",
                    "description": "Register a new user with full name, email, and password",
                    "consumes": ["application/json"],
                    "produces": ["application/json"],
                    "parameters": [
                        {
                            "in": "body",
                            "name": "body",
                            "description": "User signup information",
                            "required": True,
                            "schema": {
                                "$ref": "#/definitions/SignupRequest"
                            }
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "User created successfully",
                            "schema": {
                                "$ref": "#/definitions/AuthResponse"
                            }
                        },
                        "400": {
                            "description": "Invalid input or email already exists",
                            "schema": {
                                "$ref": "#/definitions/ErrorResponse"
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "schema": {
                                "$ref": "#/definitions/ErrorResponse"
                            }
                        }
                    }
                }
            },
            "/auth/signin": {
                "post": {
                    "tags": ["auth"],
                    "summary": "Authenticate user",
                    "description": "Login with email and password",
                    "consumes": ["application/json"],
                    "produces": ["application/json"],
                    "parameters": [
                        {
                            "in": "body",
                            "name": "body",
                            "description": "User login information",
                            "required": True,
                            "schema": {
                                "$ref": "#/definitions/SigninRequest"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "schema": {
                                "$ref": "#/definitions/AuthResponse"
                            }
                        },
                        "400": {
                            "description": "Invalid input",
                            "schema": {
                                "$ref": "#/definitions/ErrorResponse"
                            }
                        },
                        "401": {
                            "description": "Authentication failed",
                            "schema": {
                                "$ref": "#/definitions/ErrorResponse"
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "schema": {
                                "$ref": "#/definitions/ErrorResponse"
                            }
                        }
                    }
                }
            },
            "/auth/logout": {
                "get": {
                    "tags": ["auth"],
                    "summary": "Logout user",
                    "description": "Logout the current authenticated user",
                    "produces": ["application/json"],
                    "responses": {
                        "200": {
                            "description": "Logout successful",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {
                                        "type": "string",
                                        "example": "Logged out successfully"
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Not authenticated",
                            "schema": {
                                "$ref": "#/definitions/ErrorResponse"
                            }
                        },
                        "500": {
                            "description": "Internal server error",
                            "schema": {
                                "$ref": "#/definitions/ErrorResponse"
                            }
                        }
                    }
                }
            }
            # You can add more endpoints here for chat, API, etc.
        },
        "definitions": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "full_name": {
                        "type": "string",
                        "description": "User's full name"
                    },
                    "email": {
                        "type": "string",
                        "description": "User's email address"
                    }
                }
            },
            "SignupRequest": {
                "type": "object",
                "required": ["full_name", "email", "password"],
                "properties": {
                    "full_name": {
                        "type": "string",
                        "example": "John Doe",
                        "description": "User's full name"
                    },
                    "email": {
                        "type": "string",
                        "example": "john@example.com",
                        "description": "User's email address"
                    },
                    "password": {
                        "type": "string",
                        "example": "StrongP@ssword123",
                        "description": "User's password"
                    }
                }
            },
            "SigninRequest": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {
                        "type": "string",
                        "example": "john@example.com",
                        "description": "User's email address"
                    },
                    "password": {
                        "type": "string",
                        "example": "StrongP@ssword123",
                        "description": "User's password"
                    }
                }
            },
            "AuthResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Response message"
                    },
                    "user": {
                        "$ref": "#/definitions/User"
                    }
                }
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "Error message"
                    }
                }
            }
        }
    }
    
    return swagger_spec

# Add route to serve the Swagger specification as JSON
@api_docs_bp.route('/swagger.json')
def swagger_json():
    """
    Serve the Swagger specification as JSON
    """
    return jsonify(generate_swagger_spec())

# Function to register Swagger documentation routes
def register_swagger_routes(app):
    """
    Register Swagger UI blueprint with the Flask app
    """
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
    app.register_blueprint(api_docs_bp, url_prefix='/api-docs') 