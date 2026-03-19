# MLFlow AI Experiment: Text Classification Model Comparison

## Overview
This project uses **MLFlow** to systematically compare state-of-the-art machine learning models for sentiment analysis on the IMDB movie reviews dataset. We evaluate both traditional ML approaches and modern transformer-based architectures to identify the optimal balance of accuracy, speed, and resource efficiency.

## Problem Statement
**Task**: Binary text classification (positive/negative sentiment) on 50,000 movie reviews.

**Goal**: Compare multiple model architectures and determine the best-performing model(s) based on:
- Accuracy and F1 score
- Inference latency
- Model size and memory footprint
- Training efficiency

**Detailed problem statement**: [docs/problem-statement.md](docs/problem-statement.md)

## Project Structure
```
.
├── README.md              # Project documentation
├── TASKS.md              # Development task tracking
├── requirements.txt      # Python dependencies
├── config.yaml           # MLflow and experiment configuration
├── setup_mlflow.py       # MLflow tracking setup script
├── .github/workflows/    # CI/CD pipelines
│   └── test.yml
├── docs/                 # Documentation and problem statement
│   └── problem-statement.md
├── src/                  # Source code
│   ├── models/          # Model implementations
│   ├── training.py      # Training pipeline
│   ├── evaluation.py    # Metrics computation
│   └── ...
├── data/                # Processed datasets
├── models/              # Saved model artifacts
├── experiments/         # Experiment configurations
├── notebooks/           # Jupyter notebooks for exploration
└── mlruns/              # MLFlow tracking data (auto-generated)
```

## Setup

### Prerequisites
- Python 3.9+
- Git

### Option 1: Using pip (system Python)
```bash
# Install dependencies directly into system Python
pip install -r requirements.txt

# Verify environment
python verify_environment.py
```

### Option 2: Using Conda (recommended for isolation)
```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate mlflow-ai-experiment

# Verify environment
python verify_environment.py
```

### Quick Start
1. Start MLflow tracking server:
   ```bash
   mlflow ui
   ```
   Open http://localhost:5000 in your browser.

2. Explore the notebooks:
   ```bash
   jupyter lab notebooks/01_data_exploration.ipynb
   ```

3. Run baseline training:
   ```bash
   python src/train.py --model logistic_regression --config config/baseline.yaml
   ```

## Usage

### Starting MLFlow UI
```bash
mlflow ui
```
Then open http://localhost:5000 in your browser.

### Running Experiments

#### Baseline Model (TF-IDF + Logistic Regression)
```bash
python scripts/run_baseline.py
```

#### Classical ML Models
```bash
# Train baseline model using classical pipeline
python src/train.py --model logistic_regression --config config.yaml

# Train other classical models
python src/train.py --model svm --config config.yaml
python src/train.py --model random_forest --config config.yaml
python src/train.py --model xgboost --config config.yaml
```

Or train all classical models at once with the comprehensive script:
```bash
python scripts/run_classical_models.py
```

This script trains all classical models (Logistic Regression, SVM, Random Forest, XGBoost) and generates a comparison table with all metrics logged to MLflow.

#### Transformer Models
The project now includes a unified transformer interface supporting multiple architectures:

```bash
# BERT base or large
python src/train.py --model bert --config config/transformer_bert.yaml
python src/train.py --model bert-large --config config/transformer_bert.yaml

# RoBERTa
python src/train.py --model roberta --config config/transformer_roberta.yaml

# DeBERTa (v3)
python src/train.py --model deberta --config config/transformer_deberta.yaml

# XLNet
python src/train.py --model xlnet --config config/transformer_xlnet.yaml

# Or use custom HuggingFace model names
python src/train.py --model distilbert-base-uncased --config config/transformer_distilbert.yaml
python src/train.py --model google/electra-base-discriminator --config config/transformer_electra.yaml
```

