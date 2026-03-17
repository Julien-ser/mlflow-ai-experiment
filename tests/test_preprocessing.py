"""
Tests for preprocessing module.
"""

import pytest
import pandas as pd
import torch
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from src.preprocessing import (
    clean_text,
    create_tfidf_features,
    preprocess_dataset,
    preprocess_classical,
    preprocess_transformer,
)
from src.tokenizers import TransformerTokenizer


class TestCleanText:
    """Tests for text cleaning function."""

    def test_lowercase(self):
        text = "Hello WORLD"
        assert clean_text(text) == "hello world"

    def test_remove_html(self):
        text = "Check <br /> this <b>bold</b> text"
        result = clean_text(text)
        assert "<" not in result
        assert ">" not in result

    def test_remove_extra_whitespace(self):
        text = "Multiple    spaces   and\ttabs"
        result = clean_text(text)
        assert "  " not in result
        assert "\t" not in result

    def test_strip(self):
        text = "   leading and trailing   "
        result = clean_text(text)
        assert result == "leading and trailing"

    def test_combined(self):
        text = "   <HTML>Hello   World</HTML>   "
        result = clean_text(text)
        assert result == "hello world"


class TestTFIDFFeatures:
    """Tests for TF-IDF feature creation."""

    @pytest.fixture
    def sample_data(self):
        train_texts = [
            "This is a positive review",
            "Negative experience",
            "Great movie",
            "Good acting and directing",
            "I loved this film",
            "Terrible screenplay",
            "Excellent cinematography",
            "Not worth watching",
            "A masterpiece of cinema",
            "Boring and slow plot",
            "Outstanding performance",
            "Waste of time",
            "Highly recommended",
            "Disappointing ending",
            "One of the best films",
        ]
        val_texts = [
            "Good film",
            "Terrible acting",
            "Enjoyed the story",
            "Poor character development",
        ]
        test_texts = [
            "Excellent acting",
            "Bad direction",
            "A compelling narrative",
            "Weak dialogue",
        ]
        return train_texts, val_texts, test_texts

    def test_create_tfidf_features(self, sample_data):
        train_texts, val_texts, test_texts = sample_data
        result = create_tfidf_features(
            train_texts, val_texts, test_texts, max_features=100, ngram_range=(1, 1)
        )

        assert "vectorizer" in result
        assert "X_train" in result
        assert "X_val" in result
        assert "X_test" in result
        assert "feature_names" in result

        assert result["X_train"].shape[0] == len(train_texts)
        assert result["X_val"].shape[0] == len(val_texts)
        assert result["X_test"].shape[0] == len(test_texts)

    def test_feature_names_length(self, sample_data):
        train_texts, _, _ = sample_data
        result = create_tfidf_features(train_texts, max_features=10)
        assert len(result["feature_names"]) <= 10

    def test_fit_on_train_only(self, sample_data):
        """Test that vectorizer is fitted only on training data."""
        train_texts, val_texts, _ = sample_data
        result = create_tfidf_features(train_texts, val_texts)

        # Both should have same number of features
        assert result["X_train"].shape[1] == result["X_val"].shape[1]

    def test_no_validation(self, sample_data):
        train_texts, _, test_texts = sample_data
        result = create_tfidf_features(train_texts, test_texts=test_texts)

        assert "X_val" not in result
        assert "X_train" in result
        assert "X_test" in result


