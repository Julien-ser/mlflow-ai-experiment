"""
Preprocessing utilities for text classification.
"""

import re
from typing import Any, Dict, Tuple

import torch
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore

from .tokenizers import TransformerTokenizer


def clean_text(text):
    """Basic text cleaning: lowercase, remove HTML tags, extra whitespace."""
    # Convert to lowercase
    text = text.lower()

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def create_tfidf_features(
    train_texts,
    val_texts=None,
    test_texts=None,
    max_features=5000,
    ngram_range=(1, 2),
    min_df=1,
):
    """
    Create TF-IDF features from text data.

    Args:
        train_texts: Training texts
        val_texts: Validation texts (optional)
        test_texts: Test texts (optional)
        max_features: Maximum number of features
        ngram_range: N-gram range (min_n, max_n)

    Returns:
        Dictionary with features for each split
    """
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        stop_words="english",
        min_df=min_df,
        max_df=0.7,
    )

    # Fit on training data only
    X_train = vectorizer.fit_transform(train_texts)

    result = {
        "vectorizer": vectorizer,
        "X_train": X_train,
        "feature_names": vectorizer.get_feature_names_out(),
    }

    if val_texts is not None:
        X_val = vectorizer.transform(val_texts)
        result["X_val"] = X_val

    if test_texts is not None:
        X_test = vectorizer.transform(test_texts)
        result["X_test"] = X_test

    return result


def preprocess_transformer(
    train_df,
    val_df,
    test_df,
    model_name: str = "bert",
    max_length: int = 512,
    padding: bool = True,
    truncation: bool = True,
) -> Dict[str, Any]:
    """
    Preprocess datasets for transformer models: tokenize text.

    Args:
        train_df: Training DataFrame with 'text' column
        val_df: Validation DataFrame with 'text' column
        test_df: Test DataFrame with 'text' column
        model_name: Transformer model key (bert, roberta, distilbert, etc.)
        max_length: Maximum sequence length
        padding: Whether to pad sequences
        truncation: Whether to truncate sequences

    Returns:
        Dictionary with 'train', 'val', 'test' keys containing tokenized outputs
    """
    # Initialize tokenizer
    tokenizer = TransformerTokenizer(
        model_name=model_name,
        max_length=max_length,
        padding=padding,
        truncation=truncation,
    )

    # Tokenize all splits
    tokenized = tokenizer.tokenize_dataset(
        train_texts=train_df["text"].tolist(),
        val_texts=val_df["text"].tolist(),
        test_texts=test_df["text"].tolist(),
    )

    # Convert BatchEncoding to plain dict and add labels to each split
    for split in ["train", "val", "test"]:
        tokenized[split] = dict(tokenized[split])
        tokenized[split]["labels"] = torch.tensor(
            train_df["label"].values
            if split == "train"
            else val_df["label"].values
            if split == "val"
            else test_df["label"].values
        )

    return {
        "train": tokenized["train"],
        "val": tokenized["val"],
        "test": tokenized["test"],
        "tokenizer": tokenizer,
    }


def preprocess_classical(
    train_df,
    val_df,
    test_df,
    max_features: int = 5000,
    ngram_range: Tuple[int, int] = (1, 2),
) -> Dict[str, Any]:
    """
    Preprocess datasets for classical ML: clean text and create TF-IDF features.

    Args:
        train_df: Training DataFrame with 'text' column
        val_df: Validation DataFrame with 'text' column
        test_df: Test DataFrame with 'text' column
        max_features: Maximum number of TF-IDF features
        ngram_range: N-gram range (min_n, max_n)

    Returns:
        Dictionary with processed data and vectorizer
    """
    # Clean text
    train_df["cleaned_text"] = train_df["text"].apply(clean_text)
    val_df["cleaned_text"] = val_df["text"].apply(clean_text)
    test_df["cleaned_text"] = test_df["text"].apply(clean_text)

    # Create TF-IDF features
    features = create_tfidf_features(
        train_df["cleaned_text"].tolist(),
        val_df["cleaned_text"].tolist(),
        test_df["cleaned_text"].tolist(),
        max_features=max_features,
        ngram_range=ngram_range,
    )

    return {
        "train": (features["X_train"], train_df["label"].values),
        "val": (features["X_val"], val_df["label"].values),
        "test": (features["X_test"], test_df["label"].values),
        "vectorizer": features["vectorizer"],
        "feature_names": features["feature_names"],
    }


def preprocess_dataset(
    train_df,
    val_df,
    test_df,
    mode: str = "classical",
    **kwargs,
) -> Dict[str, Any]:
    """
    Unified preprocessing interface for both classical and transformer models.

    Args:
        train_df: Training DataFrame with 'text' column
        val_df: Validation DataFrame with 'text' column
        test_df: Test DataFrame with 'text' column
        mode: Preprocessing mode - 'classical' or 'transformer'
        **kwargs: Additional arguments passed to the specific preprocessing function
            For classical: max_features, ngram_range
            For transformer: model_name, max_length, padding, truncation

    Returns:
        Dictionary with processed data and metadata (vectorizer or tokenizer)
    """
    if mode == "classical":
        return preprocess_classical(train_df, val_df, test_df, **kwargs)
    elif mode == "transformer":
        return preprocess_transformer(train_df, val_df, test_df, **kwargs)
    else:
        raise ValueError(
            f"Invalid preprocessing mode: {mode}. Use 'classical' or 'transformer'."
        )
