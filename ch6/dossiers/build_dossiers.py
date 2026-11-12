"""Chapter 6 - One Excel dossier per tax expenditure discussed in the thesis.

For each measure (or group of codes) in DOSSIERS below, writes
ch6/dossiers/dossier_<code>_<short name>.xlsx with five sheets:

  Summary                code(s), French name, 2011 score, first and last annex year,
                         status in 2026, termination year and route (Chapter 5 dataset),
                         and the sources used for the Debates sheet
  Annex history          one row per code and annex year: cost, beneficiaries, status,
                         end date as recorded in the Voies et moyens annex
  Amendments             every amendment matched to the measure (02_amendments/):
                         bill, number, author, direction, outcome, short statement
  Debates                every committee or plenary passage that mentions the measure
  Evaluation references  rows of the two reviewed files of sections 6.2.1 and 6.2.2
                         that concern the measure

Inputs (data/intermediate/ unless stated)
    vm_2009_2019.parquet, vm_2020_2026.parquet     annex panel (01_inventory_panel/)
    guillaume_all.csv                              2011 scores
    ch5/tables/termination_dataset_v35.csv         status / termination (ch5/)
    amendments_classified.csv                      matched amendments and direction
    amendments_14.parquet, amendments_15_17.parquet  amendment metadata - OPTIONAL
        (large; not in the package). Without them, bill, number and outcome come from
        the amendment identifier and the matched-block files, and the author is left
        empty unless the committee heading names it.
    committee_blocks.parquet, committee_blocks_14.parquet   complete committee minutes
    debate_blocks.parquet, debate_blocks_14.parquet, debate_blocks_17.parquet
        complete plenary blocks - OPTIONAL (84/53/13 MB, not in the package)
    debate_matched.parquet, debate_matched_14.parquet       plenary blocks of matched
        amendments (fallback when the complete plenary blocks are absent)
    turns.parquet                                  corpus of interventions (plenary turns)
    ch6/6_2_1_evaluation_bodies/data/te_passages_with_evaluation_reviewed.csv
    ch6/6_2_2_evaluation_2011/data/evaluation2011_candidates_RAW_reviewed.csv

Passages are found by keyword search (KEYWORDS, case-insensitive, legal article or
name of the measure) and, for the matched files, by the amendment-measure link.
The Summary sheet records which plenary source was used. Run again in Colab with the
debate_blocks*.parquet files in data/intermediate/ to get the complete plenary record.

Output: ch6/dossiers/dossier_*.xlsx; INDEX.md is written by hand.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import INTERMEDIATE  # noqa: E402

CH5 = ROOT / "ch5" / "tables" / "termination_dataset_v35.csv"
EVAL_621 = ROOT / "ch6" / "6_2_1_evaluation_bodies" / "data" / "te_passages_with_evaluation_reviewed.csv"
EVAL_622 = ROOT / "ch6" / "6_2_2_evaluation_2011" / "data" / "evaluation2011_candidates_RAW_reviewed.csv"
MAXLEN = 32000   # Excel cell limit is 32,767 characters

# key: (codes, short name, keyword regex, flag column in the 6.2.1 file or None)
DOSSIERS = {
    "120114": (["120114"], "pension_increases",
               r"majorations? de (retraite|pension)|majoration .{0,40}trois enfants|81[\s,-]*2\s*°?\s*ter", None),
    "110215": (["110215", "110242"], "school_fees",
               r"frais de scolarit|199\s*quater\s*F", None),
    "120116": (["120116"], "work_medal",
               r"m[ée]dailles? (d.honneur )?du travail|81[\s,-]*7\s*°", None),
    "120204": (["120204"], "long_term_illness",
               r"affections? de longue dur[ée]e|\bALD\b|80\s*quinquies", None),
    "110228": (["110228", "110245"], "local_investment_funds",
               r"fonds d.investissement de proximit|\bFIP\b|199\s*terdecies", None),
    "210305": (["210305"], "corsica_investment_credit",
               r"cr[ée]dit d.imp[ôo]t (pour )?investissement en Corse|\bCIIC\b|244\s*quater\s*E", None),
    "200302": (["200302", "200311"], "research_tax_credit",
               r"cr[ée]dit d.imp[ôo]t (en faveur de la |pour la |)recherche|\bCIR\b|244\s*quater\s*B",
               "research tax credit"),
    "210324": (["210324"], "cice",
               r"\bCICE\b|comp[ée]titivit[ée] et (de l.)?emploi|244\s*quater\s*C", None),
    "520110": (["520110"], "dutreil_pact",
               r"Dutreil|engagements? (collectifs? )?de conservation|787\s*B", "Dutreil pact"),
    "110246": (["110246"], "home_services_credit",
               r"emploi d.un salari[ée] [àa] domicile|services [àa] la personne|199\s*sexdecies",
               "home services credit"),
    "320121": (["320121", "320129", "320140", "320133", "320144"], "film_audiovisual_credits",
               r"cr[ée]dits? d.imp[ôo]t (cin[ée]ma|audiovisuel|international)|\bC2I\b|\bTRIP\b|220\s*sexies|"
               r"220\s*quaterdecies|production (cin[ée]matographique|audiovisuelle)|[œo]e?uvres? (cin[ée]matographiques|audiovisuelles)",
               "film and audiovisual credits"),
}


def yr(x):
    m = re.search(r"(19|20)\d{2}", str(x))
    return int(m.group(0)) if m else np.nan


def clip(s):
    s = "" if s is None or (isinstance(s, float) and np.isnan(s)) else str(s)
    return s if len(s) <= MAXLEN else s[:MAXLEN] + " [...]"


def read_opt(name):
    p = INTERMEDIATE / name
    return pd.read_parquet(p) if p.exists() else None


# ---------------------------------------------------------------- inputs ----
def load():
    P = pd.read_parquet(INTERMEDIATE / "vm_2009_2019.parquet")
    V = pd.read_parquet(INTERMEDIATE / "vm_2020_2026.parquet")
    for d in (P, V):
        d["numero"] = d["numero"].astype(str).str.zfill(6)
    g = pd.read_csv(INTERMEDIATE / "guillaume_all.csv", dtype=str)
    g["code"] = g["code"].str.strip().str.zfill(6)
    t = pd.read_csv(CH5, dtype={"code": str, "score": str}) if CH5.exists() else pd.DataFrame(columns=["code"])
    am = pd.read_csv(INTERMEDIATE / "amendments_classified.csv", dtype=str)
    am["measure"] = am["measure"].str.zfill(6)
    meta = [read_opt(f) for f in ("amendments_14.parquet", "amendments_15_17.parquet")]
    meta = pd.concat([m for m in meta if m is not None], ignore_index=True).drop_duplicates("uid") \
        if any(m is not None for m in meta) else None
    plen = [read_opt(f) for f in ("debate_blocks_14.parquet", "debate_blocks.parquet")]
    plen = [p for p in plen if p is not None]
    return dict(P=P, V=V, g=g.drop_duplicates("code"), t=t, am=am, meta=meta, plen=plen,
                cb=pd.read_parquet(INTERMEDIATE / "committee_blocks.parquet"),
                cb14=pd.read_parquet(INTERMEDIATE / "committee_blocks_14.parquet"),
                cm=read_opt("committee_matched.parquet"), cm14=read_opt("committee_matched_14.parquet"),
                dm=read_opt("debate_matched.parquet"), dm14=read_opt("debate_matched_14.parquet"),
                turns=pd.read_parquet(INTERMEDIATE / "turns.parquet"),
                e1=pd.read_csv(EVAL_621, dtype=str), e2=pd.read_csv(EVAL_622, dtype=str))


# ---------------------------------------------------------------- sheets ----
def annex_history(D, codes):
    P = D["P"][D["P"]["numero"].isin(codes)].reset_index(drop=True)
    V = D["V"][D["V"]["numero"].isin(codes)].reset_index(drop=True)
    P = P.loc[:, ~P.columns.duplicated()]
    V = V.loc[:, ~V.columns.duplicated()]
    a = pd.DataFrame({
        "code": P["numero"], "annex year (PLF)": P["vm_year"], "label": P["libelle"],
        "cost (EUR m; three columns as printed)": P["costs"], "beneficiaries": P["benef_raw"],
        "end of qualifying event (fin du fait generateur)": P["fin_fait"],
        "status": np.where(P["declassement"].notna() & (P["declassement"].astype(str) != "nan"),
                           "declassified PLF " + P["declassement"].astype(str), "listed"),
        "legal reference": P["reference"]})
    b = pd.DataFrame({
        "code": V["numero"], "annex year (PLF)": V["vm_year"], "label": V["libelle"],
        "cost (EUR m; three columns as printed)": V["realisation"].astype(str) + " | " + V["prevision_1"].astype(str)
        + " | " + V["prevision_2"].astype(str),
        "beneficiaries": V["nombre"].astype(str) + " " + V["nature"].fillna("").astype(str),
        "end of qualifying event (fin du fait generateur)": V["fin_fait_generateur"],
        "status": np.where(V["suppression"].notna() & ~V["suppression"].astype(str).isin(["nan", "", "None"]),
                           "suppression: " + V["suppression"].astype(str) + " " + V["motif"].fillna("").astype(str),
                           "listed"),
        "legal reference": V["reference"]})
    return pd.concat([a, b]).sort_values(["code", "annex year (PLF)"])


def parse_uid(uid):
    m = re.match(r"AMANR5L(\d{2}).*?B(\d+).*?N0*(\d+)$", str(uid))
    return (m.group(1), m.group(2), m.group(3)) if m else ("", "", "")


def amendments(D, codes):
    a = D["am"][D["am"]["measure"].isin(codes)].copy()
    parts = a["uid"].map(parse_uid)
    a["legislature"] = parts.str[0]
    a["bill (texte_ref)"] = "PRJLANR5L" + a["legislature"] + "B" + parts.str[1]
    a["number"] = parts.str[2]
    a["author"] = ""
    a["outcome"] = ""
    # outcome and bill from the matched-block files where available
    for f in ("dm", "dm14", "cm", "cm14"):
        m = D[f]
        if m is not None and "sort" in m:
            s = m.drop_duplicates("uid").set_index("uid")
            a["outcome"] = a["outcome"].where(a["outcome"] != "", a["uid"].map(s["sort"]).fillna(""))
            if "texte_ref" in s:
                a["bill (texte_ref)"] = a["uid"].map(s["texte_ref"]).fillna(a["bill (texte_ref)"])
    for f in ("cm", "cm14"):          # committee heading names the author
        m = D[f]
        if m is not None:
            s = m.drop_duplicates("uid").set_index("uid")["entete"].astype(str)
            au = s.str.extract(r"(?:amendements?|amendement)\s+\S+\s+(?:de|du)\s+(M\.|Mme|M\.\s|le|la)\s*([^,.;(]{2,60})")
            a["author"] = a["author"].where(a["author"] != "",
                                            a["uid"].map((au[0].fillna("") + " " + au[1].fillna("")).str.strip()).fillna(""))
    if D["meta"] is not None:         # full metadata when the amendment tables are present
        m = D["meta"].set_index("uid")
        for col, src in (("author", ["auteur", "auteur_nom", "signataires"]), ("outcome", ["sort"]),
                         ("number", ["numero"]), ("bill (texte_ref)", ["texte_ref"])):
            for c in src:
                if c in m:
                    a[col] = a["uid"].map(m[c]).fillna(a[col])
                    break
    a = a.rename(columns={"categorie": "direction", "analyse": "short statement (LLM summary)",
                          "measure": "code", "pass": "matching pass"})
    return a[["code", "legislature", "bill (texte_ref)", "number", "uid", "author", "direction",
              "outcome", "short statement (LLM summary)", "matching pass"]].sort_values(["legislature", "number"])


def debates(D, codes, kw):
    rx = re.compile(kw, re.I)
    rows = []
    for name, df, date_col in (("committee (leg. 15-17), complete minutes", D["cb"], "date"),
                               ("committee (leg. 14), complete minutes", D["cb14"], "session")):
        hit = df[df["texte"].fillna("").str.contains(rx) | df["entete"].fillna("").str.contains(rx)]
        for _, r in hit.iterrows():
            sp = re.match(r"\s*((?:M\.|Mme)\s*[^.]{2,60})\.", str(r["texte"]))
            rows.append(dict(date=r[date_col], venue=name, speaker=sp.group(1) if sp else "",
                             amendment=r.get("amd", ""), heading=clip(r["entete"]), text=clip(r["texte"]),
                             found_by="keyword"))
    if D["plen"]:
        for df in D["plen"]:
            tcol = "texte" if "texte" in df else df.columns[-1]
            hit = df[df[tcol].fillna("").astype(str).str.contains(rx)]
            for _, r in hit.iterrows():
                rows.append(dict(date=r.get("date", ""), venue="plenary, complete blocks", speaker="",
                                 amendment=r.get("amendement", ""), heading="", text=clip(r[tcol]),
                                 found_by="keyword"))
    else:
        dm14 = D["dm14"]
        if dm14 is not None:
            sel = dm14[dm14["measure"].isin(codes) | dm14["bloc_texte"].fillna("").str.contains(rx)]
            for _, r in sel.iterrows():
                rows.append(dict(date=r["date"], venue="plenary (leg. 14), matched amendment blocks",
                                 speaker=r.get("qui_commission", "") or "", amendment=r["numero"], heading="",
                                 text=clip(r["bloc_texte"]),
                                 found_by="amendment link" if r["measure"] in codes else "keyword"))
        dm = D["dm"]
        if dm is not None:
            sel = dm[dm["measure"].isin(codes)]
            for _, r in sel.iterrows():
                txt = f"Commission ({r['qui_commission']}): {r['avis_commission']}\n" \
                      f"Government ({r['qui_gouvernement']}): {r['avis_gouvernement']}"
                rows.append(dict(date=r["date"], venue="plenary (leg. 15-17), matched amendment blocks (opinions)",
                                 speaker="", amendment=r["numero"], heading="", text=clip(txt),
                                 found_by="amendment link"))
        t = D["turns"]
        fl = t[(t["venue"] == "floor") & (t["measure"].astype(str).isin(codes) | t["texte"].str.contains(rx))]
        for _, r in fl.iterrows():
            rows.append(dict(date="", venue="plenary, corpus of interventions (turns.parquet)",
                             speaker=r["orateur"], amendment="", heading="", text=clip(r["texte"]),
                             found_by="amendment link" if str(r["measure"]) in codes else "keyword"))
    out = pd.DataFrame(rows, columns=["date", "venue", "speaker", "amendment", "heading", "text", "found_by"])
    return out.drop_duplicates(["venue", "text"]).sort_values(["date", "venue"], key=lambda s: s.astype(str))


def evaluation_refs(D, kw, flag):
    rx = re.compile(kw, re.I)
    e1 = D["e1"]
    m1 = e1["text"].fillna("").str.contains(rx)
    if flag and flag in e1:
        m1 |= e1[flag].astype(str).isin(["1", "1.0", "True", "true"])
    e2 = D["e2"]
    m2 = e2["excerpt"].fillna("").str.contains(rx)
    a = e1[m1].assign(source_file="6.2.1 te_passages_with_evaluation_reviewed.csv")
    b = e2[m2].assign(source_file="6.2.2 evaluation2011_candidates_RAW_reviewed.csv")
    out = pd.concat([a, b], ignore_index=True)
    for c in ("text", "excerpt"):
        if c in out:
            out[c] = out[c].map(clip)
    return out[["source_file"] + [c for c in out.columns if c != "source_file"]]


def summary(D, codes, plen_source):
    rows = []
    allyrs = pd.concat([D["P"][["numero", "vm_year", "libelle"]], D["V"][["numero", "vm_year", "libelle"]]])
    t = D["t"].set_index("code") if len(D["t"]) else pd.DataFrame()
    g = D["g"].set_index("code")
    for c in codes:
        h = allyrs[allyrs["numero"] == c].sort_values("vm_year")
        last = int(h["vm_year"].max()) if len(h) else None
        row = {"code": c, "French name": h["libelle"].iloc[-1] if len(h) else "",
               "2011 score": g.loc[c, "score"] if c in g.index else "not in the 2011 report",
               "first annex year": int(h["vm_year"].min()) if len(h) else "",
               "last annex year": last if last else ""}
        if c in t.index:
            r = t.loc[c]
            if r["event"] == 1:
                row["status in 2026"] = "terminated"
                row["termination year"] = int(r["event_year"])
                row["route"] = "end date recorded in the annex" if r["mechanism"] in ("end_date_unverified", "sunset") \
                    else "suppression by law"
                row["legal basis"] = r.get("legal_basis", "")
            else:
                row["status in 2026"] = "open (censored " + str(int(r["event_year"])) + ": " + str(r["basis"]) + ")"
        else:
            row["status in 2026"] = ("listed in 2026 annex" if last == 2026 else f"not listed after {last}") + \
                " (not in the Chapter 5 population)"
        rows.append(row)
    s = pd.DataFrame(rows)
    s["Debates sheet: sources"] = plen_source
    return s


def write(path, sheets):
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for name, df in sheets.items():
            df.to_excel(w, sheet_name=name, index=False)
            ws = w.sheets[name]
            ws.freeze_panes = "A2"
            for c in ws[1]:
                c.font = Font(bold=True)
            for col in ws.columns:
                width = min(80, max(10, max(min(len(str(c.value or "")), 80) for c in col) + 2))
                ws.column_dimensions[col[0].column_letter].width = width
                for c in col[1:]:
                    c.alignment = Alignment(wrap_text=width >= 60, vertical="top")


def main():
    D = load()
    plen_source = ("Committee: complete minutes (committee_blocks*.parquet). Plenary: "
                   + ("complete plenary blocks (debate_blocks*.parquet)." if D["plen"] else
                      "complete plenary blocks NOT available - plenary passages come from the blocks of "
                      "matched amendments (debate_matched*.parquet) and the corpus of interventions "
                      "(turns.parquet); re-run with debate_blocks*.parquet for the complete record."))
    print(plen_source, "\n")
    for key, (codes, short, kw, flag) in DOSSIERS.items():
        sheets = {"Summary": summary(D, codes, plen_source),
                  "Annex history": annex_history(D, codes),
                  "Amendments": amendments(D, codes),
                  "Debates": debates(D, codes, kw),
                  "Evaluation references": evaluation_refs(D, kw, flag)}
        out = HERE / f"dossier_{key}_{short}.xlsx"
        write(out, sheets)
        print(f"{out.name:<48} " + ", ".join(f"{k}: {len(v)}" for k, v in sheets.items() if k != "Summary"))


if __name__ == "__main__":
    main()
