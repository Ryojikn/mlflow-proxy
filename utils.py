import json
import logging
from urllib.parse import urlparse, urljoin
import time
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mlflow_proxy')

def get_target_url(path, mlflow_server_url):
    """
    Constructs the target URL for proxying the request.
    
    Args:
        path (str): The path part of the request URL
        mlflow_server_url (str): The base URL of the MLflow server
        
    Returns:
        str: The complete target URL
    """
    # Make sure both URLs are properly formed without double slashes
    server_url = mlflow_server_url.rstrip('/')
    path = path.lstrip('/')
    return f"{server_url}/{path}"

def is_binary_content(content_type):
    """
    Check if the content is binary based on Content-Type header.
    
    Args:
        content_type (str): The Content-Type header value
        
    Returns:
        bool: True if the content is binary, False otherwise
    """
    if not content_type:
        return False
        
    binary_types = [
        'application/octet-stream',
        'application/zip',
        'image/',
        'audio/',
        'video/'
    ]
    
    return any(binary_type in content_type for binary_type in binary_types)

def format_body_for_logging(body, content_type):
    """
    Format the request/response body for logging.
    
    Args:
        body (bytes): The body content
        content_type (str): The Content-Type header value
        
    Returns:
        str: The formatted body for logging
    """
    if not body:
        return "<empty body>"
        
    # If it's binary content, just log the type and size
    if is_binary_content(content_type):
        return f"<binary data> [Content-Type: {content_type}, Size: {len(body)} bytes]"
    
    # If it's too large, truncate it
    if len(body) > config.MAX_LOG_BODY_SIZE:
        return f"<truncated> [Size: {len(body)} bytes, showing first {config.MAX_LOG_BODY_SIZE} bytes]\n{body[:config.MAX_LOG_BODY_SIZE]}"
    
    # Try to parse JSON for better formatting
    if content_type and 'application/json' in content_type:
        try:
            parsed = json.loads(body)
            return json.dumps(parsed, indent=2)
        except:
            pass
    
    # Return as string
    try:
        return body.decode('utf-8')
    except UnicodeDecodeError:
        return f"<binary data> [Content-Type: {content_type}, Size: {len(body)} bytes]"

def log_request(req, body=None):
    """
    Log the details of an HTTP request.
    
    Args:
        req: The FastAPI request object
        body (bytes, optional): The request body if already read
    """
    if not config.LOG_REQUEST_HEADERS and not config.LOG_REQUEST_BODY:
        return
    
    
    
    logger.info(f"==== INCOMING REQUEST ====")
    # Log request method and URL
    if hasattr(req, 'method'):
        logger.info(f"Method: {req.method}")
    
    if hasattr(req, 'url'):
        logger.info(f"URL: {req.url}")
    elif hasattr(req, 'path'):
        logger.info(f"Path: {req.path}")
    
    # Log client information
    if hasattr(req, 'client'):
        logger.info(f"Client: {req.client.host}:{req.client.port}")
    elif hasattr(req, 'remote_addr'):
        logger.info(f"Client: {req.remote_addr}")
    
    # Get the forwarded for header if present (useful for proxied requests)
    forwarded_for = None
    if hasattr(req, 'headers'):
        if isinstance(req.headers, dict):
            forwarded_for = req.headers.get('X-Forwarded-For') or req.headers.get('x-forwarded-for')
        elif hasattr(req.headers, 'get'):
            forwarded_for = req.headers.get('X-Forwarded-For')
    
    if forwarded_for:
        logger.info(f"X-Forwarded-For: {forwarded_for}")
    
    # Log user agent
    user_agent = None
    if hasattr(req, 'headers'):
        if isinstance(req.headers, dict):
            user_agent = req.headers.get('User-Agent') or req.headers.get('user-agent')
        elif hasattr(req.headers, 'get'):
            user_agent = req.headers.get('User-Agent')
    
    if user_agent:
        logger.info(f"User-Agent: {user_agent}")
    
    # Log request headers if configured
    if config.LOG_REQUEST_HEADERS and hasattr(req, 'headers'):
        logger.info("Headers:")
        if isinstance(req.headers, dict):
            for name, value in req.headers.items():
                logger.info(f"  {name}: {value}")
        elif hasattr(req.headers, 'items'):
            for name, value in req.headers.items():
                logger.info(f"  {name}: {value}")
    
    # Log request body if configured
    if config.LOG_REQUEST_BODY and body:
        content_type = None
        if hasattr(req, 'headers'):
            if isinstance(req.headers, dict):
                content_type = req.headers.get('content-type') or req.headers.get('Content-Type')
            elif hasattr(req.headers, 'get'):
                content_type = req.headers.get('content-type')
        
        logger.info("Body:")
        logger.info(format_body_for_logging(body, content_type))
    
    logger.info("==== END REQUEST ====")

def log_response(resp, duration=None):
    """
    Log the details of an HTTP response.
    
    Args:
        resp: The Response object
        duration (float, optional): The duration of the request in seconds
    """
    if not config.LOG_RESPONSE_HEADERS and not config.LOG_RESPONSE_BODY:
        return

    logger.info(f"==== OUTGOING RESPONSE ====")
    logger.info(f"Status: {resp.status_code}")
    
    if duration is not None:
        logger.info(f"Duration: {duration:.3f} seconds")
    
    if config.LOG_RESPONSE_HEADERS:
        logger.info("Headers:")
        for name, value in resp.headers.items():
            logger.info(f"  {name}: {value}")
    
    if config.LOG_RESPONSE_BODY:
        content_type = resp.headers.get('Content-Type')
        body = resp.content if hasattr(resp, 'content') else b''
        
        logger.info("Body:")
        logger.info(format_body_for_logging(body, content_type))
    
    logger.info("==== END RESPONSE ====")

def get_mlflow_request_type(path, method):
    """
    Identifies the type of MLflow request.
    
    Args:
        path (str): The request path
        method (str): The HTTP method
        
    Returns:
        str: Description of the MLflow request type
    """
    # Tracking API endpoints
    if '/api/2.0/mlflow' in path:
        if '/runs/' in path:
            if method == 'POST':
                return "MLflow Tracking: Create Run"
            elif method == 'GET':
                return "MLflow Tracking: Get Run"
            elif method == 'PATCH':
                return "MLflow Tracking: Update Run"
        elif '/metrics/' in path:
            return "MLflow Tracking: Log Metrics"
        elif '/params/' in path:
            return "MLflow Tracking: Log Parameters"
        elif '/tags/' in path:
            return "MLflow Tracking: Log Tags"
        elif '/artifacts/' in path:
            if method == 'POST':
                return "MLflow Tracking: Log Artifact"
            else:
                return "MLflow Tracking: Get Artifact"
        elif '/experiments/' in path:
            if method == 'POST':
                return "MLflow Tracking: Create Experiment"
            elif method == 'GET':
                return "MLflow Tracking: Get Experiment"
            elif method == 'PATCH':
                return "MLflow Tracking: Update Experiment"
        return "MLflow Tracking API"
    
    # Registry API endpoints
    elif '/api/2.0/preview/mlflow/registered-models' in path:
        if method == 'POST':
            return "MLflow Registry: Create Model"
        elif method == 'GET':
            return "MLflow Registry: Get Model"
        return "MLflow Registry API"
    elif '/api/2.0/preview/mlflow/model-versions' in path:
        return "MLflow Registry: Model Versions"
    
    # Fallback
    return f"MLflow API: {method} {path}"
