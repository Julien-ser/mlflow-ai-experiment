"""
Baseline model implementation using TF-IDF + Logistic Regression.
This serves as a simple, interpretable baseline for text classification.
"""

import os
import joblib
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
import mlflow
import mlflow.sklearn


class BaselineModel:
    """TF-IDF + Logistic Regression baseline for text classification."""

    def __init__(self, max_features: int = 5000, ngram_range: Tuple[int, int] = (1, 2)):
        """
        Initialize baseline model.

        Args:
            max_features: Maximum number of features for TF-IDF
            ngram_range: Range of n-grams to consider (min, max)
        """
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            stop_words="english",
            min_df=2,
            max_df=0.9,
        )
        self.classifier = LogisticRegression(max_iter=1000, n_jobs=-1, random_state=42)
        self.is_fitted = False

    def preprocess(self, texts: pd.Series) -> np.ndarray:
        """Convert raw texts to TF-IDF features."""
        return self.vectorizer.transform(texts)

    def train(self, X_train: pd.Series, y_train: pd.Series) -> None:
        """
        Train the baseline model.

        Args:
            X_train: Training texts
            y_train: Training labels
        """
        # Fit vectorizer and transform
        X_train_tfidf = self.vectorizer.fit_transform(X_train)

        # Fit classifier
        self.classifier.fit(X_train_tfidf, y_train)
        self.is_fitted = True

    def predict(self, X: pd.Series) -> np.ndarray:
        """Make predictions on new data."""
        if not self.is_fitted:
            raise ValueError("Model must be trained before prediction")

        X_tfidf = self.vectorizer.transform(X)
        return self.classifier.predict(X_tfidf)

    def predict_proba(self, X: pd.Series) -> np.ndarray:
        """Get prediction probabilities."""
        if not self.is_fitted:
            raise ValueError("Model must be trained before prediction")

        X_tfidf = self.vectorizer.transform(X)
        return self.classifier.predict_proba(X_tfidf)

    def evaluate(self, X_test: pd.Series, y_test: pd.Series) -> Dict[str, Any]:
        """
        Evaluate model performance.

        Returns:
            Dictionary with metrics and confusion matrix
        """
        y_pred = self.predict(X_test)
        y_pred_proba = self.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }

        return metrics

    def log_to_mlflow(
        self,
        X_train: pd.Series,
        y_train: pd.Series,
        X_test: pd.Series,
        y_test: pd.Series,
        experiment_name: str = "baseline",
        run_name: str = "tfidf_logreg",
    ) -> None:
        """
        Train and log model to MLFlow.

        Args:
            X_train, y_train: Training data
            X_test, y_test: Test data for evaluation
            experiment_name: MLFlow experiment name
            run_name: MLFlow run name
        """
        # Set MLFlow experiment
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name=run_name):
            # Log parameters
            mlflow.log_params(
                {
                    "model_type": "TF-IDF+LogisticRegression",
                    "max_features": self.max_features,
                    "ngram_range": str(self.ngram_range),
                    "classifier": "LogisticRegression",
                    "max_iter": self.classifier.max_iter,
                    "random_state": 42,
                }
            )

            # Train model
            print("Training baseline model...")
            self.train(X_train, y_train)

            # Evaluate
            print("Evaluating model...")
            metrics = self.evaluate(X_test, y_test)

            # Log metrics
            mlflow.log_metrics(
                {
                    "accuracy": metrics["accuracy"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1": metrics["f1"],
                }
            )

            # Log model
            mlflow.sklearn.log_model(
                self.classifier, "model", registered_model_name="baseline_logreg"
            )

            # Save vectorizer as artifact
            vectorizer_path = "vectorizer.pkl"
            joblib.dump(self.vectorizer, vectorizer_path)
            mlflow.log_artifact(vectorizer_path)
            os.remove(vectorizer_path)

            print(f"Baseline logged to MLFlow run: {mlflow.active_run().info.run_id}")
            print(f"Metrics: {metrics}")

            return metrics

    def save(self, path: str) -> None:
        """Save model and vectorizer to disk."""
        if not self.is_fitted:
            raise ValueError("Model must be trained before saving")

        save_dict = {
            "vectorizer": self.vectorizer,
            "classifier": self.classifier,
            "max_features": self.max_features,
            "ngram_range": self.ngram_range,
        }
        joblib.dump(save_dict, path)

    @classmethod
    def load(cls, path: str) -> "BaselineModel":
        """Load model from disk."""
        save_dict = joblib.load(path)

        instance = cls(
            max_features=save_dict["max_features"], ngram_range=save_dict["ngram_range"]
        )
        instance.vectorizer = save_dict["vectorizer"]
        instance.classifier = save_dict["classifier"]
        instance.is_fitted = True

        return instance
