"""
Preprocessing utilities for text classification.
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer


def clean_text(text):
    """Basic text cleaning: lowercase, remove HTML tags, extra whitespace."""
    # Convert to lowercase
    text = text.lower()

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def create_tfidf_features(
    train_texts, val_texts=None, test_texts=None, max_features=5000, ngram_range=(1, 2)
):
    """
    Create TF-IDF features from text data.

    Args:
        train_texts: Training texts
        val_texts: Validation texts (optional)
        test_texts: Test texts (optional)
        max_features: Maximum number of features
        ngram_range: N-gram range (min_n, max_n)

    Returns:
        Dictionary with features for each split
    """
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        stop_words="english",
        min_df=5,
        max_df=0.7,
    )

    # Fit on training data only
    X_train = vectorizer.fit_transform(train_texts)

    result = {
        "vectorizer": vectorizer,
        "X_train": X_train,
        "feature_names": vectorizer.get_feature_names_out(),
    }

    if val_texts is not None:
        X_val = vectorizer.transform(val_texts)
        result["X_val"] = X_val

    if test_texts is not None:
        X_test = vectorizer.transform(test_texts)
        result["X_test"] = X_test

    return result


def preprocess_dataset(train_df, val_df, test_df):
    """
    Preprocess datasets: clean text and create TF-IDF features.

    Returns:
        Dictionary with processed data and vectorizer
    """
    # Clean text
    train_df["cleaned_text"] = train_df["text"].apply(clean_text)
    val_df["cleaned_text"] = val_df["text"].apply(clean_text)
    test_df["cleaned_text"] = test_df["text"].apply(clean_text)

    # Create TF-IDF features
    features = create_tfidf_features(
        train_df["cleaned_text"].tolist(),
        val_df["cleaned_text"].tolist(),
        test_df["cleaned_text"].tolist(),
    )

    return {
        "train": (features["X_train"], train_df["label"].values),
        "val": (features["X_val"], val_df["label"].values),
        "test": (features["X_test"], test_df["label"].values),
        "vectorizer": features["vectorizer"],
        "feature_names": features["feature_names"],
    }
