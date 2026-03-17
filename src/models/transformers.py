"""
Transformer model implementations for text classification with unified interface.

Supports BERT, RoBERTa, DeBERTa, XLNet with custom classification heads.
"""

import torch
import torch.nn as nn
from transformers import (
    AutoModel,
    AutoTokenizer,
    BertForSequenceClassification,
    RobertaForSequenceClassification,
    DebertaForSequenceClassification,
    XLNetForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)
import numpy as np
import mlflow
import mlflow.transformers
from typing import Dict, Any, Optional, Union, List


class TransformerModel:
    """
    Unified wrapper for HuggingFace transformer models with custom classification head.

    Provides a consistent interface for training, prediction, and MLflow logging.
    """

    # Mapping of model types to their HuggingFace classes
    MODEL_CLASSES = {
        "bert": BertForSequenceClassification,
        "roberta": RobertaForSequenceClassification,
        "deberta": DebertaForSequenceClassification,
        "xlnet": XLNetForSequenceClassification,
    }

    def __init__(
        self,
        model_name: str,
        num_labels: int = 2,
        dropout: float = 0.1,
        max_seq_length: int = 512,
        learning_rate: float = 2e-5,
        batch_size: int = 16,
        num_train_epochs: int = 3,
        weight_decay: float = 0.01,
        warmup_steps: int = 500,
        **kwargs,
    ):
        """
        Initialize transformer model.

        Args:
            model_name: HuggingFace model identifier (e.g., 'bert-base-uncased')
            num_labels: Number of output classes
            dropout: Dropout rate for classification head
            max_seq_length: Maximum sequence length for tokenization
            learning_rate: Learning rate for training
            batch_size: Batch size for training/evaluation
            num_train_epochs: Number of training epochs
            weight_decay: Weight decay for optimizer
            warmup_steps: Number of warmup steps
            **kwargs: Additional model-specific arguments
        """
        self.model_name = model_name
        self.num_labels = num_labels
        self.dropout = dropout
        self.max_seq_length = max_seq_length
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.num_train_epochs = num_train_epochs
        self.weight_decay = weight_decay
        self.warmup_steps = warmup_steps
        self.model = None
        self.tokenizer = None
        self.trainer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _get_model_class(self, model_type: str):
        """Get the appropriate HuggingFace model class based on model type."""
        if model_type not in self.MODEL_CLASSES:
            raise ValueError(
                f"Unknown model type: {model_type}. "
                f"Supported: {list(self.MODEL_CLASSES.keys())}"
            )
        return self.MODEL_CLASSES[model_type]

    def _extract_model_type(self, model_name: str) -> str:
        """Extract model type from model name (e.g., 'bert-base-uncased' -> 'bert')."""
        model_name_lower = model_name.lower()

        # Check in order of specificity to avoid false matches
        # (some names like 'roberta' contain 'bert')
        if "xlnet" in model_name_lower:
            return "xlnet"
        elif "deberta" in model_name_lower:
            return "deberta"
        elif "roberta" in model_name_lower:
            return "roberta"
        elif "bert" in model_name_lower:
            return "bert"

        raise ValueError(f"Could not determine model type from: {model_name}")

    def load_tokenizer(self):
        """Load and initialize tokenizer."""
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=True)
        return self.tokenizer

    def build_model(self):
        """Build the transformer model with classification head."""
        model_type = self._extract_model_type(self.model_name)
        model_class = self._get_model_class(model_type)

        # Load model with number of labels
        self.model = model_class.from_pretrained(
            self.model_name,
            num_labels=self.num_labels,
            problem_type="single_label_classification",
        )

        # Apply custom dropout if specified
        if self.dropout != self.model.config.hidden_dropout_prob:
            self.model.classifier.dropout.p = self.dropout

        self.model.to(self.device)
        return self.model

    def tokenize_data(self, texts, labels=None, padding=True, truncation=True):
        """
        Tokenize input texts.

        Args:
            texts: List of text strings
            labels: Optional labels for supervised learning
            padding: Whether to pad sequences
            truncation: Whether to truncate sequences

        Returns:
            Tokenized dataset
        """
        if self.tokenizer is None:
            self.load_tokenizer()

        encoding = self.tokenizer(
            texts,
            padding=padding,
            truncation=truncation,
            max_length=self.max_seq_length,
            return_tensors="pt" if self.device.type == "cpu" else None,
        )

        if labels is not None:
            encoding["labels"] = torch.tensor(labels)

        return encoding

    def train(self, train_dataset, eval_dataset=None, experiment_name=None):
        """
        Train the transformer model.

        Args:
            train_dataset: Tokenized training dataset (dict with input_ids, attention_mask, labels)
            eval_dataset: Optional tokenized validation dataset
            experiment_name: Optional MLflow experiment name

        Returns:
            Training results
        """
        if self.model is None:
            self.build_model()

        # Prepare training arguments
        output_dir = f"./output/{self.model_name.replace('/', '_')}"

        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=self.num_train_epochs,
            per_device_train_batch_size=self.batch_size,
            per_device_eval_batch_size=self.batch_size * 2,
            warmup_steps=self.warmup_steps,
            weight_decay=self.weight_decay,
            logging_dir=f"{output_dir}/logs",
            logging_steps=100,
            evaluation_strategy="steps" if eval_dataset else "no",
            eval_steps=500 if eval_dataset else None,
            save_strategy="steps",
            save_steps=500 if eval_dataset else "epoch",
            load_best_model_at_end=True if eval_dataset else False,
            metric_for_best_model="eval_accuracy" if eval_dataset else None,
            greater_is_better=True if eval_dataset else None,
            report_to="none",  # Disable wandb/tensorboard by default
            push_to_hub=False,
        )

        # Define compute_metrics function if eval_dataset provided
        def compute_metrics(eval_pred):
            """Compute metrics for evaluation."""
            predictions, labels = eval_pred
            predictions = torch.tensor(predictions)
            labels = torch.tensor(labels)

            if self.num_labels > 1:
                predictions = torch.argmax(predictions, dim=-1)

            accuracy = (predictions == labels).float().mean()

            metrics = {"accuracy": accuracy.item()}

            # Add F1 score for binary classification
            if self.num_labels == 2:
                from sklearn.metrics import f1_score

                f1 = f1_score(labels.numpy(), predictions.numpy(), average="binary")
                metrics["f1"] = f1

            return metrics

        # Create trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            compute_metrics=compute_metrics if eval_dataset else None,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            if eval_dataset
            else [],
        )

        # Train the model
        train_result = self.trainer.train()

        # Log to MLflow if experiment name provided
        if experiment_name:
            self.log_to_mlflow(experiment_name, train_result=train_result)

        return train_result

    def predict(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Make predictions on input texts.

        Args:
            texts: Single text or list of texts

        Returns:
            Predicted class labels
        """
        if self.model is None:
            raise ValueError(
                "Model not trained. Must call train() or load_model() first."
            )

        # Tokenize input
        encoding = self.tokenize_data(texts if isinstance(texts, list) else [texts])
        dataset = torch.utils.data.TensorDataset(
            encoding["input_ids"], encoding["attention_mask"]
        )

        # Get predictions
        self.model.eval()
        predictions = []

        with torch.no_grad():
            dataloader = torch.utils.data.DataLoader(
                dataset, batch_size=self.batch_size
            )
            for batch in dataloader:
                input_ids, attention_mask = [b.to(self.device) for b in batch]
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                preds = torch.argmax(logits, dim=-1).cpu().numpy()
                predictions.extend(preds)

        return np.array(predictions)

    def predict_proba(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Get prediction probabilities.

        Args:
            texts: Single text or list of texts

        Returns:
            Probability scores for each class
        """
        if self.model is None:
            raise ValueError(
                "Model not trained. Must call train() or load_model() first."
            )

        # Tokenize input
        encoding = self.tokenize_data(texts if isinstance(texts, list) else [texts])
        dataset = torch.utils.data.TensorDataset(
            encoding["input_ids"], encoding["attention_mask"]
        )

        # Get probabilities
        self.model.eval()
        probabilities = []

        with torch.no_grad():
            dataloader = torch.utils.data.DataLoader(
                dataset, batch_size=self.batch_size
            )
            for batch in dataloader:
                input_ids, attention_mask = [b.to(self.device) for b in batch]
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1).cpu().numpy()
                probabilities.extend(probs)

        return np.array(probabilities)

    def save_model(self, path: str):
        """Save model and tokenizer to disk."""
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model or tokenizer not initialized.")

        # Create directory if not exists
        import os

        os.makedirs(path, exist_ok=True)

        # Save model and tokenizer
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)

        # Save configuration
        config = {
            "model_name": self.model_name,
            "num_labels": self.num_labels,
            "dropout": self.dropout,
            "max_seq_length": self.max_seq_length,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "num_train_epochs": self.num_train_epochs,
            "weight_decay": self.weight_decay,
            "warmup_steps": self.warmup_steps,
        }

        import json

        with open(f"{path}/wrapper_config.json", "w") as f:
            json.dump(config, f, indent=2)

    def load_model(self, path: str):
        """Load model and tokenizer from disk."""
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(path)

        # Extract model type from saved config
        import json

        with open(f"{path}/wrapper_config.json", "r") as f:
            config = json.load(f)

        self.model_name = config["model_name"]
        self.num_labels = config["num_labels"]
        self.dropout = config["dropout"]
        self.max_seq_length = config["max_seq_length"]
        self.learning_rate = config["learning_rate"]
        self.batch_size = config["batch_size"]
        self.num_train_epochs = config["num_train_epochs"]
        self.weight_decay = config["weight_decay"]
        self.warmup_steps = config["warmup_steps"]

        # Rebuild model with saved config
        self.build_model()

    def log_to_mlflow(
        self, experiment_name: str, run_name: str = None, train_result=None
    ):
        """
        Log model, parameters, and metrics to MLflow.

        Args:
            experiment_name: MLflow experiment name
            run_name: Optional run name
            train_result: Optional training results to log as metrics

        Returns:
            MLflow run ID
        """
        if run_name is None:
            run_name = f"{self._extract_model_type(self.model_name)}_classifier"

        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            params = {
                "model_name": self.model_name,
                "model_type": self._extract_model_type(self.model_name),
                "num_labels": self.num_labels,
                "dropout": self.dropout,
                "max_seq_length": self.max_seq_length,
                "learning_rate": self.learning_rate,
                "batch_size": self.batch_size,
                "num_train_epochs": self.num_train_epochs,
                "weight_decay": self.weight_decay,
                "warmup_steps": self.warmup_steps,
                "device": self.device.type,
            }

            for key, value in params.items():
                mlflow.log_param(key, value)

            # Log training metrics if provided
            if train_result:
                mlflow.log_metric("train_loss", train_result.training_loss)
                mlflow.log_metric("train_steps", train_result.global_step)

                if hasattr(train_result, "metrics") and train_result.metrics:
                    for key, value in train_result.metrics.items():
                        mlflow.log_metric(f"train_{key}", value)

            # Log model using transformers flavor
            if self.model is not None and self.tokenizer is not None:
                # Create a simple pipeline for inference
                from transformers import pipeline

                classifier = pipeline(
                    "text-classification",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=0 if self.device.type == "cuda" else -1,
                )

                mlflow.transformers.log_model(
                    transformers_model={
                        "model": self.model,
                        "tokenizer": self.tokenizer,
                    },
                    artifact_path="model",
                    task="text-classification",
                    input_example="Sample text for classification",
                    signature=mlflow.models.signature.infer_signature(
                        ["input text"], [{"label": "positive", "score": 0.9}]
                    ),
                )

            # Set tags
            mlflow.set_tag("framework", "transformers")
            mlflow.set_tag("model_type", self._extract_model_type(self.model_name))
            mlflow.set_tag("task", "text_classification")

            return run.info.run_id


