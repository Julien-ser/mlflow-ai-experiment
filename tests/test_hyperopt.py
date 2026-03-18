"""
Tests for hyperparameter optimization framework.
"""

import os
import tempfile
import numpy as np
import optuna
import pytest
import uuid
from mlflow_ai_experiment.hyperopt import (
    get_transformer_search_space,
    get_classical_search_space,
    optimize_classical_model,
)


class TestSearchSpaces:
    """Test search space definitions."""

    def test_get_transformer_search_space_bert(self):
        study = optuna.create_study(load_if_exists=True)
        trial = study.ask()
        space = get_transformer_search_space(trial, "bert")
        expected_keys = {
            "learning_rate",
            "batch_size",
            "dropout",
            "num_train_epochs",
            "weight_decay",
            "warmup_steps",
            "max_seq_length",
        }
        assert set(space.keys()) == expected_keys

    def test_get_transformer_search_space_roberta(self):
        study = optuna.create_study(load_if_exists=True)
        trial = study.ask()
        space = get_transformer_search_space(trial, "roberta")
        expected_keys = {
            "learning_rate",
            "batch_size",
            "dropout",
            "num_train_epochs",
            "weight_decay",
            "warmup_steps",
            "max_seq_length",
        }
        assert set(space.keys()) == expected_keys

    @pytest.mark.parametrize(
        "model_type", ["logistic_regression", "svm", "random_forest", "xgboost"]
    )
    def test_get_classical_search_space_all_models(self, model_type):
        study = optuna.create_study(load_if_exists=True)
        trial = study.ask()
        space = get_classical_search_space(trial, model_type)
        assert isinstance(space, dict)
        assert len(space) > 0
        # Verify that all values are not None (they should be set by trial.suggest)
        for key, value in space.items():
            assert value is not None


class TestOptimizeClassical:
    """Test classical model optimization."""

    @pytest.fixture
    def temp_mlflow_uri(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            uri = f"file://{tmpdir}"
            old_uri = os.environ.get("MLFLOW_TRACKING_URI")
            os.environ["MLFLOW_TRACKING_URI"] = uri
            yield uri
            if old_uri is not None:
                os.environ["MLFLOW_TRACKING_URI"] = old_uri
            elif "MLFLOW_TRACKING_URI" in os.environ:
                del os.environ["MLFLOW_TRACKING_URI"]

    def test_optimize_logistic_regression_single_trial(self, temp_mlflow_uri):
        """Smoke test: optimize logistic regression with a single trial on tiny data."""
        np.random.seed(42)
        X_train = np.random.randn(20, 5)
        y_train = np.random.randint(0, 2, 20)
        X_val = np.random.randn(5, 5)
        y_val = np.random.randint(0, 2, 5)

        study = optimize_classical_model(
            model_type="logistic_regression",
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            experiment_name="test_hyperopt_classical",
            n_trials=1,
            timeout=None,
            study_name=f"test_logreg_{uuid.uuid4().hex}",
        )
        assert study is not None
        assert len(study.trials) == 1
        assert isinstance(study.best_value, float)
        # Verify best params contain expected keys
        expected_keys = {"C", "max_iter", "solver"}
        assert set(study.best_params.keys()) == expected_keys
