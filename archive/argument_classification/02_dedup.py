"""ARCHIVED - Remove duplicate turns from the version-3 argument classification.

Earlier stage of the project, not used in the thesis.

The same text can appear as several turns on the same measure (for example a
plenary paragraph present in two overlapping blocks). This keeps the first
turn (lowest idx) for each (text, measure) pair.

Inputs
    INTERMEDIATE / "arguments_v3.csv"   (01_classify_v3.py)
    INTERMEDIATE / "turns.parquet"      (03_debate_corpus/04_build_turns.py), for the texts
Outputs
    INTERMEDIATE / "arguments_v3_dedup.csv"   same columns as arguments_v3.csv

Thesis numbers
    None. Archived: the thesis does not use this classification.

Source
    08_arguments_v3.ipynb, cell 2 (TURNS with idx) and the first block of
    cell 14 (deduplication and write). The rest of cell 14 (position x level
    tables, OLS and GEE models) is analysis and is not kept.

Known caveats
    - The arguments_v3_dedup.csv in data/intermediate has five more columns
      (speaker_role, name, group_tag, group, bloc). Cells 10-12 of the
      notebook added them by overwriting the file, using a live call to
      nosdeputes.fr and a MANUAL name dictionary that is not defined in the
      notebook. They are not reproducible and this script does not add them.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

DATA = INTERMEDIATE


def main():
    # cell 2
    TURNS = pd.read_parquet(DATA / "turns.parquet").reset_index().rename(columns={"index": "idx"})

    # cell 14 (first block)
    A3 = pd.read_csv(DATA / "arguments_v3.csv", dtype={"measure": str})
    A3 = A3.merge(TURNS[["idx", "texte"]], on="idx", how="left")
    A3["k"] = A3["texte"].astype(str).str.strip()
    D = A3.sort_values("idx").drop_duplicates(["k", "measure"], keep="first").copy()
    D["score"] = D["score"].astype(str)
    print(f"{len(A3):,} turns -> {len(D):,} after removing duplicates on the same measure")
    D.drop(columns=["k", "texte"]).to_csv(DATA / "arguments_v3_dedup.csv", index=False)


if __name__ == "__main__":
    main()
