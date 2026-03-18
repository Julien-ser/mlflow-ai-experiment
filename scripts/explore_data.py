"""
Data exploration script for IMDB dataset.
Run this script to generate exploration statistics and visualizations.
"""

import pandas as pd  # type: ignore
import matplotlib.pyplot as plt
import seaborn as sns  # type: ignore
from collections import Counter
import re
import json
import os

# Set style for plots
plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette("husl")


def load_dataset_splits(data_dir="data"):
    """Load train, validation, and test splits."""
    train_df = pd.read_csv(f"{data_dir}/train.csv")
    val_df = pd.read_csv(f"{data_dir}/validation.csv")
    test_df = pd.read_csv(f"{data_dir}/test.csv")
    return train_df, val_df, test_df


def add_text_features(df):
    """Add text-based features to dataframe."""
    df = df.copy()
    df["text_length"] = df["text"].apply(len)
    df["word_count"] = df["text"].apply(lambda x: len(x.split()))
    df["unique_word_count"] = df["text"].apply(lambda x: len(set(x.lower().split())))
    return df


def build_vocabulary(texts):
    """Extract all words from text corpus."""
    all_words = []
    for text in texts:
        # Simple tokenization: lowercase and split on non-alphanumeric
        words = re.findall(r"\b[a-z]+\b", text.lower())
        all_words.extend(words)
    return Counter(all_words)


def plot_class_distribution(
    train, val, test, output_path="docs/class_distribution.png"
):
    """Plot class distribution for all splits."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    for idx, (df, title) in enumerate(
        zip([train, val, test], ["Train", "Validation", "Test"])
    ):
        class_counts = df["label"].value_counts()
        axes[idx].pie(
            class_counts.values,
            labels=["Negative (0)", "Positive (1)"],
            autopct="%1.1f%%",
            startangle=90,
            colors=["#ff9999", "#66b3ff"],
        )
        axes[idx].set_title(
            f"{title} Set - Class Distribution\n(Total: {len(df)} samples)"
        )

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Class distribution plot saved to {output_path}")
    plt.show()


def plot_text_analysis(train_df, output_prefix="docs/text_analysis"):
    """Plot various text analysis visualizations."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Histogram of text lengths
    axes[0, 0].hist(
        train_df["text_length"], bins=50, edgecolor="black", alpha=0.7, color="#3498db"
    )
    axes[0, 0].axvline(
        train_df["text_length"].mean(),
        color="red",
        linestyle="--",
        label=f"Mean: {train_df['text_length'].mean():.0f}",
    )
    axes[0, 0].axvline(
        train_df["text_length"].median(),
        color="green",
        linestyle="--",
        label=f"Median: {train_df['text_length'].median():.0f}",
    )
    axes[0, 0].set_xlabel("Text Length (characters)")
    axes[0, 0].set_ylabel("Frequency")
    axes[0, 0].set_title("Train Set: Text Length Distribution")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Box plot of text lengths by class
    sns.boxplot(data=train_df, x="label", y="text_length", ax=axes[0, 1])
    axes[0, 1].set_xticklabels(["Negative", "Positive"])
    axes[0, 1].set_xlabel("Sentiment")
    axes[0, 1].set_ylabel("Text Length (characters)")
    axes[0, 1].set_title("Text Length by Sentiment Class")

    # Word count distribution
    axes[1, 0].hist(
        train_df["word_count"], bins=50, edgecolor="black", alpha=0.7, color="#2ecc71"
    )
    axes[1, 0].axvline(
        train_df["word_count"].mean(),
        color="red",
        linestyle="--",
        label=f"Mean: {train_df['word_count'].mean():.0f}",
    )
    axes[1, 0].set_xlabel("Word Count")
    axes[1, 0].set_ylabel("Frequency")
    axes[1, 0].set_title("Train Set: Word Count Distribution")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Scatter: text length vs unique words
    scatter = axes[1, 1].scatter(
        train_df["text_length"],
        train_df["unique_word_count"],
        c=train_df["label"],
        cmap="coolwarm",
        alpha=0.5,
        s=10,
    )
    axes[1, 1].set_xlabel("Text Length (characters)")
    axes[1, 1].set_ylabel("Unique Word Count")
    axes[1, 1].set_title("Text Length vs. Unique Words (colored by sentiment)")
    axes[1, 1].grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=axes[1, 1], label="Sentiment (0=Neg, 1=Pos)")

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_prefix), exist_ok=True)
    plt.savefig(f"{output_prefix}.png", dpi=150, bbox_inches="tight")
    print(f"Text analysis plots saved to {output_prefix}.png")
    plt.show()


