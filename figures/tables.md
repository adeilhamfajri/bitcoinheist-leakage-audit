### Table V. Audit of the BitcoinHeist Dataset

| Property | Value |
|---|---|
| Records (address-day pairs) | 2,916,697 |
| Distinct addresses | 2,631,095 |
| Addresses occurring more than once | 96,767 |
| Records of repeated addresses | 382,369 (13.1%) |
| Ransomware records | 41,413 |
| Distinct ransomware addresses | 20,849 |
| Ransomware records of repeated addresses | 23,113 (55.8%) |
| Addresses with conflicting labels | 0 |
| Missing values; fully duplicated records | 0; 0 |
| Ransomware families | 28 |

### Table VI. PR-AUC (Mean ± SD over Seeds) by Classifier, Feature Set, and Split

| Model / features | Random | Address-disjoint | Temporal |
|---|---|---|---|
| LR / All | 0.017 ± 0.000 | 0.017 ± 0.001 | 0.011 |
| DT / All | 0.380 ± 0.003 | 0.370 ± 0.013 | 0.018 ± 0.000 |
| RF / All | 0.471 ± 0.006 | 0.455 ± 0.012 | 0.028 ± 0.000 |
| XGB / All | 0.497 ± 0.007 | 0.484 ± 0.011 | 0.028 ± 0.000 |
| LGBM / All | 0.434 ± 0.073 | 0.452 ± 0.010 | 0.027 ± 0.000 |
| LR / Topo. | 0.017 ± 0.000 | 0.017 ± 0.001 | 0.015 |
| DT / Topo. | 0.111 ± 0.001 | 0.107 ± 0.003 | 0.023 ± 0.000 |
| RF / Topo. | 0.177 ± 0.003 | 0.171 ± 0.007 | 0.025 ± 0.000 |
| XGB / Topo. | 0.144 ± 0.002 | 0.139 ± 0.004 | 0.027 ± 0.000 |
| LGBM / Topo. | 0.141 ± 0.003 | 0.134 ± 0.005 | 0.026 ± 0.000 |

All = eight numeric attributes; Topo. = six topological features. Temporal = training on 2011–2015 and testing on 2016–2018. Expected PR-AUC of a random ranking: 0.014 (random and address-disjoint splits) and 0.018 (temporal split). Under the temporal split the partition is fixed and only the model seed varies; logistic regression and XGBoost, which does not subsample, are deterministic there.

### Table VII. All Metrics for All Classifiers under the Main Protocols (All Features, Mean over Seeds)

| Model | Acc. | Prec. | Rec. | F1 | MCC | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| Random split |  |  |  |  |  |  |  |
| Majority | 0.986 | – | 0.000 | 0.000 | 0.000 | 0.014 | 0.500 |
| Random | 0.500 | 0.014 | 0.500 | 0.028 | 0.000 | 0.014 | 0.500 |
| LR | 0.986 | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.615 |
| DT | 0.987 | 0.541 | 0.407 | 0.465 | 0.463 | 0.380 | 0.785 |
| RF | 0.987 | 0.920 | 0.122 | 0.216 | 0.333 | 0.471 | 0.945 |
| XGB | 0.989 | 0.785 | 0.265 | 0.396 | 0.452 | 0.497 | 0.959 |
| LGBM | 0.988 | 0.704 | 0.270 | 0.389 | 0.430 | 0.434 | 0.956 |
| Address-disjoint split |  |  |  |  |  |  |  |
| LR | 0.986 | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.612 |
| DT | 0.986 | 0.538 | 0.397 | 0.456 | 0.455 | 0.370 | 0.776 |
| RF | 0.987 | 0.920 | 0.122 | 0.215 | 0.332 | 0.455 | 0.937 |
| XGB | 0.988 | 0.787 | 0.259 | 0.389 | 0.447 | 0.484 | 0.951 |
| LGBM | 0.988 | 0.751 | 0.264 | 0.390 | 0.441 | 0.452 | 0.948 |
| Temporal split |  |  |  |  |  |  |  |
| Majority | 0.982 | – | 0.000 | 0.000 | 0.000 | 0.018 | 0.500 |
| Random | 0.500 | 0.018 | 0.500 | 0.034 | 0.000 | 0.018 | 0.500 |
| LR | 0.982 | 0.000 | 0.000 | 0.000 | −0.002 | 0.011 | 0.303 |
| DT | 0.979 | 0.040 | 0.008 | 0.014 | 0.010 | 0.018 | 0.505 |
| RF | 0.982 | 0.103 | 0.001 | 0.003 | 0.010 | 0.028 | 0.534 |
| XGB | 0.981 | 0.088 | 0.005 | 0.010 | 0.017 | 0.028 | 0.584 |
| LGBM | 0.981 | 0.061 | 0.004 | 0.007 | 0.011 | 0.027 | 0.566 |

