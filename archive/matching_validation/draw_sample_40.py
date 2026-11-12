# Drew the 40-pair sample now archived as precision_40_v3_coded.csv (excerpt of 02_match_articles.py, main(), unchanged; runs only inside that function).
    # --- precision sample of 40 single-measure pairs (cells 40-41) ---
    pairs = pd.concat([m14, m], ignore_index=True)
    per_all = pairs.groupby("uid")["measure"].nunique()
    solo = pairs[pairs["uid"].map(per_all) == 1].drop_duplicates("uid")
    print(f"{len(solo):,} amendments resolving to one measure")

    lib = (pd.concat([P[["numero", "vm_year", "libelle", "reference"]],
                      vm[["numero", "vm_year", "libelle", "reference"]]])
             .sort_values("vm_year").drop_duplicates("numero", keep="last")
             .set_index("numero"))

    check = solo.sample(40, random_state=1)[["uid", "measure", "article", "dispositif", "expose"]].copy()
    check["mesure_libelle"] = check["measure"].map(lib["libelle"])
    check["mesure_reference"] = check["measure"].map(lib["reference"])
    for c in ["dispositif", "expose"]:
        check[c] = check[c].fillna("").str.replace(r"\s+", " ", regex=True)
    check.to_csv(DATA / "precision_check_40_v3.csv", index=False)
    print(check.shape)

