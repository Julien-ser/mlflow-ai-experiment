"""
Statistical significance testing and analysis utilities for model comparison.

This module provides functions to:
- Perform statistical tests to compare model performance
- Calculate confidence intervals using bootstrap
- Analyze metric correlations
- Generate statistical reports
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from sklearn.metrics import confusion_matrix


def mcnemar_test(
    y_true: np.ndarray, y_pred1: np.ndarray, y_pred2: np.ndarray
) -> Dict[str, Any]:
    """
    McNemar's test for comparing two classifiers on the same test set.

    H0: The two classifiers have equal error rates.

    Args:
        y_true: True labels
        y_pred1: Predictions from model 1
        y_pred2: Predictions from model 2

    Returns:
        Dictionary with test statistic, p-value, and interpretation
    """
    # Build contingency table
    both_correct = np.sum((y_pred1 == y_true) & (y_pred2 == y_true))
    m1_correct_m2_wrong = np.sum((y_pred1 == y_true) & (y_pred2 != y_true))
    m1_wrong_m2_correct = np.sum((y_pred1 != y_true) & (y_pred2 == y_true))
    both_wrong = np.sum((y_pred1 != y_true) & (y_pred2 != y_true))

    # McNemar's test focuses on the discordant pairs
    # | a  b |
    # | c  d |
    # where b = m1_correct_m2_wrong, c = m1_wrong_m2_correct
    # Test statistic: (b - c)^2 / (b + c)

    b = m1_correct_m2_wrong
    c = m1_wrong_m2_correct

    if b + c == 0:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "interpretation": "No disagreement between models",
        }

    # Use binomial exact test for small samples, chi-square for larger
    if b + c < 20:
        # Binomial test
        p_value = 2 * stats.binom.cdf(min(b, c), b + c, 0.5)
        statistic = abs(b - c)
    else:
        # Chi-square approximation with continuity correction
        statistic = ((abs(b - c) - 1) ** 2) / (b + c)
        p_value = 1 - stats.chi2.cdf(statistic, df=1)

    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "b": int(b),
        "c": int(c),
        "interpretation": f"Model1 significantly {'better' if b < c else 'worse'}"
        if p_value < 0.05
        else "No significant difference",
    }


def paired_ttest(
    scores1: np.ndarray, scores2: np.ndarray, alternative: str = "two-sided"
) -> Dict[str, Any]:
    """
    Paired t-test for comparing two models across multiple folds or bootstrap samples.

    Args:
        scores1: Performance scores for model 1 (e.g., accuracy from cross-validation)
        scores2: Performance scores for model 2
        alternative: 'two-sided', 'less', or 'greater'

    Returns:
        Dictionary with t-statistic, p-value, and effect size
    """
    if len(scores1) != len(scores2):
        raise ValueError("Score arrays must have the same length")

    if len(scores1) < 2:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "df": 0,
            "significant": False,
            "interpretation": "Insufficient samples for t-test",
        }

    # Perform paired t-test
    statistic, p_value = stats.ttest_rel(scores1, scores2, alternative=alternative)

    # Cohen's d for paired samples
    diff = scores1 - scores2
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    cohens_d = mean_diff / std_diff if std_diff > 0 else 0.0

    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "df": len(scores1) - 1,
        "mean_difference": float(mean_diff),
        "cohens_d": float(cohens_d),
        "significant": p_value < 0.05,
        "interpretation": interpret_effect_size(cohens_d),
    }


def wilcoxon_signed_rank(scores1: np.ndarray, scores2: np.ndarray) -> Dict[str, Any]:
    """
    Wilcoxon signed-rank test (non-parametric alternative to paired t-test).

    Args:
        scores1: Performance scores for model 1
        scores2: Performance scores for model 2

    Returns:
        Dictionary with test results
    """
    if len(scores1) != len(scores2):
        raise ValueError("Score arrays must have the same length")

    statistic, p_value = stats.wilcoxon(scores1, scores2)

    # Effect size r = Z / sqrt(N)
    # Approximate Z from Wilcoxon statistic
    n = len(scores1)
    expected_stat = n * (n + 1) / 4
    std_stat = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    z_score = (statistic - expected_stat) / std_stat if std_stat > 0 else 0.0
    effect_size_r = abs(z_score) / np.sqrt(n) if n > 0 else 0.0

    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "effect_size_r": float(effect_size_r),
        "significant": p_value < 0.05,
        "interpretation": interpret_effect_size(effect_size_r, non_parametric=True),
    }


def bootstrap_confidence_interval(
    metric_fn,
    data: Tuple[np.ndarray, np.ndarray],
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Calculate bootstrap confidence interval for a metric.

    Args:
        metric_fn: Function that computes metric given (y_true, y_pred)
        data: Tuple of (y_true, y_pred)
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level (e.g., 0.95 for 95% CI)
        random_state: Random seed

    Returns:
        Dictionary with mean, CI bounds, and standard error
    """
    np.random.seed(random_state)
    y_true, y_pred = data
    n = len(y_true)

    bootstrap_metrics = []

    for _ in range(n_bootstrap):
        # Sample with replacement
        indices = np.random.randint(0, n, n)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]

        metric_val = metric_fn(y_true_boot, y_pred_boot)
        bootstrap_metrics.append(metric_val)

    bootstrap_metrics = np.array(bootstrap_metrics)
    mean_metric = np.mean(bootstrap_metrics)
    std_metric = np.std(bootstrap_metrics)

    alpha = 1 - confidence
    lower = np.percentile(bootstrap_metrics, alpha / 2 * 100)
    upper = np.percentile(bootstrap_metrics, (1 - alpha / 2) * 100)

    return {
        "mean": float(mean_metric),
        "std": float(std_metric),
        "ci_lower": float(lower),
        "ci_upper": float(upper),
        "ci_width": float(upper - lower),
        "n_bootstrap": n_bootstrap,
    }


