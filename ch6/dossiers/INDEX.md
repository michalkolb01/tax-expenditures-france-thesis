# Dossiers – tax expenditures discussed in Chapter 6

One Excel file per measure, built by `build_dossiers.py` (sheets: Summary, Annex history,
Amendments, Debates, Evaluation references). Run `python ch6/dossiers/build_dossiers.py`.

| Dossier | Code(s) | Measure | Where in the thesis |
|---|---|---|---|
| `dossier_120114_pension_increases.xlsx` | 120114 | Exemption of pension increases for parents of three or more children (score 0) | 6.4, Pair A |
| `dossier_110215_school_fees.xlsx` | 110215, 110242 | School-fee reductions, secondary (score 0) and higher education (score 1) | 6.4, Pair A; 6.2.2 (known-item test, 17 October 2013) |
| `dossier_120116_work_medal.xlsx` | 120116 | Exemption of work medal bonuses (score 0) | 6.4, Pair B |
| `dossier_120204_long_term_illness.xlsx` | 120204 | Exemption of daily allowances for long-term illness (score 0) | 6.4, Pair B |
| `dossier_110228_local_investment_funds.xlsx` | 110228, 110245 | Local investment funds (FIP), mainland and Corsica (score 0) | 6.4, Pair C |
| `dossier_210305_corsica_investment_credit.xlsx` | 210305 | Corsica investment tax credit | Chapter 6 example (section to confirm) |
| `dossier_200302_research_tax_credit.xlsx` | 200302, 200311 | Research tax credit (CIR); 200311 is the collaborative research credit created in 2023 | 6.2.1 (measures most often cited with evaluation bodies) |
| `dossier_210324_cice.xlsx` | 210324 | Competitiveness and employment tax credit (CICE) | Chapter 6 example (section to confirm) |
| `dossier_520110_dutreil_pact.xlsx` | 520110 | Dutreil pact: partial exemption of inheritance and gift duties on shares under a holding commitment (CGI 787 B/C) | 6.2.1 |
| `dossier_110246_home_services_credit.xlsx` | 110246 | Home-services tax credit (employment of a home worker, CGI 199 sexdecies) | 6.2.1 |
| `dossier_320121_film_audiovisual_credits.xlsx` | 320121, 320129, 320140, 320133, 320144 | Film and audiovisual credits: film production (320121), audiovisual production (320129), international productions (320140), audiovisual distributors (320133, 2009–2011), 320144 (2021–2025, « crédit d'impôt pour dépenses de création audiovisuelle et cinématographique, redevances versées aux organismes… ») | 6.2.1 |

The section column is based on `ch6/6_4_pairs/PAIR_SOURCES.md` and on the measure flags of the 6.2.1
reviewed file; entries marked "to confirm" should be checked against the final text.

## Choice of codes where a name matches several

* **Dutreil pact:** main code **520110** (inheritance and gift duties, in force 2009–2026). Not included:
  **400111**, the exemption of shares under a collective holding commitment from the wealth tax (ISF),
  listed until 2019, which ended with the ISF.
* **Home-services credit:** main code **110246** (credit, 2009–2026). Not included: **110214**, the earlier
  reduction for taxpayers not in work, listed until 2019 and merged into the credit from 2017 (linked to
  110246 in the Chapter 5 dataset); **120134**, the exemption of employer aid for home services (a
  different measure).
* **Research tax credit:** both codes in one dossier, as requested.
* **Film and audiovisual credits:** all cinema, audiovisual and international credits in one dossier.
  Not included: 310201 (SOFICA depreciation), 110244 (SOFICA reduction) and the reduced VAT and
  licence-fee rates (730231, 740106, 950103), which are not credits.

## Sources used for the Debates sheet

* **Committee:** the complete Finance Committee minutes, legislatures 14–17
  (`committee_blocks.parquet`, `committee_blocks_14.parquet`), searched by keyword.
* **Plenary:** the raw plenary archives (DILA `.taz`, Assembly `debats_leg*.xml.zip`) and the complete
  plenary blocks (`debate_blocks*.parquet`) could not be reached when these files were built. The
  plenary passages therefore come from the blocks of matched amendments (`debate_matched*.parquet`)
  and from the corpus of interventions (`turns.parquet`). They are **not complete**. Re-run
  `build_dossiers.py` with `debate_blocks.parquet`, `debate_blocks_14.parquet` and
  `debate_blocks_17.parquet` in `data/intermediate/` to search the complete plenary record; the script
  then uses them automatically and says so in each Summary sheet.

Each dossier's Summary sheet states the source used.

## Limits

* **Amendments** lists the amendments matched to the code in `02_amendments/`. Matching was done only
  for the measures of the 2011 report, so CICE (created in 2013, not in the report), 200311 and 320140/320144 have few or
  no matched amendments. Bill, number and outcome come from the amendment identifier and the matched
  blocks; the author comes from the committee heading where there is one. With
  `amendments_14.parquet` and `amendments_15_17.parquet` present, the script fills them from the full
  amendment data. "Direction" is the classification of `02_amendments/` (`supprime`, `restreint`,
  `maintient`, `etend`, …); "short statement" is that step's one-sentence summary of the amendment.
* **Debates** are found by keyword (name, acronym or CGI article); a passage can mention several
  measures, and a keyword can occasionally match an unrelated passage. The column `found_by` says
  whether a passage was found by keyword or through the amendment link.
* **Evaluation references** are the rows of the 6.2.1 and 6.2.2 reviewed files whose text matches the
  same keywords (or, in 6.2.1, whose measure flag is set).
