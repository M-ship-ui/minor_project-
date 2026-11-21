"""Text matching module for the lost-and-found portal (reference implementation).

The module converts item reports into TF-IDF vectors and ranks stored reports of
the opposite type by cosine similarity.
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def clean(text):
    """Lower-case the text and replace punctuation with spaces."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_text(item):
    """Join the searchable fields of a report into one cleaned string."""
    parts = [
        item.get("name", ""),
        item.get("category", ""),
        item.get("description", ""),
        item.get("location", ""),
    ]
    return clean(" ".join(str(p) for p in parts if p))


def score_all(new_item, candidates):
    """Return the cosine similarity of new_item with every candidate."""
    if not candidates:
        return []
    docs = [build_text(c) for c in candidates]
    vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True)
    matrix = vectorizer.fit_transform(docs + [build_text(new_item)])
    return cosine_similarity(matrix[-1], matrix[:-1]).ravel().tolist()


def rank_matches(new_item, candidates, threshold=0.5, top_n=5):
    """Return up to top_n (candidate, score) pairs with score >= threshold."""
    if not candidates:
        return []
    scores = score_all(new_item, candidates)
    ranked = sorted(zip(candidates, scores), key=lambda p: p[1], reverse=True)
    return [(c, float(s)) for c, s in ranked if s >= threshold][:top_n]
