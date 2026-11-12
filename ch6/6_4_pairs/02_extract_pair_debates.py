"""Section 6.4 - Extract the debate passages on which each pair rests.

For each pair, the script searches the Finance Committee minutes and the
plenary blocks for the measures' names in the months when they were
decided, and writes every matching passage with its date, venue and the
decision recorded in the minutes. These are the passages read for the
"arguments" paragraph of each pair; quotations in the text come from them
(and should be checked against the official record before submission).

Inputs
    data/intermediate/committee_blocks*.parquet   Finance Committee minutes
    data/intermediate/debate_blocks*.parquet      plenary blocks (03_debate_corpus/)
Output
    data/pair_<A|B|C>_passages.csv
"""
import glob
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from config import INTERMEDIATE  # noqa: E402

OUT = Path(__file__).resolve().parent / "data"

PAIRS = {
    "A": {  # finance bill for 2014: articles 6 (pension increases) and 4 (school fees)
        "months": ["2013-10", "2013-11"],
        "sessions": ["13-14"],   # 2012-2017 committee minutes record the session, not the date
        "pattern": r"majorations? de (retraite|pension)|frais de scolarit|199 quater F",
    },
    "B": {  # finance bill for 2026, article 5
        "months": ["2025-10", "2025-11", "2026-01"],
        "pattern": r"médailles? d.honneur du travail|médailles? du travail|affections? de longue durée|\bALD\b|"
                   r"indemnités journalières|taxe sur le cancer",
    },
    "C": {  # finance bills for 2024, 2025 and 2026
        "months": ["2023-10", "2024-10", "2025-10"],
        "pattern": r"\bFIP\b|fonds d.investissement de proximité",
    },
}


def text_col(df):
    return "texte" if "texte" in df.columns else max(
        (c for c in df.columns if df[c].dtype == object), key=lambda c: df[c].astype(str).str.len().mean())


def date_of(df):
    for c in ["date", "dateSeance", "date_seance", "session"]:
        if c in df.columns:
            return df[c].astype(str).str[:10]
    return pd.Series([""] * len(df), index=df.index)


def main():
    sources = ([("committee", f) for f in sorted(glob.glob(str(INTERMEDIATE / "committee_blocks*.parquet")))] +
               [("plenary", f) for f in sorted(glob.glob(str(INTERMEDIATE / "debate_blocks*.parquet")))])
    frames = []
    for venue, f in sources:
        d = pd.read_parquet(f)
        tc = text_col(d)
        d = d.assign(_text=d[tc].astype(str), _date=date_of(d), _venue=venue, _file=Path(f).name)
        frames.append(d[["_text", "_date", "_venue", "_file"] + [c for c in ["decision"] if c in d.columns]])
    allb = pd.concat(frames, ignore_index=True)

    for pair, spec in PAIRS.items():
        rx = re.compile(spec["pattern"], re.I)
        when = allb._date.str[:7].isin(spec["months"]) | allb._date.isin(spec.get("sessions", []))
        sub = allb[when & allb._text.str.contains(spec["pattern"], case=False, regex=True)]
        rows = []
        for _, r in sub.iterrows():
            for m in list(rx.finditer(r._text))[:3]:
                rows.append({"pair": pair, "date": r._date, "venue": r._venue, "file": r._file,
                             "decision": r.get("decision", ""), "match": m.group(0),
                             "excerpt": r._text[max(0, m.start() - 1200):m.start() + 1800]})
        out = pd.DataFrame(rows).drop_duplicates("excerpt")
        out.to_csv(OUT / f"pair_{pair}_passages.csv", index=False)
        print(f"Pair {pair}: {len(out)} passages ({out.venue.value_counts().to_dict() if len(out) else {}})")


if __name__ == "__main__":
    main()
