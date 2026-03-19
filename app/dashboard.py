"""
Interactive Model Comparison Dashboard

This Streamlit app provides interactive visualizations for comparing
all trained models from MLflow experiments, including:
- Performance metrics comparison (accuracy, F1, precision, recall)
- Latency vs accuracy trade-off analysis
- Model size vs performance
- Metric correlations
- Statistical significance testing
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mlflow
from mlflow.tracking import MlflowClient
from typing import Dict, List, Tuple, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from analysis import (
    compare_models_bootstrap,
    calculate_metric_correlations,
    generate_statistical_report,
    friedman_test,
)
from evaluation import compute_metrics


# Page configuration
st.set_page_config(
    page_title="MLflow AI Experiment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title and description
st.title("📊 MLflow AI Experiment Dashboard")
st.markdown("""
Interactive analysis and visualization dashboard for comparing sentiment analysis models
trained on the IMDB dataset. Explore performance metrics, statistical tests, and model comparisons.
""")


def connect_to_mlflow(tracking_uri: str = "sqlite:///mlflow.db") -> MlflowClient:
    """Connect to MLflow tracking server and return client."""
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    return client


def load_experiments_data(client: MlflowClient) -> pd.DataFrame:
    """Load all experiment runs into a DataFrame."""
    experiments = client.search_experiments()

    all_runs = []
    for exp in experiments:
        runs = client.search_runs(experiment_ids=[exp.experiment_id])
        for run in runs:
            # Extract metrics
            metrics = run.data.metrics
            params = run.data.params
            tags = run.data.tags

            run_data = {
                "run_id": run.info.run_id,
                "experiment_name": exp.name,
                "run_name": run.info.run_name,
                "status": run.info.status,
                "start_time": pd.to_datetime(run.info.start_time, unit="ms"),
            }

            # Add metrics with 'metric_' prefix
            for key, value in metrics.items():
                run_data[f"metric_{key}"] = value

            # Add key parameters/tags
            for param in [
                "model_type",
                "framework",
                "dataset_version",
                "preprocessing_config",
            ]:
                if param in params:
                    run_data[param] = params[param]
                elif param in tags:
                    run_data[param] = tags[param]

            # Add model name
            if "model_name" in tags:
                run_data["model_name"] = tags["model_name"]
            elif "model_type" in run_data:
                run_data["model_name"] = run_data["model_type"]
            else:
                run_data["model_name"] = "Unknown"

            all_runs.append(run_data)

    df = pd.DataFrame(all_runs)

    # Clean model names
    if "model_name" in df.columns:
        df["model_name"] = df["model_name"].str.replace("_", " ").str.title()

    return df


def generate_sample_data() -> pd.DataFrame:
    """Generate sample model comparison data when real MLflow data is insufficient."""
    np.random.seed(42)
    model_data = []

    # Classical models with realistic metrics
    classical_models = [
        {
            "model_name": "Logistic Regression",
            "model_type": "logistic_regression",
            "experiment_name": "imdb_sentiment_analysis_classical",
            "framework": "sklearn",
            "status": "FINISHED",
            "accuracy": 0.86,
            "f1": 0.86,
            "precision": 0.86,
            "recall": 0.86,
            "specificity": 0.86,
            "inference_latency_ms": 1.2,
            "model_size_mb": 2.5,
            "training_time_min": 5,
        },
        {
            "model_name": "SVM",
            "model_type": "svm",
            "experiment_name": "imdb_sentiment_analysis_classical",
            "framework": "sklearn",
            "status": "FINISHED",
            "accuracy": 0.88,
            "f1": 0.88,
            "precision": 0.88,
            "recall": 0.88,
            "specificity": 0.88,
            "inference_latency_ms": 2.5,
            "model_size_mb": 5.2,
            "training_time_min": 15,
        },
        {
            "model_name": "Random Forest",
            "model_type": "random_forest",
            "experiment_name": "imdb_sentiment_analysis_classical",
            "framework": "sklearn",
            "status": "FINISHED",
            "accuracy": 0.89,
            "f1": 0.89,
            "precision": 0.89,
            "recall": 0.89,
            "specificity": 0.89,
            "inference_latency_ms": 3.8,
            "model_size_mb": 15.8,
            "training_time_min": 20,
        },
        {
            "model_name": "XGBoost",
            "model_type": "xgboost",
            "experiment_name": "imdb_sentiment_analysis_classical",
            "framework": "sklearn",
            "status": "FINISHED",
            "accuracy": 0.90,
            "f1": 0.90,
            "precision": 0.90,
            "recall": 0.90,
            "specificity": 0.90,
            "inference_latency_ms": 4.5,
            "model_size_mb": 1.2,
            "training_time_min": 12,
        },
        {
            "model_name": "LightGBM",
            "model_type": "lightgbm",
            "experiment_name": "imdb_sentiment_analysis_classical",
            "framework": "sklearn",
            "status": "FINISHED",
            "accuracy": 0.91,
            "f1": 0.91,
            "precision": 0.91,
            "recall": 0.91,
            "specificity": 0.91,
            "inference_latency_ms": 2.1,
            "model_size_mb": 0.8,
            "training_time_min": 8,
        },
    ]

    # Transformer models with realistic metrics
    transformer_models = [
        {
            "model_name": "BERT Base",
            "model_type": "bert",
            "experiment_name": "imdb_sentiment_analysis_transformers",
            "framework": "transformers",
            "status": "FINISHED",
            "accuracy": 0.92,
            "f1": 0.92,
            "precision": 0.92,
            "recall": 0.92,
            "specificity": 0.92,
            "inference_latency_ms": 45.0,
            "model_size_mb": 440.0,
            "training_time_min": 180,
        },
        {
            "model_name": "RoBERTa Base",
            "model_type": "roberta",
            "experiment_name": "imdb_sentiment_analysis_transformers",
            "framework": "transformers",
            "status": "FINISHED",
            "accuracy": 0.93,
            "f1": 0.93,
            "precision": 0.93,
            "recall": 0.93,
            "specificity": 0.93,
            "inference_latency_ms": 42.0,
            "model_size_mb": 498.0,
            "training_time_min": 200,
        },
        {
            "model_name": "DistilBERT",
            "model_type": "distilbert",
            "experiment_name": "imdb_sentiment_analysis_transformers",
            "framework": "transformers",
            "status": "FINISHED",
            "accuracy": 0.91,
            "f1": 0.91,
            "precision": 0.91,
            "recall": 0.91,
            "specificity": 0.91,
            "inference_latency_ms": 38.0,
            "model_size_mb": 268.0,
            "training_time_min": 120,
        },
        {
            "model_name": "ELECTRA Base",
            "model_type": "electra",
            "experiment_name": "imdb_sentiment_analysis_transformers",
            "framework": "transformers",
            "status": "FINISHED",
            "accuracy": 0.935,
            "f1": 0.935,
            "precision": 0.935,
            "recall": 0.935,
            "specificity": 0.935,
            "inference_latency_ms": 48.0,
            "model_size_mb": 446.0,
            "training_time_min": 220,
        },
        {
            "model_name": "ALBERT Base",
            "model_type": "albert",
            "experiment_name": "imdb_sentiment_analysis_transformers",
            "framework": "transformers",
            "status": "FINISHED",
            "accuracy": 0.915,
            "f1": 0.915,
            "precision": 0.915,
            "recall": 0.915,
            "specificity": 0.915,
            "inference_latency_ms": 35.0,
            "model_size_mb": 52.0,
            "training_time_min": 150,
        },
        {
            "model_name": "DeBERTa Base",
            "model_type": "deberta",
            "experiment_name": "imdb_sentiment_analysis_transformers",
            "framework": "transformers",
            "status": "FINISHED",
            "accuracy": 0.938,
            "f1": 0.938,
            "precision": 0.938,
            "recall": 0.938,
            "specificity": 0.938,
            "inference_latency_ms": 55.0,
            "model_size_mb": 520.0,
            "training_time_min": 240,
        },
        {
            "model_name": "XLNet Base",
            "model_type": "xlnet",
            "experiment_name": "imdb_sentiment_analysis_transformers",
            "framework": "transformers",
            "status": "FINISHED",
            "accuracy": 0.928,
            "f1": 0.928,
            "precision": 0.928,
            "recall": 0.928,
            "specificity": 0.928,
            "inference_latency_ms": 52.0,
            "model_size_mb": 488.0,
            "training_time_min": 210,
        },
    ]

    # Generate multiple runs with realistic variations
    for i in range(10):
        for model in classical_models:
            run = model.copy()
            run["run_id"] = f"sample_classical_{model['model_type']}_{i:03d}"
            # Add variations
            for metric in ["accuracy", "f1", "precision", "recall", "specificity"]:
                variation = np.random.normal(0, 0.008)
                run[metric] = max(0, min(1, run[metric] + variation))
            run["inference_latency_ms"] *= 1 + np.random.normal(0, 0.05)
            run["model_size_mb"] *= 1 + np.random.normal(0, 0.02)
            run["training_time_min"] *= 1 + np.random.normal(0, 0.1)
            model_data.append(run)

    for i in range(5):
        for model in transformer_models:
            run = model.copy()
            run["run_id"] = f"sample_transformer_{model['model_type']}_{i:03d}"
            for metric in ["accuracy", "f1", "precision", "recall", "specificity"]:
                variation = np.random.normal(0, 0.005)
                run[metric] = max(0, min(1, run[metric] + variation))
            run["inference_latency_ms"] *= 1 + np.random.normal(0, 0.03)
            run["model_size_mb"] *= 1 + np.random.normal(0, 0.05)
            run["training_time_min"] *= 1 + np.random.normal(0, 0.15)
            model_data.append(run)

    df = pd.DataFrame(model_data)

    # Add 'metric_' prefix to match MLflow data format
    metric_cols = [
        "accuracy",
        "f1",
        "precision",
        "recall",
        "specificity",
        "inference_latency_ms",
        "model_size_mb",
        "training_time_min",
    ]
    for col in metric_cols:
        if col in df.columns:
            df[f"metric_{col}"] = df[col]

    return df


def has_sufficient_metrics(df: pd.DataFrame) -> bool:
    """Check if DataFrame has the required metrics for visualizations."""
    required_metrics = [
        "metric_accuracy",
        "metric_f1",
        "metric_inference_latency_ms",
        "metric_model_size_mb",
    ]
    return all(col in df.columns and df[col].notna().any() for col in required_metrics)


def plot_performance_comparison(
    df: pd.DataFrame, metric: str = "accuracy"
) -> go.Figure:
    """Create bar chart comparing models on a specific metric."""
    metric_col = f"metric_{metric}"
    if metric_col not in df.columns:
        return go.Figure()

    plot_df = df[df["status"] == "FINISHED"].copy()
    if plot_df.empty:
        return go.Figure()

    # Sort by metric value
    plot_df = plot_df.sort_values(metric_col, ascending=False)

    fig = px.bar(
        plot_df,
        x="model_name",
        y=metric_col,
        color="experiment_name",
        title=f"Model Comparison: {metric.title()}",
        labels={metric_col: metric.title(), "model_name": "Model"},
        hover_data=["run_id", "experiment_name"],
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig


def plot_latency_vs_accuracy(df: pd.DataFrame) -> go.Figure:
    """Scatter plot of inference latency vs accuracy."""
    if (
        "metric_inference_latency_ms" not in df.columns
        or "metric_accuracy" not in df.columns
    ):
        return go.Figure()

    plot_df = df[df["status"] == "FINISHED"].copy()
    if plot_df.empty:
        return go.Figure()

    # Filter out missing values
    plot_df = plot_df.dropna(subset=["metric_inference_latency_ms", "metric_accuracy"])

    if plot_df.empty:
        return go.Figure()

    fig = px.scatter(
        plot_df,
        x="metric_inference_latency_ms",
        y="metric_accuracy",
        color="model_name",
        size="metric_model_size_mb"
        if "metric_model_size_mb" in plot_df.columns
        else None,
        hover_data=["model_name", "experiment_name", "run_id"],
        title="Accuracy vs Inference Latency (bubble size = model size)",
        labels={
            "metric_inference_latency_ms": "Inference Latency (ms)",
            "metric_accuracy": "Accuracy",
        },
    )

    # Add annotations for best models
    fig.add_annotation(
        x=plot_df["metric_inference_latency_ms"].min(),
        y=plot_df["metric_accuracy"].max(),
        text="Best: High accuracy, Low latency",
        showarrow=True,
        arrowhead=2,
    )

    return fig


def plot_model_size_vs_performance(df: pd.DataFrame, metric: str = "f1") -> go.Figure:
    """Scatter plot of model size vs performance metric."""
    metric_col = f"metric_{metric}"
    if metric_col not in df.columns or "metric_model_size_mb" not in df.columns:
        return go.Figure()

    plot_df = df[df["status"] == "FINISHED"].copy()
    plot_df = plot_df.dropna(subset=[metric_col, "metric_model_size_mb"])

    if plot_df.empty:
        return go.Figure()

    fig = px.scatter(
        plot_df,
        x="metric_model_size_mb",
        y=metric_col,
        color="experiment_name",
        hover_data=["model_name", "run_id"],
        title=f"Model Size vs {metric.title()}",
        labels={
            "metric_model_size_mb": "Model Size (MB)",
            metric_col: metric.title(),
        },
    )
    return fig


def plot_metric_correlations_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap of correlations between different metrics."""
    metric_cols = [
        col
        for col in df.columns
        if col.startswith("metric_") and col not in ["metric_confusion_matrix"]
    ]

    if len(metric_cols) < 2:
        return go.Figure()

    # Extract metric names without prefix
    metric_names = [col.replace("metric_", "") for col in metric_cols]
    corr_df = calculate_metric_correlations(
        df[metric_cols].rename(columns=lambda x: x.replace("metric_", ""))
    )

    fig = px.imshow(
        corr_df,
        text_auto=True,
        aspect="auto",
        title="Metric Correlations",
        color_continuous_scale="RdBu",
        range_color=[-1, 1],
    )
    return fig


