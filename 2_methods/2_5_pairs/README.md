# 2.5 – Selecting the pairs of measures (section 4.2.5)

| File | Supports |
|---|---|
| `01_pair_search.py` → `tables/` | 6.4: candidate pairs debated in the same bill; scores of the measures in article 5 of the PLF for 2026 |
| `02_extract_pair_debates.py` → `data/pair_*_passages.csv` | 6.4: committee and plenary passages for pairs A, B and C |
| `PAIR_SOURCES.md` | 6.4: the source of every claim about the three pairs (items marked ⚠️ to verify) |
| `dossiers/` (`build_dossiers.py`, `INDEX.md`, one workbook per measure) | 6.2–6.4: annex history, amendments, debate passages and evaluation references of every measure discussed in Chapter 6 |

Inputs: `data/intermediate/amendments_classified.csv`, the committee and plenary blocks, the panel.
The dossiers' plenary passages are complete only when the plenary blocks are present (see `dossiers/INDEX.md`).
