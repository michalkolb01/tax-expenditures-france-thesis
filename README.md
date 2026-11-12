# Replication package – Why evaluation is not enough: tax expenditures in France, 2011–2026

Master's thesis, Sciences Po (PSIA), Michal Kolb, 2026–2027.

This package contains the code and data needed to reproduce every number,
table and figure in the results chapters (5 and 6), and documents how each
dataset was built from public sources. It follows the methods chapter
(Chapter 4): `1_data/` for section 4.1, `2_methods/` for section 4.2. Each
script states in its header which numbers, tables and figures it produces;
each folder has a README.

## Map from the thesis to the code

| Thesis section | Folder |
|---|---|
| 4.1.1 The 2011 evaluation and its scores | `1_data/1_1_evaluation_2011/` |
| 4.1.2 The panel of tax expenditures, 2009–2026 (inventories, population, termination, censoring) | `1_data/1_2_panel_2009_2026/` |
| 4.1.3 The parliamentary corpus (records, amendments linked to measures, interventions) | `1_data/1_3_parliamentary_corpus/` |
| 4.2.1 Survival analysis (Kaplan–Meier) | `2_methods/2_1_survival_analysis/` |
| 4.2.2 Cox model | `2_methods/2_2_cox_model/` |
| 4.2.3 Searching the records for references to evaluations | `2_methods/2_3_evaluation_searches/` |
| 4.2.4 Reading the arguments in the corpus | `2_methods/2_4_arguments/` |
| 4.2.5 Selecting the pairs of measures | `2_methods/2_5_pairs/` |
| 5.1 Table 5.1 (scores and cost in 2011 of the 470 measures examined by the committee) | `1_data/1_1_evaluation_2011/` (`02_table_5_1.py`) |
| 5.1 Population of 379 measures (278 scored: 95 / 81 / 42 / 60; 101 not scored) | `1_data/1_2_panel_2009_2026/` (`03_build_termination_v35.py`) |
| 5.2 Terminations by score (41/95, 33/81, 10/42, 15/60, 38/101); routes (111 / 26); 13 scheduled closures; Figure 5.1 | `2_methods/2_1_survival_analysis/` |
| 5.3 Cox models (0.77; with controls 0.79; without scheduled closures 0.76); Figure 5.2 | `2_methods/2_2_cox_model/` |
| 5.4 Terminations per year; Figure 5.3; Cox by period (0.62 / 0.85) | `2_methods/2_2_cox_model/` |
| 6.1 The two bases: complete records; corpus of interventions (5,340 turns; 3,352 distinct interventions on 129 measures) | `1_data/1_3_parliamentary_corpus/` |
| 6.2.1 Evaluation bodies (494 of 20,000 passages) | `2_methods/2_3_evaluation_searches/6_2_1_evaluation_bodies/` |
| 6.2.2 References to the 2011 evaluation (58) | `2_methods/2_3_evaluation_searches/6_2_2_evaluation_2011/` |
| 6.3 Reading of the arguments (23 measures, 648 passages) | `2_methods/2_4_arguments/` |
| 6.4 The three pairs; dossiers of the measures discussed | `2_methods/2_5_pairs/` |

Shared data are in `data/` (`raw/` for downloaded sources, `intermediate/` for built datasets; see
`data/README.md`); `src/` holds `config.py` (paths) and `thesis_style.py` (figure style); figures go to
`figures/`. Earlier stages and files that the thesis does not use are in `archive/` (argument classification, the v2 Chapter 5 build, the matching validation samples).

## Two bases in Chapter 6

* **References to evaluations (6.2)** are counted in the complete committee and plenary records,
  2011–2026, by keyword search followed by manual reading of every match
  (`2_methods/2_3_evaluation_searches/`). The complete record is used so that no reference made outside
  the debate on an amendment is missed.
* **Arguments (6.3) and the pairs (6.4)** draw on the corpus of interventions linked to measures
  through the amendments they discuss (`data/intermediate/turns.parquet`, `arguments_v3_dedup.csv`),
  read by hand. The corpus is used because it tells us which measure each intervention concerns.

## Status

| Part | Status |
|---|---|
| Chapter 5 numbers and Table 5.1 | ✅ reproduce (run after the reorganisation) |
| Figures 5.1–5.3 | ✅ in `figures/` (PDF + PNG), built from commit 9e95334 with Latin Modern installed; the PDFs embed LMRoman10 (checked with `pdffonts`) |
| 6.2.1, 6.2.2, 6.3, 6.4 | ✅ reproduce (run after the reorganisation) |
| Dossiers | ⚠️ plenary passages complete only after a run in Colab with the plenary blocks, see below |
| Pipeline (`1_data/`) | ✅ scripts, prompts and manifests; downloads, PDF parsing and the LLM step not re-run (raw data needed) |

## Quick start

```bash
pip install -r requirements.txt
export THESIS_ROOT=/path/to/this/package
python 1_data/1_2_panel_2009_2026/03_build_termination_v35.py
python 2_methods/2_1_survival_analysis/01_kaplan_meier.py
python 2_methods/2_2_cox_model/01_cox_models.py
python 2_methods/2_3_evaluation_searches/6_2_2_evaluation_2011/02_analyse_references.py
```

