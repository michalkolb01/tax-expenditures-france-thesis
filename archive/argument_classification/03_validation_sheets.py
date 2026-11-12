"""ARCHIVED - Hand-validation sheets for the version-3 argument classification.

Earlier stage of the project, not used in the thesis.

Draws two samples for checking by hand: 60 classified turns stratified by
category (up to 6 per category, off-topic excluded), and 30 turns the model
flagged as off-topic. The human columns are left empty, to be filled in.

Inputs
    INTERMEDIATE / "arguments_v3.csv"   (01_classify_v3.py)
    INTERMEDIATE / "turns.parquet"      (1_data/1_3_parliamentary_corpus/3_blocks_and_turns/04_build_turns.py)
    INTERMEDIATE / "vm_2009_2019.parquet", "vm_2020_2026.parquet" (measure labels)
Outputs
    INTERMEDIATE / "validation_arguments_v3.csv"   60 turns + human_position,
        human_categorie, human_note
    INTERMEDIATE / "validation_offtopic_v3.csv"    30 turns + human_offtopic, human_note

Thesis numbers
    None. Archived: the thesis does not use this classification.

Source
    08_arguments_v3.ipynb, cells 2 (setup: TURNS, labels) and 34.

Known caveats
    - Re-running overwrites any hand coding already entered in the two files.
    - validation_random100.csv and human_validation_34.xlsx (in
      archive/argument_classification/) were not produced by any notebook cell;
      their origin is not documented in code.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

DATA = INTERMEDIATE


def main():
    # cell 2
    P = pd.read_parquet(DATA / "vm_2009_2019.parquet")
    vm = pd.read_parquet(DATA / "vm_2020_2026.parquet")
    lib = (pd.concat([P[["numero", "vm_year", "libelle", "reference"]],
                      vm[["numero", "vm_year", "libelle", "reference"]]])
           .sort_values("vm_year").drop_duplicates("numero", keep="last")
           .set_index("numero"))["libelle"]
    TURNS = pd.read_parquet(DATA / "turns.parquet").reset_index().rename(columns={"index": "idx"})

    # cell 34
    A3 = pd.read_csv(DATA / "arguments_v3.csv", dtype={"measure": str})
    T = TURNS[["idx", "texte"]]
    A = A3.merge(T, on="idx", how="left")
    A["mesure"] = A["measure"].map(lambda m: str(lib.get(m, "?"))[:120])

    # 1. 60 classified turns, stratified by category (about 6 per category)
    sub = A[A["categorie"].notna() & (A["categorie"] != "hors_sujet")]
    val_args = (sub.groupby("categorie", group_keys=False)
                .apply(lambda g: g.sample(min(len(g), 6), random_state=2026)))
    val_args = val_args.sample(frac=1, random_state=1)          # shuffle so categories are mixed
    cols = ["idx", "venue", "mesure", "texte", "position", "categorie", "detail",
            "argument_principal", "preuve", "organisme"]
    out1 = val_args[cols].assign(human_position="", human_categorie="", human_note="")
    out1.to_csv(DATA / "validation_arguments_v3.csv", index=False)

    # 2. 30 turns flagged off-topic
    out2 = A[A["categorie"] == "hors_sujet"].sample(30, random_state=2026)[["idx", "venue", "mesure", "texte"]]
    out2 = out2.assign(human_offtopic="", human_note="")
    out2.to_csv(DATA / "validation_offtopic_v3.csv", index=False)
    print(len(out1), "classified turns |", len(out2), "off-topic turns -> saved in", DATA)


if __name__ == "__main__":
    main()