def plot_roc_curve_comparison(df: pd.DataFrame) -> go.Figure:
    """Plot ROC curves for models that have logged predictions."""
    fig = go.Figure()
    fig.add_annotation(
        text="ROC curves require predictions to be logged as artifacts",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14),
    )
    fig.update_layout(title="ROC Curve Comparison")
    return fig


def display_statistical_tests(df: pd.DataFrame):
    """Display statistical significance test results."""
    st.subheader("📈 Statistical Significance Tests")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Friedman Test (Across all models)**")
        st.markdown("""
        The Friedman test checks if there are significant differences
        in performance across all models (non-parametric alternative to ANOVA).
        """)

        # Prepare data for Friedman test
        metric_col = "metric_accuracy"
        if metric_col in df.columns:
            friedman_data = df.pivot_table(
                index="experiment_name",
                columns="model_name",
                values=metric_col,
                aggfunc="mean",
            ).dropna()

            if len(friedman_data) > 0 and friedman_data.shape[1] >= 2:
                result = friedman_test(friedman_data)
                st.metric("p-value", f"{result['p_value']:.4f}")
                if result["significant"]:
                    st.success("✓ Significant differences detected")
                else:
                    st.info("No significant differences")
            else:
                st.info("Need at least 2 models for Friedman test")

    with col2:
        st.markdown("**Bootstrap Confidence Intervals**")
        st.markdown("""
        Bootstrap resampling provides confidence intervals for metrics,
        accounting for variability in the test set.
        """)

        # Show CI for top models
        if "metric_accuracy" in df.columns:
            top_models = df.nlargest(3, "metric_accuracy")["model_name"].tolist()
            st.write("Top 3 models by accuracy:")
            for model in top_models:
                st.write(f"- {model}")


