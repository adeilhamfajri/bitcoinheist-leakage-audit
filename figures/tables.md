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

### Table VI. PR-AUC (Mean ± SD over Repetitions) by Classifier, Feature Set, and Split

| Model / features | Random | Address-disjoint | Temporal |
|---|---|---|---|
| LR / All | 0.017 ± 0.000 | 0.017 ± 0.000 | 0.011 |
| DT / All | 0.382 ± 0.004 | 0.371 ± 0.009 | 0.018 ± 0.000 |
| RF / All | 0.469 ± 0.006 | 0.458 ± 0.009 | 0.028 ± 0.000 |
| XGB / All | 0.495 ± 0.005 | 0.485 ± 0.008 | 0.028 ± 0.000 |
| LGBM / All | 0.442 ± 0.054 | 0.456 ± 0.010 | 0.027 ± 0.000 |
| LR / Topo. | 0.017 ± 0.000 | 0.017 ± 0.001 | 0.015 |
| DT / Topo. | 0.110 ± 0.002 | 0.108 ± 0.003 | 0.023 ± 0.000 |
| RF / Topo. | 0.177 ± 0.003 | 0.174 ± 0.006 | 0.025 ± 0.000 |
| XGB / Topo. | 0.143 ± 0.002 | 0.139 ± 0.003 | 0.027 ± 0.000 |
| LGBM / Topo. | 0.140 ± 0.002 | 0.136 ± 0.005 | 0.026 ± 0.000 |

All = eight numeric attributes; Topo. = six topological features. Random and address-disjoint: ten splits. Temporal = training on 2011–2015 and testing on 2016–2018, five model seeds. Expected PR-AUC of a random ranking: 0.014 (random and address-disjoint splits) and 0.018 (temporal split). Under the temporal split the partition is fixed and only the model seed varies; logistic regression and XGBoost, which does not subsample, are deterministic there.

### Table VII. All Metrics for All Classifiers under the Main Protocols (All Features, Mean over Repetitions)

| Model | Acc. | Prec. | Rec. | F1 | MCC | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| Random split |  |  |  |  |  |  |  |
| Majority | 0.986 | – | 0.000 | 0.000 | 0.000 | 0.014 | 0.500 |
| Random | 0.500 | 0.014 | 0.500 | 0.028 | 0.000 | 0.014 | 0.500 |
| LR | 0.986 | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.615 |
| DT | 0.987 | 0.542 | 0.409 | 0.466 | 0.464 | 0.382 | 0.786 |
| RF | 0.987 | 0.915 | 0.122 | 0.216 | 0.332 | 0.469 | 0.945 |
| XGB | 0.989 | 0.785 | 0.266 | 0.398 | 0.453 | 0.495 | 0.959 |
| LGBM | 0.988 | 0.722 | 0.272 | 0.394 | 0.438 | 0.442 | 0.956 |
| Address-disjoint split |  |  |  |  |  |  |  |
| LR | 0.986 | 0.000 | 0.000 | 0.000 | 0.000 | 0.017 | 0.614 |
| DT | 0.987 | 0.536 | 0.401 | 0.459 | 0.457 | 0.371 | 0.778 |
| RF | 0.987 | 0.917 | 0.121 | 0.213 | 0.330 | 0.458 | 0.939 |
| XGB | 0.988 | 0.784 | 0.263 | 0.393 | 0.450 | 0.485 | 0.953 |
| LGBM | 0.988 | 0.749 | 0.269 | 0.396 | 0.444 | 0.456 | 0.950 |
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

| Feature set | With overlap | Without overlap | Difference (95% CI) | p |
|---|---|---|---|---|
| Leak injection: same-address records added to the training partition of an address-disjoint split |  |  |  |  |
| All features | 0.510 | 0.511 | −0.001 (−0.004 to +0.003) | 0.65 |
| Topological features | 0.138 | 0.143 | −0.005 (−0.006 to −0.003) | < 0.001 |
| Address purge: same-address records deleted from the training partition of a random split |  |  |  |  |
| All features | 0.495 | 0.413 | +0.082 (+0.079 to +0.085) | < 0.001 |
| Topological features | 0.143 | 0.117 | +0.026 (+0.025 to +0.027) | < 0.001 |

