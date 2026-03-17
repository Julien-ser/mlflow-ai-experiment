"""
Tests for transformer model implementations.
"""

import pytest
import torch
import numpy as np
from src.models.transformers import (
    TransformerModel,
    BERTModel,
    RoBERTaModel,
    DeBERTaModel,
    XLNetModel,
    create_transformer_model,
    create_transformer_model_from_name,
)


class TestTransformerModel:
    """Test the base TransformerModel class."""

    def test_initialization(self):
        """Test model initialization with default and custom parameters."""
        model = TransformerModel(
            model_name="bert-base-uncased",
            num_labels=3,
            dropout=0.2,
            max_seq_length=256,
        )

        assert model.model_name == "bert-base-uncased"
        assert model.num_labels == 3
        assert model.dropout == 0.2
        assert model.max_seq_length == 256
        assert model.device in [torch.device("cpu"), torch.device("cuda")]

    def test_extract_model_type(self):
        """Test model type extraction from model name."""
        model = TransformerModel(model_name="bert-base-uncased")

        assert model._extract_model_type("bert-base-uncased") == "bert"
        assert model._extract_model_type("roberta-base") == "roberta"
        assert model._extract_model_type("microsoft/deberta-v3-base") == "deberta"
        assert model._extract_model_type("xlnet-base-cased") == "xlnet"

    def test_invalid_model_type_extraction(self):
        """Test error handling for invalid model name."""
        model = TransformerModel(model_name="invalid-model")

        with pytest.raises(ValueError, match="Could not determine model type"):
            model._extract_model_type("unknown-model-xyz")

    def test_get_model_class(self):
        """Test getting model class by type."""
        model = TransformerModel(model_name="bert-base-uncased")

        from transformers import BertForSequenceClassification

        assert model._get_model_class("bert") == BertForSequenceClassification

        from transformers import RobertaForSequenceClassification

        assert model._get_model_class("roberta") == RobertaForSequenceClassification

    def test_invalid_model_class(self):
        """Test error handling for invalid model type."""
        model = TransformerModel(model_name="bert-base-uncased")

        with pytest.raises(ValueError, match="Unknown model type"):
            model._get_model_class("invalid_type")


class TestSpecificModels:
    """Test specific model subclasses."""

    @pytest.mark.parametrize(
        "model_class,expected_name",
        [
            (BERTModel, "bert-base-uncased"),
            (RoBERTaModel, "roberta-base"),
            (DeBERTaModel, "microsoft/deberta-v3-base"),
            (XLNetModel, "xlnet-base-cased"),
        ],
    )
    def test_default_model_names(self, model_class, expected_name):
        """Test that each model class has correct default model name."""
        model = model_class()
        assert model.model_name == expected_name

    @pytest.mark.parametrize(
        "model_class,custom_name",
        [
            (BERTModel, "bert-large-uncased"),
            (RoBERTaModel, "roberta-large"),
            (DeBERTaModel, "microsoft/deberta-v3-large"),
            (XLNetModel, "xlnet-large-cased"),
        ],
    )
    def test_custom_model_names(self, model_class, custom_name):
        """Test that custom model names are respected."""
        model = model_class(model_name=custom_name)
        assert model.model_name == custom_name


class TestFactoryFunctions:
    """Test factory functions."""

    @pytest.mark.parametrize(
        "model_type,expected_class",
        [
            ("bert", BERTModel),
            ("roberta", RoBERTaModel),
            ("deberta", DeBERTaModel),
            ("xlnet", XLNetModel),
        ],
    )
    def test_create_transformer_model(self, model_type, expected_class):
        """Test create_transformer_model factory."""
        model = create_transformer_model(model_type, num_labels=5)
        assert isinstance(model, expected_class)
        assert model.num_labels == 5

    @pytest.mark.parametrize(
        "model_name,expected_type",
        [
            ("bert-base-uncased", "bert"),
            ("roberta-base", "roberta"),
            ("microsoft/deberta-v3-base", "deberta"),
            ("xlnet-base-cased", "xlnet"),
            ("distilbert-base-uncased", "bert"),  # distilbert contains 'bert'
        ],
    )
    def test_create_transformer_model_from_name(self, model_name, expected_type):
        """Test create_transformer_model_from_name factory."""
        model = create_transformer_model_from_name(model_name, num_labels=3)
        assert isinstance(model, (BERTModel, RoBERTaModel, DeBERTaModel, XLNetModel))
        assert model.model_name == model_name
        assert model.num_labels == 3

    def test_invalid_model_type(self):
        """Test error handling for invalid model type."""
        with pytest.raises(ValueError, match="Unknown transformer model"):
            create_transformer_model("invalid_model")


class TestModelIntegrity:
    """Test model building and tokenization."""

    @pytest.mark.slow
    @pytest.mark.parametrize(
        "model_type,model_name",
        [
            ("bert", "bert-base-uncased"),
            ("roberta", "roberta-base"),
            ("deberta", "microsoft/deberta-v3-base"),
            ("xlnet", "xlnet-base-cased"),
        ],
    )
    def test_build_model(self, model_type, model_name):
        """Test building model architecture."""
        model = create_transformer_model(
            model_type, model_name=model_name, num_labels=2
        )

        # Build model (downloads weights on first run)
        built_model = model.build_model()

        assert built_model is not None
        assert model.model is not None
        assert model.tokenizer is not None
        assert model.model.config.num_labels == 2

    @pytest.mark.slow
    def test_tokenize_data(self):
        """Test tokenization of input texts."""
        model = create_transformer_model("bert", num_labels=2)
        model.load_tokenizer()

        texts = ["Hello world!", "Another test sentence."]
        encoding = model.tokenize_data(texts)

        assert "input_ids" in encoding
        assert "attention_mask" in encoding
        assert encoding["input_ids"].shape[0] == 2
        assert encoding["input_ids"].shape[1] <= model.max_seq_length

    def test_tokenize_data_with_labels(self):
        """Test tokenization with labels."""
        model = create_transformer_model("bert", num_labels=2)
        model.load_tokenizer()

        texts = ["Positive text", "Negative text"]
        labels = [1, 0]
        encoding = model.tokenize_data(texts, labels=labels)

        assert "labels" in encoding
        assert torch.equal(encoding["labels"], torch.tensor(labels))


class TestConfiguration:
    """Test model configuration and hyperparameters."""

    def test_custom_hyperparameters(self):
        """Test that custom hyperparameters are properly set."""
        custom_params = {
            "num_labels": 5,
            "dropout": 0.3,
            "max_seq_length": 128,
            "learning_rate": 1e-5,
            "batch_size": 32,
            "num_train_epochs": 5,
            "weight_decay": 0.05,
            "warmup_steps": 100,
        }

        model = TransformerModel(model_name="bert-base-uncased", **custom_params)

        for key, value in custom_params.items():
            assert getattr(model, key) == value

    def test_default_hyperparameters(self):
        """Test default hyperparameter values."""
        model = TransformerModel(model_name="bert-base-uncased")

        assert model.num_labels == 2
        assert model.dropout == 0.1
        assert model.max_seq_length == 512
        assert model.learning_rate == 2e-5
        assert model.batch_size == 16
        assert model.num_train_epochs == 3
        assert model.weight_decay == 0.01
        assert model.warmup_steps == 500


@pytest.mark.skip(reason="Requires actual training data and time")
class TestTraining:
    """Test training functionality (skipped by default)."""

    def test_train_basic(self):
        """Test basic training loop."""
        # This would require actual tokenized datasets
        # Can be enabled manually when needed
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
