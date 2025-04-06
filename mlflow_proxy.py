from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import logging
import time
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import config
from utils import (
    get_target_url, log_request, log_response, 
    get_mlflow_request_type, logger
)

app = FastAPI(title="MLflow Proxy", description="A proxy server for MLflow")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Simple in-memory statistics storage
stats: Dict[str, Any] = {
    "requests": 0,
    "errors": 0,
    "total_request_time": 0,
    "request_types": {},
    "status_codes": {},
    "last_requests": []  # Will keep the last 100 requests for display
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Show the dashboard page with proxy status and statistics."""
    if not config.ENABLE_DASHBOARD:
        return "MLflow Proxy Server is running. Dashboard is disabled."
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "stats": stats, "mlflow_server": config.MLFLOW_SERVER_URL}
    )

@app.get("/api/stats", response_class=JSONResponse)
async def get_stats():
    """API endpoint to get current proxy statistics."""
    if not config.ENABLE_DASHBOARD:
        return JSONResponse(
            content={"error": "Dashboard is disabled"}, 
            status_code=403
        )
    
    return stats

@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "mlflow_server": config.MLFLOW_SERVER_URL,
        "requests_proxied": stats["requests"]
    }

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy(request: Request, path: str):
    """
    Main proxy function that forwards requests to the MLflow server.
    
    Args:
        request (Request): The FastAPI request object
        path (str): The path part of the URL
        
    Returns:
        Response: The proxied response from the MLflow server
    """
    target_url = get_target_url(path, config.MLFLOW_SERVER_URL)
    
    # Read request details
    method = request.method
    headers = {key: value for key, value in request.headers.items() if key.lower() != 'host'}
    body = await request.body()
    params = dict(request.query_params)
    
    # Identify MLflow request type
    request_type = get_mlflow_request_type(path, method)
    
    # Update statistics
    stats["requests"] += 1
    stats["request_types"][request_type] = stats["request_types"].get(request_type, 0) + 1
    
    # Log the incoming request
    log_request(request, body)
    target_url = get_target_url(path, request.headers.get('x-original-host'))
    
    # Make the request to the actual MLflow server
    start_time = time.time()
    try:
        response = requests.request(
            method=method,
            url=target_url,
            headers=headers,
            data=body,
            params=params,
            stream=True,  # Important for handling large responses
            allow_redirects=False  # We will handle redirects manually
        )
        
        # Calculate request duration
        duration = time.time() - start_time
        stats["total_request_time"] += duration
        
        # Update status code statistics
        status_code = str(response.status_code)
        stats["status_codes"][status_code] = stats["status_codes"].get(status_code, 0) + 1
        
        # Log the response from MLflow server
        log_response(response, duration)
        
        # Store request in history
        request_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": method,
            "path": path,
            "type": request_type,
            "status_code": response.status_code,
            "duration": round(duration, 3)
        }
        stats["last_requests"].insert(0, request_entry)
        stats["last_requests"] = stats["last_requests"][:100]  # Keep only last 100
        
        # Create a FastAPI response from the MLflow server response
        headers_dict = dict(response.headers)
        
        # Return a streaming response
        return StreamingResponse(
            content=response.iter_content(chunk_size=1024),
            status_code=response.status_code,
            headers=headers_dict
        )
        
    except requests.RequestException as e:
        # Handle any errors during the request
        stats["errors"] += 1
        error_message = f"Error proxying to MLflow server: {str(e)}"
        logger.error(error_message)
        
        return JSONResponse(
            content={
                "error": error_message,
                "mlflow_server": config.MLFLOW_SERVER_URL
            },
            status_code=502  # Bad Gateway
        )
