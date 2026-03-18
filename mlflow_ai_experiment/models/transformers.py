"""
Transformer model implementations for text classification with unified interface.

Supports BERT, RoBERTa, DeBERTa, XLNet with custom classification heads.
"""
# mypy: ignore-errors

from typing import List, Optional, Union

import mlflow
import warnings

import numpy as np
import torch

# Suppress torch.jit.script deprecation warning for Python 3.14+
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module=r"torch\.jit\._script",
)

from transformers import (
    AlbertForSequenceClassification,
    AutoTokenizer,
    BertForSequenceClassification,
    DebertaForSequenceClassification,
    DistilBertForSequenceClassification,
    EarlyStoppingCallback,
    ElectraForSequenceClassification,
    GPT2ForSequenceClassification,
    RobertaForSequenceClassification,
    Trainer,
    TrainingArguments,
    XLNetForSequenceClassification,
)

from ..experiment_tracker import set_standard_tags, log_model_artifact

# TensorFlow availability
try:
    import tensorflow as tf  # type: ignore  # noqa: F401  # pyright: ignore[reportMissingImports]

    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


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
        "electra": ElectraForSequenceClassification,
        "albert": AlbertForSequenceClassification,
        "distilbert": DistilBertForSequenceClassification,
        "gpt2": GPT2ForSequenceClassification,
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
        backend: str = "pytorch",
        early_stopping_patience: int = 3,
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
        self.backend = backend
        self.early_stopping_patience = early_stopping_patience
        if self.backend not in ["pytorch", "tensorflow"]:
            raise ValueError(
                f"Unsupported backend: {self.backend}. Choose 'pytorch' or 'tensorflow'."
            )
        self.model = None
        self.tokenizer = None
        self.trainer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _get_model_class(self, model_type: str):
        """Get the appropriate HuggingFace model class based on model type and backend."""
        if self.backend == "pytorch":
            if model_type not in self.MODEL_CLASSES:
                raise ValueError(
                    f"Unknown model type: {model_type}. "
                    f"Supported: {list(self.MODEL_CLASSES.keys())}"
                )
            return self.MODEL_CLASSES[model_type]
        elif self.backend == "tensorflow":
            # Lazy import to avoid top-level dependency
            from transformers import (
                TFAutoModelForSequenceClassification,  # type: ignore
            )

            return TFAutoModelForSequenceClassification
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def _extract_model_type(self, model_name: str) -> str:
        """Extract model type from model name (e.g., 'bert-base-uncased' -> 'bert')."""
        model_name_lower = model_name.lower()

        # Check in order of specificity to avoid false matches
        if "xlnet" in model_name_lower:
            return "xlnet"
        elif "deberta" in model_name_lower:
            return "deberta"
        elif "roberta" in model_name_lower:
            return "roberta"
        elif "albert" in model_name_lower:
            return "albert"
        elif "electra" in model_name_lower:
            return "electra"
        elif "distilbert" in model_name_lower:
            return "distilbert"
        elif "gpt2" in model_name_lower or "gpt-" in model_name_lower:
            return "gpt2"
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

        # Apply custom dropout for PyTorch models only
        if (
            self.backend == "pytorch"
            and self.dropout != self.model.config.hidden_dropout_prob
        ):
            self.model.classifier.dropout.p = self.dropout

        # Move model to device only for PyTorch
        if self.backend == "pytorch":
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
        assert self.tokenizer is not None

        # Determine return tensor format based on backend
        if self.backend == "tensorflow":
            return_tensors = "tf"
        else:
            return_tensors = "pt"
        encoding = self.tokenizer(
            texts,
            padding=padding,
            truncation=truncation,
            max_length=self.max_seq_length,
            return_tensors=return_tensors,
        )

        if labels is not None:
            if self.backend == "tensorflow":
                if TF_AVAILABLE:
                    import tensorflow as tf  # type: ignore

                    encoding["labels"] = tf.constant(labels)
                else:
                    raise ImportError(
                        "TensorFlow is not installed. Please install tensorflow to use the tensorflow backend."
                    )
            else:
                encoding["labels"] = torch.tensor(labels)

        return encoding

    def train(
        self,
        train_dataset,
        eval_dataset=None,
        experiment_name=None,
        training_args=None,
        dataset_version: str = "v1.0",
        preprocessing_config: str = "standard",
    ):
        """
        Train the transformer model with flexible configuration.

        Args:
            train_dataset: Tokenized training dataset
            eval_dataset: Optional tokenized validation dataset
            experiment_name: Optional MLflow experiment name
            training_args: Optional dict of TrainingArguments overrides
            dataset_version: Version of the dataset used
            preprocessing_config: Preprocessing configuration used

        Returns:
            Training results
        """
        if self.model is None:
            self.build_model()

        if training_args is None:
            training_args = {}

        output_dir = f"./output/{self.model_name.replace('/', '_')}"

        # Base arguments
        args = {
            "output_dir": output_dir,
            "num_train_epochs": self.num_train_epochs,
            "per_device_train_batch_size": self.batch_size,
            "per_device_eval_batch_size": self.batch_size * 2,
            "warmup_steps": self.warmup_steps,
            "weight_decay": self.weight_decay,
            "logging_dir": f"{output_dir}/logs",
            "logging_steps": 100,
            "evaluation_strategy": "steps" if eval_dataset else "no",
            "eval_steps": 500 if eval_dataset else None,
            "save_strategy": "steps",
            "save_steps": 500 if eval_dataset else "epoch",
            "load_best_model_at_end": True if eval_dataset else False,
            "metric_for_best_model": "eval_accuracy" if eval_dataset else None,
            "greater_is_better": True if eval_dataset else None,
            "report_to": "none",
            "push_to_hub": False,
        }
        args.update(training_args)

        # Select backend-specific trainer classes
        if self.backend == "pytorch":
            TrainerClass = Trainer
            ArgsClass = TrainingArguments
        elif self.backend == "tensorflow":
            if not TF_AVAILABLE:
                raise ImportError(
                    "TensorFlow is not installed. Please install tensorflow to use the tensorflow backend."
                )
            # Handle mixed precision: check for fp16 flag, set policy, and remove from args
            if args.pop("fp16", False):
                if TF_AVAILABLE:
                    import tensorflow as tf  # type: ignore

                    tf.keras.mixed_precision.set_global_policy("mixed_float16")
                else:
                    raise ImportError(
                        "TensorFlow is not installed. Please install tensorflow to use the tensorflow backend."
                    )
            from transformers import TFTrainer  # type: ignore
            from transformers import TFTrainingArguments  # type: ignore

            TrainerClass = TFTrainer
            ArgsClass = TFTrainingArguments
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

        # Extract early_stopping_patience if provided, default to model's setting
        early_stopping_patience = args.pop(
            "early_stopping_patience", self.early_stopping_patience
        )

        # Create training arguments object
        training_args_obj = ArgsClass(**args)

        # Define compute_metrics function
        def compute_metrics(eval_pred):
            predictions, labels = eval_pred
            predictions = torch.tensor(predictions)
            labels = torch.tensor(labels)

            if self.num_labels > 1:
                predictions = torch.argmax(predictions, dim=-1)

            accuracy = (predictions == labels).float().mean()
            metrics = {"accuracy": accuracy.item()}

            if self.num_labels == 2:
                from sklearn.metrics import f1_score

                f1 = f1_score(labels.numpy(), predictions.numpy(), average="binary")
                metrics["f1"] = f1

            return metrics

        # Prepare callbacks
        callbacks = []
        if eval_dataset:
            callbacks.append(
                EarlyStoppingCallback(early_stopping_patience=early_stopping_patience)
            )

        # Create trainer
        self.trainer = TrainerClass(
            model=self.model,
            args=training_args_obj,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            compute_metrics=compute_metrics if eval_dataset else None,
            callbacks=callbacks,
        )

        # Train
        train_result = self.trainer.train()

        # Log to MLflow if experiment name provided
        if experiment_name:
            self.log_to_mlflow(
                experiment_name,
                train_result=train_result,
                dataset_version=dataset_version,
                preprocessing_config=preprocessing_config,
            )

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
        self,
        experiment_name: str,
        run_name: Optional[str] = None,
        train_result=None,
        dataset_version: str = "v1.0",
        preprocessing_config: str = "standard",
    ):
        """
        Log model, parameters, and metrics to MLflow.

        Args:
            experiment_name: MLflow experiment name
            run_name: Optional run name
            train_result: Optional training results to log as metrics
            dataset_version: Version of the dataset used
            preprocessing_config: Preprocessing configuration used

        Returns:
            MLflow run ID
        """
        if run_name is None:
            run_name = f"{self._extract_model_type(self.model_name)}_classifier"

        mlflow.set_experiment(experiment_name)

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

            # Log model using the central utility
            if self.model is not None and self.tokenizer is not None:
                model_type = self._extract_model_type(self.model_name)
                log_model_artifact(
                    model=self.model,
                    model_type=model_type,
                    framework="transformers",
                    artifact_path="model",
                    tokenizer=self.tokenizer,
                    task="text-classification",
                    input_example="Sample text for classification",
                )

            # Set standardized tags
            set_standard_tags(
                model_type=self._extract_model_type(self.model_name),
                dataset_version=dataset_version,
                preprocessing_config=preprocessing_config,
                framework="transformers",
                task="text_classification",
            )

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


