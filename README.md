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

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mlflow-ai-experiment
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify installation:
   ```bash
   python -c "import mlflow; print(f'MLFlow version: {mlflow.__version__}')"
   ```

## Usage

### Starting MLFlow UI
```bash
mlflow ui
```
Then open http://localhost:5000 in your browser.

### Running Experiments
```bash
# Train baseline model
python src/train.py --model logistic_regression --config config/baseline.yaml

# Train transformer model
python src/train.py --model bert --config config/bert.yaml
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
**Phase 1: Planning & Setup** - In Progress
- [x] Problem statement and requirements defined (see [docs/problem-statement.md](docs/problem-statement.md))
- [ ] MLFlow tracking infrastructure setup
- [ ] Development environment creation
- [ ] Baseline model implementation

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
