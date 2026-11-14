"""Feature drift of the combined-protocol test groups with address-grouped cross-validation (third revision).
Usage: python src/07_grouped_two_sample_test.py <path-to-BitcoinHeistData.csv> <outdir>
Same groups, references, sampling cap, and LightGBM model as 06_combined_drift.py. The classifier two-sample test (C2ST) is now
computed twice on the same records:
  grouped  - StratifiedGroupKFold(3) with the address as group, so that no address has records in both the training
             and the held-out fold (reported in the paper);
  ordinary - StratifiedKFold(3) as in 06_combined_drift.py (sensitivity analysis).
The 95% CI of the grouped ROC-AUC is an address-level cluster bootstrap (1,000 resamples) of the out-of-fold scores.
Writes <outdir>/combined_drift2.csv."""
import sys, time, warnings
import numpy as np, pandas as pd
from scipy.stats import ks_2samp
from sklearn.model_selection import cross_val_predict, StratifiedKFold, StratifiedGroupKFold
from sklearn.metrics import roc_auc_score
from lightgbm import LGBMClassifier
warnings.filterwarnings('ignore')
SRC, OUT = sys.argv[1], sys.argv[2]
TOPO = ['length', 'weight', 'count', 'looped', 'neighbors', 'income']
N_BOOT = 1000
df = pd.read_csv(SRC); df['y'] = (df.label != 'white').astype(int); df['addr_code'] = df.address.astype('category').cat.codes
y = df.y.values; groups = df.addr_code.values; yr = df.year.values; fam = df.label.values; idx = np.arange(len(df)); X = df[TOPO].values
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def model(seed): return LGBMClassifier(n_estimators=100, num_leaves=31, learning_rate=0.1, n_jobs=2, random_state=seed, verbose=-1)

def c2st(a, b, seed=0, cap=20000):
    rng = np.random.default_rng(seed); a = a if len(a) <= cap else rng.choice(a, cap, replace=False); b = b if len(b) <= cap else rng.choice(b, cap, replace=False)
    rows = np.r_[a, b]; t = np.r_[np.zeros(len(a)), np.ones(len(b))]; g = groups[rows]; k = int(min(3, len(a), len(b)))
    p_ord = cross_val_predict(model(seed), X[rows], t, cv=StratifiedKFold(k, shuffle=True, random_state=seed), method='predict_proba')[:, 1]
    k_g = int(min(3, len(np.unique(g[t == 0])), len(np.unique(g[t == 1]))))
    p_grp = cross_val_predict(model(seed), X[rows], t, groups=g, cv=StratifiedGroupKFold(k_g, shuffle=True, random_state=seed), method='predict_proba')[:, 1]
    u, inv = np.unique(g, return_inverse=True); A = len(u); br = np.random.default_rng(12345); bs = np.empty(N_BOOT)
    for i in range(N_BOOT):
        w = np.bincount(br.integers(0, A, A), minlength=A)[inv].astype(float)
        bs[i] = roc_auc_score(t, p_grp, sample_weight=w) if (w[t == 0].sum() > 0 and w[t == 1].sum() > 0) else np.nan
    return {'c2st_auc': float(roc_auc_score(t, p_grp)), 'c2st_lo': float(np.nanpercentile(bs, 2.5)), 'c2st_hi': float(np.nanpercentile(bs, 97.5)),
            'c2st_auc_ordinary': float(roc_auc_score(t, p_ord)), 'n_addr_ref_cv': int(len(np.unique(g[t == 0]))), 'n_addr_test_cv': int(len(np.unique(g[t == 1]))), 'folds_grouped': k_g}

out = []
def add(tag, group, status, ref_label, a, b):
    r = {'test': tag, 'group': group, 'status': status, 'reference': ref_label, 'n_ref': len(a), 'n_test': len(b),
         'n_addr_ref': int(len(np.unique(groups[a]))), 'n_addr_test': int(len(np.unique(groups[b])))}
    for j, c in enumerate(TOPO): r['ks_' + c] = float(ks_2samp(X[a, j], X[b, j]).statistic); r['med_ref_' + c] = float(np.median(X[a, j])); r['med_test_' + c] = float(np.median(X[b, j]))
    r['ks_mean'] = float(np.mean([r['ks_' + c] for c in TOPO])); r['ks_max'] = float(np.max([r['ks_' + c] for c in TOPO])); r.update(c2st(a, b))
    out.append(r); log(tag, group, status, len(a), len(b), 'grouped', round(r['c2st_auc'], 3), (round(r['c2st_lo'], 3), round(r['c2st_hi'], 3)), 'ordinary', round(r['c2st_auc_ordinary'], 3))
    pd.DataFrame(out).to_csv(OUT + '/combined_drift2.csv', index=False)

settings = [(B, [B + 1], f'{B+1}') for B in range(2011, 2017)] + [(2015, [2016, 2017, 2018], '2016-2018')]
for B, tys, tag in settings:
    hist = idx[yr <= B]; te0 = idx[np.isin(yr, tys)]; te = te0[~np.isin(groups[te0], np.unique(groups[hist]))]
    hpos = hist[y[hist] == 1]; known = set(fam[hpos])
    add(tag, 'white', 'white', 'white records of the training years', hist[y[hist] == 0], te[y[te] == 0])
    for k in np.unique(fam[te][y[te] == 1]):
        b = te[fam[te] == k]
        if len(b) < 30: continue
        if k in known:
            a = hist[fam[hist] == k]
            if len(a) >= 30: add(tag, k, 'continuing', 'same family in the training years', a, b)
        else: add(tag, k, 'emerging', 'all ransomware of the training years', hpos, b)
log('EXP6 DONE')
