"""
Unified training pipeline for classical and transformer models.
Supports both PyTorch and TensorFlow backends, with features like logging,
checkpointing, early stopping, mixed precision, and comprehensive experiment tracking.
"""

from __future__ import annotations

import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
import numpy as np
import mlflow
import joblib

if TYPE_CHECKING:
    from torch.utils.data import DataLoader, Dataset
    import torch
    import torch.optim as optim

# Runtime imports (optional PyTorch)
try:
    import torch
    from torch.utils.data import DataLoader, Dataset
    import torch.optim as optim

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore

# Optional TensorFlow import
try:
    import tensorflow as tf  # type: ignore

    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

from .models.classical import (
    LogisticRegressionModel,
    SVMModel,
    RandomForestModel,
    XGBoostModel,
)
from .models.transformers import TransformerModel
from .evaluation import compute_metrics

logger = logging.getLogger(__name__)


class Trainer:
    """
    Unified trainer supporting classical ML models and transformer models.
    Handles training loops, logging, checkpointing, early stopping, mixed precision.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        model_type: str = "classical",
        backend: str = "pytorch",
    ) -> None:
        self.config = config
        self.model_type = model_type
        self.backend = backend
        # Device setup
        self.device = None
        if TORCH_AVAILABLE:
            assert torch is not None
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.optimizer = None
        self.scaler = None  # Initialized lazily in _train_transformer if needed
        self.early_stopping_counter = 0
        self.checkpoint_path = Path(config.get("checkpoint_dir", "checkpoints"))
        self.checkpoint_path.mkdir(parents=True, exist_ok=True)

        # MLflow setup
        self.mlflow_enabled = config.get("mlflow_tracking", True)
        if self.mlflow_enabled:
            mlflow.set_tracking_uri(config.get("mlflow_uri", "mlruns"))
            experiment_name = config.get("mlflow_experiment_name", "experiment")
            mlflow.set_experiment(experiment_name)

        self.start_time = time.time()

    def _prepare_model(self, model_config: Dict[str, Any]) -> None:
        """
        Prepare model based on type and backend.
        """
        if self.model_type == "classical":
            model_cls = {
                "logistic_regression": LogisticRegressionModel,
                "svm": SVMModel,
                "random_forest": RandomForestModel,
                "xgboost": XGBoostModel,
            }
            if model_config["name"] not in model_cls:
                raise ValueError(f"Unsupported classical model: {model_config['name']}")
            self.model = model_cls[model_config["name"]](model_config["params"])
            self.optimizer = None
        elif self.model_type == "transformer":
            if not TORCH_AVAILABLE:
                raise RuntimeError("Transformer training requires PyTorch")
            transformer = TransformerModel(
                model_name=model_config["model_name"],
                num_labels=model_config.get("num_labels", 2),
                config=model_config,
            )
            transformer.build_model()
            self.model = transformer.model
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def _prepare_optimizer(
        self, optimizer_config: Optional[Dict[str, Any]] = None
    ) -> None:
        if optimizer_config is None:
            optimizer_config = {}
        optimizer_name = optimizer_config.get("name", "adam")
        lr = optimizer_config.get("lr", 1e-4)

        if self.backend == "pytorch":
            if not TORCH_AVAILABLE:
                raise RuntimeError("PyTorch is not available")
            assert self.model is not None, (
                "Model must be initialized before preparing optimizer"
            )
            assert optim is not None
            if optimizer_name == "adam":
                self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
            elif optimizer_name == "adamw":
                self.optimizer = optim.AdamW(self.model.parameters(), lr=lr)
            elif optimizer_name == "sgd":
                self.optimizer = optim.SGD(self.model.parameters(), lr=lr)
            else:
                raise ValueError(f"Unsupported optimizer: {optimizer_name}")
        elif self.backend == "tensorflow":
            raise NotImplementedError("TensorFlow backend not yet implemented")
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def _prepare_dataloaders(
        self,
        train_dataset: Any,
        valid_dataset: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Prepare train and validation DataLoaders.
        """
        assert DataLoader is not None, "DataLoader is not available"
        assert self.device is not None, "Device not initialized"
        batch_size = self.config.get("batch_size", 32)
        num_workers = self.config.get("num_workers", 0)
        pin_memory = self.device.type == "cuda"

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=pin_memory,
        )
        valid_loader = None
        if valid_dataset is not None:
            valid_loader = DataLoader(
                valid_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=num_workers,
                pin_memory=pin_memory,
            )
        return {"train": train_loader, "valid": valid_loader}

    def _train_classical(
        self,
        train_dataset: Tuple[np.ndarray, np.ndarray],
        valid_dataset: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    ) -> Dict[str, float]:
        """
        Train a classical model.
        """
        assert self.model is not None
        X_train, y_train = train_dataset
        logger.info("Training classical model...")
        start_time = time.time()
        self.model.fit(X_train, y_train)
        training_duration = time.time() - start_time
        logger.info(f"Training completed in {training_duration:.2f} seconds")

        # Evaluate on training set
        y_pred_train = self.model.predict(X_train)
        train_metrics = compute_metrics(y_train, y_pred_train)
        train_metrics["training_time"] = training_duration

        # Evaluate on validation set if provided
        val_metrics: Dict[str, float] = {}
        if valid_dataset is not None:
            X_val, y_val = valid_dataset
            y_pred_val = self.model.predict(X_val)
            val_metrics = compute_metrics(y_val, y_pred_val)
            val_metrics["validation_time"] = time.time() - start_time

        # Log to MLflow
        if self.mlflow_enabled:
            mlflow.log_metrics({f"train_{k}": v for k, v in train_metrics.items()})
            for k, v in val_metrics.items():
                mlflow.log_metric(f"val_{k}", v)
            # Save model artifact
            model_path = self.checkpoint_path / "classical_model.joblib"
            joblib.dump(self.model, model_path)
            mlflow.log_artifact(str(model_path))

        return {**train_metrics, **val_metrics}

    def _train_transformer(
        self,
        train_dataset: Any,
        valid_dataset: Optional[Any] = None,
    ) -> Dict[str, float]:
        """
        Train a transformer model using PyTorch.
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not available for transformer training")
        assert torch is not None
        assert self.model is not None

        # Initialize scaler for mixed precision if needed
        if self.scaler is None and self.config.get("mixed_precision", False):
            from torch.cuda.amp import GradScaler

            self.scaler = GradScaler()

        # Prepare optimizer if not already
        if self.optimizer is None:
            optimizer_config = self.config.get("optimizer", {})
            self._prepare_optimizer(optimizer_config)
        assert self.optimizer is not None

        # Prepare dataloaders
        loaders = self._prepare_dataloaders(train_dataset, valid_dataset)
        train_loader = loaders["train"]
        valid_loader = loaders["valid"]

        # Import autocast for mixed precision
        from torch.cuda.amp import autocast

        num_epochs = self.config.get("num_epochs", 3)
        best_val_metric = float("inf")
        patience = self.config.get("early_stopping_patience", 5)

        total_start_time = time.time()

        for epoch in range(num_epochs):
            epoch_start = time.time()
            self.model.train()
            total_loss = 0.0
            for batch in train_loader:  # type: ignore
                batch = {k: v.to(self.device) for k, v in batch.items()}
                self.optimizer.zero_grad()
                if self.scaler:
                    with autocast():
                        outputs = self.model(**batch)
                        loss = outputs.loss
                    self.scaler.scale(loss).backward()
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    outputs = self.model(**batch)
                    loss = outputs.loss
                    loss.backward()
                    self.optimizer.step()
                total_loss += loss.item()
            avg_train_loss = total_loss / len(train_loader)

            # Validation
            val_metrics = None
            avg_val_loss = None
            if valid_loader is not None:
                self.model.eval()
                val_loss = 0.0
                all_preds = []
                all_labels = []
                with torch.no_grad():
                    for batch in valid_loader:  # type: ignore
                        batch = {k: v.to(self.device) for k, v in batch.items()}
                        outputs = self.model(**batch)
                        loss = outputs.loss
                        val_loss += loss.item()
                        logits = outputs.logits
                        preds = torch.argmax(logits, dim=-1)
                        all_preds.extend(preds.cpu().numpy())
                        all_labels.extend(batch["labels"].cpu().numpy())
                avg_val_loss = val_loss / len(valid_loader)
                val_metrics = compute_metrics(np.array(all_labels), np.array(all_preds))
                val_metrics["val_loss"] = avg_val_loss

            epoch_time = time.time() - epoch_start
            logger.info(
                f"Epoch {epoch + 1}/{num_epochs} - Train loss: {avg_train_loss:.4f}"
                + (f" - Val loss: {avg_val_loss:.4f}" if val_metrics else "")
            )

            # Log epoch metrics to MLflow
            if self.mlflow_enabled:
                mlflow.log_metric("train_loss", avg_train_loss, step=epoch)
                if val_metrics:
                    for k, v in val_metrics.items():
                        mlflow.log_metric(k, v, step=epoch)

            # Checkpoint: save best model based on validation loss
            current_val_metric = (
                avg_val_loss if avg_val_loss is not None else avg_train_loss
            )
            if current_val_metric < best_val_metric:
                best_val_metric = current_val_metric
                checkpoint_file = self.checkpoint_path / "best_model.pt"
                torch.save(self.model.state_dict(), checkpoint_file)
                logger.info(f"Checkpoint saved at {checkpoint_file}")
                self.early_stopping_counter = 0
            else:
                self.early_stopping_counter += 1
                if self.early_stopping_counter >= patience:
                    logger.info("Early stopping triggered")
                    break

        total_time = time.time() - total_start_time
        final_metrics = {"total_training_time": total_time}
        if self.mlflow_enabled:
            mlflow.log_metrics(final_metrics)
            # Log best model as artifact
            if self.checkpoint_path.joinpath("best_model.pt").exists():
                mlflow.log_artifact(str(self.checkpoint_path / "best_model.pt"))

        return final_metrics

    def train(
        self,
        train_dataset: Any,
        valid_dataset: Optional[Any] = None,
    ) -> Dict[str, float]:
        """
        Main training entry point.
        """
        # Prepare model
        model_config = self.config.get("model", {})
        self._prepare_model(model_config)

        # Log parameters
        if self.mlflow_enabled:
            mlflow.log_params(self.config)

        # Train based on model type
        if self.model_type == "classical":
            if not isinstance(train_dataset, tuple) or len(train_dataset) != 2:
                raise ValueError(
                    "For classical models, train_dataset must be a tuple (X, y)"
                )
            metrics = self._train_classical(train_dataset, valid_dataset)
        elif self.model_type == "transformer":
            metrics = self._train_transformer(train_dataset, valid_dataset)
        else:
            raise ValueError(f"Unsupported model_type: {self.model_type}")

        logger.info("Training completed. Metrics: %s", metrics)
        return metrics

    def evaluate(self, test_dataset: Any) -> Dict[str, float]:
        """
        Evaluate the trained model on a test set.
        """
        if self.model is None:
            raise RuntimeError("Model has not been trained yet")

        if self.model_type == "classical":
            if not isinstance(test_dataset, tuple):
                raise ValueError(
                    "For classical models, test_dataset must be a tuple (X, y)"
                )
            X_test, y_test = test_dataset
            y_pred = self.model.predict(X_test)
            metrics = compute_metrics(y_test, y_pred)
        elif self.model_type == "transformer":
            if not TORCH_AVAILABLE:
                raise RuntimeError("Transformer evaluation requires PyTorch")
            assert torch is not None
            self.model.eval()
            if isinstance(test_dataset, DataLoader):
                loader = test_dataset
            else:
                loader = DataLoader(
                    test_dataset,
                    batch_size=self.config.get("batch_size", 32),
                    shuffle=False,
                )
            all_preds = []
            all_labels = []
            with torch.no_grad():
                for batch in loader:  # type: ignore
                    batch = {k: v.to(self.device) for k, v in batch.items()}
                    outputs = self.model(**batch)
                    logits = outputs.logits
                    preds = torch.argmax(logits, dim=-1)
                    all_preds.extend(preds.cpu().numpy())
                    all_labels.extend(batch["labels"].cpu().numpy())
            metrics = compute_metrics(np.array(all_labels), np.array(all_preds))
        else:
            raise ValueError(f"Unsupported model_type: {self.model_type}")

        if self.mlflow_enabled:
            for k, v in metrics.items():
                mlflow.log_metric(f"test_{k}", v)

        return metrics
