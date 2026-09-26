"""Unit tests for model configuration and training contracts."""

from unittest.mock import MagicMock, patch

import pytest

from src.models.model_config import (
    DECISION_TREE_CONFIG,
    DEFAULT_FEATURES_COL,
    DEFAULT_LABEL_COL,
    GBT_CONFIG,
    LOGISTIC_REGRESSION_CONFIG,
    MODEL_ORDER,
    RANDOM_FOREST_CONFIG,
    get_all_model_configs,
    get_model_config,
    get_model_names,
)
from src.models.trainer import (
    load_model,
    save_model,
    split_data,
    train_all_models,
)


def test_model_names_order_and_completeness() -> None:
    """Verify that all four models are present in deterministic execution order."""
    expected_order = ["logistic_regression", "random_forest", "decision_tree", "gbt"]
    assert list(MODEL_ORDER) == expected_order
    assert get_model_names() == expected_order


def test_logistic_regression_configuration() -> None:
    """Verify Logistic Regression hyperparameters and target columns."""
    cfg = get_model_config("logistic_regression")
    assert cfg.name == "logistic_regression"
    assert cfg.estimator_name == "LogisticRegression"
    assert cfg.features_col == DEFAULT_FEATURES_COL
    assert cfg.label_col == DEFAULT_LABEL_COL
    assert cfg.hyperparameters == {
        "maxIter": 100,
        "regParam": 0.01,
    }
    assert cfg.artifact_path == "models/logistic_regression"
    assert cfg == LOGISTIC_REGRESSION_CONFIG


def test_random_forest_configuration() -> None:
    """Verify Random Forest hyperparameters and target columns."""
    cfg = get_model_config("random_forest")
    assert cfg.name == "random_forest"
    assert cfg.estimator_name == "RandomForestClassifier"
    assert cfg.features_col == DEFAULT_FEATURES_COL
    assert cfg.label_col == DEFAULT_LABEL_COL
    assert cfg.hyperparameters == {
        "numTrees": 50,
        "maxDepth": 8,
    }
    assert cfg.artifact_path == "models/random_forest"
    assert cfg == RANDOM_FOREST_CONFIG


def test_decision_tree_configuration() -> None:
    """Verify Decision Tree hyperparameters and target columns."""
    cfg = get_model_config("decision_tree")
    assert cfg.name == "decision_tree"
    assert cfg.estimator_name == "DecisionTreeClassifier"
    assert cfg.features_col == DEFAULT_FEATURES_COL
    assert cfg.label_col == DEFAULT_LABEL_COL
    assert cfg.hyperparameters == {
        "maxDepth": 6,
        "minInstancesPerNode": 3,
    }
    assert cfg.artifact_path == "models/decision_tree"
    assert cfg == DECISION_TREE_CONFIG


def test_gbt_configuration() -> None:
    """Verify Gradient Boosted Trees hyperparameters and target columns."""
    cfg = get_model_config("gbt")
    assert cfg.name == "gbt"
    assert cfg.estimator_name == "GBTClassifier"
    assert cfg.features_col == DEFAULT_FEATURES_COL
    assert cfg.label_col == DEFAULT_LABEL_COL
    assert cfg.hyperparameters == {
        "maxIter": 30,
        "maxDepth": 5,
        "stepSize": 0.1,
    }
    assert cfg.artifact_path == "models/gbt"
    assert cfg == GBT_CONFIG


def test_get_all_model_configs() -> None:
    """Verify get_all_model_configs returns list of all four model configs."""
    configs = get_all_model_configs()
    assert len(configs) == 4
    assert [c.name for c in configs] == list(MODEL_ORDER)


def test_get_model_config_invalid_name_raises_key_error() -> None:
    """Verify unknown model name raises KeyError."""
    with pytest.raises(KeyError, match="Unknown model name"):
        get_model_config("unsupported_model")


def test_split_data_validation() -> None:
    """Verify split_data parameter and column validation."""
    mock_df = MagicMock()
    mock_df.columns = ["features", "readmission_target"]
    mock_df.randomSplit.return_value = (MagicMock(), MagicMock())

    train_df, test_df = split_data(mock_df, train_ratio=0.8, test_ratio=0.2, seed=42)
    mock_df.randomSplit.assert_called_once_with([0.8, 0.2], seed=42)
    assert train_df is not None
    assert test_df is not None


def test_split_data_invalid_ratios() -> None:
    """Verify ValueError on invalid split ratios."""
    mock_df = MagicMock()
    with pytest.raises(ValueError, match="Train and test ratios must be between 0 and 1"):
        split_data(mock_df, train_ratio=1.5, test_ratio=0.2)


def test_split_data_missing_features_column() -> None:
    """Verify ValueError when features column is absent."""
    mock_df = MagicMock()
    mock_df.columns = ["other_col", "readmission_target"]
    with pytest.raises(ValueError, match="Required features column 'features' not found"):
        split_data(mock_df)


def test_split_data_missing_label_column() -> None:
    """Verify ValueError when label column is absent."""
    mock_df = MagicMock()
    mock_df.columns = ["features", "other_col"]
    with pytest.raises(ValueError, match="Required label column 'readmission_target' not found"):
        split_data(mock_df)


def test_save_model_invokes_writer() -> None:
    """Verify save_model invokes model.write().overwrite().save()."""
    mock_model = MagicMock()
    mock_writer = MagicMock()
    mock_model.write.return_value = mock_writer
    mock_writer.overwrite.return_value = mock_writer

    save_model(mock_model, "models/test_model", overwrite=True)
    mock_model.write.assert_called_once()
    mock_writer.overwrite.assert_called_once()
    mock_writer.save.assert_called_once_with("models/test_model")


def test_load_model_unsupported_name() -> None:
    """Verify load_model raises ValueError on unsupported model name."""
    with patch("src.models.trainer.LogisticRegressionModel", MagicMock()):
        with pytest.raises(ValueError, match="Unsupported model name for loading"):
            load_model("unknown_name", "models/unknown")


def test_train_all_models_orchestration() -> None:
    """Verify train_all_models orchestrates fitting, persistence, and cleanup."""
    mock_train_df = MagicMock()
    mock_test_df = MagicMock()
    mock_vector = MagicMock()
    mock_vector.size = 286
    mock_train_df.count.return_value = 79472
    mock_test_df.count.return_value = 19868
    mock_train_df.select.return_value.first.return_value = {"features": mock_vector}

    mock_fitted_model = MagicMock()

    with (
        patch("src.models.trainer.train_model", return_value=(mock_fitted_model, 1.25)),
        patch("src.models.trainer.save_model") as mock_save,
        patch("src.models.trainer.load_model", return_value=mock_fitted_model) as mock_load,
    ):
        results = train_all_models(
            train_df=mock_train_df,
            test_df=mock_test_df,
            output_base_dir="models",
            save_artifacts=True,
        )

        assert len(results) == 4
        assert list(results.keys()) == list(MODEL_ORDER)
        for name in MODEL_ORDER:
            meta = results[name]
            assert meta["train_row_count"] == 79472
            assert meta["test_row_count"] == 19868
            assert meta["feature_dimension"] == 286
            assert meta["training_duration_seconds"] == 1.25
            assert meta["artifact_path"] == f"models/{name}"
            assert meta["model_loaded_verified"] is True

        assert mock_save.call_count == 4
        assert mock_load.call_count == 4
        assert mock_train_df.persist.called or mock_train_df.cache.called
        mock_train_df.unpersist.assert_called_once()
        mock_test_df.unpersist.assert_called_once()
