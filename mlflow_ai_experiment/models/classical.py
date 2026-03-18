"""
Classical ML model implementations for text classification.
"""

from typing import Any, Dict, Optional

import joblib  # type: ignore
import mlflow
import mlflow.sklearn as mlflow_sklearn  # type: ignore
import numpy as np
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV  # type: ignore
from sklearn.ensemble import RandomForestClassifier  # type: ignore
from sklearn.linear_model import LogisticRegression  # type: ignore
from sklearn.svm import LinearSVC  # type: ignore

from ..experiment_tracker import set_standard_tags


class LogisticRegressionModel:
    """Logistic Regression with TF-IDF features."""

    def __init__(self, params=None):
        self.params = params or {
            "C": 1.0,
            "max_iter": 1000,
            "solver": "liblinear",
            "random_state": 42,
        }
        self.model = None

    def train(self, X_train, y_train, X_val, y_val):
        """Train model with optional hyperparameter tuning."""
        self.model = LogisticRegression(**self.params)
        self.model.fit(X_train, y_train)

        # Calculate metrics
        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)

        return {"train_accuracy": train_score, "val_accuracy": val_score}

    def predict(self, X) -> np.ndarray:
        """Make predictions."""
        assert self.model is not None
        return self.model.predict(X)  # type: ignore[return-type]

    def predict_proba(self, X) -> np.ndarray:
        """Get prediction probabilities."""
        assert self.model is not None
        return self.model.predict_proba(X)  # type: ignore[return-type]

    def log_to_mlflow(
        self,
        experiment_name,
        run_name="logistic_regression",
        X_test=None,
        y_test=None,
        dataset_version="v1.0",
        preprocessing_config="standard",
    ):
        """Log model and parameters to MLFlow."""
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            for key, value in self.params.items():
                mlflow.log_param(key, value)

            # Log model
            if X_test is not None:
                mlflow_sklearn.log_model(self.model, "model", input_example=X_test[:1])
            else:
                mlflow_sklearn.log_model(self.model, "model")

            # Log evaluation metrics if test data provided
            if X_test is not None and y_test is not None:
                assert self.model is not None
                from sklearn.metrics import accuracy_score  # type: ignore
                from sklearn.metrics import f1_score, precision_score, recall_score

                y_pred = self.predict(X_test)

                mlflow.log_metric("accuracy", accuracy_score(y_test, y_pred))
                mlflow.log_metric(
                    "precision", precision_score(y_test, y_pred, zero_division="warn")
                )
                mlflow.log_metric(
                    "recall", recall_score(y_test, y_pred, zero_division="warn")
                )
                mlflow.log_metric("f1", f1_score(y_test, y_pred, zero_division="warn"))

            # Set standardized tags
            set_standard_tags(
                run=run,
                model_type="logistic_regression",
                dataset_version=dataset_version,
                preprocessing_config=preprocessing_config,
                framework="sklearn",
            )

            return run.info.run_id

    def save_model(self, path):
        """Save model to disk."""
        joblib.dump(self.model, path)

    @classmethod
    def load_model(cls, path, params=None):
        """Load model from disk."""
        instance = cls(params)
        instance.model = joblib.load(path)
        return instance


