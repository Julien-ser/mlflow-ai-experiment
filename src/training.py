"""
Unified training pipeline for classical and transformer models.
"""

import os
import yaml
import mlflow
from typing import Union, Dict, Any

from .data_loader import load_imdb_dataset
from .preprocessing import preprocess_dataset
from .models.classical import create_model as create_classical_model
from .models.transformers import create_transformer_model
from .evaluation import evaluate_model


class TrainingPipeline:
    def __init__(self, config: Union[str, Dict[str, Any]]):
        if isinstance(config, str):
            with open(config, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = config
        self._validate_config()

    def _validate_config(self):
        required_keys = ["model", "mlflow"]
        for k in required_keys:
            if k not in self.config:
                raise ValueError(f"Missing required config key: {k}")
        model_cfg = self.config["model"]
        if "type" not in model_cfg:
            raise ValueError("model.type is required")
        if model_cfg["type"] not in ["classical", "transformer"]:
            raise ValueError("model.type must be 'classical' or 'transformer'")

    def setup_mlflow(self):
        mlflow_cfg = self.config["mlflow"]
        tracking_uri = mlflow_cfg.get("tracking_uri", "mlruns")
        experiment_name = mlflow_cfg.get("experiment_name", "default")
        mlflow.set_tracking_uri(tracking_uri)
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
            else:
                experiment_id = experiment.experiment_id
            mlflow.set_experiment(experiment_id)
        except Exception as e:
            print(f"Warning: MLFlow setup error: {e}")
        return mlflow_cfg

    def load_data(self):
        dataset_cfg = self.config.get("data", {})
        dataset_name = dataset_cfg.get("dataset", "imdb")
        if dataset_name != "imdb":
            raise NotImplementedError("Only IMDB dataset is supported currently")
        config_path = dataset_cfg.get("config_path", "config.yaml")
        return load_imdb_dataset(config_path if os.path.exists(config_path) else None)

    def preprocess_data(self, train_df, val_df, test_df):
        model_type = self.config["model"]["type"]
        if model_type == "classical":
            processed = preprocess_dataset(train_df, val_df, test_df)
            return processed
        else:
            return {
                "train": (train_df["text"].tolist(), train_df["label"].tolist()),
                "val": (val_df["text"].tolist(), val_df["label"].tolist()),
                "test": (test_df["text"].tolist(), test_df["label"].tolist()),
            }

    def create_model(self):
        model_cfg = self.config["model"]
        model_type = model_cfg["type"]
        model_name = model_cfg["name"]
        hyperparams = {
            k: v for k, v in model_cfg.items() if k not in ["type", "name", "backend"]
        }
        if model_type == "classical":
            return create_classical_model(model_name, model_cfg.get("params"))
        else:
            return create_transformer_model(model_name, **hyperparams)

    def train(self):
        mlflow_cfg = self.setup_mlflow()
        train_df, val_df, test_df = self.load_data()
        data = self.preprocess_data(train_df, val_df, test_df)
        model = self.create_model()
        model_type = self.config["model"]["type"]

        run_name = self.config.get("run_name", f"{model_type}_training")
        with mlflow.start_run(run_name=run_name) as run:
            self._log_config_params()

            if model_type == "classical":
                X_train, y_train = data["train"]
                X_val, y_val = data["val"]
                X_test, y_test = data["test"]
                # Train
                train_metrics = model.train(X_train, y_train, X_val, y_val)
                mlflow.log_metric("train_accuracy", train_metrics["train_accuracy"])
                mlflow.log_metric("val_accuracy", train_metrics["val_accuracy"])
                # Test evaluation
                test_metrics = evaluate_model(
                    model, X_test, y_test, log_to_mlflow=False
                )
                for key, value in test_metrics.items():
                    mlflow.log_metric(f"test_{key}", value)
                # Log model as artifact
                self._log_classical_model_artifact(
                    model, model_name, model_cfg.get("params", {})
                )
            else:
                train_texts, train_labels = data["train"]
                val_texts, val_labels = data["val"]
                test_texts, test_labels = data["test"]
                # Training arguments from config
                training_args = self.config.get("training_args", {}).copy()
                if self.config.get("mixed_precision", False):
                    training_args["fp16"] = True
                # Tokenize
                model.load_tokenizer()
                train_dataset = model.tokenize_data(train_texts, train_labels)
                val_dataset = model.tokenize_data(val_texts, val_labels)
                test_dataset = model.tokenize_data(test_texts, test_labels)
                # Train (includes its own MLflow logging as nested run)
                model.train(
                    train_dataset,
                    val_dataset,
                    experiment_name=mlflow_cfg["experiment_name"],
                    training_args=training_args,
                )
                # Evaluate on test set in this outer run
                test_preds = model.predict(test_texts)
                from sklearn.metrics import (
                    accuracy_score,
                    precision_score,
                    recall_score,
                    f1_score,
                )

                test_accuracy = accuracy_score(test_labels, test_preds)
                test_precision = precision_score(
                    test_labels, test_preds, zero_division=0
                )
                test_recall = recall_score(test_labels, test_preds, zero_division=0)
                test_f1 = f1_score(test_labels, test_preds, zero_division=0)
                mlflow.log_metric("test_accuracy", test_accuracy)
                mlflow.log_metric("test_precision", test_precision)
                mlflow.log_metric("test_recall", test_recall)
                mlflow.log_metric("test_f1", test_f1)

        return {"run_id": run.info.run_id}

    def _log_config_params(self):
        def flatten_dict(d, parent_key="", sep="."):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        flat_params = flatten_dict(self.config)
        for key, value in flat_params.items():
            mlflow.log_param(key, value)

    def _log_classical_model_artifact(self, model, model_name, params):
        import joblib, tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/model.pkl"
            model.save_model(path)
            mlflow.log_artifact(path, artifact_path="model")
        mlflow.set_tag("model_type", "classical")
        mlflow.set_tag("model_name", model_name)
