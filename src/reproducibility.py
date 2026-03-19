"""
Reproducibility utilities for deterministic training and environment logging.

This module ensures that experiments can be reproduced exactly by:
- Setting random seeds for all random number generators
- Logging complete environment information to MLFlow
- Providing a reproducibility checklist
"""

import os
import random
import sys
import platform
from typing import Any, Dict, List, Optional, Tuple
import mlflow
import numpy as np
import torch


def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for all random number generators to ensure reproducibility.

    Args:
        seed: The seed value to use across all RNGs (default: 42)
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # For deterministic GPU operations
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Set hash seed for Python
    os.environ["PYTHONHASHSEED"] = str(seed)

    # Set TensorFlow seed if available
    try:
        import tensorflow as tf

        tf.random.set_seed(seed)
    except ImportError:
        pass

    mlflow.log_param("random_seed", seed)


def log_environment_info() -> Dict[str, Any]:
    """
    Log complete environment information to MLFlow for reproducibility.

    Returns:
        Dictionary containing all environment details
    """
    env_info = {
        "python_version": sys.version,
        "python_version_full": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "system": platform.system(),
        "node": platform.node(),
    }

    # CUDA information if available
    if torch.cuda.is_available():
        env_info.update(
            {
                "cuda_available": True,
                "cuda_version": torch.version.cuda,
                "gpu_count": torch.cuda.device_count(),
                "gpu_names": [
                    torch.cuda.get_device_name(i)
                    for i in range(torch.cuda.device_count())
                ],
            }
        )
    else:
        env_info["cuda_available"] = False

    # Log to MLFlow
    for key, value in env_info.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            mlflow.log_param(f"env_{key}", value)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                mlflow.log_param(f"env_{key}_{i}", str(item))

    # Log package versions
    import pkg_resources

    packages = [
        "mlflow",
        "torch",
        "tensorflow",
        "transformers",
        "datasets",
        "scikit-learn",
        "numpy",
        "pandas",
        "xgboost",
        "lightgbm",
        "optuna",
        "ray[tune]",
    ]

    for pkg in packages:
        try:
            version = pkg_resources.get_distribution(pkg).version
            mlflow.log_param(f"pkg_{pkg.replace('[', '_').replace(']', '')}", version)
            env_info[f"pkg_{pkg}"] = version
        except pkg_resources.DistributionNotFound:
            pass

    return env_info


def log_training_configuration(
    model_name: str,
    model_params: Dict[str, Any],
    training_params: Dict[str, Any],
    preprocessing_params: Dict[str, Any],
    dataset_info: Dict[str, Any],
) -> None:
    """
    Log complete training configuration to MLFlow.

    Args:
        model_name: Name/type of the model
        model_params: Model-specific hyperparameters
        training_params: Training configuration (epochs, batch size, learning rate, etc.)
        preprocessing_params: Data preprocessing configuration
        dataset_info: Dataset information (size, version, splits)
    """
    # Log model identification
    mlflow.log_param("model_name", model_name)
    mlflow.log_param("model_family", _infer_model_family(model_name))

    # Log model parameters
    for key, value in model_params.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            mlflow.log_param(f"model_{key}", value)

    # Log training parameters
    for key, value in training_params.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            mlflow.log_param(f"train_{key}", value)

    # Log preprocessing parameters
    for key, value in preprocessing_params.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            mlflow.log_param(f"preproc_{key}", value)
        elif isinstance(value, (list, dict)):
            mlflow.log_param(f"preproc_{key}", str(value))

    # Log dataset information
    for key, value in dataset_info.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            mlflow.log_param(f"data_{key}", value)


def _infer_model_family(model_name: str) -> str:
    """Infer the model family from the model name."""
    model_name_lower = model_name.lower()

    if any(
        x in model_name_lower
        for x in [
            "bert",
            "roberta",
            "deberta",
            "xlnet",
            "electra",
            "albert",
            "distilbert",
            "gpt",
        ]
    ):
        return "transformer"
    elif any(
        x in model_name_lower
        for x in ["logistic", "svm", "random_forest", "xgboost", "lightgbm"]
    ):
        return "classical"
    else:
        return "unknown"


def get_reproducibility_checklist() -> List[Tuple[str, bool, str]]:
    """
    Get a checklist of reproducibility best practices.

    Returns:
        List of tuples: (check_item, is_complete, notes)
    """
    checklist = [
        (
            "Random seed set and logged",
            False,
            "Ensure set_seed() is called at the start",
        ),
        (
            "Environment info logged",
            False,
            "All Python, package, and hardware details captured",
        ),
        ("Model parameters logged", False, "All hyperparameters should be in MLFlow"),
        (
            "Training parameters logged",
            False,
            "Optimizer, LR schedule, epochs, batch size",
        ),
        (
            "Preprocessing parameters logged",
            False,
            "Tokenization, cleaning, augmentation",
        ),
        ("Dataset version logged", False, "Dataset checksum and version information"),
        ("Code version logged (git hash)", False, "Commit hash for exact code state"),
        ("Model artifact saved", False, "Complete model files saved to MLFlow or disk"),
        ("Evaluation metrics logged", False, "All performance metrics captured"),
    ]

    return checklist


def log_git_info() -> Optional[Dict[str, str]]:
    """
    Log Git repository information if available.

    Returns:
        Dictionary with git info or None if not in a git repo
    """
    try:
        import subprocess

        git_hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("ascii")
            .strip()
        )
        git_branch = (
            subprocess.check_output(["git", "branch", "--show-current"])
            .decode("ascii")
            .strip()
        )
        git_status = (
            subprocess.check_output(["git", "status", "--porcelain"])
            .decode("ascii")
            .strip()
        )

        git_info = {
            "commit_hash": git_hash,
            "branch": git_branch,
            "has_uncommitted": len(git_status) > 0,
        }

        mlflow.log_param("git_commit", git_hash)
        mlflow.log_param("git_branch", git_branch)
        mlflow.log_param("git_dirty", len(git_status) > 0)

        return git_info
    except (subprocess.CalledProcessError, FileNotFoundError):
        mlflow.log_param("git_available", False)
        return None


def verify_reproducibility_setup() -> Dict[str, Any]:
    """
    Verify that all reproducibility measures are in place.

    Returns:
        Dictionary with verification results and missing items
    """
    verification = {"all_checks_passed": True, "missing_items": [], "warnings": []}

    # Check if seed was logged
    try:
        current_run = mlflow.active_run()
        if current_run:
            run_data = mlflow.get_run(current_run.info.run_id)
            if "random_seed" not in run_data.data.params:
                verification["missing_items"].append("random_seed not logged")
                verification["all_checks_passed"] = False
    except:
        pass

    # Check environment info
    required_env_params = ["env_python_version", "env_platform"]
    try:
        current_run = mlflow.active_run()
        if current_run:
            run_data = mlflow.get_run(current_run.info.run_id)
            for param in required_env_params:
                if param not in run_data.data.params:
                    verification["missing_items"].append(f"{param} not logged")
                    verification["all_checks_passed"] = False
    except:
        pass

    return verification
