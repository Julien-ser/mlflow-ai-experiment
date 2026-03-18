"""
Hyperparameter optimization framework using Optuna with MLflow integration.

Provides automated hyperparameter search across transformer and classical models.
"""

import os
from typing import Any, Callable, Dict, Optional, Tuple

import mlflow
import numpy as np
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler

from .data_loader import load_imdb_dataset
from .experiment_tracker import setup_mlflow_tracking, set_standard_tags
from .preprocessing import preprocess_dataset
from .models.classical import (
    LogisticRegressionModel,
    RandomForestModel,
    SVMModel,
    XGBoostModel,
)
from .models.transformers import (
    BERTModel,
    DeBERTaModel,
    DistilBERTModel,
    ELECTRAModel,
    GPT2Model,
    ALBERTModel,
    XLNetModel,
    RoBERTaModel,
    TransformerModel,
    create_transformer_model,
)


# ==================== Search Space Definitions ====================


def get_transformer_search_space(
    trial: optuna.Trial, model_type: str
) -> Dict[str, Any]:
    """
    Define search space for transformer models.

    Args:
        trial: Optuna trial
        model_type: Type of transformer ('bert', 'roberta', 'deberta', etc.)

    Returns:
        Dictionary of hyperparameters
    """
    space = {
        "learning_rate": trial.suggest_float("learning_rate", 1e-5, 5e-5, log=True),
        "batch_size": trial.suggest_categorical("batch_size", [8, 16, 32]),
        "dropout": trial.suggest_float("dropout", 0.1, 0.3),
        "num_train_epochs": trial.suggest_int("num_train_epochs", 2, 5),
        "weight_decay": trial.suggest_float("weight_decay", 0.0, 0.1),
        "warmup_steps": trial.suggest_int("warmup_steps", 0, 1000),
        "max_seq_length": trial.suggest_categorical("max_seq_length", [128, 256, 512]),
    }
    return space


def get_classical_search_space(trial: optuna.Trial, model_type: str) -> Dict[str, Any]:
    """
    Define search space for classical ML models.

    Args:
        trial: Optuna trial
        model_type: Type of model ('logistic_regression', 'svm', 'random_forest', 'xgboost')

    Returns:
        Dictionary of hyperparameters
    """
    if model_type == "logistic_regression":
        return {
            "C": trial.suggest_float("C", 1e-3, 10.0, log=True),
            "max_iter": trial.suggest_int("max_iter", 500, 2000),
            "solver": trial.suggest_categorical("solver", ["liblinear", "lbfgs"]),
        }
    elif model_type == "svm":
        return {
            "C": trial.suggest_float("C", 1e-3, 10.0, log=True),
            "max_iter": trial.suggest_int("max_iter", 1000, 5000),
        }
    elif model_type == "random_forest":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 5, 30),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
        }
    elif model_type == "xgboost":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        }
    else:
        raise ValueError(f"Unknown model type: {model_type}")


# ==================== Objective Functions ====================


def objective_transformer(
    trial: optuna.Trial,
    model_type: str,
    train_dataset,
    val_dataset,
    experiment_name: str,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
) -> float:
    """
    Objective function for transformer model hyperparameter optimization.

    Args:
        trial: Optuna trial
        model_type: Type of transformer model
        train_dataset: Tokenized training dataset
        val_dataset: Tokenized validation dataset
        experiment_name: MLflow experiment name
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration

    Returns:
        Validation accuracy (to maximize)
    """
    # Get hyperparameters from trial
    params = get_transformer_search_space(trial, model_type)

    # Create model with suggested hyperparameters
    model = create_transformer_model(
        model_type,
        num_labels=2,
        max_seq_length=params["max_seq_length"],
        dropout=params["dropout"],
        learning_rate=params["learning_rate"],
        batch_size=params["batch_size"],
        num_train_epochs=params["num_train_epochs"],
        weight_decay=params["weight_decay"],
        warmup_steps=params["warmup_steps"],
    )

    # Train model
    result = model.train(
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        experiment_name=experiment_name,
        dataset_version=dataset_version,
        preprocessing_config=preprocessing_config,
    )

    # Extract final validation accuracy from trainer
    if hasattr(result, "metrics") and result.metrics:
        val_accuracy = result.metrics.get("eval_accuracy", 0.0)
    else:
        # If no metrics available, use a default or compute manually
        val_accuracy = 0.0

    return val_accuracy


def objective_classical(
    trial: optuna.Trial,
    model_type: str,
    X_train,
    y_train,
    X_val,
    y_val,
    experiment_name: str,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
) -> float:
    """
    Objective function for classical model hyperparameter optimization.

    Args:
        trial: Optuna trial
        model_type: Type of classical model
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        experiment_name: MLflow experiment name
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration

    Returns:
        Validation accuracy (to maximize)
    """
    # Get hyperparameters from trial
    params = get_classical_search_space(trial, model_type)

    # Create and train model
    model_class = {
        "logistic_regression": LogisticRegressionModel,
        "svm": SVMModel,
        "random_forest": RandomForestModel,
        "xgboost": XGBoostModel,
    }[model_type]

    model = model_class(params=params)
    result = model.train(X_train, y_train, X_val, y_val)

    # Log to MLflow
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=f"{model_type}_optuna_{trial.number}"):
        # Log parameters
        for key, value in params.items():
            mlflow.log_param(key, value)

        # Log metrics
        mlflow.log_metric("train_accuracy", result["train_accuracy"])
        mlflow.log_metric("val_accuracy", result["val_accuracy"])

        # Log model
        model.log_to_mlflow(
            experiment_name=experiment_name,
            run_name=f"{model_type}_optuna_{trial.number}",
            X_test=X_val[:1] if hasattr(X_val, "__getitem__") else None,
            y_test=y_val[:1] if hasattr(y_val, "__getitem__") else None,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
        )

        # Set standard tags
        set_standard_tags(
            model_type=model_type,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
            framework="sklearn",
            task="text_classification",
        )

    return result["val_accuracy"]


