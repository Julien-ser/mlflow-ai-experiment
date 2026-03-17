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
```

#### Transformer Models
```bash
python src/train.py --model bert --config config.yaml
```

### Evaluating Models
```bash
python src/evaluate.py --model-path models/best_model/
```

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

### Transformer Models
- BERT (base and large)
- RoBERTa
- DistilBERT
- DeBERTa
- XLNet
- ELECTRA
- ALBERT

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
from src.data_loader import load_and_log_dataset

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
  - `config.yaml` with experiment parameters
  - `setup_mlflow.py` script to initialize tracking
  - Project directory structure created
- [x] Development environment creation
  - `requirements.txt` with all core dependencies
  - `environment.yml` for Conda users
  - `verify_environment.py` script for validation
- [x] Baseline model implementation
  - `src/baseline.py` with TF-IDF + Logistic Regression
  - Project structure complete with `src/`, `data/`, `models/`, `experiments/`, `notebooks/`

  **Phase 2: Data Management & Preprocessing** - In Progress
  - [x] Dataset download and preparation
    - IMDB dataset downloaded using HuggingFace `datasets` library
    - Train/validation/test splits created (22,501 / 2,501 / 25,001 samples)
    - Processed files saved in `data/` as CSV
    - Data exploration notebook: `notebooks/01_data_exploration.ipynb`
    - Dataset loading utility: `src/data_loader.py`
  - [x] Text preprocessing pipeline
    - Modular preprocessing functions: `src/preprocessing.py`
    - Tokenization strategies for classical ML (TF-IDF) and transformers (BERT, RoBERTa, DistilBERT, etc.)
    - Unified interface: `preprocess_dataset()` supporting both modes
    - Comprehensive test suite: `tests/test_preprocessing.py` (26 tests passing)
  - [x] Data utilities for MLFlow logging ✓ **COMPLETED**
    - **Data versioning**: Checksum-based versioning system (`src/data_versioning.py`)
      - SHA-256 hashes for dataset splits
      - Automatic version manifest generation (`data/version_manifest.yaml`)
      - Dataset integrity verification
    - **MLFlow logging utilities**: (`src/data_utils.py`)
      - Dataset statistics logging (sample counts, class distribution, text lengths)
      - Preprocessing parameters tracking
      - Dataset artifact storage (CSV/Parquet)
      - Comprehensive data reports in Markdown format
      - One-command logging: `prepare_data_for_mlflow()`
    - **Enhanced data loader**: `src/data_loader.py` now includes:
      - `load_and_log_dataset()` function for automatic MLFlow logging
      - Integrated versioning and manifest creation
    - Updated `scripts/prepare_data.py` to use new logging features
   - [x] Data pipeline performance benchmarking ✓ **COMPLETED**
     - Created benchmark script: `scripts/benchmark_data.py`
     - Benchmarks cover data loading, classical preprocessing (TF-IDF), and transformer tokenization
     - Performance metrics logged to MLFlow experiment `data_pipeline_benchmarks`
     - Documentation: [docs/data_performance.md](docs/data_performance.md)
     - Results provide optimization recommendations for batch sizes and model selection

See [TASKS.md](TASKS.md) for full task list.

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