class SVMModel:
    """Support Vector Machine with TF-IDF features and probability calibration."""

    def __init__(self, params=None):
        self.params = params or {"C": 1.0, "max_iter": 1000, "random_state": 42}
        self.base_model = None
        self.model = None  # This will hold the calibrated model

    def train(self, X_train, y_train, X_val, y_val):
        """Train SVM model with probability calibration using cross-validation."""
        # Use LinearSVC as base classifier and calibrate using CV
        self.model = CalibratedClassifierCV(
            LinearSVC(**self.params),
            method="sigmoid",
            cv=2,  # Use 2-fold CV for calibration
        )
        self.model.fit(X_train, y_train)

        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)

        return {"train_accuracy": train_score, "val_accuracy": val_score}

    def predict(self, X) -> np.ndarray:
        """Make predictions."""
        assert self.model is not None
        return self.model.predict(X)  # type: ignore[return-type]

    def predict_proba(self, X) -> np.ndarray:
        """Get prediction probabilities."""
        assert self.model is not None
        return self.model.predict_proba(X)  # type: ignore[return-type]

    def log_to_mlflow(
        self,
        experiment_name,
        run_name="svm",
        X_test=None,
        y_test=None,
        dataset_version="v1.0",
        preprocessing_config="standard",
    ):
        """Log model to MLFlow."""
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name=run_name) as run:
            for key, value in self.params.items():
                mlflow.log_param(key, value)

            # Log model
            if X_test is not None:
                mlflow_sklearn.log_model(self.model, "model", input_example=X_test[:1])
            else:
                mlflow_sklearn.log_model(self.model, "model")

            # Log evaluation metrics if test data provided
            if X_test is not None and y_test is not None:
                assert self.model is not None
                from sklearn.metrics import accuracy_score  # type: ignore
                from sklearn.metrics import f1_score, precision_score, recall_score

                y_pred = self.predict(X_test)

                mlflow.log_metric("accuracy", accuracy_score(y_test, y_pred))
                mlflow.log_metric(
                    "precision", precision_score(y_test, y_pred, zero_division="warn")
                )
                mlflow.log_metric(
                    "recall", recall_score(y_test, y_pred, zero_division="warn")
                )
                mlflow.log_metric("f1", f1_score(y_test, y_pred, zero_division="warn"))

            # Set standardized tags
            set_standard_tags(
                run=run,
                model_type="svm",
                dataset_version=dataset_version,
                preprocessing_config=preprocessing_config,
                framework="sklearn",
            )

            return run.info.run_id

    def save_model(self, path):
        """Save model to disk."""
        joblib.dump(self.model, path)

    @classmethod
    def load_model(cls, path, params=None):
        """Load model from disk."""
        instance = cls(params)
        instance.model = joblib.load(path)
        return instance


class RandomForestModel:
    """Random Forest classifier."""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params: Dict[str, Any] = params or {
            "n_estimators": 100,
            "max_depth": 10,
            "random_state": 42,
            "n_jobs": -1,
        }
        self.model = None

    def train(self, X_train, y_train, X_val, y_val):
        """Train Random Forest model."""
        self.model = RandomForestClassifier(**self.params)  # type: ignore
        self.model.fit(X_train, y_train)

        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)

        return {"train_accuracy": train_score, "val_accuracy": val_score}

    def predict(self, X):
        """Make predictions."""
        assert self.model is not None
        return self.model.predict(X)

    def predict_proba(self, X) -> np.ndarray:
        """Get prediction probabilities."""
        assert self.model is not None
        return self.model.predict_proba(X)  # type: ignore[return-type]

    def log_to_mlflow(
        self,
        experiment_name,
        run_name="random_forest",
        X_test=None,
        y_test=None,
        dataset_version="v1.0",
        preprocessing_config="standard",
    ):
        """Log model to MLFlow."""
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name=run_name) as run:
            for key, value in self.params.items():
                mlflow.log_param(key, value)

            # Log model
            if X_test is not None:
                mlflow_sklearn.log_model(self.model, "model", input_example=X_test[:1])
            else:
                mlflow_sklearn.log_model(self.model, "model")

            # Log evaluation metrics if test data provided
            if X_test is not None and y_test is not None:
                assert self.model is not None
                from sklearn.metrics import accuracy_score  # type: ignore
                from sklearn.metrics import f1_score, precision_score, recall_score

                y_pred = self.predict(X_test)

                mlflow.log_metric("accuracy", accuracy_score(y_test, y_pred))
                mlflow.log_metric(
                    "precision", precision_score(y_test, y_pred, zero_division="warn")
                )
                mlflow.log_metric(
                    "recall", recall_score(y_test, y_pred, zero_division="warn")
                )
                mlflow.log_metric("f1", f1_score(y_test, y_pred, zero_division="warn"))

            # Set standardized tags
            set_standard_tags(
                run=run,
                model_type="random_forest",
                dataset_version=dataset_version,
                preprocessing_config=preprocessing_config,
                framework="sklearn",
            )

            return run.info.run_id

    def save_model(self, path):
        """Save model to disk."""
        joblib.dump(self.model, path)

    @classmethod
    def load_model(cls, path, params=None):
        """Load model from disk."""
        instance = cls(params)
        instance.model = joblib.load(path)
        return instance