The transformer models are implemented in `src/models/transformers.py` with:
- Unified `TransformerModel` base class with consistent API
- Specific wrappers: `BERTModel`, `RoBERTaModel`, `DeBERTaModel`, `XLNetModel`
- Factory functions: `create_transformer_model()` and `create_transformer_model_from_name()`
- Support for custom classification heads with configurable dropout
 - Automatic MLflow logging with transformers flavor

### Viewing Dashboards & Analysis

#### Interactive Streamlit Dashboard
An interactive dashboard for model comparison and analysis:
```bash
streamlit run app/dashboard.py
```
Then open http://localhost:8501 in your browser.

The dashboard provides:
- Performance comparison across all models (bar charts)
- Latency vs accuracy trade-off analysis
- Model size vs performance visualizations
- Metric correlation heatmaps
- Statistical significance testing (Friedman test, bootstrap CIs)
- Exportable results tables

**Note**: The dashboard automatically loads data from MLflow. If insufficient data exists, it will display sample data for demonstration.

#### Jupyter Notebook Analysis
For detailed exploratory analysis:
```bash
jupyter lab notebooks/analysis.ipynb
```

The analysis notebook includes:
- Comprehensive data exploration
- Statistical testing (Friedman, Nemenyi, bootstrap)
- Correlation analysis
- Production deployment recommendations
- Key insights and visualizations

#### Documentation
Detailed model comparison report: [docs/model_comparison.md](docs/model_comparison.md)

### Evaluating Models

The project includes a comprehensive automated evaluation suite that computes all metrics (accuracy, precision, recall, F1, confusion matrix, inference latency, memory footprint) and logs them consistently.

#### Single Model Evaluation
```bash
python src/evaluate.py --model-path models/best_model/
```

#### Batch Evaluation & Comparison
Evaluate all models from an MLflow experiment and generate comparison tables:
```bash
python scripts/evaluate_all.py \
  --experiment-name "my_experiment" \
  --test-data data/test.csv \
  --output-dir comparison_results
```

Or evaluate specific runs:
```bash
python scripts/evaluate_all.py \
  --run-ids <run_id1> <run_id2> \
  --test-data data/test.csv
```

All results are automatically logged to MLflow and saved as CSV/JSON comparison tables.

## Data Pipeline Performance Benchmark

The project includes a comprehensive benchmark to measure data loading and preprocessing performance across different batch sizes and configurations.

### Running the Benchmark

```bash
# Install psutil if not already installed
pip install psutil

# Run the benchmark (logs results to MLFlow)
python scripts/benchmark_data.py
```

The benchmark measures:
- **Data loading**: Time and memory for loading IMDB dataset with different batch sizes
- **Classical preprocessing**: TF-IDF vectorization with various feature counts
- **Transformer tokenization**: BERT, RoBERTa, DistilBERT tokenization throughput

All results are automatically logged to MLFlow in the `data_pipeline_benchmarks` experiment.

### Viewing Results

```bash
# Start MLFlow UI
mlflow ui
# Open http://localhost:5000
```

Detailed analysis and recommendations are available in:
- [docs/data_performance.md](docs/data_performance.md)

### Benchmark Outputs

The script generates CSV files with detailed metrics and uploads them as MLFlow artifacts:
- `data_loading_benchmark.csv`
- `classical_preprocessing_benchmark.csv`
- `transformer_preprocessing_benchmark.csv`

## Model Categories

### Classical ML Models
- Logistic Regression (baseline)
- Support Vector Machines (SVM)
- Random Forest
- XGBoost
- LightGBM

### Transformer Models
The project includes a **unified transformer interface** with support for:

**Core architectures** (directly implemented):
- BERT (base, large, and any HuggingFace variant)
- RoBERTa (base, large)
- DeBERTa (v3 base/large)
- XLNet (base, large)

**Extended support** (any HuggingFace model):
- DistilBERT
- ELECTRA
- ALBERT
- GPT-2/3 for classification
- And any other text-classification model from HuggingFace Hub

