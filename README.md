# Replication package – Why evaluation is not enough: tax expenditures in France, 2011–2026

Master's thesis, Sciences Po (PSIA), Michal Kolb, 2026–2027.

This package contains the code and data needed to reproduce every number,
table and figure in the results chapters (5 and 6), and documents how each
dataset was built from public sources. It is organised in two parts:

1. **The pipeline** (folders `00_` to `03_`): from the downloaded public
   sources to the analysis datasets.
2. **The chapters** (folders `ch5/` and `ch6/`): one folder per section, each
   script stating in its header which numbers, tables and figures of the
   thesis it produces.

Earlier stages that the thesis no longer uses are in `archive/` (see below).

## Two bases in Chapter 6

* **References to evaluations (6.2)** are counted in the complete committee and plenary records,
  2011–2026, by keyword search followed by manual reading of every match
  (`ch6/6_2_1_evaluation_bodies/`, `ch6/6_2_2_evaluation_2011/`). The complete record is used so that
  no reference made outside the debate on an amendment is missed.
* **Arguments (6.3) and the pairs (6.4)** draw on the corpus of interventions linked to measures
  through the amendments they discuss (`data/intermediate/turns.parquet`, `arguments_v3_dedup.csv`),
  read by hand. The corpus is used because it tells us which measure each intervention concerns.

## Quick start

```bash
pip install -r requirements.txt
# figures use Latin Modern Roman, the LaTeX font:
sudo apt-get install fonts-lmodern      # or install from https://ctan.org/pkg/lm
export THESIS_ROOT=/path/to/this/package
python ch5/build_termination_v35.py
python ch5/02_survival_models.py
python ch6/6_2_2_evaluation_2011/02_analyse_references.py
```

Scripts named `01_search_*` read the complete raw records and take hours;
they need the raw data in `data/raw/` (see `data/README.md`). Scripts named
`02_analyse_*` start from the reviewed files included in the package and run
in seconds: they reproduce the numbers in the text.

In Google Colab, mount Drive, set `THESIS_ROOT` to the package folder and
run the scripts with `!python`.

## Map from the thesis to the code

### Chapter 5 – The 2011 evaluation and the termination of tax expenditures

| Section | Content | Script | Status |
|---|---|---|---|
| 5.1 | Table 5.1 (scores and cost in 2011 of the 470 measures examined by the committee: 11,764 / 28,236 / 11,393 / 9,305 / 4,935; total 65,633 € m); population of 379 measures (278 scored: 95 / 81 / 42 / 60; 101 not scored) | `ch5/build_termination_v35.py`, `ch5/02_survival_models.py` | ✅ reproduces |
| 5.2 | Terminated by 2026: 41/95, 33/81, 10/42, 15/60, 38/101 (137); routes 111 end dates / 26 suppressions; 13 scored measures with a closure scheduled in 2011; Figure 5.1 (Kaplan–Meier) | `ch5/02_survival_models.py`, `ch5/03_figures.py` | ✅ numbers reproduce; ⚠️ figure not yet rendered (font); ⚠️ route split depends on the column (see discrepancies) |
| 5.3 | Cox models: HR 0.77 per score point (0.64–0.93, p = 0.006); with controls 0.786 (0.653–0.946), rounded 0.79; without the 13 scheduled closures 0.76; Figure 5.2 | `ch5/02_survival_models.py`, `ch5/03_figures.py` | ✅ numbers reproduce; ⚠️ figure not yet rendered |
| 5.4 | Terminations per year; Figure 5.3; Cox by period: 0.62 (p = 0.009) for 2011–2014, 0.85 (p = 0.15) from 2015 | `ch5/02_survival_models.py`, `ch5/03_figures.py` | ✅ numbers reproduce; ⚠️ figure not yet rendered |
| – | The survival dataset for reading by hand: one row per measure, status year by year, the 91 measures not followed and why | `ch5/export_termination_panel.py` → `ch5/termination_panel_by_year.xlsx` | ✅ counts match Chapter 5 |
| – | Rules, censoring and every hand-coded decision with its legal basis | `ch5/CHANGELOG.md` | ✅ |

### Chapter 6 – Tax expenditures in the parliamentary debates

| Section | Content | Script | Status |
|---|---|---|---|
| 6.1 | The two bases: complete records; corpus of interventions linked to measures (5,340 turns; 3,352 distinct interventions on 129 measures) | `03_debate_corpus/` | ✅ corpus included; scripts rebuild it from the raw records |
| 6.2.1 | Evaluation bodies: 494 of 20,000 passages (2.5%); shares by body; periods; timing of citations | `ch6/6_2_1_evaluation_bodies/01_search_evaluation_bodies.py` (search), `02_analyse_reviewed.py` (counts) | ✅ reproduces |
| 6.2.2 | References to the 2011 evaluation: 58; by period; use; known-item test | `ch6/6_2_2_evaluation_2011/01_search_2011_report.py`, `02_analyse_references.py` | ✅ reproduces |
| 6.3 | Reading of the arguments: selection of 23 measures, 648 passages, read by hand | `ch6/6_3_arguments/01_build_reading_workbook.py` | ✅ reproduces |
| 6.4 | Choice of the pairs; debate passages; sources of every claim | `ch6/6_4_pairs/01_pair_search.py`, `02_extract_pair_debates.py`, `PAIR_SOURCES.md` | ✅ (items marked ⚠️ in PAIR_SOURCES.md to verify) |
| 6.2–6.4 | One dossier per measure discussed (annex history, amendments, debates, evaluation references) | `ch6/dossiers/build_dossiers.py`, `ch6/dossiers/INDEX.md` | ⚠️ plenary passages incomplete until re-run with the complete plenary blocks (see INDEX.md) |

