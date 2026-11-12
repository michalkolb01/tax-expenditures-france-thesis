"""Extract the 470 measures and their scores from the 2011 Guillaume report.

Pipeline step, no thesis number directly (feeds the population and the
score of each measure used in chapter 5, Table 5.1, and the matching in
02_amendments/).

Reads Annex IV of the report of the Comité d'évaluation des dépenses
fiscales et des niches sociales (2011), "Présentation simplifiée des
évaluations des dépenses fiscales", and recovers one record per measure:
code, numbered (six-digit code or "DF ... NR" fiche), tax, label,
evaluating body, cost 2011, beneficiaries, budget mission, score ("0"-"3"
or "Non évalué"). The third block of the table (niches sociales) is cut.
The extraction is checked against the report's own totals (page 29): 470
measures; score 0: 125, 1: 99, 2: 46, 3: 69, Non évalué: 131. The script
stops if any count differs.

Inputs
    data/raw/guillaume_2011/*.pdf    the report (first PDF found)
Outputs
    data/intermediate/guillaume_all.csv          470 measures (449 numbered,
                                                 21 unnumbered); columns
                                                 code, numbered, impot,
                                                 libelle, evaluateur,
                                                 cost_2011, beneficiaires,
                                                 mission, score, raw
    data/intermediate/guillaume_scored_0_1.csv   224 measures scored 0 or 1
Needs
    pip install pypdf pandas

Source
    Master Thesis_2 TEs (2_TEs.ipynb), cells 2 (setup), 4 (find the table
    pages, 177-250), 6 (one record per measure), 8 (split into columns),
    10 (check against the report totals), 12 (save).

Caveats
    - The raw folder was raw/guillaume/ in the notebook; it is
      data/raw/guillaume_2011/ here, as in data/README.md.
    - Three PDF problems are handled in the code: the column headers repeat
      on every page and are glued to the previous page's last row; one
      measure is written "Df" instead of "DF"; the cost column uses a
      Unicode hyphen for "no figure".
    - Four unnumbered measures share a fiche reference; they are made
      distinct with a " (1)", " (2)" suffix.
"""
import re
import sys
from pathlib import Path

import pandas as pd
import pypdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

IMPOTS = [
    "Mesures communes à l'impôt sur le revenu et à l'impôt sur les sociétés",
    "Taxe intérieure de consommation sur les produits énergétiques",
    "Taxe applicable aux voitures particulières",
    "Taxe foncière sur les propriétés non bâties",
    "Taxe foncière sur les propriétés bâties",
    "Contribution foncière des entreprises",
    "Droits d'enregistrement et de timbre",
    "Impôt de solidarité sur la fortune",
    "Redevance audiovisuelle",
    "Taxe sur la valeur ajoutée",
    "Taxe sur les commerces",
    "Impôt sur les sociétés",
    "Impôt sur la fortune",
    "Fiscalité directe locale",
    "Taxe professionnelle",
    "Impôt sur le revenu",
    "Taxe sur les salaires",
    "Taxe d'habitation",
    "Divers",
]


def loose(s):
    """Match a phrase even where the PDF split a word across two lines."""
    return r"\s*".join(re.escape(c) for c in s if not c.isspace())


IMPOT_RE = re.compile("^(" + "|".join(loose(i) for i in
                      sorted(IMPOTS, key=len, reverse=True)) + ")", re.IGNORECASE)
CANON = {re.sub(r"\s+", "", i).lower(): i for i in IMPOTS}

NR_CODE = re.compile(r"[Dd][Ff]\s+\S+(?:\s*[‐-]\s*\S+)?\s+NR\s*\d*(?:\s*[‐-]?\s*\d+)*")

# The cost column uses a Unicode hyphen for "no figure", not an ASCII one.
TAIL = re.compile(
    r"(?P<evaluateur>(?:Direction|Mission|Contrôle|DSS|DGDDI|Inspection)[^|]*?)\s+"
    r"(?P<cost_2011>nc|ε|[\d][\d ]*|[-‐–—])\s+"
    r"(?P<beneficiaires>Entreprises et Ménages|Entreprises|Ménages|Collectivités[^0-9]*?)\s+"
    r"(?P<mission>.+?)\s+"
    r"(?:Non\s*évalué|[0-3])\s*(?:Source\s*:.*)?$")

SCORE = re.compile(r"(Non\s*évalué|[0-3])\s*(?:Source\s*:.*)?$")

COLS = ["code", "numbered", "impot", "libelle", "evaluateur",
        "cost_2011", "beneficiaires", "mission", "score"]