Both models of a pair are scored on identical test records. Leak injection changes only the overlap: the address-disjoint training records are kept and the same-address records are added, so the difference measures the effect of overlap (five splits for the topological features). Address purge changes the overlap and the training population at the same time, because the deletion removes most repeated-address ransomware records from training; its difference is therefore not a measure of leakage. Difference = with overlap minus without, averaged over the splits; a negative value means that the model trained with overlap scores lower. The 95% CI is the t-interval of the mean paired difference and p is from a paired t-test; both describe the observed splits of one dataset and are read as descriptive.

### Table IX. Withheld-Family Protocol: Records per Family and Recall (95% CI) at a Validation-Calibrated 1% FPR

| Family | Total | Train | Test | Recall, known | Recall, withheld |
|---|---|---|---|---|---|
| CryptoWall | 12,390 | 8,698 | 3,692 | 0.074 (0.053–0.103) | 0.021 (0.014–0.033) |
| CryptoLocker | 9,315 | 6,312 | 3,003 | 0.056 (0.040–0.077) | 0.031 (0.021–0.043) |
| Cerber | 9,223 | 6,456 | 2,767 | 0.322 (0.293–0.347) | 0.004 (0.002–0.008) |
| Locky | 6,625 | 4,650 | 1,975 | 0.287 (0.263–0.316) | 0.026 (0.018–0.035) |
| CryptXXX | 2,419 | 1,711 | 708 | 0.727 (0.675–0.780) | 0.005 (0.000–0.015) |
| NoobCrypt | 483 | 323 | 160 | 0.036 (0.000–0.080) | 0.027 (0.000–0.057) |
| DMALockerv3 | 354 | 260 | 94 | 0.150 (0.000–0.390) | 0.144 (0.000–0.359) |
| DMALocker | 251 | 152 | 99 | 0.166 (0.000–0.307) | 0.165 (0.000–0.307) |
| Pooled, Eq. (2) | 41,060 | 28,562 | 12,498 | 0.196 (0.175–0.230) | 0.021 (0.017–0.026) |
| Macro average | – | – | – | 0.227 (0.195–0.266) | 0.053 (0.019–0.092) |

Total = ransomware records of the family in the complete dataset; Train, Test = mean number in the training partition (fitting and validation parts, divided 80%/20% by address) and in the test partition over five address-disjoint splits. Every test partition also contains about 862,653 white records, which determine the realized FPR. Known = family present in the fitting part; Withheld = family removed from it. Recall is the mean over the splits; the 95% CI is the percentile interval of the address-level bootstrap replicates pooled over the splits.

### Table X. Combined Temporal, Address-Disjoint, and Emerging-Family Protocol (XGB)

| Test | nE | nC | π | PR-AUC all | PR-AUC topo. | FPR (%) | RE | RC |
|---|---|---|---|---|---|---|---|---|
| 2012 | 0 | 429 | 0.001 | 0.004 | 0.002 | 1.49 | – | 0.045 |
| 2013 | 10 | 6,691 | 0.019 | 0.035 | 0.030 | 1.71 | 0.000 | 0.057 |
| 2014 | 9,160 | 137 | 0.025 | 0.022 | 0.047 | 1.97 | 0.074 | 0.029 |
| 2015 | 73 | 3,398 | 0.010 | 0.020 | 0.015 | 1.37 | 0.027 | 0.018 |
| 2016 | 15,374 | 104 | 0.042 | 0.077 | 0.065 | 1.18 | 0.027 | 0.042 |
| 2017 | 43 | 3,380 | 0.009 | 0.014 | 0.062 | 1.68 | 0.062 | 0.241 |
| 2016–2018 | 18,851 | 104 | 0.018 | 0.028 | 0.027 | 1.10 | 0.023 | 0.042 |

Training on all years before the test period; test records restricted to addresses unseen in training. nE, nC = ransomware test records of emerging and continuing families; π = positive rate of the test partition. FPR, RE, and RC = realized false-positive rate and recall on emerging and continuing families for the topological model at the threshold calibrated to 1% FPR on validation data. Means over three seeds; confidence intervals are given in Table XII and Fig. 5.

