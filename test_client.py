"""
Test client for MLflow Proxy.

This script demonstrates how to use the MLflow Python client to interact with the
MLflow server through our proxy.

Before running, make sure:
1. The MLflow server is running
2. The MLflow proxy is running
3. The environment variables are set correctly

Usage:
    python test_client.py
"""

import os
import mlflow
import time
import numpy as np
import argparse
from random import random

import requests
from urllib.parse import urlparse

# Save the original requests.Session.request method
_original_request = requests.Session.request

# Your MLflow host and optional path prefix
MLFLOW_HOST = "localhost:6150"  # or IP
MLFLOW_PATH_PREFIX = "/api/2.0"

# Define our custom patch
def patched_request(self, method, url, **kwargs):
    parsed_url = urlparse(url)
    print(parsed_url)

    is_mlflow = (
        parsed_url.netloc == MLFLOW_HOST and
        parsed_url.path.startswith(MLFLOW_PATH_PREFIX)
    )

    if is_mlflow:
        headers = kwargs.get("headers", {})
        headers["X-Original-Host"] = "http://localhost:5001"
        kwargs["headers"] = headers

    print(url)

    return _original_request(self, method, url, **kwargs)

# Apply the monkey patch
requests.Session.request = patched_request

def run_tracking_test(tracking_uri, experiment_name="proxy-test"):
    """
    Run a test of MLflow tracking operations through the proxy.
    
    Args:
        tracking_uri (str): The MLflow tracking URI (should point to the proxy)
        experiment_name (str): Name of the experiment to create
    """
    print(f"Setting tracking URI to: {tracking_uri}")
    mlflow.set_tracking_uri(tracking_uri)
    
    # Create or get experiment
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment:
            experiment_id = experiment.experiment_id
            print(f"Using existing experiment '{experiment_name}' (ID: {experiment_id})")
        else:
            experiment_id = mlflow.create_experiment(experiment_name)
            print(f"Created new experiment '{experiment_name}' (ID: {experiment_id})")
    except Exception as e:
        print(f"Error setting up experiment: {e}")
        return
    
    # Start a run
    with mlflow.start_run(experiment_id=experiment_id) as run:
        run_id = run.info.run_id
        print(f"Started run with ID: {run_id}")
        
        # Log some parameters
        mlflow.log_param("param1", random())
        mlflow.log_param("param2", random())
        print("Logged parameters")
        
        # Log some metrics
        for i in range(5):
            mlflow.log_metric("metric1", random(), step=i)
            mlflow.log_metric("metric2", random() * 2, step=i)
            time.sleep(0.1)  # Small delay to space out the requests
        print("Logged metrics")
        
        # Log a tag
        mlflow.set_tag("tag1", "proxy-test")
        print("Logged tag")
        
        # Log an artifact (create a simple file)
        with open("test_artifact.txt", "w") as f:
            f.write("This is a test artifact created by the MLflow proxy test client.")
        
        mlflow.log_artifact("test_artifact.txt")
        print("Logged artifact")
        
        # Clean up the test file
        os.remove("test_artifact.txt")
        
    print(f"Run completed successfully: {run_id}")
    print(f"View results at: {tracking_uri}/#/experiments/{experiment_id}/runs/{run_id}")

def run_registry_test(tracking_uri, model_name="proxy-test-model"):
    """
    Run a test of MLflow model registry operations through the proxy.
    
    Args:
        tracking_uri (str): The MLflow tracking URI (should point to the proxy)
        model_name (str): Name of the model to register
    """
    print(f"Setting tracking URI to: {tracking_uri}")
    mlflow.set_tracking_uri(tracking_uri)
    
    # Create a simple model
    from sklearn.ensemble import RandomForestRegressor
    import pandas as pd
    
    X = np.random.rand(100, 4)
    y = X[:, 0] + 2 * X[:, 1] + np.random.rand(100)
    
    model = RandomForestRegressor(n_estimators=10)
    model.fit(X, y)
    
    # Start a run to log the model
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        print(f"Started run with ID: {run_id}")
        
        # Log the model
        mlflow.sklearn.log_model(
            model, 
            "random_forest_model",
            registered_model_name=model_name
        )
        print(f"Logged and registered model: {model_name}")
        
    print(f"Model registry test completed successfully")
    print(f"View model at: {tracking_uri}/#/models/{model_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test MLflow Proxy")
    parser.add_argument(
        "--tracking-uri", 
        type=str, 
        default="http://localhost:6150",
        help="The URI of the MLflow Proxy server"
    )
    parser.add_argument(
        "--test-type",
        type=str,
        choices=["tracking", "registry", "both"],
        default="both",
        help="Type of test to run"
    )
    
    args = parser.parse_args()
    
    if args.test_type in ["tracking", "both"]:
        print("=== Running Tracking API Test ===")
        run_tracking_test(args.tracking_uri)
        print()
    
    if args.test_type in ["registry", "both"]:
        print("=== Running Registry API Test ===")
        run_registry_test(args.tracking_uri)
