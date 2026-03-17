import argparse
import yaml
import logging
from sklearn.model_selection import train_test_split
from datasets import load_dataset
from .training import Trainer
from .preprocessing import create_tfidf_features
from .tokenizers import TransformerTokenizer

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Unified training pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="config/training.yaml",
        help="Path to training configuration YAML",
    )
    parser.add_argument(
        "--data-config",
        type=str,
        default="config.yaml",
        help="Path to data configuration YAML (optional if training config includes 'data')",
    )
    args = parser.parse_args()

    # Load training config
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    # Load data config (either from separate file or from training config)
    data_config = config.get("data")
    if data_config is None:
        with open(args.data_config, "r") as f:
            full_config = yaml.safe_load(f)
            data_config = full_config.get("data", {})
            # Merge training section for random seed
            if "training" in full_config and "random_seed" not in config:
                config["random_seed"] = full_config["training"].get("random_seed", 42)

    model_type = config.get("model_type", "transformer")
    random_seed = config.get("random_seed", 42)

    logger.info(f"Loading dataset: {data_config.get('dataset_name', 'imdb')}")
    dataset = load_dataset(data_config["dataset_name"])
    train_data = dataset[data_config["train_split"]]
    test_data = dataset[data_config["test_split"]]

    # Split training data into train and validation
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        train_data["text"],
        train_data["label"],
        test_size=data_config["validation_split_ratio"],
        random_state=random_seed,
        stratify=train_data["label"],
    )

    logger.info(
        f"Dataset splits: train={len(train_texts)}, val={len(val_texts)}, test={len(test_data)}"
    )

    # Preprocess data based on model type
    if model_type == "classical":
        # Classical models need TF-IDF features
        preprocess_config = config.get("preprocessing", {})
        max_features = preprocess_config.get("max_features", 5000)
        ngram_range = tuple(preprocess_config.get("ngram_range", [1, 2]))
        min_df = preprocess_config.get("min_df", 5)

        features = create_tfidf_features(
            train_texts=list(train_texts),
            val_texts=list(val_texts),
            test_texts=list(test_data["text"]),
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
        )

        # Prepare train/val datasets as (X, y) tuples
        train_dataset = (features["X_train"], train_labels)
        valid_dataset = (features["X_val"], val_labels)
        test_dataset = (features["X_test"], test_data["label"])

    elif model_type == "transformer":
        # Transformer models need tokenized datasets
        model_config = config.get("model", {})
        model_name = model_config.get("model_name", "bert-base-uncased")
        max_length = model_config.get("max_seq_length", 512)

        tokenizer = TransformerTokenizer(
            model_name=model_name,
            max_length=max_length,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )

        # Tokenize all splits
        tokenized = tokenizer.tokenize_dataset(
            train_texts=list(train_texts),
            val_texts=list(val_texts),
            test_texts=list(test_data["text"]),
        )

        # Create torch Dataset
        from torch.utils.data import Dataset

        class TextDataset(Dataset):
            def __init__(self, encodings, labels):
                self.encodings = encodings
                self.labels = labels

            def __len__(self):
                return len(self.labels)

            def __getitem__(self, idx):
                item = {key: val[idx] for key, val in self.encodings.items()}
                item["labels"] = self.labels[idx]
                return item

        train_dataset = TextDataset(tokenized["train"], train_labels)
        valid_dataset = TextDataset(tokenized["val"], val_labels)
        test_dataset = TextDataset(tokenized["test"], test_data["label"])

    else:
        raise ValueError(f"Unsupported model_type: {model_type}")

    # Initialize trainer
    trainer = Trainer(config, model_type=model_type)

    # Train
    logger.info("Starting training...")
    results = trainer.train(train_dataset, valid_dataset)
    print(f"Training completed. Metrics: {results}")

    # Evaluate on test set
    logger.info("Evaluating on test set...")
    test_metrics = trainer.evaluate(test_dataset)
    print(f"Test metrics: {test_metrics}")


if __name__ == "__main__":
    main()
