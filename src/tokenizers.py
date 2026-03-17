"""
Tokenization utilities for transformer models.
"""

from transformers import AutoTokenizer
from typing import Dict, List, Optional
import torch


class TransformerTokenizer:
    """Wrapper for HuggingFace transformer tokenizers with consistent interface."""

    MODEL_NAMES = {
        "bert": "bert-base-uncased",
        "roberta": "roberta-base",
        "distilbert": "distilbert-base-uncased",
        "electra": "google/electra-base-discriminator",
        "albert": "albert-base-v2",
        "deberta": "microsoft/deberta-base",
        "xlnet": "xlnet-base-cased",
    }

    def __init__(
        self,
        model_name: str,
        max_length: int = 512,
        padding: bool = True,
        truncation: bool = True,
        return_tensors: str = "pt",
    ):
        """
        Initialize tokenizer for a specific transformer model.

        Args:
            model_name: Model key (bert, roberta, distilbert, etc.) or full HF model name
            max_length: Maximum sequence length
            padding: Whether to pad sequences
            truncation: Whether to truncate sequences
            return_tensors: Tensor format ('pt' for PyTorch, 'tf' for TensorFlow)
        """
        if model_name in self.MODEL_NAMES:
            model_id = self.MODEL_NAMES[model_name]
        else:
            model_id = model_name

        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.max_length = max_length
        self.padding = padding
        self.truncation = truncation
        self.return_tensors = return_tensors
        self.model_name = model_name

    def tokenize(
        self,
        texts: List[str],
        padding: Optional[bool] = None,
        truncation: Optional[bool] = None,
        max_length: Optional[int] = None,
        return_tensors: Optional[str] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Tokenize a list of texts.

        Args:
            texts: List of text strings to tokenize
            padding: Override default padding setting
            truncation: Override default truncation setting
            max_length: Override default max length
            return_tensors: Override default tensor format

        Returns:
            Dictionary with input_ids, attention_mask, and token_type_ids (if applicable)
        """
        encoded = self.tokenizer(
            texts,
            padding=padding if padding is not None else self.padding,
            truncation=truncation if truncation is not None else self.truncation,
            max_length=max_length or self.max_length,
            return_tensors=return_tensors or self.return_tensors,
        )

        return encoded

    def tokenize_dataset(
        self,
        train_texts: List[str],
        val_texts: List[str],
        test_texts: List[str],
        **kwargs,
    ) -> Dict[str, Dict[str, torch.Tensor]]:
        """
        Tokenize train/validation/test splits.

        Args:
            train_texts: Training texts
            val_texts: Validation texts
            test_texts: Test texts
            **kwargs: Additional arguments passed to tokenize()

        Returns:
            Dictionary with 'train', 'val', 'test' keys, each containing tokenized outputs
        """
        return {
            "train": self.tokenize(train_texts, **kwargs),
            "val": self.tokenize(val_texts, **kwargs),
            "test": self.tokenize(test_texts, **kwargs),
        }

    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs back to text."""
        result = self.tokenizer.decode(token_ids)
        # Ensure result is a string (tokenizer.decode may return list for batched inputs)
        return result if isinstance(result, str) else result[0] if result else ""

    def save(self, path: str) -> None:
        """Save tokenizer to disk."""
        self.tokenizer.save_pretrained(path)

    @classmethod
    def get_supported_models(cls) -> List[str]:
        """Get list of supported model keys."""
        return list(cls.MODEL_NAMES.keys())
