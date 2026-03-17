"""
Data pipeline performance benchmark script.
Measures data loading times, preprocessing throughput, and memory usage for different batch sizes.
"""

import sys
import os
import time
import gc
import psutil
import pandas as pd
from datasets import load_dataset
from sklearn.model_selection import train_test_split
import mlflow

# Add project root to path for absolute imports
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.preprocessing import preprocess_classical, clean_text
from src.tokenizers import TransformerTokenizer
from src.data_loader import load_imdb_dataset


def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def benchmark_data_loading(batch_sizes=[1000, 5000, 10000, 25000]):
    """
    Benchmark data loading performance with different batch sizes.

    Args:
        batch_sizes: List of batch sizes to test (number of samples to load at once)

    Returns:
        DataFrame with timing results for each batch size
    """
    print("\n" + "=" * 80)
    print("BENCHMARK: Data Loading")
    print("=" * 80)

    results = []

    for batch_size in batch_sizes:
        print(f"\nTesting batch size: {batch_size}")

        gc.collect()

        start_time = time.time()
        start_memory = get_memory_usage()

        # Load dataset - simulate batch loading by using slicing
        dataset = load_dataset("imdb")

        # Simulate batch loading: get first N samples from train split
        train_data = dataset["train"].select(
            range(min(batch_size, len(dataset["train"])))
        )

        # Perform train/val split
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            train_data["text"],
            train_data["label"],
            test_size=0.1,
            random_state=42,
            stratify=train_data["label"],
        )

        end_time = time.time()
        end_memory = get_memory_usage()

        elapsed = end_time - start_time
        memory_delta = end_memory - start_memory
        samples_loaded = len(train_texts) + len(val_texts)

        results.append(
            {
                "batch_size": batch_size,
                "load_time_seconds": round(elapsed, 4),
                "samples_loaded": samples_loaded,
                "throughput_samples_per_second": round(samples_loaded / elapsed, 2)
                if elapsed > 0
                else 0,
                "memory_delta_mb": round(memory_delta, 2),
                "total_memory_mb": round(end_memory, 2),
            }
        )

        print(f"  Load time: {elapsed:.4f}s")
        print(f"  Samples loaded: {samples_loaded}")
        print(f"  Throughput: {samples_loaded / elapsed:.2f} samples/sec")
        print(f"  Memory delta: {memory_delta:.2f} MB")

    return pd.DataFrame(results)


