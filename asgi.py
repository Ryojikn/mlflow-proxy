from mlflow_proxy import app as application
import config
from utils import logger

# This file exposes the ASGI application for Gunicorn
# Use with: gunicorn -k uvicorn.workers.UvicornWorker asgi:application

# Log startup information
logger.info(f"MLflow Proxy Server configured on {config.FASTAPI_HOST}:{config.FASTAPI_PORT}")
logger.info(f"Proxying requests to MLflow server at: {config.MLFLOW_SERVER_URL}")