## Pipeline

| Folder | Step | Source notebook | Status |
|---|---|---|---|
| `00_acquisition/` | Download the Assembly open data (amendments, files, plenary records), DILA records 2011–2017 and Finance Committee minutes; manifests | *Master Thesis_1 Scraping* (cells 0–24); *Master Thesis_7 Committee Debates* (downloads) | ✅ scripts and manifests (downloads not re-run) |
| `01_inventory_panel/` | Parse the 2011 report (scores) and the annexes (tome II, 2009–2026) into the panel | *Master Thesis_2 TEs*, *Master Thesis_3 Tome II*; panel workbook from `Untitled9.ipynb` | ✅ scripts (not re-run: raw PDFs needed) |
| `02_amendments/` | Parse amendments; match them to measures by tax-code article; LLM verification of each match and direction of each amendment; validation samples | *Master Thesis_1 Scraping* (cells 25–34), *Master Thesis_4 Matching*, *Master Thesis 5_Classification*, `12_matching_validation.ipynb` | ✅ scripts and prompts (LLM step not re-run) |
| `03_debate_corpus/` | Split plenary and committee records into blocks; link blocks to matched amendments; build the speaking turns (`turns.parquet`) | *Master Thesis_6 Debates*, *Master Thesis_7 Committee Debates* | ✅ scripts (not re-run: raw records needed) |
| `figures/` | All figures, in Latin Modern Roman, as PDF for LaTeX | `src/thesis_style.py`, `ch5/03_figures.py` | ⚠️ Figures 5.1–5.3 to render (see below) |

Each script's docstring lists the notebook cells it was taken from. Each folder's README lists its
known caveats.

## Archive (not used in the thesis)

* `archive/argument_classification/` – the automated classification of interventions into argument
  categories (prompts, scripts, validation files). The thesis does not classify interventions or report
  shares of arguments.
* `archive/ch5_v2/` – an earlier build of the Chapter 5 dataset (v2, 391 measures) and its reports.

## Discrepancies and open points found while assembling the package

1. **Routes, 111 / 26.** The chapter's split groups the column `mechanism` (`end_date_unverified` +
   `sunset` = 111; `repeal` + `underlying_tax_reform` + `external` = 26). The column `basis` gives
   121 / 16 (end date in latest edition 114 + frozen end date 7; hand-coded 16). Ten measures coded
   `repeal` take their year from the annex end date. See `ch5/tables/route_by_basis.csv`. The chapter
   numbers have not been changed.
2. **Table 5.1** is computed over the 470 measures of the report, not the 379 followed (as the chapter
   says: "measures examined by the committee").
3. **Figures 5.1–5.3** were not rendered: Latin Modern could not be installed where the package was
   assembled. Run `python ch5/03_figures.py` with `fonts-lmodern` installed and check
   `pdffonts figures/fig5_*.pdf` (LMRoman10-Regular embedded).
4. **Dossiers:** the plenary passages come from the blocks of matched amendments and the corpus, not yet
   from the complete plenary blocks (`debate_blocks*.parquet`, too large for the package); re-run
   `build_dossiers.py` with them.
5. **Pipeline notebooks** contained several versions of some steps. The scripts keep the version that
   wrote the file used in the thesis. Open points:
   * `committee_blocks.parquet` was written with the earlier end-of-block rule (7_Committee cell 9); a
     later cell improved the rule but saved only `committee_matched.parquet`.
   * `amendments_15_17.parquet` has 648,213 rows for 598,947 amendments (duplicates from a merge;
     downstream steps deduplicate).
   * The first 600 rows of `classified_multi.csv` were written by an earlier version of the multi-article loop.
   * The 40-pair pilot of the LLM matching is not included; its "hand coding" column is named
     `claude_relevant`; `classification_meta.json` hard-codes validation figures no cell computes.
   * `turns.parquet` does not include legislature 14 and has no date or amendment identifier.
6. **`arguments_v3_dedup.csv`**: the reading workbook (6.3) uses its identifier and measure code, and also
   two columns of the archived classification to leave out off-topic or procedural interventions before
   reading (see `data/README.md`).

## Figures and LaTeX

`src/thesis_style.py` sets every figure in **Latin Modern Roman 10** (text)
and **Computer Modern** (maths), the fonts of a LaTeX document using
`\usepackage{lmodern}`. Figures are saved as vector PDF with embedded fonts:

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\textwidth]{figures/fig5_1_survival_by_score.pdf}
  \caption{...}
\end{figure}
```

Set `TEXT_WIDTH_IN` and `BODY_PT` in `src/thesis_style.py` to the text width
and font size of your LaTeX document, so that figure text matches body text.

## Large language model

One pipeline step used a large language model (Anthropic Claude, `claude-sonnet-4-5`, via the API):
the verification of amendment–measure matches and the direction of each amendment
(`02_amendments/03_llm_verify_classify.py`). The prompts are stored with the code; the API key is read
from the environment variable `ANTHROPIC_API_KEY`. The LLM labels cannot be regenerated identically.

## Licence and sources

Code: MIT (see LICENSE). Data: derived from public records of the Assemblée nationale,
DILA and the Ministry of the Economy and Finance (Licence Ouverte / Etalab).
Speakers are quoted in their public capacity.
