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
 - [ ] Data utilities for MLFlow logging
 - [ ] Data pipeline performance benchmarking

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
