# Swagger API Documentation

This project uses Swagger UI to provide interactive API documentation for the backend. You can use this UI to explore and test all available API endpoints with example values.

## Accessing Swagger UI

When the backend server is running, you can access the Swagger UI documentation at:

```
http://localhost:5000/swagger/ui
```

## Features

- **Interactive Documentation**: Explore all API endpoints with detailed descriptions
- **Request Examples**: See example request payloads for each endpoint
- **Testing Interface**: Try out API endpoints directly from the browser
- **Response Models**: View expected response formats and status codes

## Available Endpoints

The API is organized into the following namespaces:

### Authentication

- `POST /auth/signup`: Create a new user account
- `POST /auth/signin`: Authenticate a user (login)
- `GET /auth/logout`: Log out a user

### Other Resources

Additional endpoints for chat functionality and other API services are also documented in the Swagger UI.

## Using Swagger UI

1. **Navigate** to http://localhost:5000/swagger/ui
2. **Explore** the available endpoints by expanding the namespaces
3. **Try Out** an endpoint by clicking the "Try it out" button
4. **Fill in** the required parameters and request body
5. **Execute** the request and see the response

## Notes

- Some endpoints require authentication. You'll need to log in first before accessing those endpoints.
- For secure testing, the Swagger UI is only available in development mode. 