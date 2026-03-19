"""
Model export utilities for standardized packaging and deployment formats.

This module provides functions to export trained models to various formats:
- PyTorch models: .pt, TorchScript, ONNX
- Classical ML models: .pkl (joblib)
- Generic: Copy artifacts with standardized structure

Supports deployment to:
- Local inference
- ONNX Runtime
- TensorFlow Serving
- TorchServe
- Custom serving stacks
"""

import os
import shutil
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import joblib
import mlflow
from mlflow.tracking import MlflowClient
from mlflow import artifacts
import numpy as np
import torch
from torch.jit import ScriptModule


class ModelExporter:
    """Unified interface for exporting models to various deployment formats."""

    SUPPORTED_FORMATS = ["pytorch", "torchscript", "onnx", "pickle", "mlflow"]

    def __init__(self, export_dir: str = "models/best_models"):
        """
        Initialize ModelExporter.

        Args:
            export_dir: Base directory for exported models
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_model(
        self,
        model: Any,
        model_name: str,
        model_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        format: str = "pytorch",
        tokenizer: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
        export_path: Optional[str] = None,
    ) -> str:
        """
        Export a model to the specified format with standardized structure.

        Args:
            model: The trained model object
            model_name: Name of the model (e.g., "deberta-base", "xgboost")
            model_type: Type category ("transformer", "classical")
            metadata: Additional metadata to save
            format: Export format (pytorch, torchscript, onnx, pickle, mlflow)
            tokenizer: Tokenizer object (required for transformers)
            config: Model configuration
            export_path: Custom export path (overrides default)

        Returns:
            Path to the exported model directory
        """
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {format}. Choose from {self.SUPPORTED_FORMATS}"
            )

        # Create export directory
        if export_path:
            model_dir = Path(export_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_dir = self.export_dir / f"{model_name}_{model_type}" / timestamp

        model_dir.mkdir(parents=True, exist_ok=True)

        # Create standard metadata
        full_metadata = {
            "model_name": model_name,
            "model_type": model_type,
            "export_format": format,
            "export_timestamp": datetime.now().isoformat(),
            "mlflow_run_id": self._get_current_run_id(),
            **(metadata or {}),
        }

        # Export based on format
        if model_type == "transformer":
            self._export_transformer(
                model, model_dir, format, tokenizer, config, full_metadata
            )
        elif model_type == "classical":
            self._export_classical(model, model_dir, format, config, full_metadata)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Save metadata as JSON
        with open(model_dir / "metadata.json", "w") as f:
            json.dump(full_metadata, f, indent=2, default=str)

        # Save inference example
        self._save_inference_example(model_dir, model, model_type)

        return str(model_dir)

    def _export_transformer(
        self,
        model: Any,
        model_dir: Path,
        format: str,
        tokenizer: Optional[Any],
        config: Optional[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> None:
        """Export transformer model."""
        if format == "pytorch":
            # Save PyTorch state dict
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "config": config or model.config.to_dict()
                    if hasattr(model, "config")
                    else {},
                },
                model_dir / "model.pt",
            )

        elif format == "torchscript":
            # Trace and save TorchScript
            model.eval()
            # Create dummy input for tracing
            if hasattr(model, "config"):
                seq_len = getattr(model.config, "max_position_embeddings", 512)
            else:
                seq_len = 512

            dummy_input = torch.zeros(1, seq_len, dtype=torch.long)
            with torch.no_grad():
                traced_result = torch.jit.trace(model, dummy_input)
                # Handle both old and new torch.jit.trace return formats
                if isinstance(traced_result, tuple):
                    traced_model = traced_result[0]
                else:
                    traced_model = traced_result
                traced_model.save(str(model_dir / "model.pt"))

        elif format == "onnx":
            # Export to ONNX
            model.eval()
            if hasattr(model, "config"):
                seq_len = getattr(model.config, "max_position_embeddings", 512)
            else:
                seq_len = 512

            # Create dummy inputs as tuple
            input_ids = torch.zeros(1, seq_len, dtype=torch.long)
            attention_mask = torch.ones(1, seq_len, dtype=torch.long)

            # Export - must call model with tuple of inputs or use appropriate wrapper
            class ModelWrapper(torch.nn.Module):
                def __init__(self, model):
                    super().__init__()
                    self.model = model

                def forward(self, input_ids, attention_mask):
                    outputs = self.model(
                        input_ids=input_ids, attention_mask=attention_mask
                    )
                    return outputs.logits

            wrapped_model = ModelWrapper(model)

            torch.onnx.export(
                wrapped_model,
                (input_ids, attention_mask),
                str(model_dir / "model.onnx"),
                input_names=["input_ids", "attention_mask"],
                output_names=["logits"],
                dynamic_axes={
                    "input_ids": {0: "batch_size", 1: "sequence"},
                    "attention_mask": {0: "batch_size", 1: "sequence"},
                    "logits": {0: "batch_size"},
                },
                opset_version=14,
            )

        # Save tokenizer if provided
        if tokenizer is not None:
            tokenizer.save_pretrained(str(model_dir / "tokenizer"))

        # Save config separately
        if config and format != "pytorch":
            with open(model_dir / "config.json", "w") as f:
                json.dump(config, f, indent=2)

    def _export_classical(
        self,
        model: Any,
        model_dir: Path,
        format: str,
        config: Optional[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> None:
        """Export classical ML model."""
        if format == "pickle":
            joblib.dump(model, model_dir / "model.pkl")
        else:
            # For classical models, pickle is the standard
            joblib.dump(model, model_dir / "model.pkl")

    def _get_current_run_id(self) -> str:
        """Get current MLFlow run ID if available."""
        try:
            current_run = mlflow.active_run()
            if current_run:
                return current_run.info.run_id
        except:
            pass
        return "unknown"

    def _save_inference_example(
        self, model_dir: Path, model: Any, model_type: str
    ) -> None:
        """Save example inference code."""
        if model_type == "transformer":
            example = '''#!/usr/bin/env python3
"""
Example inference script for the exported model.
"""

import torch
from transformers import AutoTokenizer

# Load model and tokenizer
model_path = "{}"  # model directory
tokenizer_path = model_path + "/tokenizer"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model state dict
checkpoint = torch.load(model_path + "/model.pt", map_location=device)
# Reconstruct model from config and state dict
# (Implementation depends on specific model architecture)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

def predict(text: str) -> dict:
    """Run inference on a single text."""
    inputs = tokenizer(
        text,
        truncation=True,
        padding=True,
        max_length=512,
        return_tensors="pt"
    ).to(device)
    
    # Get predictions
    # model.eval()
    # with torch.no_grad():
    #     outputs = model(**inputs)
    #     probs = torch.softmax(outputs.logits, dim=-1)
    #     pred = torch.argmax(probs, dim=-1)
    
    return {
        "prediction": 0,  # placeholder
        "confidence": 0.0,  # placeholder
        "logits": []  # placeholder
    }

if __name__ == "__main__":
    sample_text = "This movie was fantastic! I loved every minute of it."
    result = predict(sample_text)
    print(f"Prediction: {result}")
'''
        else:
            example = '''#!/usr/bin/env python3
"""
Example inference script for the exported model.
"""

import joblib
import pandas as pd
import numpy as np

# Load model
model_path = "{}"

model = joblib.load(model_path + "/model.pkl")

def predict(features: np.ndarray) -> dict:
    """Run inference on feature vector."""
    # prediction = model.predict(features.reshape(1, -1))[0]
    # proba = model.predict_proba(features.reshape(1, -1))[0]
    
    return {
        "prediction": 0,  # placeholder
        "confidence": 0.0,  # placeholder
        "probabilities": []  # placeholder
    }

if __name__ == "__main__":
    # Example usage
    print("Model loaded. Implement feature extraction for your use case.")
'''

        with open(model_dir / "inference_example.py", "w") as f:
            f.write(example.format(str(model_dir)))

    @staticmethod
    def copy_from_mlflow(
        run_id: str,
        model_name: str,
        model_type: str,
        destination: str,
        mlflow_tracking_uri: Optional[str] = None,
    ) -> str:
        """
        Copy a trained model from MLFlow to the best_models directory.

        Args:
            run_id: MLFlow run ID containing the model
            model_name: Name to give the exported model
            model_type: Type category ("transformer" or "classical")
            destination: Export directory
            mlflow_tracking_uri: MLFlow tracking URI (if not default)

        Returns:
            Path to the exported model
        """
        if mlflow_tracking_uri:
            mlflow.set_tracking_uri(mlflow_tracking_uri)

        # Get the run
        run = mlflow.get_run(run_id)

        # Determine model flavor
        run_artifacts = mlflow.tracking.MlflowClient().list_artifacts(run_id)
        model_artifact = None
        for artifact in run_artifacts:
            if artifact.is_dir and artifact.path.startswith("model"):
                model_artifact = artifact.path
                break

        if not model_artifact:
            raise ValueError(f"No model artifact found in run {run_id}")

        # Download artifact
        local_path = mlflow.artifacts.download_artifacts(
            run_id=run_id, artifact_path=model_artifact
        )

        # Copy to destination with standardized structure
        exporter = ModelExporter(export_dir=destination)

        # Determine format based on files present
        local_path_obj = Path(local_path)
        files = [f.name for f in local_path_obj.iterdir()]

        if "model.onnx" in files:
            format = "onnx"
        elif "model.pt" in files:
            format = "pytorch"
        else:
            format = "pickle"

        # Create export path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Path(destination) / f"{model_name}_{model_type}" / timestamp
        export_path.mkdir(parents=True, exist_ok=True)

        # Copy all artifacts
        for file in local_path_obj.iterdir():
            if file.is_file():
                shutil.copy2(file, export_path / file.name)

        # Create metadata
        metadata = {
            "model_name": model_name,
            "model_type": model_type,
            "mlflow_run_id": run_id,
            "original_experiment": run.data.tags.get("mlflow.runName", "unknown"),
            "export_timestamp": datetime.now().isoformat(),
            "metrics": {k: v for k, v in run.data.metrics.items()},
            "params": {k: v for k, v in run.data.params.items()},
        }

        with open(export_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return str(export_path)


def export_best_model_from_run(
    run_id: str,
    model_name: str,
    model_type: str,
    destination: str = "models/best_models",
    formats: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Export a model from an MLFlow run to the best_models directory.

    Args:
        run_id: MLFlow run ID
        model_name: Name for the model
        model_type: Type of model
        destination: Destination directory
        formats: List of formats to export (default: ["pytorch", "onnx"] for transformers)

    Returns:
        Dictionary mapping format to export path
    """
    default_formats = {"transformer": ["pytorch", "onnx"], "classical": ["pickle"]}
    formats = formats or default_formats.get(model_type, ["pickle"])

    exporter = ModelExporter(export_dir=destination)

    # For MLFlow export, we copy the artifact
    export_path = ModelExporter.copy_from_mlflow(
        run_id=run_id,
        model_name=model_name,
        model_type=model_type,
        destination=destination,
    )

    return {"copied": export_path}


