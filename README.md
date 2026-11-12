# Replication package – Why evaluation is not enough: tax expenditures in France, 2011–2026

Master's thesis, Sciences Po (PSIA), Michal Kolb, 2026–2027.

This package contains the code and data needed to reproduce every number,
table and figure in the results chapters (5 and 6), and documents how each
dataset was built from public sources. It is organised in two parts:

1. **The pipeline** (folders `00_` to `04_`): from the downloaded public
   sources to the analysis datasets.
2. **The chapters** (folders `ch5/` and `ch6/`): one folder per section, each
   script stating in its header which numbers, tables and figures of the
   thesis it produces.

## Quick start

```bash
pip install -r requirements.txt
# figures use Latin Modern Roman, the LaTeX font:
sudo apt-get install fonts-lmodern      # or install from https://ctan.org/pkg/lm
export THESIS_ROOT=/path/to/this/package
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
| 5.1 | Table 5.1 (scores and cost in 2011); population of 379 measures (278 scored, 101 not) | `ch5/build_termination_v35.py`, `ch5/write_reports.py` | to add |
| 5.2 | Shares terminated by score; routes (end dates vs suppressions); Figure 5.1 (Kaplan–Meier) | `ch5/` | to add |
| 5.3 | Cox models (HR 0.77 per score point; with controls 0.79; without scheduled closures 0.76); Figure 5.2 | `ch5/` | to add |
| 5.4 | Terminations per year; Figure 5.3; Cox by period (0.62 / 0.85) | `ch5/` | to add |

### Chapter 6 – Tax expenditures in the parliamentary debates

| Section | Content | Script | Status |
|---|---|---|---|
| 6.1 | Corpus description (3,352 interventions, 129 measures) | `03_debate_corpus/`, `04_argument_classification/` | to add |
| 6.2.1 | Evaluation bodies: 494 of 20,000 passages (2.5%); shares by body; periods; timing of citations | `ch6/6_2_1_evaluation_bodies/01_search_evaluation_bodies.py` (search), `02_analyse_reviewed.py` (counts) | ✅ reproduces |
| 6.2.2 | References to the 2011 evaluation: 58; by period; use; known-item test | `ch6/6_2_2_evaluation_2011/01_search_2011_report.py`, `02_analyse_references.py` | ✅ reproduces |
| 6.3 | Reading of the arguments: selection of 23 measures, 648 passages | `ch6/6_3_arguments/01_build_reading_workbook.py` | ✅ reproduces |
| 6.4 | Choice of the pairs; debate passages; sources of every claim | `ch6/6_4_pairs/01_pair_search.py`, `02_extract_pair_debates.py`, `PAIR_SOURCES.md` | ✅ (items marked ⚠️ in PAIR_SOURCES.md to verify) |

## Pipeline

| Folder | Step | Source notebook | Status |
|---|---|---|---|
| `00_acquisition/` | Download the inventories, amendments, plenary and committee records; manifests | *Master Thesis_1 Scraping* | to add |
| `01_inventory_panel/` | Parse the annexes (tome II, 2009–2026) and the 2011 scores into the panel | *Master Thesis_2 TEs*, *Master Thesis_3 Tome II* | to add |
| `02_amendments/` | Match amendments to measures (article of the tax code + LLM verification); direction of each amendment; validation | *Master Thesis_4 Matching*, `12_matching_validation.ipynb` | to add |
| `03_debate_corpus/` | Split plenary and committee records into blocks and speaking turns; link turns to measures | *Master Thesis_6 Debates*, *Master Thesis_7 Committee Debates* | to add |
| `04_argument_classification/` | Automated classification of interventions (finding aid for 6.3); validation | *Master Thesis_5 Classification*, `08_arguments_v3.ipynb` | to add |
| `figures/` | All figures, in Latin Modern Roman, as PDF for LaTeX | `src/thesis_style.py` | style ready |

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

## Large language models

Two steps used a large language model (Anthropic Claude, via the API):
verification of amendment–measure matches (`02_amendments/`) and the
classification of interventions (`04_argument_classification/`). The prompts
are stored with the code. Both steps were validated by hand on random
samples; the validation files are included. The classification is used in
the thesis only to select passages for reading, not to report shares.

## Licence and sources

Code: MIT (see LICENSE). Data: derived from public records of the Assemblée nationale,
DILA and the Ministry of the Economy and Finance (Licence Ouverte / Etalab).
Speakers are quoted in their public capacity.