class ELECTRAModel(TransformerModel):
    """ELECTRA model wrapper."""

    def __init__(self, **kwargs):
        kwargs.setdefault("model_name", "google/electra-base-discriminator")
        super().__init__(**kwargs)


class ALBERTModel(TransformerModel):
    """ALBERT model wrapper."""

    def __init__(self, **kwargs):
        kwargs.setdefault("model_name", "albert-base-v2")
        super().__init__(**kwargs)


class DistilBERTModel(TransformerModel):
    """DistilBERT model wrapper."""

    def __init__(self, **kwargs):
        kwargs.setdefault("model_name", "distilbert-base-uncased")
        super().__init__(**kwargs)


class GPT2Model(TransformerModel):
    """GPT-2 model wrapper."""

    def __init__(self, **kwargs):
        kwargs.setdefault("model_name", "gpt2")
        super().__init__(**kwargs)


def create_transformer_model(model_type: str, **kwargs) -> TransformerModel:
    """
    Factory function to create transformer model instances.

    Args:
        model_type: Type of transformer model ('bert', 'roberta', 'deberta', 'xlnet',
                    'electra', 'albert', 'distilbert', 'gpt2')
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
        "electra": ELECTRAModel,
        "albert": ALBERTModel,
        "distilbert": DistilBERTModel,
        "gpt2": GPT2Model,
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
