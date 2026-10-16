"""A conventional text classifier trained on Northstar's own ticket history.

TF-IDF over words and character n-grams, then one logistic regression each for
category, team and priority. It learns from the labels agents set when they
closed tickets (Apr-Sep 2026), which are right about nine times in ten. It is
the option Northstar could run in-house with no outside service.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

TARGETS = {"category": "closed_category", "team": "closed_team", "priority": "closed_priority"}
SEED = 20261009


def text_of(df: pd.DataFrame) -> pd.Series:
    # the plan matters to the routing and priority rules, so it goes in as a token
    return ("plan_" + df["plan"].str.lower() + " " + df["subject"].fillna("") + " \n " + df["body"].fillna(""))


def _pipeline(c: float) -> Pipeline:
    features = FeatureUnion([
        ("words", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, lowercase=True)),
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True, max_features=60000)),
    ])
    return Pipeline([("features", features),
                     ("model", LogisticRegression(C=c, max_iter=3000, class_weight="balanced", random_state=SEED))])


class TicketModel:
    def __init__(self, c: dict[str, float] | None = None):
        self.c = c or {"category": 4.0, "team": 4.0, "priority": 4.0}
        self.models: dict[str, Pipeline] = {}

    def fit(self, history: pd.DataFrame) -> "TicketModel":
        x = text_of(history)
        for target, column in TARGETS.items():
            self.models[target] = _pipeline(self.c[target]).fit(x, history[column])
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        x = text_of(df)
        out = pd.DataFrame({"ticket_id": df["ticket_id"].values})
        for target, model in self.models.items():
            proba = model.predict_proba(x)
            best = proba.argmax(axis=1)
            out[target] = model.classes_[best]
            out[f"{target}_confidence"] = np.round(proba.max(axis=1), 4)
        # one confidence per ticket: the weakest of the three decisions
        out["confidence"] = out[[f"{t}_confidence" for t in self.models]].min(axis=1)
        return out


def tune(history: pd.DataFrame, dev: pd.DataFrame, grid=(0.03, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0)) -> dict[str, float]:
    """Pick C for each target on the dev set (gold labels). The test set is not touched."""
    best = {}
    x_hist, x_dev = text_of(history), text_of(dev)
    for target, column in TARGETS.items():
        scores = {}
        for c in grid:
            m = _pipeline(c).fit(x_hist, history[column])
            scores[c] = float((m.predict(x_dev) == dev[f"gold_{target}"]).mean())
        best[target] = max(scores, key=lambda k: (scores[k], -k))
    return best