Acc. = accuracy; Prec. = precision; Rec. = recall. Precision, recall, F1, and MCC are computed at a threshold of 0.5. Majority = every record labeled white; Random = uniform random scores (expected values). The baselines of the address-disjoint split equal those of the random split to three decimals.

### Table VIII. Paired Tests of the Effect of Address Overlap on PR-AUC (XGB, Ten Splits)

| Experiment / features | With overlap | Without | Difference (95% CI) | p |
|---|---|---|---|---|
| Injection / All | 0.510 | 0.511 | −0.001 (−0.004 to +0.003) | 0.65 |
| Injection / Topo. | 0.138 | 0.143 | −0.005 (−0.006 to −0.003) | < 0.001 |
| Purge / All | 0.495 | 0.413 | +0.082 (+0.079 to +0.085) | < 0.001 |
| Purge / Topo. | 0.143 | 0.117 | +0.026 (+0.025 to +0.027) | < 0.001 |

Both models of a pair are scored on identical test records. Injection (leak injection): same-address records are added to the training partition of an address-disjoint split, so both models are trained on repeated addresses (five splits for the topological features). Purge (address purge): same-address records are deleted from the training partition of a random split, which also removes most repeated addresses from training. Difference = with overlap minus without; paired t-test.

### Table IX. Withheld-Family Protocol: Records per Family and Recall at a Validation-Calibrated 1% FPR

| Family | Total | Fit | Val. | Test | Known | Withheld |
|---|---|---|---|---|---|---|
| CryptoWall | 12,390 | 6,847 | 1,851 | 3,692 | 0.074 | 0.021 |
| CryptoLocker | 9,315 | 5,118 | 1,194 | 3,003 | 0.056 | 0.031 |
| Cerber | 9,223 | 5,158 | 1,297 | 2,767 | 0.322 | 0.004 |
| Locky | 6,625 | 3,724 | 926 | 1,975 | 0.287 | 0.026 |
| CryptXXX | 2,419 | 1,359 | 352 | 708 | 0.727 | 0.005 |
| NoobCrypt | 483 | 285 | 37 | 160 | 0.036 | 0.027 |
| DMALockerv3 | 354 | 178 | 81 | 94 | 0.150 | 0.146 |
| DMALocker | 251 | 107 | 45 | 99 | 0.166 | 0.165 |
| Pooled, Eq. (2) | 41,060 | 22,776 | 5,786 | 12,498 | 0.196 | 0.021 |
| Macro average |  |  |  |  | 0.227 | 0.053 |

Total = records in the complete dataset; Fit, Val., Test = mean number of records in the fitting, validation, and test parts over five address-disjoint splits. Known = family present in the fitting part; Withheld = family removed from it.

### Table X. Combined Temporal, Address-Disjoint, and Emerging-Family Protocol (XGB)

