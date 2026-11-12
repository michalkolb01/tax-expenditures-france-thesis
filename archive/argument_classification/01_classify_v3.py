"""ARCHIVED - Classification of speaking turns by argument (version 3).

Earlier stage of the project, not used in the thesis.

Sends each speaking turn of turns.parquet (5,340 turns on 129 measures) to
claude-sonnet-4-5 with prompt_arguments_v3.txt and records the position
(defend / critique / neutre), the main argument and its category, the level
derived from the category in code (verification / validation / vindication /
hors_fond, after Fischer 1995), the evidence cited, the body cited and
whether cost is mentioned. Writes in batches of 50 and resumes where it
stopped; at the end keeps one row per turn (the latest successful one).

Inputs
    INTERMEDIATE / "turns.parquet"          (1_data/1_3_parliamentary_corpus/3_blocks_and_turns/04_build_turns.py);
        its row index becomes the column idx, the key of every argument file
    INTERMEDIATE / "vm_2009_2019.parquet", "vm_2020_2026.parquet"
        (Voies et moyens panel: label and legal reference of each measure)
    prompt_arguments_v3.txt (next to this script; verbatim PROMPT_V3)
    Environment variable ANTHROPIC_API_KEY (the notebook used the Colab
    secret ANTHROPIC_KEY).
Outputs
    INTERMEDIATE / "arguments_v3.csv"   one row per turn: idx, measure, score,
        venue, orateur, role, position, categorie, niveau, detail,
        argument_principal, preuve, organisme, cout_mentionne, raw

Thesis numbers
    None. Archived: the thesis does not use this classification.

Source
    08_arguments_v3.ipynb, cells 2 (setup), 16 (PROMPT_V3 -> prompt file,
    NIVEAU), 18 (classify_v3), 23 (full run). Cells 19-21 (pilot on 40 turns,
    pilot_v3_40c.csv) are not kept; cells 3-13, 24-33, 35-38 are analysis.
    Requires: pip install anthropic.
    The superseded prompts of 7_Committee.ipynb are kept for the record as
    prompt_arguments_v0.txt (cell 88), v1.txt (cell 90), v1_1.txt (cell 92)
    and v2.txt (cell 104; arguments_v2.csv); they were superseded by v3 and
    no script is provided for them.

Changes from the notebook
    Drive paths replaced by src/config.py; API key read from the
    environment; PROMPT_V3 loaded from prompt_arguments_v3.txt.

Known caveats
    - Not run for the replication package (costly LLM step); outputs depend
      on the model version.
    - Cells 10-12 of 08_arguments_v3.ipynb added speaker and parliamentary
      group columns to arguments_v3_dedup.csv through a live call to
      nosdeputes.fr and a MANUAL dictionary that is not defined in the
      notebook; those columns cannot be reproduced and are not built here.
"""
import json
import os
import sys
import time
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

HERE = Path(__file__).resolve().parent
DATA = INTERMEDIATE
MODEL = "claude-sonnet-4-5"
PROMPT_V3 = (HERE / "prompt_arguments_v3.txt").read_text(encoding="utf-8")

# cell 16
NIVEAU = {"efficacite": "verification", "cout": "verification", "aubaine": "verification",
          "ciblage": "verification",
          "besoin": "validation", "conception": "validation",
          "valeurs": "vindication",
          "renvoi": "hors_fond", "procedure": "hors_fond", "autre": "hors_fond",
          "hors_sujet": "hors_fond"}

# cell 18
EMPTY = {"position": None, "categorie": None, "niveau": None, "detail": None,
         "argument_principal": None, "preuve": None, "organisme": None, "cout_mentionne": None}