### Table XI(a). Combined Protocol for All Classifiers at the Fixed Boundary: Training on 2011–2015, Test on 2016–2018 (Topological Features)

| Model | PR-AUC | Emerging recall | Continuing recall | FPR (%) |
|---|---|---|---|---|
| LR | 0.015 (0.015–0.016) | 0.009 (0.008–0.011) | 0.019 (0.000–0.052) | 1.58 (1.50–1.63) |
| DT | 0.023 (0.022–0.024) | 0.018 (0.013–0.023) | 0.022 (0.000–0.051) | 1.24 (1.18–1.34) |
| RF | 0.025 (0.025–0.026) | 0.020 (0.016–0.024) | 0.058 (0.000–0.099) | 1.17 (1.10–1.25) |
| XGB | 0.027 (0.026–0.028) | 0.023 (0.020–0.026) | 0.042 (0.000–0.088) | 1.10 (1.02–1.17) |
| LGBM | 0.026 (0.025–0.027) | 0.023 (0.019–0.026) | 0.048 (0.000–0.083) | 1.05 (0.97–1.13) |

18,851 emerging-family and 104 continuing-family test records; positive rate 0.018. Emerging recall, continuing recall = recall on emerging-family and continuing-family records (RE and RC of Table X) at the threshold calibrated to 1% FPR on validation data; FPR = realized false-positive rate on the test partition. Values are means over three seeds, with the 95% CI of the address-level bootstrap pooled over the seeds in parentheses.

### Table XI(b). Combined Protocol for All Classifiers Pooled over the Six Yearly Origins: Test Years 2012–2017 (Topological Features)

| Model | Emerging recall | Continuing recall | FPR (%) |
|---|---|---|---|
| LR | 0.020 (0.014–0.030) | 0.043 (0.031–0.058) | 1.78 (1.68–1.86) |
| DT | 0.025 (0.021–0.029) | 0.068 (0.062–0.074) | 1.29 (1.25–1.37) |
| RF | 0.038 (0.031–0.044) | 0.100 (0.093–0.108) | 1.75 (1.70–1.82) |
| XGB | 0.044 (0.039–0.050) | 0.091 (0.083–0.099) | 1.57 (1.49–1.64) |
| LGBM | 0.044 (0.038–0.050) | 0.080 (0.075–0.087) | 1.52 (1.50–1.54) |

24,660 emerging-family and 14,139 continuing-family test records. Columns and intervals as in Table XI(a). Recall = detected records of the six test years divided by all records of the group; FPR = false alerts divided by all white test records. PR-AUC is not reported, because it is not pooled across years with different positive rates (Table X).

### Table XII. Combined Protocol by Family (E = Emerging, C = Continuing): Recall of XGB and Feature Drift Relative to the Training Data

| Test | Family | Type | n | Recall (95% CI) | Drift KS | Drift AUC (95% CI) |
|---|---|---|---|---|---|---|
| 2012 | CryptoLocker | C | 429 | 0.045 (0.011–0.130) | 0.196 | 0.580 (0.392–0.713) |
| 2013 | CryptoLocker | C | 6,691 | 0.057 (0.045–0.070) | 0.154 | 0.693 (0.656–0.724) |
| 2014 | CryptoWall | E | 9,157 | 0.074 (0.061–0.088) | 0.129 | 0.799 (0.773–0.820) |
| 2015 | NoobCrypt | C | 113 | 0.035 (0.000–0.089) | 0.126 | 0.663 (0.520–0.749) |
| 2015 | CryptoWall | C | 3,232 | 0.018 (0.010–0.025) | 0.227 | 0.961 (0.953–0.968) |
| 2016 | CryptXXX | E | 2,419 | 0.019 (0.010–0.031) | 0.232 | 0.991 (0.986–0.994) |
| 2016 | DMALocker | C | 102 | 0.042 (0.000–0.091) | 0.210 | 0.255 (0.080–0.919) |
| 2016 | DMALockerv3 | E | 193 | 0.052 (0.010–0.112) | 0.224 | 0.879 (0.837–0.926) |
| 2016 | Cerber | E | 6,043 | 0.003 (0.002–0.004) | 0.259 | 0.962 (0.959–0.966) |
| 2016 | Locky | E | 6,585 | 0.052 (0.045–0.060) | 0.190 | 0.961 (0.957–0.965) |
| 2017 | DMALockerv3 | C | 129 | 0.072 (0.009–0.160) | 0.130 | 0.598 (0.401–0.787) |
| 2017 | Cerber | C | 3,180 | 0.247 (0.221–0.270) | 0.115 | 0.850 (0.842–0.857) |

