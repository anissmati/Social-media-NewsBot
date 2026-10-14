import sys
import os
import pickle
from datetime import datetime, timezone
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from connectors.gnews_connector import GnewsConnector
from connectors.newsapi_connector import newsAPI_connector

from config import *

# Path to /models/scoring_model.pkl
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MODEL_PKL_PATH = os.path.join(PROJECT_ROOT, 'models', 'scoring_model.pkl')

# The previous BBC World RSS feed was returned for every query (it does not
# support category searches), which made a Technology/Sports/etc. request show
# the same articles. Only use sources which actually receive the query.
connect = [GnewsConnector(), newsAPI_connector()]

_model_artifact = None


def _get_model_artifact():
    global _model_artifact
    if _model_artifact is None:
        if not os.path.exists(MODEL_PKL_PATH):
            raise FileNotFoundError(
                f"Model file not found at {MODEL_PKL_PATH}. "
                "Run the export cell in notebooks/scoring_model_training.ipynb first."
            )
        with open(MODEL_PKL_PATH, "rb") as f:
            _model_artifact = pickle.load(f)
    return _model_artifact


def fetch_data(query: str):
    results = []
    for connection in connect:
        results = results + [article for article in connection.fetch_news(query)]
    return results


# Helper functions for token overlap and Jaccard similarity (from your notebook)
def calculate_jaccard_similarity(row):
    t_words = set(str(row["title"]).lower().split())
    s_words = set(str(row["summary"]).lower().split())

    union = t_words.union(s_words)
    if not union:
        return 0.0
    return len(t_words.intersection(s_words)) / len(union)


def calculate_overlap_ratio(row):
    """Calculates how much of the title's vocabulary appears in the summary."""
    t_words = set(str(row["title"]).lower().split())
    s_words = set(str(row["summary"]).lower().split())

    if not t_words:
        return 0.0
    return len(t_words.intersection(s_words)) / len(t_words)


# Creating new features (from your notebook)
def new(df):
    # Article age
    df["published_at"] = pd.to_datetime(
        df["published_at"], utc=True, errors="coerce", format="mixed"
    )
    df["collected_at"] = pd.to_datetime(
        df["collected_at"], utc=True, errors="coerce"
    )

    df["article_age"] = np.round(
        (df["collected_at"] - df["published_at"]).dt.total_seconds() / 3600, 1
    )

    # Extract the day
    df["publish_day"] = df["published_at"].dt.strftime("%a")

    # Extract the time
    df["publish_hour"] = df["published_at"].dt.hour

    # Is weekend
    df["is_weekend"] = df["publish_day"].isin(["Sun", "Sat"]).astype(int)

    # text complexity features
    df["title_len"] = df["title"].str.len()
    df["summary_len"] = df["summary"].str.len()

    df["title_word_count"] = df["title"].str.split().str.len()
    df["summary_word_count"] = df["summary"].str.split().str.len()

    df["title_to_summary_ratio"] = df["title_len"] / (df["summary_len"] + 1)

    df["caps_ratio"] = df["title"].apply(
        lambda t: sum(1 for c in str(t) if c.isupper()) / max(len(str(t)), 1)
    )

    df["punctuation_triggers"] = df["title"].str.count(r"[!?]")

    df["has_digits"] = df["title"].str.contains(r"\d").astype(int)

    df["source_category_interaction"] = df["source_name"] + "_" + df["category"]

    df["text_similarity"] = df.apply(calculate_jaccard_similarity, axis=1)
    df["overlap_ratio"] = df.apply(calculate_overlap_ratio, axis=1)

    return df


# drop the unused data (from your notebook)
def drop(df):
    drop_cols = [
        "id",
        "article_hash",
        "url",
        "fetch_channel",
        "score_reason",
        "published_at",
        "collected_at",
    ]
    df = df.drop(columns=[col for col in drop_cols if col in df.columns])

    return df


# data cleaning (from your notebook)
def clean(df):
    median_age = (
        np.median(df["article_age"].dropna())
        if not df["article_age"].dropna().empty
        else 0.0
    )
    df["article_age"] = df["article_age"].fillna(median_age)

    df["is_clickbait"] = df["is_clickbait"].map({True: 1, False: 0}).fillna(0).astype(int)

    return df


def _normalize_article_fields(articles: list):
    """Normalizes source strings and timezone-aware published_at datetimes on NewsItem objects."""
    current_time = datetime.now(timezone.utc)
    rows = []

    for article in articles:
        # Normalize source string
        artSrc = article.source
        if isinstance(artSrc, tuple):
            raw_str = str(artSrc[-1])
        else:
            raw_str = str(artSrc)

        if ":" in raw_str:
            clean_src_str = raw_str.split(":")[-1].strip()
        else:
            clean_src_str = raw_str.strip()

        article.source = clean_src_str

        # Normalize published_at datetime
        pub_at = article.published_at
        if isinstance(pub_at, str):
            try:
                pub_datetime = datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
            except ValueError:
                pub_datetime = pd.to_datetime(pub_at, utc=True, errors="coerce").to_pydatetime()
        else:
            pub_datetime = pub_at

        if pub_datetime is None or pd.isna(pub_datetime):
            pub_datetime = current_time
        elif pub_datetime.tzinfo is None:
            pub_datetime = pub_datetime.replace(tzinfo=timezone.utc)

        article.published_at = pub_datetime

        rows.append(
            {
                "title": str(article.title or ""),
                "summary": str(article.summary or ""),
                "source_name": clean_src_str,
                "category": str(getattr(article, "category", "Uncategorized") or "Uncategorized"),
                "published_at": pub_datetime,
                "collected_at": current_time,
                "is_clickbait": bool(getattr(article, "is_clickbait", False)),
            }
        )

    return pd.DataFrame(rows)


def score_articles(data: list):
    if not data:
        return data

    artifact = _get_model_artifact()
    model = artifact["model"]
    tfidf_title = artifact["tfidf_title"]
    tfidf_summary = artifact["tfidf_summary"]
    cat_cols = artifact["cat_cols"]
    saved_categories = artifact.get("categories", {})

    # 1. Build DataFrame from NewsItem list and apply notebook feature engineering
    df = _normalize_article_fields(data)
    df = new(df)
    df = drop(df)
    df = clean(df)

    # 2. Transform title and summary with fitted TF-IDF vectorizers
    title_feats = pd.DataFrame(
        tfidf_title.transform(df["title"].fillna("")).toarray(),
        columns=[f"title_tfidf_{i}" for i in range(50)],
        index=df.index,
    )
    summary_feats = pd.DataFrame(
        tfidf_summary.transform(df["summary"].fillna("")).toarray(),
        columns=[f"summary_tfidf_{i}" for i in range(50)],
        index=df.index,
    )

    X_final = pd.concat(
        [df.drop(columns=["title", "summary"]), title_feats, summary_feats],
        axis=1,
    )

    # 3. Cast categorical columns using the training categories
    for col in cat_cols:
        if col in X_final.columns:
            if col in saved_categories:
                X_final[col] = pd.Categorical(
                    X_final[col], categories=saved_categories[col]
                )
            else:
                X_final[col] = X_final[col].astype("category")

    if "feature_columns" in artifact:
        X_final = X_final[artifact["feature_columns"]]

    # 4. Predict scores using LightGBM model
    predictions = model.predict(X_final)

    for article, pred in zip(data, predictions):
        article.score = float(np.round(pred, 2))

    return data