"""
Tests for classical ML model implementations.
"""

import pytest
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from mlflow_ai_experiment.models.classical import (
    LogisticRegressionModel,
    SVMModel,
    RandomForestModel,
    XGBoostModel,
    create_model,
)

# Sample data for testing
TEXTS = ["good movie", "bad film", "great acting", "terrible plot"]
LABELS = np.array([1, 0, 1, 0])


def test_logistic_regression():
    """Test Logistic Regression model."""
    vectorizer = TfidfVectorizer(max_features=10)
    X = vectorizer.fit_transform(TEXTS)

    model = LogisticRegressionModel(
        params={"C": 1.0, "max_iter": 100, "random_state": 42}
    )
    model.train(X, LABELS, X, LABELS)

    predictions = model.predict(X)
    assert len(predictions) == len(LABELS)
    assert model.predict_proba(X).shape == (len(LABELS), 2)

    # Test save and load
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        path = f.name
    try:
        model.save_model(path)
        loaded = LogisticRegressionModel.load_model(path)
        loaded_predictions = loaded.predict(X)
        np.testing.assert_array_equal(predictions, loaded_predictions)
    finally:
        import os

        os.remove(path)


def test_svm():
    """Test SVM model."""
    vectorizer = TfidfVectorizer(max_features=10)
    X = vectorizer.fit_transform(TEXTS)

    model = SVMModel(params={"C": 1.0, "max_iter": 200, "random_state": 42})
    model.train(X, LABELS, X, LABELS)

    predictions = model.predict(X)
    assert len(predictions) == len(LABELS)
    # SVM may not have predict_proba depending on the implementation

    # Test save and load
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        path = f.name
    try:
        model.save_model(path)
        loaded = SVMModel.load_model(path)
        loaded_predictions = loaded.predict(X)
        np.testing.assert_array_equal(predictions, loaded_predictions)
    finally:
        os.remove(path)


def test_random_forest():
    """Test Random Forest model."""
    vectorizer = TfidfVectorizer(max_features=10)
    X = vectorizer.fit_transform(TEXTS)

    model = RandomForestModel(
        params={"n_estimators": 10, "max_depth": 3, "random_state": 42}
    )
    model.train(X, LABELS, X, LABELS)

    predictions = model.predict(X)
    assert len(predictions) == len(LABELS)
    assert model.predict_proba(X).shape == (len(LABELS), 2)

    # Test save and load
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        path = f.name
    try:
        model.save_model(path)
        loaded = RandomForestModel.load_model(path)
        loaded_predictions = loaded.predict(X)
        np.testing.assert_array_equal(predictions, loaded_predictions)
    finally:
        os.remove(path)


def test_xgboost():
    """Test XGBoost model."""
    vectorizer = TfidfVectorizer(max_features=10)
    X = vectorizer.fit_transform(TEXTS)

    model = XGBoostModel(
        params={"n_estimators": 10, "max_depth": 3, "random_state": 42}
    )
    model.train(X, LABELS, X, LABELS)

    predictions = model.predict(X)
    assert len(predictions) == len(LABELS)
    assert model.predict_proba(X).shape == (len(LABELS), 2)

    # Test save and load
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        path = f.name
    try:
        model.save_model(path)
        loaded = XGBoostModel.load_model(path)
        loaded_predictions = loaded.predict(X)
        np.testing.assert_array_equal(predictions, loaded_predictions)
    finally:
        os.remove(path)


def test_create_model_factory():
    """Test model factory function."""
    for model_type in ["logistic_regression", "svm", "random_forest", "xgboost"]:
        model = create_model(model_type)
        assert model is not None
        assert hasattr(model, "train")
        assert hasattr(model, "predict")
        assert hasattr(model, "predict_proba")
        assert hasattr(model, "log_to_mlflow")
        assert hasattr(model, "save_model")
        assert hasattr(model, "load_model")

    # Test invalid model type
    with pytest.raises(ValueError):
        create_model("invalid_model")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