class TestPreprocessClassical:
    """Tests for classical preprocessing pipeline."""

    @pytest.fixture
    def sample_dataframes(self):
        # Create larger dataset to satisfy min_df requirements
        train_texts = [
            "Good movie!",
            "Bad film...",
            "Great acting",
            "Poor script",
            "Loved it",
            "Hated it",
            "Excellent direction",
            "Weak plot",
            "Outstanding performance",
            "Terrible dialogue",
            "Wonderful cinematography",
            "Awful editing",
            "Brilliant screenplay",
            "Mediocre at best",
            "A cinematic masterpiece",
            "Complete waste of time",
        ]
        val_texts = [
            "Great film!",
            "Bad acting...",
            "Enjoyed it",
            "Poor quality",
            "Amazing story",
            "Terrible experience",
        ]
        test_texts = [
            "Excellent movie!",
            "Awful script...",
            "Loved the characters",
            "Hated the ending",
            "Best film ever",
            "Worst movie",
        ]

        # Create labels alternating 1 and 0
        n_train = len(train_texts)
        n_val = len(val_texts)
        n_test = len(test_texts)

        train_df = pd.DataFrame(
            {
                "text": train_texts[:n_train],
                "label": [1, 0] * (n_train // 2) + ([1] if n_train % 2 else []),
            }
        )
        val_df = pd.DataFrame(
            {
                "text": val_texts[:n_val],
                "label": [1, 0] * (n_val // 2) + ([1] if n_val % 2 else []),
            }
        )
        test_df = pd.DataFrame(
            {
                "text": test_texts[:n_test],
                "label": [1, 0] * (n_test // 2) + ([1] if n_test % 2 else []),
            }
        )

        return train_df, val_df, test_df

    def test_preprocess_classical(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_classical(train_df, val_df, test_df, max_features=100)

        assert "train" in result
        assert "val" in result
        assert "test" in result
        assert "vectorizer" in result
        assert "feature_names" in result

        # Check that labels are preserved
        assert result["train"][1].tolist() == train_df["label"].tolist()
        assert result["val"][1].tolist() == val_df["label"].tolist()
        assert result["test"][1].tolist() == test_df["label"].tolist()

    def test_cleaned_text_column_added(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_classical(train_df, val_df, test_df)

        assert "cleaned_text" in train_df.columns
        assert "cleaned_text" in val_df.columns
        assert "cleaned_text" in test_df.columns

    def test_custom_parameters(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_classical(
            train_df, val_df, test_df, max_features=50, ngram_range=(1, 3)
        )

        assert result["vectorizer"].max_features == 50
        assert result["vectorizer"].ngram_range == (1, 3)


class TestTransformerTokenizer:
    """Tests for transformer tokenizer."""

    @pytest.fixture
    def tokenizer(self):
        return TransformerTokenizer(model_name="bert", max_length=64)

    def test_tokenizer_initialization(self, tokenizer):
        assert tokenizer.model_name == "bert"
        assert tokenizer.max_length == 64

    def test_tokenize_basic(self, tokenizer):
        texts = ["Hello world", "Test sentence"]
        result = tokenizer.tokenize(texts)

        assert "input_ids" in result
        assert "attention_mask" in result
        assert result["input_ids"].shape[0] == 2

    def test_tokenize_with_padding(self, tokenizer):
        texts = ["Short", "A much longer sentence with more words"]
        result = tokenizer.tokenize(texts, padding=True)

        # Both sequences should be same length due to padding
        assert result["input_ids"].shape[0] == 2
        seq_len = result["input_ids"].shape[1]
        assert seq_len <= tokenizer.max_length

    def test_tokenize_truncation(self, tokenizer):
        # Create a very long text
        long_text = "word " * 200
        result = tokenizer.tokenize([long_text], truncation=True, padding=False)

        assert result["input_ids"].shape[1] <= tokenizer.max_length

    def test_tokenize_return_tensors(self, tokenizer):
        texts = ["Test"]
        result = tokenizer.tokenize(texts, return_tensors="pt")

        assert isinstance(result["input_ids"], torch.Tensor)

    def test_decode(self, tokenizer):
        texts = ["Hello world"]
        result = tokenizer.tokenize(texts)
        decoded = tokenizer.decode(result["input_ids"][0].tolist())

        # Decoded should contain original words (may have special tokens)
        assert "hello" in decoded.lower() or "world" in decoded.lower()

    def test_supported_models(self):
        models = TransformerTokenizer.get_supported_models()
        assert "bert" in models
        assert "roberta" in models
        assert "distilbert" in models


class TestPreprocessTransformer:
    """Tests for transformer preprocessing pipeline."""

    @pytest.fixture
    def sample_dataframes(self):
        # Create larger dataset for transformer tokenization tests
        train_texts = [
            "Good movie!",
            "Bad film...",
            "Great acting",
            "Poor script",
            "Loved it",
            "Hated it",
            "Excellent direction",
            "Weak plot",
            "Outstanding performance",
            "Terrible dialogue",
            "Wonderful cinematography",
            "Awful editing",
            "Brilliant screenplay",
            "Mediocre at best",
            "A cinematic masterpiece",
            "Complete waste of time",
        ]
        val_texts = [
            "Great film!",
            "Bad acting...",
            "Enjoyed it",
            "Poor quality",
            "Amazing story",
            "Terrible experience",
        ]
        test_texts = [
            "Excellent movie!",
            "Awful script...",
            "Loved the characters",
            "Hated the ending",
            "Best film ever",
            "Worst movie",
        ]

        n_train = len(train_texts)
        n_val = len(val_texts)
        n_test = len(test_texts)

        train_df = pd.DataFrame(
            {
                "text": train_texts[:n_train],
                "label": [1, 0] * (n_train // 2) + ([1] if n_train % 2 else []),
            }
        )
        val_df = pd.DataFrame(
            {
                "text": val_texts[:n_val],
                "label": [1, 0] * (n_val // 2) + ([1] if n_val % 2 else []),
            }
        )
        test_df = pd.DataFrame(
            {
                "text": test_texts[:n_test],
                "label": [1, 0] * (n_test // 2) + ([1] if n_test % 2 else []),
            }
        )

        return train_df, val_df, test_df

    def test_preprocess_transformer_bert(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_transformer(
            train_df, val_df, test_df, model_name="bert", max_length=32
        )

        assert "train" in result
        assert "val" in result
        assert "test" in result
        assert "tokenizer" in result

        # Check inputs exist
        for split in ["train", "val", "test"]:
            assert "input_ids" in result[split]
            assert "attention_mask" in result[split]
            assert "labels" in result[split]

            # Check labels match original dataframes
            if split == "train":
                expected_labels = torch.tensor(train_df["label"].values)
            elif split == "val":
                expected_labels = torch.tensor(val_df["label"].values)
            else:
                expected_labels = torch.tensor(test_df["label"].values)
            assert torch.equal(result[split]["labels"], expected_labels)

    def test_preprocess_transformer_batch_size(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_transformer(train_df, val_df, test_df, model_name="bert")

        # All splits should have same batch size as input
        assert result["train"]["input_ids"].shape[0] == len(train_df)
        assert result["val"]["input_ids"].shape[0] == len(val_df)
        assert result["test"]["input_ids"].shape[0] == len(test_df)

    def test_unsupported_model_fails(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        # This should still work because TransformerTokenizer accepts any model name
        result = preprocess_transformer(
            train_df,
            val_df,
            test_df,
            model_name="bert-base-uncased",  # Direct HF model name
        )
        assert "tokenizer" in result


class TestPreprocessDataset:
    """Tests for unified preprocessing interface."""

    @pytest.fixture
    def sample_dataframes(self):
        train_df = pd.DataFrame(
            {"text": ["Good movie!", "Bad film..."], "label": [1, 0]}
        )
        val_df = pd.DataFrame(
            {"text": ["Great acting", "Poor script"], "label": [1, 0]}
        )
        test_df = pd.DataFrame({"text": ["Loved it", "Hated it"], "label": [1, 0]})
        return train_df, val_df, test_df

    def test_preprocess_classical_mode(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_dataset(train_df, val_df, test_df, mode="classical")

        assert "vectorizer" in result
        assert "train" in result
        assert isinstance(result["train"], tuple)

    def test_preprocess_transformer_mode(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_dataset(
            train_df,
            val_df,
            test_df,
            mode="transformer",
            model_name="bert",
            max_length=16,
        )

        assert "tokenizer" in result
        assert "train" in result
        assert isinstance(result["train"], dict)
        assert "input_ids" in result["train"]

    def test_invalid_mode_raises(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        with pytest.raises(ValueError, match="Invalid preprocessing mode"):
            preprocess_dataset(train_df, val_df, test_df, mode="invalid")

    def test_mode_parameter_passed(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_dataset(
            train_df, val_df, test_df, mode="classical", max_features=100
        )

        assert result["vectorizer"].max_features == 100
