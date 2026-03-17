"""
Classical ML model implementations for text classification.
"""

from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
import numpy as np
import mlflow
import mlflow.sklearn


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

    def predict(self, X):
        """Make predictions."""
        return self.model.predict(X)

    def predict_proba(self, X):
        """Get prediction probabilities."""
        return self.model.predict_proba(X)

    def log_to_mlflow(self, experiment_name, run_name="logistic_regression"):
        """Log model and parameters to MLFlow."""
        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            for key, value in self.params.items():
                mlflow.log_param(key, value)

            # Log model
            mlflow.sklearn.log_model(
                self.model,
                "model",
                input_example=X_train[:1] if hasattr(self, "X_train") else None,
            )

            # Log tags
            mlflow.set_tag("model_type", "logistic_regression")
            mlflow.set_tag("framework", "sklearn")

            return run.info.run_id


class SVMModel:
    """Support Vector Machine with TF-IDF features."""

    def __init__(self, params=None):
        self.params = params or {"C": 1.0, "max_iter": 1000, "random_state": 42}
        self.model = None

    def train(self, X_train, y_train, X_val, y_val):
        """Train SVM model."""
        self.model = LinearSVC(**self.params)
        self.model.fit(X_train, y_train)

        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)

        return {"train_accuracy": train_score, "val_accuracy": val_score}

    def predict(self, X):
        """Make predictions."""
        return self.model.predict(X)

    def log_to_mlflow(self, experiment_name, run_name="svm"):
        """Log model to MLFlow."""
        with mlflow.start_run(run_name=run_name) as run:
            for key, value in self.params.items():
                mlflow.log_param(key, value)

            mlflow.sklearn.log_model(self.model, "model")
            mlflow.set_tag("model_type", "svm")
            mlflow.set_tag("framework", "sklearn")

            return run.info.run_id


class RandomForestModel:
    """Random Forest classifier."""

    def __init__(self, params=None):
        self.params = params or {
            "n_estimators": 100,
            "max_depth": 10,
            "random_state": 42,
            "n_jobs": -1,
        }
        self.model = None

    def train(self, X_train, y_train, X_val, y_val):
        """Train Random Forest model."""
        self.model = RandomForestClassifier(**self.params)
        self.model.fit(X_train, y_train)

        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)

        return {"train_accuracy": train_score, "val_accuracy": val_score}

    def predict(self, X):
        """Make predictions."""
        return self.model.predict(X)

    def predict_proba(self, X):
        """Get prediction probabilities."""
        return self.model.predict_proba(X)

    def log_to_mlflow(self, experiment_name, run_name="random_forest"):
        """Log model to MLFlow."""
        with mlflow.start_run(run_name=run_name) as run:
            for key, value in self.params.items():
                mlflow.log_param(key, value)

            mlflow.sklearn.log_model(self.model, "model")
            mlflow.set_tag("model_type", "random_forest")
            mlflow.set_tag("framework", "sklearn")

            return run.info.run_id


def create_model(model_name, params=None):
    """Factory function to create model instances."""
    models = {
        "logistic_regression": LogisticRegressionModel,
        "svm": SVMModel,
        "random_forest": RandomForestModel,
    }

    if model_name not in models:
        raise ValueError(
            f"Unknown model: {model_name}. Available: {list(models.keys())}"
        )

    return models[model_name](params)
