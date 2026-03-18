# Example Hyperparameter Optimization Results

This document presents example results from running hyperparameter optimization on the IMDB dataset.

## Classical Models

| Model                | Best Accuracy | Best Params                                              |
|----------------------|---------------|----------------------------------------------------------|
| Logistic Regression  | 0.85          | C=0.5, max_iter=1000, solver='liblinear'               |
| SVM                  | 0.84          | C=1.2, max_iter=2000                                     |
| Random Forest        | 0.83          | n_estimators=200, max_depth=15, min_samples_split=5     |
| XGBoost              | 0.86          | n_estimators=150, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.9 |

## Transformer Models

| Model       | Best Accuracy | Best Params                                                                                  |
|-------------|---------------|----------------------------------------------------------------------------------------------|
| BERT        | 0.89          | lr=2e-5, batch_size=16, dropout=0.2, epochs=3, weight_decay=0.01, warmup_steps=500, max_seq_length=256 |
| RoBERTa     | 0.90          | lr=1.5e-5, batch_size=32, dropout=0.15, epochs=4, weight_decay=0.005, warmup_steps=300, max_seq_length=512 |

*Note: These are illustrative examples. Actual results may vary based on data and compute resources.*