Scripts named `01_search_*` read the complete raw records and take hours; they need the raw data in
`data/raw/`. Scripts named `02_analyse_*` start from the reviewed files included in the package and run
in seconds.

## Steps to run in Colab

The figures need the Latin Modern fonts, and the dossiers need the complete plenary blocks
(`debate_blocks.parquet`, `debate_blocks_14.parquet`, `debate_blocks_17.parquet`), which are too large
for the repository. Copy them into `data/intermediate/` of the package folder in Drive, then:

```python
from google.colab import drive
drive.mount('/content/drive')
```

```bash
!apt-get -qq install -y fonts-lmodern
!pip install -q lifelines
```

```python
import os
os.environ["THESIS_ROOT"] = "/content/drive/MyDrive/tax-expenditures-france-thesis"   # the package folder
%cd /content/drive/MyDrive/tax-expenditures-france-thesis
```

```bash
!python 2_methods/2_1_survival_analysis/02_figure_5_1.py
!python 2_methods/2_2_cox_model/02_figures_5_2_5_3.py
!python 2_methods/2_5_pairs/dossiers/build_dossiers.py
!pdffonts figures/fig5_1_survival_by_score.pdf
!pdffonts figures/fig5_2_cox_hazard_ratios.pdf
!pdffonts figures/fig5_3_terminations_per_year.pdf
```

Each `pdffonts` listing should show `LMRoman10-Regular` (and `CMMI10`/`CMR10` for mathematics) with
`emb yes`. `build_dossiers.py` prints which plenary source it used; with the blocks present it says
"complete plenary blocks".

## Discrepancies and open points

1. **Routes, 111 / 26.** The chapter groups terminations by `mechanism` (how the measure ended):
   `end_date_unverified` + `sunset` = 111, `repeal` + `underlying_tax_reform` + `external` = 26.
   `end_date_unverified` is the default for cases not audited by hand. The column `basis` (where the
   year comes from) gives 121 / 16. Both columns and their cross-tabulation are in
   `1_data/1_2_panel_2009_2026/CHANGELOG.md` and `termination_panel_by_year.xlsx`.
2. **Table 5.1** is computed over the 470 measures examined by the committee, not the 379 followed.
3. **Amendment matching.** Amendments are matched to measures on the tax-code article
   (*Master Thesis_4 Matching*, cells 25 and 27); each candidate link is checked by a language model,
   which also labels the direction of the amendment (*Master Thesis 5_Classification*, cells 6, 13,
   20–27). There is no hand validation of the matching. In the thesis the corpus is used only to locate
   debates, which are then read. The validation samples drawn in the notebooks, whose coding was not done
   by the author, are archived in `archive/matching_validation/` and not used; a 100-pair sample
   (`12_matching_validation.ipynb`) was prepared but not coded.
4. **Proportional hazards.** Scaled Schoenfeld residual tests do not reject proportionality (score
   p = 0.72 in the main model, 0.71 with controls; global p = 0.72 and 0.46);
   `2_methods/2_2_cox_model/tables/ph_tests.csv`.
5. **Committee blocks.** `committee_blocks.parquet` was written with the earlier end-of-block rule
   (*Master Thesis_7 Committee Debates*, cell 9). The later rule (cell 23) also closes a block at
   "Suivant l'avis …, la commission adopte/rejette …"; under the earlier rule those lines stay inside the
   block, which then runs on to the next amendment heading. The block openings, and so the 8,276 blocks,
   are the same; the earlier file keeps more text per block (decision captured in 86% of blocks against
   92%) and drops nothing that the later rule keeps, so the keyword searches of 6.2.1 and 6.2.2, which read the block texts, can only
   find the same references or more; a passage can occasionally be attached to the preceding amendment.
6. **Pipeline notebooks** had several versions of some steps; the scripts keep the version that wrote
   the file used in the thesis. Other open points: `amendments_15_17.parquet` has 648,213 rows for
   598,947 amendments (duplicates from a merge, removed downstream); the first 600 rows of
   `classified_multi.csv` come from an earlier loop; `turns.parquet` excludes legislature 14 and has no
   date or amendment identifier.

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

One pipeline step used a large language model (Anthropic Claude, `claude-sonnet-4-5`, via the API): each
candidate amendment–measure link found on the tax-code article is checked by the model, which also labels
the direction of the amendment (`1_data/1_3_parliamentary_corpus/2_amendments/03_llm_verify_classify.py`).
There is no hand validation of this step; the corpus is used only to locate debates, which are then read.
The prompts are stored with the code; the API key is read from the environment variable
`ANTHROPIC_API_KEY`. The labels cannot be regenerated identically.

## Licence and sources

Code: MIT (see LICENSE). Data: derived from public records of the Assemblée nationale,
DILA and the Ministry of the Economy and Finance (Licence Ouverte / Etalab).
Speakers are quoted in their public capacity.
