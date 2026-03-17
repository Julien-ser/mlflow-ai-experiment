# Problem Statement: Text Classification with MLFlow

## Domain Selection
**Text Classification** using the **IMDB movie reviews dataset** for **sentiment analysis**.

## Dataset
- **Dataset**: IMDB Movie Reviews
- **Source**: HuggingFace `datasets` library (`imdb` dataset)
- **Task**: Binary sentiment classification (positive/negative reviews)
- **Size**: 50,000 reviews (25,000 train, 25,000 test)
- **Features**: Raw text reviews with corresponding sentiment labels

## Problem Definition
Train and compare multiple state-of-the-art machine learning models to perform sentiment analysis on movie reviews. The goal is to identify which model(s) provide the best balance of accuracy, speed, and resource efficiency for this specific NLP task.

## Evaluation Metrics
Primary metrics to be tracked and compared:

1. **Accuracy**: Overall classification accuracy
2. **F1 Score**: Harmonic mean of precision and recall (balanced metric)
3. **Inference Time**: Average time per prediction (milliseconds)
4. **Memory Footprint**: Model size and RAM usage during inference
5. **Training Time**: Total training duration
6. **Precision & Recall**: Per-class metrics for detailed analysis

## Baseline Expectations
- **Baseline Model**: TF-IDF + Logistic Regression
- **Expected Baseline Accuracy**: ~85-88%
- **Expected Baseline F1**: ~85-88%
- **Success Criteria**:
  - At least 3 transformer-based models (BERT, RoBERTa, DistilBERT) should outperform baseline by ≥2%
  - At least 1 model should achieve >90% accuracy
  - Inference time for best model should be <100ms on CPU
  - Complete MLFlow tracking for all experiments with consistent metrics

## Scope
- Compare classical ML models (Logistic Regression, SVM, Random Forest, XGBoost)
- Compare transformer models (BERT, RoBERTa, DeBERTa, XLNet, ELECTRA, ALBERT, DistilBERT)
- Include model size and inference speed in final recommendations
- Provide reproducibility through MLFlow experiment tracking

## Deliverables
- Trained and evaluated models across multiple architectures
- Comprehensive MLFlow experiment comparison dashboard
- Final report with recommendations based on accuracy vs. efficiency tradeoffs
- Best 3 models saved and documented for deployment