class BERTModel(TransformerModel):
    """BERT model wrapper."""

    def __init__(self, **kwargs):
        kwargs.setdefault("model_name", "bert-base-uncased")
        super().__init__(**kwargs)


class RoBERTaModel(TransformerModel):
    """RoBERTa model wrapper."""

    def __init__(self, **kwargs):
        kwargs.setdefault("model_name", "roberta-base")
        super().__init__(**kwargs)


class DeBERTaModel(TransformerModel):
    """DeBERTa model wrapper."""

    def __init__(self, **kwargs):
        kwargs.setdefault("model_name", "microsoft/deberta-v3-base")
        super().__init__(**kwargs)


class XLNetModel(TransformerModel):
    """XLNet model wrapper."""

    def __init__(self, **kwargs):
        kwargs.setdefault("model_name", "xlnet-base-cased")
        super().__init__(**kwargs)


def create_transformer_model(model_type: str, **kwargs) -> TransformerModel:
    """
    Factory function to create transformer model instances.

    Args:
        model_type: Type of transformer model ('bert', 'roberta', 'deberta', 'xlnet')
        **kwargs: Additional configuration parameters

    Returns:
        Instantiated transformer model wrapper

    Example:
        >>> model = create_transformer_model("bert", num_labels=2, dropout=0.2)
        >>> model.load_tokenizer()
        >>> model.build_model()
    """
    model_classes = {
        "bert": BERTModel,
        "roberta": RoBERTaModel,
        "deberta": DeBERTaModel,
        "xlnet": XLNetModel,
    }

    if model_type not in model_classes:
        raise ValueError(
            f"Unknown transformer model: {model_type}. "
            f"Supported: {list(model_classes.keys())}"
        )

    return model_classes[model_type](**kwargs)


def create_transformer_model_from_name(model_name: str, **kwargs) -> TransformerModel:
    """
    Create transformer model from full model name.

    Automatically detects model type from name and creates appropriate wrapper.

    Args:
        model_name: Full HuggingFace model identifier
        **kwargs: Additional configuration parameters

    Returns:
        Instantiated transformer model wrapper

    Example:
        >>> model = create_transformer_model_from_name("distilbert-base-uncased", num_labels=2)
    """
    base = TransformerModel(model_name=model_name, **kwargs)
    model_type = base._extract_model_type(model_name)
    return create_transformer_model(model_type, model_name=model_name, **kwargs)