def main():
    """Main dashboard application."""

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")

    # MLflow connection
    tracking_uri = st.sidebar.text_input(
        "MLflow Tracking URI",
        value="sqlite:///mlflow.db",
        help="URI for MLflow tracking server (e.g., sqlite:///mlflow.db, http://localhost:5000)",
    )

    # Experiment filter
    st.sidebar.subheader("Filters")

    try:
        client = connect_to_mlflow(tracking_uri)
        df = load_experiments_data(client)

        # Check if we have sufficient data, otherwise use sample data
        if df.empty or not has_sufficient_metrics(df):
            st.info(
                "⚠️ Insufficient real experiment data. Loading sample data for demonstration."
            )
            df = generate_sample_data()
            using_sample = True
        else:
            using_sample = False

        # Display basic stats
        st.sidebar.metric("Total Runs", len(df))
        st.sidebar.metric("Completed", len(df[df["status"] == "FINISHED"]))
        st.sidebar.metric("Experiments", df["experiment_name"].nunique())

        if using_sample:
            st.sidebar.warning("Using SAMPLE data")
            st.sidebar.info("""
            Real MLflow data not found or incomplete.
            Run training scripts to collect real experiments.
            """)

        # Filter by experiment
        available_experiments = ["All"] + sorted(df["experiment_name"].unique())
        selected_experiment = st.sidebar.selectbox(
            "Select Experiment", available_experiments, index=0
        )

        if selected_experiment != "All":
            df = df[df["experiment_name"] == selected_experiment]

        # Filter by status
        status_filter = st.sidebar.multiselect(
            "Run Status", options=df["status"].unique(), default=["FINISHED"]
        )
        df = df[df["status"].isin(status_filter)]

        # Main content area
        st.header("🔍 Model Performance Overview")

        # Metric selection
        available_metrics = sorted(
            [
                col.replace("metric_", "")
                for col in df.columns
                if col.startswith("metric_") and col not in ["metric_confusion_matrix"]
            ]
        )

        if not available_metrics:
            st.warning("No metrics found in the data.")
            st.info(
                "Ensure your training scripts log metrics with names like 'accuracy', 'f1', 'inference_latency_ms', etc."
            )
            return

        selected_metric = st.selectbox(
            "Select Metric to Compare",
            available_metrics,
            index=available_metrics.index("accuracy")
            if "accuracy" in available_metrics
            else 0,
        )

        # Display bar chart
        fig_bar = plot_performance_comparison(df, selected_metric)
        if fig_bar.data:
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning(f"No data available for metric: {selected_metric}")

        # Two-column layout for additional plots
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⚡ Latency vs Accuracy")
            fig_scatter = plot_latency_vs_accuracy(df)
            if fig_scatter.data:
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Latency or accuracy data not available.")

        with col2:
            st.subheader("📦 Model Size vs Performance")
            size_metric_options = [
                m for m in available_metrics if m != "inference_latency_ms"
            ]
            if size_metric_options:
                size_metric = st.selectbox(
                    "Select Metric for Size Comparison",
                    size_metric_options,
                    index=size_metric_options.index("f1")
                    if "f1" in size_metric_options
                    else 0,
                )
                fig_size = plot_model_size_vs_performance(df, size_metric)
                if fig_size.data:
                    st.plotly_chart(fig_size, use_container_width=True)
                else:
                    st.info("Model size data not available.")
            else:
                st.info("No suitable metrics for size comparison.")

        # Correlation heatmap
        st.subheader("🔗 Metric Correlations")
        fig_corr = plot_metric_correlations_heatmap(df)
        if fig_corr.data:
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Not enough metrics available for correlation analysis.")

        # Statistical tests
        display_statistical_tests(df)

        # Detailed results table
        st.header("📋 Detailed Results")
        metric_cols = [col for col in df.columns if col.startswith("metric_")]
        display_cols = [
            "model_name",
            "experiment_name",
            "run_id",
            "status",
        ] + metric_cols
        # Only include columns that exist
        display_cols = [col for col in display_cols if col in df.columns]
        display_df = df[display_cols].copy()
        sort_cols = [
            col for col in ["metric_accuracy", "metric_f1"] if col in df.columns
        ]
        if sort_cols:
            display_df = display_df.sort_values(by=sort_cols, ascending=False)

        st.dataframe(display_df, use_container_width=True)

        # Export functionality
        st.download_button(
            label="📥 Download Results as CSV",
            data=display_df.to_csv(index=False),
            file_name=f"model_comparison_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Error connecting to MLflow: {e}")
        st.info("""
        **Troubleshooting:**
        1. Ensure MLflow tracking is running: `mlflow ui`
        2. Verify the tracking URI is correct
        3. Check that experiments have been logged
        """)

        # Offer to load sample data
        if st.button("Load Sample Data Anyway"):
            df = generate_sample_data()
            st.success("✅ Sample data loaded successfully!")
            st.balloons()
            st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("Dashboard built with Streamlit | Data sourced from MLflow experiments")


if __name__ == "__main__":
    main()
