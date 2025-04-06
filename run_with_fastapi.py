import uvicorn
from mlflow_proxy import app
import config
from utils import logger

if __name__ == "__main__":
    logger.info(f"Starting MLflow Proxy Server with FastAPI on {config.FASTAPI_HOST}:{config.FASTAPI_PORT}")
    logger.info(f"Proxying requests to MLflow server at: {config.MLFLOW_SERVER_URL}")
    uvicorn.run(app, host=config.FASTAPI_HOST, port=config.FASTAPI_PORT, reload=True)