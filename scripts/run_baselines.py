"""Score today's keyword rules and train and score the in-house text model.

    python scripts/run_baselines.py

Writes predictions for dev, test and the seen-wording reference set to
results/rules/ and results/ml/. The text model's settings are chosen on dev
only; test is scored once with those settings.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from triage import DATA, RESULTS  # noqa: E402
from triage.evaluate import write_json  # noqa: E402
from triage.ml import TicketModel, tune  # noqa: E402
from triage.rules import classify  # noqa: E402

SPLITS = {"dev": "dev.csv", "test": "test.csv", "reference_seen_wording": "reference_seen_wording.csv"}


def main() -> None:
    history = pd.read_csv(DATA / "history" / "tickets_2026_04_09.csv", keep_default_na=False)
    sets = {k: pd.read_csv(DATA / "eval" / v, keep_default_na=False) for k, v in SPLITS.items()}

    for name, df in sets.items():
        pred = pd.DataFrame([{"ticket_id": r.ticket_id, **classify(r.subject, r.body)} for r in df.itertuples()])
        out = RESULTS / "rules" / f"{name}_predictions.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        pred.to_csv(out, index=False, lineterminator="\n")

    c = tune(history, sets["dev"])
    model = TicketModel(c).fit(history)
    write_json(RESULTS / "ml" / "model_settings.json",
               {"trained_on": "data/history/tickets_2026_04_09.csv (closed-ticket labels)", "training_tickets": len(history),
                "regularisation_C_chosen_on_dev": c, "features": "TF-IDF word 1-2 grams + character 3-5 grams, plan as a token",
                "model": "logistic regression, one per target, class_weight=balanced"})
    for name, df in sets.items():
        model.predict(df).to_csv(RESULTS / "ml" / f"{name}_predictions.csv", index=False, lineterminator="\n", float_format="%.4f")
    print(f"rules and text model scored on {', '.join(sets)}; C chosen on dev: {c}")


if __name__ == "__main__":
    main()