def create_model_manifest(
    models_dir: str = "models/best_models",
    output_file: str = "models/best_models/manifest.json",
) -> Dict[str, Any]:
    """
    Create a manifest file for all exported models.

    Args:
        models_dir: Directory containing exported models
        output_file: Path to save the manifest

    Returns:
        Manifest dictionary
    """
    models_path = Path(models_dir)
    manifest = {"generated_at": datetime.now().isoformat(), "models": {}}

    if not models_path.exists():
        return manifest

    # Scan all model subdirectories
    for model_family_dir in models_path.iterdir():
        if model_family_dir.is_dir():
            family_name = model_family_dir.name
            manifest["models"][family_name] = {}

            for model_version_dir in model_family_dir.iterdir():
                if model_version_dir.is_dir():
                    version_name = model_version_dir.name
                    metadata_file = model_version_dir / "metadata.json"

                    if metadata_file.exists():
                        with open(metadata_file) as f:
                            metadata = json.load(f)

                        manifest["models"][family_name][version_name] = metadata

    # Save manifest
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def verify_model_artifact(model_path: str) -> Dict[str, Any]:
    """
    Verify that a model artifact is complete and valid.

    Args:
        model_path: Path to the model directory

    Returns:
        Verification results
    """
    model_dir = Path(model_path)
    verification = {
        "path": str(model_dir),
        "exists": model_dir.exists(),
        "has_metadata": (model_dir / "metadata.json").exists(),
        "has_model_file": False,
        "has_tokenizer": (model_dir / "tokenizer").exists()
        if (model_dir / "tokenizer").exists()
        else False,
        "has_inference_example": (model_dir / "inference_example.py").exists(),
        "file_sizes": {},
        "is_valid": False,
    }

    if not model_dir.exists():
        return verification

    # Check for model files
    model_files = ["model.pt", "model.pkl", "model.onnx", "config.json"]
    for file in model_files:
        file_path = model_dir / file
        if file_path.exists():
            verification["has_model_file"] = True
            verification["file_sizes"][file] = file_path.stat().st_size

    # Overall validity
    verification["is_valid"] = (
        verification["has_metadata"] and verification["has_model_file"]
    )

    return verification