| Test | nE | nC | π | PR-AUC all | PR-AUC topo. | FPR (%) | RE | RC |
|---|---|---|---|---|---|---|---|---|
| 2012 | 0 | 429 | 0.001 | 0.004 | 0.002 | 1.49 | – | 0.045 |
| 2013 | 10 | 6,691 | 0.019 | 0.035 | 0.030 | 1.72 | 0.000 | 0.057 |
| 2014 | 9,160 | 137 | 0.025 | 0.022 | 0.047 | 2.01 | 0.076 | 0.029 |
| 2015 | 73 | 3,398 | 0.010 | 0.020 | 0.015 | 1.37 | 0.027 | 0.018 |
| 2016 | 15,374 | 104 | 0.042 | 0.077 | 0.065 | 1.18 | 0.027 | 0.042 |
| 2017 | 43 | 3,380 | 0.009 | 0.014 | 0.062 | 1.68 | 0.062 | 0.241 |
| 2016–2018 | 18,851 | 104 | 0.018 | 0.028 | 0.027 | 1.10 | 0.023 | 0.042 |

Training on all years before the test period; test records restricted to addresses unseen in training. nE, nC = ransomware test records of emerging and continuing families; π = positive rate of the test partition. FPR, RE, and RC = realized false-positive rate and recall on emerging and continuing families for the topological model at the threshold calibrated to 1% FPR on validation data. Means over three seeds.

### Table XI. XGB with Class Weighting

| Features / split | PR-AUC (unw.) | PR-AUC (w.) | Prec. (w.) | Recall (w.) |
|---|---|---|---|---|
| All / Random | 0.493 | 0.448 | 0.103 | 0.887 |
| All / Address | 0.485 | 0.437 | 0.102 | 0.869 |
| All / Temporal | 0.028 | 0.029 | 0.036 | 0.173 |
| Topo. / Random | 0.144 | 0.134 | 0.050 | 0.694 |
| Topo. / Address | 0.140 | 0.131 | 0.049 | 0.687 |
| Topo. / Temporal | 0.027 | 0.028 | 0.028 | 0.584 |

unw. = unweighted model; w. = positive class weighted by the ratio of negative to positive training records. Means over the same three seeds.

### Statistics quoted in the text

