"""
Interactive Model Comparison Dashboard

This Streamlit app provides interactive visualizations for comparing
all trained models from MLflow experiments, including:
- Performance metrics comparison (accuracy, F1, precision, recall)
- Latency vs accuracy trade-off analysis
- Model size vs performance
- Metric correlations
- Statistical significance testing
- ROC curves and confusion matrices (when predictions available)
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

            # Add metrics
            for key, value in metrics.items():
                run_data[f"metric_{key}"] = value

            # Add key parameters
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

            # Add model name from tags or params
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


def plot_performance_comparison(
    df: pd.DataFrame, metric: str = "accuracy"
) -> go.Figure:
    """Create bar chart comparing models on a specific metric."""
    if f"metric_{metric}" not in df.columns:
        return go.Figure()

    plot_df = df[df["status"] == "FINISHED"].copy()
    if plot_df.empty:
        return go.Figure()

    # Sort by metric value
    plot_df = plot_df.sort_values(f"metric_{metric}", ascending=False)

    fig = px.bar(
        plot_df,
        x="model_name",
        y=f"metric_{metric}",
        color="experiment_name",
        title=f"Model Comparison: {metric.title()}",
        labels={f"metric_{metric}": metric.title(), "model_name": "Model"},
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

    # Add annotations for best models (top-right corner is ideal: high accuracy, low latency)
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
    if f"metric_{metric}" not in df.columns or "metric_model_size_mb" not in df.columns:
        return go.Figure()

    plot_df = df[df["status"] == "FINISHED"].copy()
    plot_df = plot_df.dropna(subset=[f"metric_{metric}", "metric_model_size_mb"])

    if plot_df.empty:
        return go.Figure()

    fig = px.scatter(
        plot_df,
        x="metric_model_size_mb",
        y=f"metric_{metric}",
        color="experiment_name",
        hover_data=["model_name", "run_id"],
        title=f"Model Size vs {metric.title()}",
        labels={
            "metric_model_size_mb": "Model Size (MB)",
            f"metric_{metric}": metric.title(),
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

    corr_df = calculate_metric_correlations(
        df[metric_cols].rename(columns=lambda x: x.replace("metric_", ""))
    )

    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        title="Metric Correlations",
        color_continuous_scale="RdBu",
        range_color=[-1, 1],
    )
    return fig


def plot_roc_curve_comparison(df: pd.DataFrame) -> go.Figure:
    """Plot ROC curves for models that have logged predictions."""
    # This would require actual predictions to be logged
    # Placeholder implementation
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

            if len(friedman_data) > 0:
                result = friedman_test(friedman_data)
                st.metric("p-value", f"{result['p_value']:.4f}")
                if result["significant"]:
                    st.success("✓ Significant differences detected")
                else:
                    st.info("No significant differences")

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

        if df.empty:
            st.warning("No experiment runs found in MLflow tracking.")
            st.info(
                "Run some experiments first using `python src/train.py` or the training scripts."
            )
            return

        # Display basic stats
        st.sidebar.metric("Total Runs", len(df))
        st.sidebar.metric("Completed", len(df[df["status"] == "FINISHED"]))
        st.sidebar.metric("Experiments", df["experiment_name"].nunique())

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
            st.warning("No metrics found in the logged runs.")
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
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col2:
            st.subheader("📦 Model Size vs Performance")
            size_metric = st.selectbox(
                "Select Metric for Size Comparison",
                [m for m in available_metrics if m != "inference_latency_ms"],
                index=available_metrics.index("f1") if "f1" in available_metrics else 0,
            )
            fig_size = plot_model_size_vs_performance(df, size_metric)
            st.plotly_chart(fig_size, use_container_width=True)

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
        display_df = df[display_cols].sort_values(
            by=[col for col in ["metric_accuracy", "metric_f1"] if col in df.columns],
            ascending=False,
        )
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

    # Footer
    st.markdown("---")
    st.markdown("Dashboard built with Streamlit | Data sourced from MLflow experiments")


if __name__ == "__main__":
    main()