def compare_models_bootstrap(
    y_true: np.ndarray,
    predictions: Dict[str, np.ndarray],
    metric_fn,
    n_bootstrap: int = 1000,
    paired: bool = True,
) -> pd.DataFrame:
    """
    Compare multiple models using bootstrap confidence intervals.

    Args:
        y_true: True labels
        predictions: Dictionary mapping model names to predictions
        metric_fn: Metric function
        n_bootstrap: Number of bootstrap samples
        paired: If True, use paired bootstrap (same resamples for all models)

    Returns:
        DataFrame with comparison results
    """
    model_names = list(predictions.keys())
    n_models = len(model_names)

    results = []

    for model in model_names:
        y_pred = predictions[model]
        ci = bootstrap_confidence_interval(
            metric_fn, (y_true, y_pred), n_bootstrap=n_bootstrap
        )
        results.append({"model": model, **ci})

    df = pd.DataFrame(results)

    # Add pairwise comparisons if paired
    if paired and n_models > 1:
        comparisons = []
        np.random.seed(42)
        n = len(y_true)
        bootstrap_indices = [np.random.randint(0, n, n) for _ in range(n_bootstrap)]

        for i in range(n_models):
            for j in range(i + 1, n_models):
                model_i = model_names[i]
                model_j = model_names[j]

                diffs = []
                for indices in bootstrap_indices:
                    y_true_boot = y_true[indices]
                    pred_i = predictions[model_i][indices]
                    pred_j = predictions[model_j][indices]

                    metric_i = metric_fn(y_true_boot, pred_i)
                    metric_j = metric_fn(y_true_boot, pred_j)
                    diffs.append(metric_i - metric_j)

                diffs = np.array(diffs)
                mean_diff = np.mean(diffs)
                ci_lower = np.percentile(diffs, 2.5)
                ci_upper = np.percentile(diffs, 97.5)
                p_value = np.mean(diffs <= 0) if mean_diff >= 0 else np.mean(diffs >= 0)
                p_value = min(p_value, 1 - p_value) * 2  # Two-sided

                comparisons.append(
                    {
                        "model_1": model_i,
                        "model_2": model_j,
                        "mean_difference": float(mean_diff),
                        "ci_lower": float(ci_lower),
                        "ci_upper": float(ci_upper),
                        "p_value": float(p_value),
                        "significant": p_value < 0.05,
                    }
                )

        return df, pd.DataFrame(comparisons)

    return df


def friedman_test(scores: pd.DataFrame) -> Dict[str, Any]:
    """
    Friedman test for comparing multiple models across multiple datasets/folds.

    Args:
        scores: DataFrame where rows are datasets/folds and columns are models

    Returns:
        Dictionary with test statistic, p-value, and interpretation
    """
    # Convert to required format
    if isinstance(scores, pd.DataFrame):
        data_array = scores.values
    else:
        data_array = np.array(scores)

    # Friedman test
    statistic, p_value = stats.friedmanchisquare(
        *[data_array[:, i] for i in range(data_array.shape[1])]
    )

    # Nemenyi post-hoc test if significant
    nemenyi_results = None
    if p_value < 0.05:
        # Simple Nemenyi critical difference
        k = data_array.shape[1]  # number of models
        n = data_array.shape[0]  # number of datasets/folds
        q_alpha = _get_nemenyi_critical_value(k, alpha=0.05)
        cd = q_alpha * np.sqrt(k * (k + 1) / (6 * n))

        # Compute average ranks
        ranks = np.zeros_like(data_array)
        for i in range(n):
            ranks[i] = stats.rankdata(-data_array[i])  # Higher is better, so negate

        avg_ranks = np.mean(ranks, axis=0)

        nemenyi_results = {
            "critical_difference": float(cd),
            "average_ranks": {
                f"model_{i}": float(rank) for i, rank in enumerate(avg_ranks)
            },
        }

    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "n_datasets": data_array.shape[0],
        "n_models": data_array.shape[1],
        "nemenyi": nemenyi_results,
        "interpretation": "At least one model differs significantly"
        if p_value < 0.05
        else "No significant differences detected",
    }


