"""
Hyperparameter optimization framework using Optuna with MLflow integration.

Provides automated hyperparameter search across transformer and classical models.
"""

from typing import Any, Callable, Dict, Optional, Protocol, Type, cast

import mlflow
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler

from .experiment_tracker import setup_mlflow_tracking, set_standard_tags
from .models.classical import (
    LogisticRegressionModel,
    RandomForestModel,
    SVMModel,
    XGBoostModel,
)
from .models.transformers import create_transformer_model


class ClassicalModel(Protocol):
    """Protocol for classical ML models."""

    def __init__(self, params: Any = None) -> None: ...

    def train(
        self,
        X_train: Any,
        y_train: Any,
        X_val: Any,
        y_val: Any,
    ) -> Dict[str, float]: ...

    def log_to_mlflow(
        self,
        experiment_name: str,
        run_name: str,
        X_test: Any = None,
        y_test: Any = None,
        dataset_version: str = "v1.0",
        preprocessing_config: str = "standard",
    ) -> Any: ...


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
    model_class: Type[ClassicalModel] = cast(
        Type[ClassicalModel],
        {
            "logistic_regression": LogisticRegressionModel,
            "svm": SVMModel,
            "random_forest": RandomForestModel,
            "xgboost": XGBoostModel,
        }[model_type],
    )

    model: Any = model_class(params=params)
    result = model.train(X_train, y_train, X_val, y_val)

    # Log to MLflow
    trial_num = trial.number
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=f"{model_type}_optuna_{trial_num}"):
        # Log parameters
        for key, value in params.items():
            mlflow.log_param(key, value)

        # Log metrics
        mlflow.log_metric("train_accuracy", result["train_accuracy"])
        mlflow.log_metric("val_accuracy", result["val_accuracy"])

        # Log model
        model.log_to_mlflow(
            experiment_name=experiment_name,
            run_name=f"{model_type}_optuna_{trial_num}",
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
        load_if_exists=True,
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
        load_if_exists=True,
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


# ==================== Ray Tune Integration ====================


def get_transformer_search_space_ray() -> Dict[str, Any]:
    """
    Define search space for transformer models for Ray Tune.

    Returns:
        Dictionary of hyperparameter search spaces using Ray Tune syntax
    """
    # Lazy import Ray to make it optional
    try:
        from ray import tune
    except ImportError as e:
        raise ImportError(
            "Ray Tune is required for this function. Install with: pip install 'ray[tune]>=2.7.0'"
        ) from e

    return {
        "learning_rate": tune.loguniform(1e-5, 5e-5),
        "batch_size": tune.choice([8, 16, 32]),
        "dropout": tune.uniform(0.1, 0.3),
        "num_train_epochs": tune.randint(2, 6),
        "weight_decay": tune.uniform(0.0, 0.1),
        "warmup_steps": tune.randint(0, 1001),
        "max_seq_length": tune.choice([128, 256, 512]),
    }


def get_classical_search_space_ray(model_type: str) -> Dict[str, Any]:
    """
    Define search space for classical ML models for Ray Tune.

    Args:
        model_type: Type of model ('logistic_regression', 'svm', 'random_forest', 'xgboost')

    Returns:
        Dictionary of hyperparameter search spaces using Ray Tune syntax
    """
    # Lazy import Ray to make it optional
    try:
        from ray import tune
    except ImportError as e:
        raise ImportError(
            "Ray Tune is required for this function. Install with: pip install 'ray[tune]>=2.7.0'"
        ) from e

    if model_type == "logistic_regression":
        return {
            "C": tune.loguniform(1e-3, 10.0),
            "max_iter": tune.randint(500, 2001),
            "solver": tune.choice(["liblinear", "lbfgs"]),
        }
    elif model_type == "svm":
        return {
            "C": tune.loguniform(1e-3, 10.0),
            "max_iter": tune.randint(1000, 5001),
        }
    elif model_type == "random_forest":
        return {
            "n_estimators": tune.randint(50, 301),
            "max_depth": tune.randint(5, 31),
            "min_samples_split": tune.randint(2, 11),
        }
    elif model_type == "xgboost":
        return {
            "n_estimators": tune.randint(50, 301),
            "max_depth": tune.randint(3, 11),
            "learning_rate": tune.loguniform(0.01, 0.3),
            "subsample": tune.uniform(0.6, 1.0),
            "colsample_bytree": tune.uniform(0.6, 1.0),
        }
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def _train_transformer_ray(
    config: Dict[str, Any],
    model_type: str,
    train_dataset,
    val_dataset,
    experiment_name: str,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
) -> Dict[str, float]:
    """
    Ray Tune trainable function for transformer models.

    Args:
        config: Hyperparameter configuration from Ray Tune
        model_type: Type of transformer model
        train_dataset: Tokenized training dataset
        val_dataset: Tokenized validation dataset
        experiment_name: MLflow experiment name
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration

    Returns:
        Dictionary with validation accuracy
    """
    # Lazy import Ray to make it optional
    try:
        from ray import tune
    except ImportError as e:
        raise ImportError(
            "Ray Tune is required for this function. Install with: pip install 'ray[tune]>=2.7.0'"
        ) from e

    setup_mlflow_tracking()
    trial_num = tune.get_trial_id()

    with mlflow.start_run(run_name=f"{model_type}_ray_tune_{trial_num}"):
        # Log parameters
        for key, value in config.items():
            mlflow.log_param(key, value)

        # Set standard tags
        set_standard_tags(
            model_type=model_type,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
            framework="transformers",
            task="text_classification",
        )

        # Create model with hyperparameters
        model = create_transformer_model(
            model_type,
            num_labels=2,
            max_seq_length=config["max_seq_length"],
            dropout=config["dropout"],
            learning_rate=config["learning_rate"],
            batch_size=config["batch_size"],
            num_train_epochs=config["num_train_epochs"],
            weight_decay=config["weight_decay"],
            warmup_steps=config["warmup_steps"],
        )

        # Train model
        result = model.train(
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            experiment_name=experiment_name,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
        )

        # Extract validation accuracy
        if hasattr(result, "metrics") and result.metrics:
            val_accuracy = result.metrics.get("eval_accuracy", 0.0)
        else:
            val_accuracy = 0.0

        mlflow.log_metric("val_accuracy", val_accuracy)

    return {"val_accuracy": val_accuracy}


def _train_classical_ray(
    config: Dict[str, Any],
    model_type: str,
    X_train,
    y_train,
    X_val,
    y_val,
    experiment_name: str,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
) -> Dict[str, float]:
    """
    Ray Tune trainable function for classical models.

    Args:
        config: Hyperparameter configuration from Ray Tune
        model_type: Type of classical model
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        experiment_name: MLflow experiment name
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration

    Returns:
        Dictionary with validation accuracy
    """
    # Lazy import Ray to make it optional
    try:
        from ray import tune
    except ImportError as e:
        raise ImportError(
            "Ray Tune is required for this function. Install with: pip install 'ray[tune]>=2.7.0'"
        ) from e

    setup_mlflow_tracking()
    trial_num = tune.get_trial_id()

    model_class: Type[ClassicalModel] = cast(
        Type[ClassicalModel],
        {
            "logistic_regression": LogisticRegressionModel,
            "svm": SVMModel,
            "random_forest": RandomForestModel,
            "xgboost": XGBoostModel,
        }[model_type],
    )

    model = model_class(params=config)
    result = model.train(X_train, y_train, X_val, y_val)

    with mlflow.start_run(run_name=f"{model_type}_ray_tune_{trial_num}"):
        # Log parameters
        for key, value in config.items():
            mlflow.log_param(key, value)

        # Log metrics
        mlflow.log_metric("train_accuracy", result["train_accuracy"])
        mlflow.log_metric("val_accuracy", result["val_accuracy"])

        # Log model
        model.log_to_mlflow(
            experiment_name=experiment_name,
            run_name=f"{model_type}_ray_tune_{trial_num}",
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

    return {"val_accuracy": result["val_accuracy"]}


def optimize_transformer_model_ray(
    model_type: str,
    train_dataset,
    val_dataset,
    experiment_name: str,
    n_trials: int = 20,
    timeout: Optional[float] = None,
    study_name: Optional[str] = None,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
    search_alg: Optional[str] = "hyperopt",
) -> Any:
    """
    Run hyperparameter optimization for a transformer model using Ray Tune.

    Args:
        model_type: Type of transformer model
        train_dataset: Tokenized training dataset
        val_dataset: Tokenized validation dataset
        experiment_name: MLflow experiment name
        n_trials: Number of optimization trials
        timeout: Timeout in seconds
        study_name: Name for the Ray Tune experiment
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration
        search_alg: Search algorithm to use ('hyperopt', 'random', 'asha')

    Returns:
        Ray Tune ExperimentAnalysis object
    """
    # Lazy import Ray to make it optional
    try:
        from ray import tune
        from ray.tune import ExperimentAnalysis
        from ray.tune.search import ConcurrencyLimiter
        from ray.tune.search.hyperopt import HyperoptSearch
    except ImportError as e:
        raise ImportError(
            "Ray Tune is required for this function. Install with: pip install 'ray[tune]>=2.7.0'"
        ) from e

    if study_name is None:
        study_name = f"{model_type}_ray_hyperopt"

    setup_mlflow_tracking()

    # Define search space
    search_space = get_transformer_search_space_ray()

    # Choose search algorithm
    if search_alg == "hyperopt":
        search_alg_obj = HyperoptSearch(
            space=None,  # We provide space directly to tune.run
            metric="val_accuracy",
            mode="max",
            random_state_seed=42,
        )
        search_alg_obj = ConcurrencyLimiter(search_alg_obj, max_concurrent=4)
        scheduler = None
    elif search_alg == "asha":
        from ray.tune.schedulers import ASHAScheduler

        scheduler = ASHAScheduler(
            metric="val_accuracy",
            mode="max",
            max_t=10,
            grace_period=1,
            reduction_factor=2,
        )
        search_alg_obj = None
    else:  # random search
        search_alg_obj = None
        scheduler = None

    # Wrap trainable with data
    trainable = tune.with_parameters(
        _train_transformer_ray,
        model_type=model_type,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        experiment_name=experiment_name,
        dataset_version=dataset_version,
        preprocessing_config=preprocessing_config,
    )

    # Wrap with search algorithm if specified
    if search_alg_obj:
        trainable = tune.with_search_algorithm(trainable, search_alg_obj)

    # Run optimization
    analysis = tune.run(
        trainable,
        config=search_space,
        num_samples=n_trials,
        time_budget_s=timeout,
        storage_path=f"file:///tmp/ray_results/{study_name}",
        name=study_name,
        resources_per_trial={"cpu": 2, "gpu": 0},  # Adjust based on availability
        scheduler=scheduler,
        verbose=1,
    )

    # Log best results to MLflow
    mlflow.set_experiment(experiment_name)
    best_trial = analysis.get_best_trial(metric="val_accuracy", mode="max")
    best_config = best_trial.config
    best_metric = best_trial.last_result["val_accuracy"]

    with mlflow.start_run(run_name=f"{model_type}_ray_hyperopt_best"):
        mlflow.log_params(best_config)
        mlflow.log_metric("best_val_accuracy", best_metric)
        mlflow.set_tag("model_type", model_type)
        mlflow.set_tag("study_name", study_name)
        mlflow.set_tag("n_trials", n_trials)
        mlflow.set_tag("framework", "ray_tune")

    return analysis


def optimize_classical_model_ray(
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
    search_alg: Optional[str] = "hyperopt",
) -> Any:
    """
    Run hyperparameter optimization for a classical model using Ray Tune.

    Args:
        model_type: Type of classical model
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        experiment_name: MLflow experiment name
        n_trials: Number of optimization trials
        timeout: Timeout in seconds
        study_name: Name for the Ray Tune experiment
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration
        search_alg: Search algorithm to use ('hyperopt', 'random', 'asha')

    Returns:
        Ray Tune ExperimentAnalysis object
    """
    # Lazy import Ray to make it optional
    try:
        from ray import tune
        from ray.tune import ExperimentAnalysis
        from ray.tune.search import ConcurrencyLimiter
        from ray.tune.search.hyperopt import HyperoptSearch
    except ImportError as e:
        raise ImportError(
            "Ray Tune is required for this function. Install with: pip install 'ray[tune]>=2.7.0'"
        ) from e

    if study_name is None:
        study_name = f"{model_type}_ray_hyperopt"

    setup_mlflow_tracking()

    # Define search space
    search_space = get_classical_search_space_ray(model_type)

    # Choose search algorithm
    if search_alg == "hyperopt":
        search_alg_obj = HyperoptSearch(
            space=None,
            metric="val_accuracy",
            mode="max",
            random_state_seed=42,
        )
        search_alg_obj = ConcurrencyLimiter(search_alg_obj, max_concurrent=4)
        scheduler = None
    elif search_alg == "asha":
        from ray.tune.schedulers import ASHAScheduler

        scheduler = ASHAScheduler(
            metric="val_accuracy",
            mode="max",
            max_t=10,
            grace_period=1,
            reduction_factor=2,
        )
        search_alg_obj = None
    else:  # random search
        search_alg_obj = None
        scheduler = None

    # Wrap trainable with data
    trainable = tune.with_parameters(
        _train_classical_ray,
        model_type=model_type,
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        experiment_name=experiment_name,
        dataset_version=dataset_version,
        preprocessing_config=preprocessing_config,
    )

    # Wrap with search algorithm if specified
    if search_alg_obj:
        trainable = tune.with_search_algorithm(trainable, search_alg_obj)

    # Run optimization
    analysis = tune.run(
        trainable,
        config=search_space,
        num_samples=n_trials,
        time_budget_s=timeout,
        storage_path=f"file:///tmp/ray_results/{study_name}",
        name=study_name,
        resources_per_trial={"cpu": 2, "gpu": 0},
        scheduler=scheduler,
        verbose=1,
    )

    # Log best results to MLflow
    mlflow.set_experiment(experiment_name)
    best_trial = analysis.get_best_trial(metric="val_accuracy", mode="max")
    best_config = best_trial.config
    best_metric = best_trial.last_result["val_accuracy"]

    with mlflow.start_run(run_name=f"{model_type}_ray_hyperopt_best"):
        mlflow.log_params(best_config)
        mlflow.log_metric("best_val_accuracy", best_metric)
        mlflow.set_tag("model_type", model_type)
        mlflow.set_tag("study_name", study_name)
        mlflow.set_tag("n_trials", n_trials)
        mlflow.set_tag("framework", "ray_tune")

    return analysis


def optimize_all_transformers_ray(
    model_types: list,
    train_dataset,
    val_dataset,
    experiment_name: str,
    n_trials: int = 10,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
    search_alg: Optional[str] = "hyperopt",
) -> Dict[str, Any]:
    """
    Run optimization for multiple transformer models using Ray Tune.

    Args:
        model_types: List of transformer model types to optimize
        train_dataset: Tokenized training dataset
        val_dataset: Tokenized validation dataset
        experiment_name: MLflow experiment name
        n_trials: Number of trials per model
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration
        search_alg: Search algorithm to use

    Returns:
        Dictionary mapping model types to their analysis objects
    """
    results = {}
    for model_type in model_types:
        print(f"Optimizing {model_type} with Ray Tune...")
        analysis = optimize_transformer_model_ray(
            model_type=model_type,
            train_dataset=train_dataset,
            val_dataset=val_dataset,
            experiment_name=experiment_name,
            n_trials=n_trials,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
            search_alg=search_alg,
        )
        best_metric = analysis.get_best_trial(
            metric="val_accuracy", mode="max"
        ).last_result["val_accuracy"]
        results[model_type] = analysis
        print(f"Best accuracy for {model_type}: {best_metric:.4f}")
    return results


def optimize_all_classical_ray(
    model_types: list,
    X_train,
    y_train,
    X_val,
    y_val,
    experiment_name: str,
    n_trials: int = 10,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
    search_alg: Optional[str] = "hyperopt",
) -> Dict[str, Any]:
    """
    Run optimization for multiple classical models using Ray Tune.

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
        search_alg: Search algorithm to use

    Returns:
        Dictionary mapping model types to their analysis objects
    """
    results = {}
    for model_type in model_types:
        print(f"Optimizing {model_type} with Ray Tune...")
        analysis = optimize_classical_model_ray(
            model_type=model_type,
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            experiment_name=experiment_name,
            n_trials=n_trials,
            dataset_version=dataset_version,
            preprocessing_config=preprocessing_config,
            search_alg=search_alg,
        )
        best_metric = analysis.get_best_trial(
            metric="val_accuracy", mode="max"
        ).last_result["val_accuracy"]
        results[model_type] = analysis
        print(f"Best accuracy for {model_type}: {best_metric:.4f}")
    return results


def get_best_params_ray(analysis: Any) -> Dict[str, Any]:
    """
    Extract best hyperparameters from a Ray Tune analysis.

    Args:
        analysis: Completed Ray Tune experiment

    Returns:
        Dictionary of best hyperparameters
    """
    best_trial = analysis.get_best_trial(metric="val_accuracy", mode="max")
    return best_trial.config


# ==================== Unified Interface ====================


Backend = str  # Literal["optuna", "ray"]


def optimize_model(
    model_type: str,
    X_train=None,
    y_train=None,
    train_dataset=None,
    val_dataset=None,
    experiment_name: str = "hyperopt_experiment",
    backend: Backend = "optuna",
    n_trials: int = 20,
    timeout: Optional[float] = None,
    study_name: Optional[str] = None,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
    **backend_kwargs,
) -> Any:
    """
    Unified hyperparameter optimization interface supporting both Optuna and Ray Tune.

    Args:
        model_type: Type of model (e.g., 'bert', 'roberta', 'logistic_regression', etc.)
        X_train: Training features for classical models
        y_train: Training labels for classical models
        train_dataset: Tokenized training dataset for transformers
        val_dataset: Tokenized validation dataset for transformers
        experiment_name: MLflow experiment name
        backend: Optimization backend ('optuna' or 'ray')
        n_trials: Number of optimization trials
        timeout: Timeout in seconds
        study_name: Name for the study/experiment
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration
        **backend_kwargs: Additional arguments passed to the backend-specific function
            For Ray Tune: search_alg (default: 'hyperopt')

    Returns:
        Study object (Optuna) or ExperimentAnalysis (Ray Tune)

    Raises:
        ValueError: If required arguments are missing or model type is unknown
    """
    if backend == "optuna":
        # Determine if it's a transformer or classical model
        transformer_models = {"bert", "roberta", "deberta", "distilbert", "albert"}
        is_transformer = model_type in transformer_models

        if is_transformer:
            if train_dataset is None or val_dataset is None:
                raise ValueError(
                    "train_dataset and val_dataset are required for transformer models"
                )
            return optimize_transformer_model(
                model_type=model_type,
                train_dataset=train_dataset,
                val_dataset=val_dataset,
                experiment_name=experiment_name,
                n_trials=n_trials,
                timeout=timeout,
                study_name=study_name,
                dataset_version=dataset_version,
                preprocessing_config=preprocessing_config,
            )
        else:
            if X_train is None or y_train is None or X_val is None or y_val is None:
                # Try to get from provided data
                raise ValueError(
                    "X_train, y_train, X_val, y_val are required for classical models"
                )
            return optimize_classical_model(
                model_type=model_type,
                X_train=X_train,
                y_train=y_train,
                X_val=X_val,
                y_val=y_val,
                experiment_name=experiment_name,
                n_trials=n_trials,
                timeout=timeout,
                study_name=study_name,
                dataset_version=dataset_version,
                preprocessing_config=preprocessing_config,
            )
    elif backend == "ray":
        transformer_models = {"bert", "roberta", "deberta", "distilbert", "albert"}
        is_transformer = model_type in transformer_models

        if is_transformer:
            if train_dataset is None or val_dataset is None:
                raise ValueError(
                    "train_dataset and val_dataset are required for transformer models"
                )
            return optimize_transformer_model_ray(
                model_type=model_type,
                train_dataset=train_dataset,
                val_dataset=val_dataset,
                experiment_name=experiment_name,
                n_trials=n_trials,
                timeout=timeout,
                study_name=study_name,
                dataset_version=dataset_version,
                preprocessing_config=preprocessing_config,
                **backend_kwargs,
            )
        else:
            if X_train is None or y_train is None or X_val is None or y_val is None:
                raise ValueError(
                    "X_train, y_train, X_val, y_val are required for classical models"
                )
            return optimize_classical_model_ray(
                model_type=model_type,
                X_train=X_train,
                y_train=y_train,
                X_val=X_val,
                y_val=y_val,
                experiment_name=experiment_name,
                n_trials=n_trials,
                timeout=timeout,
                study_name=study_name,
                dataset_version=dataset_version,
                preprocessing_config=preprocessing_config,
                **backend_kwargs,
            )
    else:
        raise ValueError(f"Unknown backend: {backend}. Choose 'optuna' or 'ray'.")


def optimize_all_models(
    model_types: list,
    X_train=None,
    y_train=None,
    X_val=None,
    y_val=None,
    train_dataset=None,
    val_dataset=None,
    experiment_name: str = "hyperopt_experiment",
    backend: Backend = "optuna",
    n_trials: int = 10,
    dataset_version: str = "v1.0",
    preprocessing_config: str = "standard",
    **backend_kwargs,
) -> Dict[str, Any]:
    """
    Unified interface for optimizing multiple models.

    Args:
        model_types: List of model types to optimize
        X_train: Training features for classical models
        y_train: Training labels for classical models
        X_val: Validation features for classical models
        y_val: Validation labels for classical models
        train_dataset: Tokenized training dataset for transformers
        val_dataset: Tokenized validation dataset for transformers
        experiment_name: MLflow experiment name
        backend: Optimization backend ('optuna' or 'ray')
        n_trials: Number of trials per model
        dataset_version: Dataset version
        preprocessing_config: Preprocessing configuration
        **backend_kwargs: Additional arguments passed to the backend-specific function

    Returns:
        Dictionary mapping model types to their optimization results
    """
    transformer_models = {"bert", "roberta", "deberta", "distilbert", "albert"}
    classical_models = {"logistic_regression", "svm", "random_forest", "xgboost"}

    # Separate model types by category
    transformer_list = [m for m in model_types if m in transformer_models]
    classical_list = [m for m in model_types if m in classical_models]

    results = {}

    if backend == "optuna":
        if transformer_list:
            results.update(
                optimize_all_transformers(
                    transformer_list,
                    train_dataset=train_dataset,
                    val_dataset=val_dataset,
                    experiment_name=experiment_name,
                    n_trials=n_trials,
                    dataset_version=dataset_version,
                    preprocessing_config=preprocessing_config,
                )
            )
        if classical_list:
            results.update(
                optimize_all_classical(
                    classical_list,
                    X_train=X_train,
                    y_train=y_train,
                    X_val=X_val,
                    y_val=y_val,
                    experiment_name=experiment_name,
                    n_trials=n_trials,
                    dataset_version=dataset_version,
                    preprocessing_config=preprocessing_config,
                )
            )
    elif backend == "ray":
        if transformer_list:
            results.update(
                optimize_all_transformers_ray(
                    transformer_list,
                    train_dataset=train_dataset,
                    val_dataset=val_dataset,
                    experiment_name=experiment_name,
                    n_trials=n_trials,
                    dataset_version=dataset_version,
                    preprocessing_config=preprocessing_config,
                    **backend_kwargs,
                )
            )
        if classical_list:
            results.update(
                optimize_all_classical_ray(
                    classical_list,
                    X_train=X_train,
                    y_train=y_train,
                    X_val=X_val,
                    y_val=y_val,
                    experiment_name=experiment_name,
                    n_trials=n_trials,
                    dataset_version=dataset_version,
                    preprocessing_config=preprocessing_config,
                    **backend_kwargs,
                )
            )
    else:
        raise ValueError(f"Unknown backend: {backend}. Choose 'optuna' or 'ray'.")

    return results
