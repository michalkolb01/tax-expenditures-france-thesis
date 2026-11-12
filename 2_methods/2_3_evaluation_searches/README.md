# 2.3 – Searching the records for references to evaluations (section 4.2.3)

Keyword search of the complete committee and plenary records, 2011–2026, followed by manual reading of
every match. The complete record is used so that no reference made outside the debate on an amendment
is missed.

| Folder | Scripts | Supports |
|---|---|---|
| `6_2_1_evaluation_bodies/` | `01_search_evaluation_bodies.py` (search, hours, needs `data/raw/`); `02_analyse_reviewed.py` (counts from the reviewed file in `data/`) | 6.2.1: 494 of 20,000 passages (2.5%) cite an evaluation body; shares by body; periods; timing of citations |
| `6_2_2_evaluation_2011/` | `01_search_2011_report.py`; `02_analyse_references.py` | 6.2.2: 58 references to the 2011 evaluation; by period; use; known-item test |

Inputs: `data/raw/` (DILA and Assembly plenary records) and `data/intermediate/committee_blocks*.parquet`.
The reviewed files (`*/data/*_reviewed.csv`) record the hand reading of every match.