# ==================== Optimization Runner ====================


def optimize_transformer_model(
    model_type: str,
    train_dataset,
    val_dataset,
    experiment_name: str,
    n_trials: int = 20,
    timeout: Optional[float] = None,
    study_name: Optional[str] = None,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
) -> optuna.Study:
    """
    Run hyperparameter optimization for a transformer model.

    Args:
        model_type: Type of transformer model
        train_dataset: Tokenized training dataset
        val_dataset: Tokenized validation dataset
        experiment_name: MLflow experiment name
        n_trials: Number of optimization trials
        timeout: Timeout in seconds
        study_name: Name for the Optuna study
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration

    Returns:
        Optuna study object
    """
    if study_name is None:
        study_name = f"{model_type}_hyperopt"

    setup_mlflow_tracking()

    sampler = TPESampler(seed=42)
    pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=0, interval_steps=1)

    study = optuna.create_study(
        study_name=study_name,
        direction="maximize",
        sampler=sampler,
        pruner=pruner,
        storage=f"sqlite:///optuna_{study_name}.db",
    )

    def objective_wrapper(trial):
        return objective_transformer(
            trial=trial,
            model_type=model_type,
            train_dataset=train_dataset,
            val_dataset=val_dataset,
            experiment_name=experiment_name,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
        )

    study.optimize(objective_wrapper, n_trials=n_trials, timeout=timeout)

    # Log best parameters and value to MLflow
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=f"{model_type}_hyperopt_best"):
        mlflow.log_params(study.best_params)
        mlflow.log_metric("best_val_accuracy", study.best_value)
        mlflow.set_tag("model_type", model_type)
        mlflow.set_tag("study_name", study_name)
        mlflow.set_tag("n_trials", n_trials)

    return study


def optimize_classical_model(
    model_type: str,
    X_train,
    y_train,
    X_val,
    y_val,
    experiment_name: str,
    n_trials: int = 20,
    timeout: Optional[float] = None,
    study_name: Optional[str] = None,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
) -> optuna.Study:
    """
    Run hyperparameter optimization for a classical model.

    Args:
        model_type: Type of classical model
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        experiment_name: MLflow experiment name
        n_trials: Number of optimization trials
        timeout: Timeout in seconds
        study_name: Name for the Optuna study
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration

    Returns:
        Optuna study object
    """
    if study_name is None:
        study_name = f"{model_type}_hyperopt"

    setup_mlflow_tracking()

    sampler = TPESampler(seed=42)
    pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=0, interval_steps=1)

    study = optuna.create_study(
        study_name=study_name,
        direction="maximize",
        sampler=sampler,
        pruner=pruner,
        storage=f"sqlite:///optuna_{study_name}.db",
    )

    def objective_wrapper(trial):
        return objective_classical(
            trial=trial,
            model_type=model_type,
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            experiment_name=experiment_name,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
        )

    study.optimize(objective_wrapper, n_trials=n_trials, timeout=timeout)

    # Log best parameters and value to MLflow
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=f"{model_type}_hyperopt_best"):
        mlflow.log_params(study.best_params)
        mlflow.log_metric("best_val_accuracy", study.best_value)
        mlflow.set_tag("model_type", model_type)
        mlflow.set_tag("study_name", study_name)
        mlflow.set_tag("n_trials", n_trials)

    return study


# ==================== Convenience Functions ====================


def optimize_all_transformers(
    model_types: list,
    train_dataset,
    val_dataset,
    experiment_name: str,
    n_trials: int = 10,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
) -> Dict[str, optuna.Study]:
    """
    Run optimization for multiple transformer models.

    Args:
        model_types: List of transformer model types to optimize
        train_dataset: Tokenized training dataset
        val_dataset: Tokenized validation dataset
        experiment_name: MLflow experiment name
        n_trials: Number of trials per model
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration

    Returns:
        Dictionary mapping model types to their study objects
    """
    results = {}
    for model_type in model_types:
        print(f"Optimizing {model_type}...")
        study = optimize_transformer_model(
            model_type=model_type,
            train_dataset=train_dataset,
            val_dataset=val_dataset,
            experiment_name=experiment_name,
            n_trials=n_trials,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
        )
        results[model_type] = study
        print(f"Best accuracy for {model_type}: {study.best_value:.4f}")
    return results


def optimize_all_classical(
    model_types: list,
    X_train,
    y_train,
    X_val,
    y_val,
    experiment_name: str,
    n_trials: int = 10,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
) -> Dict[str, optuna.Study]:
    """
    Run optimization for multiple classical models.

    Args:
        model_types: List of classical model types to optimize
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        experiment_name: MLflow experiment name
        n_trials: Number of trials per model
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration

    Returns:
        Dictionary mapping model types to their study objects
    """
    results = {}
    for model_type in model_types:
        print(f"Optimizing {model_type}...")
        study = optimize_classical_model(
            model_type=model_type,
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            experiment_name=experiment_name,
            n_trials=n_trials,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
        )
        results[model_type] = study
        print(f"Best accuracy for {model_type}: {study.best_value:.4f}")
    return results


def get_best_params(study: optuna.Study) -> Dict[str, Any]:
    """
    Extract best hyperparameters from a study.

    Args:
        study: Completed Optuna study

    Returns:
        Dictionary of best hyperparameters
    """
    return study.best_params