All transformer models share the same API via `TransformerModel` base class with:
- Consistent training, prediction, and logging interfaces
- Customizable classification heads
- Automatic device management (CPU/GPU)
- MLflow transformers flavor integration

## Tracking Experiments
All experiments are automatically tracked in MLFlow with:
- Model parameters
- Performance metrics
- System metrics (inference time, memory usage)
- Model artifacts
- Dataset version information

## Data Utilities & Versioning

### Data Versioning (`src/data_versioning.py`)
The project implements checksum-based data versioning to ensure reproducibility:
- **Automatic version detection**: SHA-256 hashes of dataset content
- **Version manifest**: `data/version_manifest.yaml` stores checksums and timestamps
- **Integrity verification**: `verify_dataset_integrity()` ensures datasets haven't changed
- **Version string**: Compact format (e.g., `v1.0-a1b2c3d4`) for tracking

### MLFlow Data Logging (`src/data_utils.py`)
Comprehensive utilities to log data information to MLFlow:
- `log_dataset_statistics()`: Sample counts, class distribution, text lengths
- `log_preprocessing_parameters()`: Track preprocessing configuration
- `log_data_artifacts()`: Save dataset splits as artifacts (CSV/Parquet)
- `create_and_log_data_report()`: Generate markdown data reports
- `prepare_data_for_mlflow()`: All-in-one function for complete data logging

### Usage Example
```python
from mlflow_ai_experiment.data_loader import load_and_log_dataset

# Load data and automatically log to MLFlow with versioning
train_df, val_df, test_df = load_and_log_dataset(
    log_to_mlflow=True,
    preprocessing_params={
        "cleaning": "lowercase, remove_html",
        "tokenization": "bert-base-uncased",
    }
)
```

This automatically:
- Calculates dataset checksums
- Creates `data/version_manifest.yaml`
- Logs statistics, parameters, and artifacts to MLFlow
- Generates a comprehensive data report

## Current Status

**Phase 1: Planning & Setup** - ✓ Complete
- [x] Problem statement and requirements defined (see [docs/problem-statement.md](docs/problem-statement.md))
- [x] MLFlow tracking infrastructure setup
- [x] Development environment creation
- [x] Baseline model implementation

**Phase 2: Data Management & Preprocessing** - ✓ Complete
- [x] Dataset download and preparation
- [x] Text preprocessing pipeline
- [x] Data utilities for MLFlow logging
- [x] Data pipeline performance benchmarking

**Phase 3: Model Implementation & Training** - ✓ Complete
- [x] HuggingFace transformer integration
- [x] Classical ML model implementations
- [x] State-of-the-art models (ELECTRA, ALBERT, DistilBERT)
- [x] Unified training pipeline

**Phase 4: Experimentation, Logging & Analysis** - ✓ Complete
- [x] Comprehensive MLFlow experiment tracking
- [x] Hyperparameter optimization framework
- [x] Automated model evaluation suite
- [x] Interactive dashboards and visualizations
- [x] Final report and recommendations
- [x] Reproducibility framework
- [x] Model artifact management and export utilities

**Project Status: 100% COMPLETE** ✅

All deliverables have been successfully implemented and documented. See the [Final Report](docs/FINAL_REPORT.md) for comprehensive results and recommendations.

## Dependencies
Key dependencies (see [requirements.txt](requirements.txt) for complete list):
- `mlflow` - Experiment tracking and model registry
- `transformers` - HuggingFace transformer models
- `torch` or `tensorflow` - Deep learning backend
- `datasets` - HuggingFace datasets library
- `scikit-learn` - Classical ML algorithms
- `pandas`, `numpy` - Data manipulation
- `optuna` or `ray[tune]` - Hyperparameter optimization (optional)

## License
[Add license information here]

## Contact
[Add contact/team information here]