Families with at least 100 test records. Type: E = emerging family, C = continuing family; n = test records with an address unseen in training. Recall = detection recall at the calibrated threshold. Drift is measured between the test records and their reference in the training years (the same family for C, all ransomware for E). Drift KS = Kolmogorov–Smirnov statistic averaged over the six topological features. Drift AUC = ROC-AUC of a classifier two-sample test that separates test from reference records (0.5 = indistinguishable), with three-fold cross-validation in which all records of an address fall into the same fold; the 95% CI is a cluster bootstrap over addresses of the out-of-fold scores. The drift AUC quantifies how distinguishable the two feature distributions are; it is not a measure of ransomware detection performance.

### Table XIII. Operational Measures at the Threshold Calibrated to a 1% FPR on Validation Data

| Model | Alerts per 1,000 | False alerts per 1,000 | Precision | Recall | False alerts per true alert | Alerts per split (true alerts) |
|---|---|---|---|---|---|---|
| Random split, all features (875,010 test records, 12,424 ransomware) |  |  |  |  |  |  |
| RF | 16.82 | 9.82 | 0.416 | 0.493 | 1.4 | 14,716 (6,125) |
| XGB | 17.32 | 9.90 | 0.429 | 0.523 | 1.3 | 15,157 (6,496) |
| LGBM | 17.20 | 9.89 | 0.425 | 0.515 | 1.4 | 15,048 (6,396) |
| Combined protocol 2016–2018, all features (1,068,307 test records, 18,955 ransomware) |  |  |  |  |  |  |
| RF | 10.86 | 10.04 | 0.076 | 0.046 | 12.2 | 11,606 (877) |
| XGB | 10.66 | 9.87 | 0.074 | 0.045 | 12.5 | 11,392 (845) |
| LGBM | 10.13 | 9.37 | 0.074 | 0.043 | 12.4 | 10,819 (806) |
| Combined protocol 2016–2018, topological features (1,068,307 test records, 18,955 ransomware) |  |  |  |  |  |  |
| RF | 11.85 | 11.49 | 0.031 | 0.021 | 31.4 | 12,662 (390) |
| XGB | 11.18 | 10.77 | 0.037 | 0.023 | 26.2 | 11,942 (439) |
| LGBM | 10.77 | 10.36 | 0.038 | 0.023 | 25.5 | 11,504 (434) |

Denominator of the per-1,000 measures = all test records of the protocol (white and ransomware). Alerts = test records scored above the threshold; false alerts = white records among them (false positives); true alerts = ransomware records among them. Precision = true alerts / alerts; recall = true alerts / ransomware test records. All rates and ratios are computed from the counts summed over three seeds before rounding; the last column gives the mean number of alerts per split, with the true alerts in parentheses.

### Table XIV. XGB with Class Weighting

| Features / split | PR-AUC (unw.) | PR-AUC (w.) | Prec. (w.) | Recall (w.) |
|---|---|---|---|---|
| All / Random | 0.493 | 0.448 | 0.103 | 0.887 |
| All / Address | 0.485 | 0.437 | 0.102 | 0.869 |
| All / Temporal | 0.028 | 0.029 | 0.036 | 0.173 |
| Topo. / Random | 0.144 | 0.134 | 0.050 | 0.694 |
| Topo. / Address | 0.140 | 0.131 | 0.049 | 0.687 |
| Topo. / Temporal | 0.027 | 0.028 | 0.028 | 0.584 |

unw. = without class weighting; w. = with class weighting (positive class weighted by the ratio of negative to positive training records). Both columns are means over the same three seeds; Tables VI and VII report ten splits for the random and address-disjoint protocols.

### Table XV. Between-Repetition Variation and Sampling Uncertainty of Key Estimates (Topological Features)