class XGBoostModel:
    """XGBoost classifier with GPU support."""

    def __init__(self, params=None):
        self.params = params or {
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "n_jobs": -1,
            "eval_metric": "logloss",
            "tree_method": "hist",  # Use 'gpu_hist' if GPU available
        }
        self.model = None

    def train(self, X_train, y_train, X_val, y_val):
        """Train XGBoost model."""
        self.model = xgb.XGBClassifier(**self.params)

        # Prepare validation set for early stopping
        eval_set = [(X_train, y_train), (X_val, y_val)]

        self.model.fit(X_train, y_train, eval_set=eval_set, verbose=False)

        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)

        return {"train_accuracy": train_score, "val_accuracy": val_score}

    def predict(self, X) -> np.ndarray:
        """Make predictions."""
        assert self.model is not None
        return self.model.predict(X)  # type: ignore[return-type]

    def predict_proba(self, X) -> np.ndarray:
        """Get prediction probabilities."""
        assert self.model is not None
        return self.model.predict_proba(X)  # type: ignore[return-type]

    def log_to_mlflow(
        self,
        experiment_name,
        run_name="xgboost",
        X_test=None,
        y_test=None,
        dataset_version="v1.0",
        preprocessing_config="standard",
    ):
        """Log model to MLFlow."""
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name=run_name) as run:
            for key, value in self.params.items():
                mlflow.log_param(key, value)

            # Log model
            if X_test is not None:
                mlflow_sklearn.log_model(self.model, "model", input_example=X_test[:1])
            else:
                mlflow_sklearn.log_model(self.model, "model")

            # Log evaluation metrics if test data provided
            if X_test is not None and y_test is not None:
                assert self.model is not None
                from sklearn.metrics import accuracy_score  # type: ignore
                from sklearn.metrics import f1_score, precision_score, recall_score

                y_pred = self.predict(X_test)

                mlflow.log_metric("accuracy", accuracy_score(y_test, y_pred))
                mlflow.log_metric(
                    "precision", precision_score(y_test, y_pred, zero_division="warn")
                )
                mlflow.log_metric(
                    "recall", recall_score(y_test, y_pred, zero_division="warn")
                )
                mlflow.log_metric("f1", f1_score(y_test, y_pred, zero_division="warn"))

            # Set standardized tags
            set_standard_tags(
                run=run,
                model_type="xgboost",
                dataset_version=dataset_version,
                preprocessing_config=preprocessing_config,
                framework="xgboost",
            )

            return run.info.run_id

    def save_model(self, path):
        """Save model to disk."""
        joblib.dump(self.model, path)

    @classmethod
    def load_model(cls, path, params=None):
        """Load model from disk."""
        instance = cls(params)
        instance.model = joblib.load(path)
        return instance


def create_model(model_name, params=None):
    """Factory function to create model instances."""
    models = {
        "logistic_regression": LogisticRegressionModel,
        "svm": SVMModel,
        "random_forest": RandomForestModel,
        "xgboost": XGBoostModel,
    }

    if model_name not in models:
        raise ValueError(
            f"Unknown model: {model_name}. Available: {list(models.keys())}"
        )

    return models[model_name](params)