def check_data_quality(train_df, val_df, test_df):
    """Perform data quality checks."""
    print("\n=== DATA QUALITY CHECKS ===\n")

    all_dfs = [("Train", train_df), ("Validation", val_df), ("Test", test_df)]

    # Missing values
    print("Missing Values:")
    for name, df in all_dfs:
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(f"  {name}: {missing.sum()} missing values")
            print(f"    Details: {missing[missing > 0].to_dict()}")
        else:
            print(f"  {name}: ✓ No missing values")

    # Empty texts
    print("\nEmpty Texts:")
    for name, df in all_dfs:
        empty_count = (df["text"].str.len() == 0).sum()
        if empty_count > 0:
            print(f"  {name}: {empty_count} empty texts ⚠️")
        else:
            print(f"  {name}: ✓ No empty texts")

    # Duplicate texts
    print("\nDuplicate Texts:")
    for name, df in all_dfs:
        duplicates = df["text"].duplicated().sum()
        if duplicates > 0:
            print(f"  {name}: {duplicates} duplicate texts ⚠️")
        else:
            print(f"  {name}: ✓ No duplicate texts")

    # Label distribution
    print("\nClass Distribution:")
    for name, df in all_dfs:
        dist = df["label"].value_counts(normalize=True).sort_index()
        print(f"  {name}: Neg={dist.get(0, 0):.2%}, Pos={dist.get(1, 0):.2%}")


def generate_summary(
    train_df, val_df, test_df, vocab, output_path="docs/dataset_summary.json"
):
    """Generate dataset summary and save to JSON."""
    summary = {
        "total_samples": len(train_df) + len(val_df) + len(test_df),
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "test_samples": len(test_df),
        "train_class_balance": train_df["label"].value_counts(normalize=True).to_dict(),
        "avg_text_length": float(train_df["text_length"].mean()),
        "avg_word_count": float(train_df["word_count"].mean()),
        "avg_unique_words": float(train_df["unique_word_count"].mean()),
        "vocabulary_size": len(vocab),
        "total_tokens": int(sum(vocab.values())),
        "missing_values": int(train_df.isnull().sum().sum()),
        "duplicate_texts": int(train_df["text"].duplicated().sum()),
        "max_text_length": int(train_df["text_length"].max()),
        "min_text_length": int(train_df["text_length"].min()),
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== DATASET SUMMARY ===")
    print(f"Total dataset size: {summary['total_samples']:,} samples")
    print(
        f"Split: {summary['train_samples']:,} train / {summary['val_samples']:,} val / {summary['test_samples']:,} test"
    )
    print(f"Class balance (train): {summary['train_class_balance']}")
    print(f"Average text length: {summary['avg_text_length']:.0f} characters")
    print(f"Average word count: {summary['avg_word_count']:.0f} words")
    print(f"Vocabulary size: {summary['vocabulary_size']:,} unique words")
    print(f"Missing values: {summary['missing_values']}")
    print(f"Duplicate texts: {summary['duplicate_texts']}")
    print(f"\nSummary saved to {output_path}")

    return summary


def main():
    """Run complete data exploration pipeline."""
    print("=" * 60)
    print("IMDB DATASET EXPLORATION")
    print("=" * 60)

    # Load data
    print("\n1. Loading dataset splits...")
    train_df, val_df, test_df = load_dataset_splits()
    print(f"   Train: {len(train_df)}, Validation: {len(val_df)}, Test: {len(test_df)}")

    # Add features
    print("\n2. Computing text features...")
    train_df = add_text_features(train_df)
    val_df = add_text_features(val_df)
    test_df = add_text_features(test_df)
    print("   Features added: text_length, word_count, unique_word_count")

    # Print basic info
    print("\n3. Basic Dataset Info:")
    print(f"   Columns: {train_df.columns.tolist()}")
    print(f"   Train set dtypes:\n{train_df.dtypes}")

    # Class distribution
    print("\n4. Class Distribution (Train):")
    print(train_df["label"].value_counts())

    # Build vocabulary
    print("\n5. Building vocabulary...")
    vocab = build_vocabulary(train_df["text"])
    print(f"   Vocabulary size: {len(vocab):,} unique words")
    print(f"   Total tokens: {sum(vocab.values()):,}")
    print("   Top 10 words:", ", ".join([w for w, _ in vocab.most_common(10)]))

    # Data quality checks
    check_data_quality(train_df, val_df, test_df)

    # Generate plots
    print("\n6. Generating visualizations...")
    plot_class_distribution(train_df, val_df, test_df)
    plot_text_analysis(train_df)

    # Generate summary
    print("\n7. Generating summary...")
    summary = generate_summary(train_df, val_df, test_df, vocab)

    print("\n" + "=" * 60)
    print("EXPLORATION COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