```
{
 "pi_random": 0.014198694872058605,
 "maj": 0.9858013051279414,
 "pi_addr_min": 0.013095460126068834,
 "pi_addr_max": 0.015359968553315385,
 "n_test_addr_min": 873967,
 "n_test_addr_max": 876179,
 "pi_temp": 0.01771814070724294,
 "n_test_temp": 1079120,
 "pos_test_temp": 19120,
 "n_train_temp": 1837577,
 "pos_seen": 0.5433090332076166,
 "rows_seen": 0.11810195638580452,
 "temp_pos_seen": 0.0086297071129707,
 "temp_rows_seen": 0.0100202016457854,
 "welch_all": {
  "diff": 0.013242964277448532,
  "t": 2.3101302018675525,
  "p": 0.05701761948337537,
  "n": [
   5,
   5
  ],
  "sd_r": 0.00652445751676871,
  "sd_a": 0.011033711128716768
 },
 "welch_notime": {
  "diff": 0.004818584627959227,
  "t": 2.4122719026841115,
  "p": 0.047841398632431684,
  "n": [
   5,
   5
  ],
  "sd_r": 0.0023881586114596733,
  "sd_a": 0.0037745624622602288
 },
 "purge_all": {
  "mean": 0.08186279430174867,
  "sd": 0.004406613795889924,
  "ci": [
   0.07871049269091321,
   0.08501509591258413
  ],
  "t": 58.74644287203738,
  "p": 6.045181949013051e-13,
  "n": 10,
  "full": 0.4950501056540812,
  "purged": 0.41318731135233244,
  "wilcoxon_p": 0.001953125
 },
 "purge_notime": {
  "mean": 0.025925335963005957,
  "sd": 0.001737677776373187,
  "ci": [
   0.02468227616532565,
   0.027168395760686265
  ],
  "t": 47.17969687066237,
  "p": 4.324195216384222e-12,
  "n": 10,
  "full": 0.14321458031435258,
  "purged": 0.11728924435134665,
  "wilcoxon_p": 0.001953125
 },
 "purged_share": 0.08871296138928249,
 "purged_pos_share": 0.49406326537652206,
 "n_purged": 181124.1,
 "pos_purged": 14322.4,
 "inject_all": {
  "mean": -0.0007064974449861761,
  "sd": 0.004770093138878625,
  "ci": [
   -0.004118816514006285,
   0.0027058216240339328
  ],
  "t": -0.46836424828615303,
  "p": 0.650660017479789,
  "n": 10,
  "clean": 0.510914784020965,
  "leaky": 0.5102082865759788,
  "d_seen": 0.022285974648917357,
  "d_unseen": -0.01742295494195443,
  "p_seen": 3.340010503931188e-07,
  "p_unseen": 3.158555489021735e-06,
  "ap_clean_seen": 0.1615907729366366,
  "ap_leaky_seen": 0.18387674758555395,
  "ap_clean_unseen": 0.5792570594878506,
  "ap_leaky_unseen": 0.561834104545896,
  "rec_clean_seen": 0.11826039277987702,
  "rec_leaky_seen": 0.13751138446440267,
  "rec_clean_unseen": 0.45085794767986415,
  "rec_leaky_unseen": 0.4472068386867223
 },
 "inject_notime": {
  "mean": -0.004895818218803599,
  "sd": 0.0012389808078862945,
  "ci": [
   -0.006434216082421425,
   -0.003357420355185773
  ],
  "t": -8.835796545874716,
  "p": 0.0009056579194455557,
  "n": 5,
  "clean": 0.14284079977359565,
  "leaky": 0.13794498155479204,
  "d_seen": 0.006494018352702821,
  "d_unseen": -0.01650158530039004,
  "p_seen": 0.005589202124031132,
  "p_unseen": 3.803087292833387e-06,
  "ap_clean_seen": 0.02726125066721958,
  "ap_leaky_seen": 0.033755269019922395,
  "ap_clean_unseen": 0.14740348080310056,
  "ap_leaky_unseen": 0.13090189550271053,
  "rec_clean_seen": 0.006585441498563579,
  "rec_leaky_seen": 0.008215388896136242,
  "rec_clean_unseen": 0.02945289309686234,
  "rec_leaky_unseen": 0.014710185363266081
 },
 "inj_pos_moved": 3339.6,
 "inj_n_moved": 53318.4,
 "inj_pos_moved_share": 0.11558905583783878,
 "inj_pos_test_seen_share": 0.3982812756438697,
 "inj_pos_test": 9131.1,
 "inj_pos_test_seen": 3640.9,
 "pg": {
  "pos_train": 28989.0,
  "pos_train_purged": 14720.666666666666,
  "pos_train_repeated": 16159.0,
  "pos_train_purged_repeated": 1890.6666666666667,
  "pos_test_seen": 6759.0,
  "pos_test_unseen": 5665.0,
  "ap_full": 0.493349380725459,
  "ap_purged": 0.4135357165332962,
  "ap_full_seen": 0.22582520642287704,
  "ap_purged_seen": 0.0784700940418116,
  "ap_full_unseen": 0.5647691615144036,
  "ap_purged_unseen": 0.6395923922845986,
  "rec_full_seen": 0.11830575679564374,
  "rec_purged_seen": 0.05449123327988863,
  "rec_full_unseen": 0.4401122939073188,
  "rec_purged_unseen": 0.48860126558069616,
  "n": 3
 },
 "z_pool_known": 0.19558329332693228,
 "z_pool_zero": 0.02121939510321647,
 "z_macro_known": 0.22745026383339068,
 "z_macro_zero": 0.0532729006306916,
 "z_pool_known_sd": 0.014548145558499316,
 "z_pool_zero_sd": 0.0013142045749018165,
 "z_fpr_known": [
  0.0095516844540257,
  0.010265872877717
 ],
 "z_fpr_zero": [
  0.0094366848515825,
  0.010426340276884
 ],
 "z_seeds": 5,
 "z_paired_p": 1.1287325329024236e-05
}
```