| Estimate | k | Mean (pooled 95% CI) | SD between | SE within | Per-repetition 95% CIs |
|---|---|---|---|---|---|
| Withheld family, known (LGBM) | 5 | 0.196 (0.175–0.230) | 0.0145 | 0.0074 | 0.169–0.236 |
| Withheld family, withheld (LGBM) | 5 | 0.021 (0.017–0.026) | 0.0013 | 0.0021 | 0.016–0.027 |
| Combined 2016–2018, PR-AUC (XGB) | 3 | 0.027 (0.026–0.028) | 0.0004 | 0.0004 | 0.026–0.028 |
| Combined 2016–2018, RE (XGB) | 3 | 0.023 (0.020–0.026) | 0.0015 | 0.0012 | 0.019–0.027 |
| Combined 2014, RE (XGB) | 3 | 0.074 (0.061–0.088) | 0.0014 | 0.0065 | 0.060–0.088 |
| Combined 2017, RC (XGB) | 3 | 0.241 (0.216–0.263) | 0.0130 | 0.0075 | 0.212–0.266 |
| ΔPR-AUC × 10^3^, RF − XGB, 2016–2018 | 3 | −1.5 (−2.3 to −0.5) | 0.7 | 0.2 | −2.4 to −0.4 |
| ΔPR-AUC × 10^3^, LGBM − XGB, 2016–2018 | 3 | −0.7 (−1.0 to −0.3) | 0.2 | 0.1 | −1.1 to −0.3 |

k = number of repetitions (address-disjoint splits for the withheld-family protocol, seeds for the combined protocol). SD between = standard deviation of the point estimates over the repetitions; SE within = mean standard deviation of the address-level bootstrap replicates within one repetition; per-repetition 95% CIs = lowest lower and highest upper limit of the intervals computed separately for each repetition. Δ = paired difference on identical resamples, given in units of 0.001.

### Statistics quoted in the text

```
{
 "pi_random": 0.014198694872058607,
 "maj": 0.9858013051279414,
 "pi_addr_min": 0.013095460126068834,
 "pi_addr_max": 0.015359968553315385,
 "n_test_addr_min": 873429,
 "n_test_addr_max": 876179,
 "n_addr_splits": 10,
 "pi_temp": 0.01771814070724294,
 "n_test_temp": 1079120,
 "pos_test_temp": 19120,
 "n_train_temp": 1837577,
 "pos_seen": 0.5434733747220838,
 "rows_seen": 0.11802357838282383,
 "temp_pos_seen": 0.0086297071129707,
 "temp_rows_seen": 0.0100202016457854,
 "welch_all": {
  "diff": 0.00978796350759259,
  "t": 3.123813250352034,
  "p": 0.006813374458486286,
  "n": [
   10,
   10
  ],
  "sd_r": 0.005356478242415899,
  "sd_a": 0.008335839850527353
 },
 "welch_notime": {
  "diff": 0.003982553051862514,
  "t": 3.3788927262723316,
  "p": 0.004619615219813396,
  "n": [
   10,
   10
  ],
  "sd_r": 0.0017483800148934431,
  "sd_a": 0.003291727970744572
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
 "z_pool_zero": 0.02113938230116814,
 "z_macro_known": 0.22745026383339068,
 "z_macro_zero": 0.05300890024135145,
 "z_pool_known_sd": 0.014548145558499316,
 "z_pool_zero_sd": 0.0012739085275592778,
 "z_fpr_known": [
  0.0095516844540257,
  0.0102600703269157
 ],
 "z_fpr_zero": [
  0.0094081197422318,
  0.010426340276884
 ],
 "z_seeds": 5,
 "z_paired_p": 1.1297315156980086e-05,
 "z_pool_known_ci": [
  0.17461703530919542,
  0.22992341887926898
 ],
 "z_pool_zero_ci": [
  0.01677570832527252,
  0.025975670392095144
 ],
 "z_macro_known_ci": [
  0.19543184039876457,
  0.26611073413850395
 ],
 "z_macro_zero_ci": [
  0.019077022167443867,
  0.09174948992864547
 ],
 "z_white_test": 862652.8
}
```