REPORT = {"0": 125, "1": 99, "2": 46, "3": 69, "Non évalué": 131}


def find_records(reader):
    """Step 1-2: locate the table pages and cut the text into records."""
    pages = [i for i in range(len(reader.pages))
             if all(k in re.sub(r"\s+", " ", reader.pages[i].extract_text() or "")
                    for k in ("Score", "Libellé de la mesure", "Chiffrage"))]

    print(f"table on pages {pages[0]}–{pages[-1]} ({len(pages)} pages)")
    assert len(pages) > 50, "expected around 74 table pages"

    chunks = []
    for i in pages:
        t = re.sub(r"\s+", " ", reader.pages[i].extract_text() or "")
        m = re.search(r"Score\s*attribu[ée]\s*", t)
        chunks.append(t[m.end():] if m else t)
    blob = " ".join(chunks)

    ns = re.search(r"\b1\s+Exon[ée]rations à vocation g[ée]n[ée]rale", blob)
    df_blob = blob[:ns.start()]

    # One measure is written "Df" rather than "DF", hence the case-insensitive prefix.
    records = [p.strip() for p in
               re.split(r"(?=\b\d{6}\s|\b[Dd][Ff]\s+[A-ZÉÈ])", df_blob)
               if re.match(r"^(\d{6}|[Dd][Ff]\s)", p.strip())]

    print(f"{len(records)} records "
          f"({sum(1 for p in records if p[0].isdigit())} numbered, "
          f"{sum(1 for p in records if not p[0].isdigit())} unnumbered)")
    return records


def split_columns(records):
    """Step 3: recover the fields by anchoring on closed lists."""
    rows = []
    for p in records:
        code = p[:6] if p[0].isdigit() else NR_CODE.match(p).group(0)
        rest = p[len(code):].lstrip(" *")

        s = SCORE.search(p)
        row = {"code": re.sub(r"\s+", " ", code),
               "numbered": p[0].isdigit(),
               "score": re.sub(r"\s+", " ", s.group(1)) if s else None,
               "raw": p}

        im = IMPOT_RE.match(rest)
        if im:
            row["impot"] = CANON.get(re.sub(r"\s+", "", im.group(1)).lower(), im.group(1))
            rest = rest[im.end():].strip()

        m = TAIL.search(p)
        if m:
            d = {k: re.sub(r"\s+", " ", v).strip() for k, v in m.groupdict().items()}
            d["cost_2011"] = d["cost_2011"].replace(" ", "")
            row.update(d)
            ev = m.group("evaluateur")
            row["libelle"] = rest[:rest.index(ev)].strip() if ev in rest else rest

        rows.append(row)

    g = pd.DataFrame(rows)[COLS + ["raw"]]

    # Four unnumbered measures share a fiche reference because the report only
    # sometimes applies its own suffix convention. Make them distinct.
    dup = g["code"].duplicated(keep=False)
    if dup.any():
        g.loc[dup, "code"] = (g.loc[dup, "code"] + " ("
                              + g.loc[dup].groupby("code").cumcount().add(1).astype(str) + ")")

    for col in ["score", "impot", "libelle", "mission"]:
        print(f"{col:10} {g[col].notna().sum()}/{len(g)}")
    return g


def check_totals(g):
    """Step 4: the report's published score totals (page 29)."""
    got = g["score"].value_counts().to_dict()

    ok = len(g) == 470
    print(f"{'':18}{'found':>7}{'report':>8}")
    print(f"{'measures':18}{len(g):>7}{470:>8}")
    for k, want in REPORT.items():
        v = got.get(k, 0)
        ok &= v == want
        print(f"score {k:<12}{v:>7}{want:>8}{'' if v == want else '   <--'}")

    assert ok, "extraction does not match the report's published totals"
    print("\nall counts match")


def main():
    PDF = next((RAW / "guillaume_2011").glob("*.pdf"))
    print(PDF)
    reader = pypdf.PdfReader(PDF)

    g = split_columns(find_records(reader))
    check_totals(g)

    g.to_csv(INTERMEDIATE / "guillaume_all.csv", index=False)
    pop = g[g["score"].isin(["0", "1"])]
    pop.to_csv(INTERMEDIATE / "guillaume_scored_0_1.csv", index=False)

    print(f"{len(g)} measures -> guillaume_all.csv")
    print(f"{len(pop)} scored 0 or 1 -> guillaume_scored_0_1.csv")


if __name__ == "__main__":
    main()