def _get_nemenyi_critical_value(k: int, alpha: float = 0.05) -> float:
    """Get critical value for Nemenyi test."""
    # Precomputed critical values for Nemenyi test
    # For alpha=0.05
    critical_values = {
        2: 1.960,
        3: 2.343,
        4: 2.569,
        5: 2.727,
        6: 2.850,
        7: 2.949,
        8: 3.031,
        9: 3.102,
        10: 3.164,
    }

    if k <= 10:
        return critical_values.get(k, critical_values[10])
    else:
        # Approximate using studentized range
        return stats.t.ppf(1 - alpha / (k * (k - 1) / 2), k * (k + 1) / 2)


def interpret_effect_size(effect_size: float, non_parametric: bool = False) -> str:
    """
    Interpret effect size magnitude.

    Args:
        effect_size: Cohen's d (or r for non-parametric)
        non_parametric: If True, interpret as r (0.1 small, 0.3 medium, 0.5 large)
                      If False, interpret as d (0.2 small, 0.5 medium, 0.8 large)
    """
    if non_parametric:
        # Cohen's suggestion for r
        if abs(effect_size) < 0.1:
            magnitude = "very small"
        elif abs(effect_size) < 0.3:
            magnitude = "small"
        elif abs(effect_size) < 0.5:
            magnitude = "medium"
        else:
            magnitude = "large"
    else:
        # Cohen's d
        if abs(effect_size) < 0.2:
            magnitude = "very small"
        elif abs(effect_size) < 0.5:
            magnitude = "small"
        elif abs(effect_size) < 0.8:
            magnitude = "medium"
        else:
            magnitude = "large"

    direction = "positive" if effect_size > 0 else "negative"
    return f"{magnitude} effect ({direction})"


def calculate_metric_correlations(
    results_df: pd.DataFrame,
    metrics: List[str] = [
        "accuracy",
        "f1",
        "precision",
        "recall",
        "inference_latency_ms",
        "model_size_mb",
    ],
) -> pd.DataFrame:
    """
    Calculate correlations between different metrics.

    Args:
        results_df: DataFrame with model results
        metrics: List of metric columns to correlate

    Returns:
        Correlation matrix DataFrame
    """
    available_metrics = [m for m in metrics if m in results_df.columns]
    corr_matrix = results_df[available_metrics].corr(method="pearson")
    return corr_matrix


def generate_statistical_report(
    comparison_df: pd.DataFrame,
    predictions: Optional[Dict[str, np.ndarray]] = None,
    y_true: Optional[np.ndarray] = None,
    significance_tests: bool = True,
) -> str:
    """
    Generate a comprehensive statistical report.

    Args:
        comparison_df: DataFrame with model comparison results
        predictions: Dictionary of model predictions for pairwise tests
        y_true: True labels for pairwise tests
        significance_tests: Whether to perform pairwise significance tests

    Returns:
        Markdown formatted report
    """
    report_lines = [
        "# Statistical Analysis Report\n",
        "## Summary\n",
        f"Total models compared: {len(comparison_df)}\n",
        "\n## Model Performance Rankings\n",
    ]

    # Sort by accuracy
    if "accuracy" in comparison_df.columns:
        sorted_df = comparison_df.sort_values("accuracy", ascending=False)
        for idx, row in sorted_df.iterrows():
            report_lines.append(
                f"- {row['model_name']}: accuracy={row['accuracy']:.4f}, f1={row.get('f1', 'N/A'):.4f}"
            )

    report_lines.extend(
        [
            "\n## Metric Correlations\n",
            "Correlations between different evaluation metrics:\n",
        ]
    )

    # Calculate correlations
    corr_matrix = calculate_metric_correlations(comparison_df)
    report_lines.append(corr_matrix.to_markdown())

    # Pairwise significance tests if predictions provided
    if significance_tests and predictions is not None and y_true is not None:
        report_lines.extend(
            [
                "\n## Pairwise Significance Tests (McNemar's Test)\n",
                "Comparing model predictions on test set:\n",
            ]
        )

        model_names = list(predictions.keys())
        for i in range(len(model_names)):
            for j in range(i + 1, len(model_names)):
                result = mcnemar_test(
                    y_true, predictions[model_names[i]], predictions[model_names[j]]
                )
                report_lines.append(
                    f"### {model_names[i]} vs {model_names[j]}\n"
                    f"- Statistic: {result['statistic']:.4f}\n"
                    f"- P-value: {result['p_value']:.4f}\n"
                    f"- Significant: {'Yes' if result['significant'] else 'No'}\n"
                    f"- Discordant pairs: b={result['b']}, c={result['c']}\n"
                    f"- Interpretation: {result['interpretation']}\n"
                )

    return "\n".join(report_lines)