# cell 2
def strip_accents(s):
    if not s:
        return s
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def load_setup():
    P = pd.read_parquet(DATA / "vm_2009_2019.parquet")
    vm = pd.read_parquet(DATA / "vm_2020_2026.parquet")
    lib_all = (pd.concat([P[["numero", "vm_year", "libelle", "reference"]],
                          vm[["numero", "vm_year", "libelle", "reference"]]])
               .sort_values("vm_year").drop_duplicates("numero", keep="last")
               .set_index("numero"))
    lib = lib_all["libelle"]
    ref = lib_all["reference"]
    TURNS = pd.read_parquet(DATA / "turns.parquet").reset_index().rename(columns={"index": "idx"})
    print(f"{len(TURNS):,} turns, {TURNS['measure'].nunique()} measures")
    return lib, ref, TURNS


# cell 18
def classify_v3(row, client, lib, ref, retries=2):
    p = PROMPT_V3.format(mesure=f"{lib.get(row['measure'], '?')} "
                                f"(base légale : article {ref.get(row['measure'], '?')} du CGI)"[:450],
                         texte=str(row["texte"])[:2500])
    for k in range(retries + 1):
        out = client.messages.create(model=MODEL, max_tokens=400,
                                     messages=[{"role": "user", "content": p}]).content[0].text
        try:
            j = json.loads(out[out.find("{"): out.rfind("}") + 1])
            break
        except Exception:
            if k == retries:
                return {**EMPTY, "raw": out}
            time.sleep(1)
    cat = strip_accents(str(j.get("categorie", "")))
    detail = j.get("detail")
    return {"position": strip_accents(str(j.get("position", ""))),
            "categorie": cat, "niveau": NIVEAU.get(cat),
            "detail": strip_accents(str(detail)) if detail not in (None, "", "null") else None,
            "argument_principal": str(j.get("argument_principal", ""))[:200],
            "preuve": strip_accents(str(j.get("preuve", ""))),
            "organisme": strip_accents(str(j.get("organisme", ""))),
            "cout_mentionne": bool(j.get("cout_mentionne")) if j.get("cout_mentionne") is not None else None,
            "raw": out}


def main():
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    lib, ref, TURNS = load_setup()

    # cell 23
    OUT3 = DATA / "arguments_v3.csv"

    def load_done():
        if not OUT3.exists():
            return set()
        d = pd.read_csv(OUT3)
        return set(d.loc[d["categorie"].notna(), "idx"])      # only successful rows count as done

    done = load_done()
    todo = TURNS[~TURNS["idx"].isin(done)].reset_index(drop=True)
    print(f"{len(done):,} done, {len(todo):,} to go")

    buf, fails = [], 0
    for i, r in todo.iterrows():
        try:
            o = classify_v3(r, client, lib, ref)
            fails = 0
        except (NameError, AttributeError, KeyError, TypeError):
            raise
        except Exception as e:
            fails += 1
            print(f"  error on turn {r['idx']}: {type(e).__name__}: {str(e)[:120]}")
            if fails >= 5:
                if buf:
                    pd.DataFrame(buf).to_csv(OUT3, mode="a", header=not OUT3.exists(), index=False)
                print("\nStopped after 5 errors in a row (out of credit or API down). "
                      "Fix the cause, then rerun: it resumes where it stopped.")
                break
            continue
        buf.append({"idx": r["idx"], "measure": r["measure"], "score": r.get("score"),
                    "venue": r["venue"], "orateur": r.get("orateur"),
                    "role": "rapporteur" if "rapporteur" in str(r.get("orateur", "")).lower() else "autre",
                    **o})
        if len(buf) >= 50 or i == len(todo) - 1:
            pd.DataFrame(buf).to_csv(OUT3, mode="a", header=not OUT3.exists(), index=False)
            buf = []
            print(f"  {i+1:,}/{len(todo):,}")

    # keep one row per turn (the latest successful one)
    A3 = pd.read_csv(OUT3, dtype={"measure": str})
    A3 = (A3.sort_values("categorie", na_position="first")
          .drop_duplicates("idx", keep="last").sort_values("idx"))
    A3.to_csv(OUT3, index=False)
    print(f"\n{A3['categorie'].notna().sum():,} of {len(TURNS):,} turns classified")


if __name__ == "__main__":
    main()