def benchmark_classical_preprocessing(
    batch_sizes=[1000, 5000], max_features_list=[1000, 5000, 10000]
):
    """
    Benchmark classical preprocessing (TF-IDF) with different batch sizes and feature counts.
    """
    print("\n" + "=" * 80)
    print("BENCHMARK: Classical Preprocessing (TF-IDF)")
    print("=" * 80)

    results = []

    # Load full dataset once
    print("\nLoading dataset...")
    train_df, val_df, test_df = load_imdb_dataset()
    full_train_size = len(train_df)
    print(f"Full training set size: {full_train_size} samples")

    for batch_size in batch_sizes:
        if batch_size > full_train_size:
            print(f"\nSkipping batch size {batch_size} (exceeds dataset size)")
            continue

        for max_features in max_features_list:
            print(f"\nTesting batch_size={batch_size}, max_features={max_features}")

            # Take a subset of data
            subset_train = train_df.head(batch_size)
            subset_val = val_df.head(min(batch_size // 10, len(val_df)))

            # Clean text
            gc.collect()
            start_time = time.time()
            start_memory = get_memory_usage()

            # Clean text
            subset_train["cleaned_text"] = subset_train["text"].apply(clean_text)
            subset_val["cleaned_text"] = subset_val["text"].apply(clean_text)

            cleaning_time = time.time() - start_time
            cleaning_memory = get_memory_usage() - start_memory

            # Create TF-IDF features
            from sklearn.feature_extraction.text import TfidfVectorizer

            vectorizer = TfidfVectorizer(
                max_features=max_features,
                ngram_range=(1, 2),
                stop_words="english",
                min_df=1,
                max_df=0.7,
            )

            X_train = vectorizer.fit_transform(subset_train["cleaned_text"].tolist())
            X_val = vectorizer.transform(subset_val["cleaned_text"].tolist())

            total_time = time.time() - start_time
            total_memory = get_memory_usage() - start_memory

            # Calculate throughput
            total_samples = len(subset_train) + len(subset_val)
            throughput = total_samples / total_time if total_time > 0 else 0

            results.append(
                {
                    "batch_size": batch_size,
                    "max_features": max_features,
                    "cleaning_time_seconds": round(cleaning_time, 4),
                    "total_time_seconds": round(total_time, 4),
                    "samples_processed": total_samples,
                    "throughput_samples_per_second": round(throughput, 2),
                    "memory_delta_mb": round(total_memory, 2),
                    "feature_matrix_shape": str(X_train.shape),  # type: ignore
                }
            )

            print(f"  Cleaning time: {cleaning_time:.4f}s")
            print(f"  Total preprocessing time: {total_time:.4f}s")
            print(f"  Throughput: {throughput:.2f} samples/sec")
            print(f"  Memory delta: {total_memory:.2f} MB")
            print(f"  Feature matrix shape: {X_train.shape}")  # type: ignore

    return pd.DataFrame(results)


def benchmark_transformer_preprocessing(
    batch_sizes=[100, 500, 1000], model_names=["bert", "distilbert", "roberta"]
):
    """
    Benchmark transformer tokenization with different batch sizes and models.
    """
    print("\n" + "=" * 80)
    print("BENCHMARK: Transformer Preprocessing (Tokenization)")
    print("=" * 80)

    results = []

    # Load dataset
    print("\nLoading dataset...")
    train_df, val_df, test_df = load_imdb_dataset()
    full_train_size = len(train_df)
    print(f"Full training set size: {full_train_size} samples")

    for model_name in model_names:
        print(f"\n{'=' * 60}")
        print(f"Testing model: {model_name}")
        print(f"{'=' * 60}")

        for batch_size in batch_sizes:
            if batch_size > full_train_size:
                print(f"\nSkipping batch size {batch_size} (exceeds dataset size)")
                continue

            print(f"\nTesting batch_size={batch_size}")

            # Take subset of data
            subset_train = train_df.head(batch_size)
            subset_val = val_df.head(min(batch_size // 10, len(val_df)))

            gc.collect()
            start_time = time.time()
            start_memory = get_memory_usage()

            try:
                # Tokenize
                tokenizer = TransformerTokenizer(
                    model_name=model_name, max_length=128, padding=True, truncation=True
                )

                # Tokenize in batches to simulate realistic pipeline
                all_input_ids = []
                all_attention_masks = []

                # Process in mini-batches to avoid memory issues
                mini_batch_size = 32
                for i in range(0, len(subset_train), mini_batch_size):
                    batch_texts = (
                        subset_train["text"].iloc[i : i + mini_batch_size].tolist()
                    )
                    tokenized = tokenizer.tokenize(batch_texts)
                    all_input_ids.extend(tokenized["input_ids"])
                    all_attention_masks.extend(tokenized["attention_mask"])

                total_time = time.time() - start_time
                total_memory = get_memory_usage() - start_memory

                # Calculate throughput
                total_samples = len(subset_train)
                throughput = total_samples / total_time if total_time > 0 else 0

                results.append(
                    {
                        "model_name": model_name,
                        "batch_size": batch_size,
                        "tokenization_time_seconds": round(total_time, 4),
                        "samples_tokenized": total_samples,
                        "throughput_samples_per_second": round(throughput, 2),
                        "memory_delta_mb": round(total_memory, 2),
                        "max_length": 128,
                        "mini_batch_size": mini_batch_size,
                    }
                )

                print(f"  Tokenization time: {total_time:.4f}s")
                print(f"  Throughput: {throughput:.2f} samples/sec")
                print(f"  Memory delta: {total_memory:.2f} MB")

            except Exception as e:
                print(f"  ERROR: {str(e)}")
                results.append(
                    {
                        "model_name": model_name,
                        "batch_size": batch_size,
                        "tokenization_time_seconds": None,
                        "samples_tokenized": 0,
                        "throughput_samples_per_second": 0,
                        "memory_delta_mb": None,
                        "max_length": 128,
                        "mini_batch_size": 32,
                        "error": str(e),
                    }
                )

    return pd.DataFrame(results)


def main():
    """Run all benchmarks and log to MLFlow."""
    print("=" * 80)
    print("DATA PIPELINE PERFORMANCE BENCHMARK")
    print("=" * 80)

    # Set up MLFlow
    mlflow.set_tracking_uri("mlruns")
    experiment_name = "data_pipeline_benchmarks"

    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
        else:
            experiment_id = experiment.experiment_id
        mlflow.set_experiment(experiment_id)
    except Exception as e:
        print(f"Warning: MLFlow setup error: {e}")

    with mlflow.start_run(run_name="benchmark_run"):
        # Run benchmarks
        data_loading_results = benchmark_data_loading()
        classical_results = benchmark_classical_preprocessing()
        transformer_results = benchmark_transformer_preprocessing()

        # Log results to MLFlow
        print("\n" + "=" * 80)
        print("LOGGING RESULTS TO MLFlow")
        print("=" * 80)

        # Log data loading metrics
        for _, row in data_loading_results.iterrows():
            mlflow.log_metric(
                f"data_loading_time_batch_{row['batch_size']}",
                float(row["load_time_seconds"]),  # type: ignore
            )
            mlflow.log_metric(
                f"data_loading_throughput_batch_{row['batch_size']}",
                float(row["throughput_samples_per_second"]),  # type: ignore
            )
            mlflow.log_metric(
                f"data_loading_memory_batch_{row['batch_size']}",
                float(row["memory_delta_mb"]),  # type: ignore
            )

        # Log classical preprocessing metrics
        for _, row in classical_results.iterrows():
            key = f"classical_batch{int(row['batch_size'])}_features{int(row['max_features'])}"
            mlflow.log_metric(f"classical_time_{key}", float(row["total_time_seconds"]))  # type: ignore
            mlflow.log_metric(
                f"classical_throughput_{key}",
                float(row["throughput_samples_per_second"]),  # type: ignore
            )
            mlflow.log_metric(f"classical_memory_{key}", float(row["memory_delta_mb"]))  # type: ignore

        # Log transformer preprocessing metrics
        for _, row in transformer_results.iterrows():
            tokenization_time = row["tokenization_time_seconds"]
            # Check if tokenization_time is NaN or None
            if tokenization_time is None or (
                isinstance(tokenization_time, float) and pd.isna(tokenization_time)
            ):
                continue
            key = f"transformer_{row['model_name']}_batch{int(row['batch_size'])}"
            mlflow.log_metric(f"tokenization_time_{key}", float(tokenization_time))  # type: ignore
            mlflow.log_metric(
                f"tokenization_throughput_{key}",
                float(row["throughput_samples_per_second"]),  # type: ignore
            )
            mlflow.log_metric(
                f"tokenization_memory_{key}",
                float(row["memory_delta_mb"]),  # type: ignore
            )

        # Save results as CSV artifacts
        data_loading_results.to_csv("data_loading_benchmark.csv", index=False)
        classical_results.to_csv("classical_preprocessing_benchmark.csv", index=False)
        transformer_results.to_csv(
            "transformer_preprocessing_benchmark.csv", index=False
        )

        mlflow.log_artifact("data_loading_benchmark.csv")
        mlflow.log_artifact("classical_preprocessing_benchmark.csv")
        mlflow.log_artifact("transformer_preprocessing_benchmark.csv")

        print("\nBenchmark complete!")
        print(f"MLFlow experiment: {experiment_name}")
        active_run = mlflow.active_run()
        if active_run:
            print(f"Run ID: {active_run.info.run_id}")
        else:
            print("Run ID: N/A (no active run)")

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        print("\nData Loading Performance:")
        print(data_loading_results.to_string(index=False))

        print("\nClassical Preprocessing Performance:")
        print(
            classical_results[
                [
                    "batch_size",
                    "max_features",
                    "total_time_seconds",
                    "throughput_samples_per_second",
                    "memory_delta_mb",
                ]
            ].to_string(index=False)
        )

        print("\nTransformer Preprocessing Performance:")
        print(
            transformer_results[
                [
                    "model_name",
                    "batch_size",
                    "tokenization_time_seconds",
                    "throughput_samples_per_second",
                    "memory_delta_mb",
                ]
            ].to_string(index=False)
        )

        # Clean up temporary files
        for f in [
            "data_loading_benchmark.csv",
            "classical_preprocessing_benchmark.csv",
            "transformer_preprocessing_benchmark.csv",
        ]:
            if os.path.exists(f):
                os.remove(f)


if __name__ == "__main__":
    main()
