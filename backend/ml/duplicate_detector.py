import pandas as pd
import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "bangalore_properties.csv")
THRESHOLD = 0.75


class DuplicateDetector:
    def __init__(self):
        self._df    = None
        self._vec   = None
        self._tfidf = None

    def _load(self):
        if self._df is not None:
            return
        if not os.path.exists(DATA_PATH):
            self._df = pd.DataFrame()
            return
        df = pd.read_csv(DATA_PATH)
        df["_text"] = (df["title"].fillna("") + " " +
                       df["description"].fillna("") + " " +
                       df["city"].fillna(""))
        self._df    = df
        self._vec   = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self._tfidf = self._vec.fit_transform(df["_text"])

    def check(self, title: str, description: str, city: str,
              price: float, area_sqft: float) -> dict:
        self._load()
        if self._df is None or self._df.empty:
            return {"is_duplicate": False, "duplicates": []}

        query = f"{title} {description} {city}"
        qvec  = self._vec.transform([query])
        sims  = cosine_similarity(qvec, self._tfidf).flatten()

        results = []
        for idx in np.where(sims >= THRESHOLD)[0]:
            row   = self._df.iloc[idx]
            score = float(sims[idx])
            if (abs(row["price"]     - price)     / max(price,    1) < 0.1 and
                abs(row["area_sqft"] - area_sqft) / max(area_sqft, 1) < 0.1):
                score = min(1.0, score * 1.1)
            if score >= THRESHOLD:
                results.append({
                    "similar_property_text": str(row.get("title", "Unknown")),
                    "similarity_score":      round(score, 3),
                })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return {"is_duplicate": len(results) > 0, "duplicates": results[:5]}


duplicate_detector = DuplicateDetector()