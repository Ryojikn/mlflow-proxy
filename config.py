import os

# Default fallback MLflow server URL if not provided through environment variables
DEFAULT_MLFLOW_SERVER_URL = "http://localhost:5001"

# Get MLflow server URL from environment variable or use default
MLFLOW_SERVER_URL = os.environ.get("MLFLOW_SERVER_URL", DEFAULT_MLFLOW_SERVER_URL)

# Configure logging levels
LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")

# FASTAPI server configuration
FASTAPI_HOST = "http://localhost"
FASTAPI_PORT = 6150

# Dashboard configuration
ENABLE_DASHBOARD = os.environ.get("ENABLE_DASHBOARD", "true").lower() == "true"

# Configuration for logging of requests/responses
# Set to false to disable logging of specific request or response parts
LOG_REQUEST_HEADERS = True
LOG_REQUEST_BODY = True
LOG_RESPONSE_HEADERS = True
LOG_RESPONSE_BODY = True

# Maximum size of response body to log (in bytes)
# Useful to prevent huge responses from flooding logs
MAX_LOG_BODY_SIZE = int(os.environ.get("MAX_LOG_BODY_SIZE", 10000))
