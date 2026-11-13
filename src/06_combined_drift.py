"""Feature drift of the test groups of the combined protocol relative to their training reference.
Usage: python src/06_combined_drift.py <path-to-BitcoinHeistData.csv> <outdir>
For every origin and every ransomware family with at least 30 test records (addresses unseen in training):
reference = records of the same family in the training years (continuing family) or all ransomware records of the
training years (emerging family). Drift = two-sample Kolmogorov-Smirnov statistic per topological feature and the
cross-validated ROC-AUC of a classifier that separates reference from test records (classifier two-sample test).
The same measures are computed for the white test records against the white training records."""
import sys, time, warnings
import numpy as np, pandas as pd
from scipy.stats import ks_2samp
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import roc_auc_score
from lightgbm import LGBMClassifier
warnings.filterwarnings('ignore')
SRC, OUT = sys.argv[1], sys.argv[2]
TOPO = ['length', 'weight', 'count', 'looped', 'neighbors', 'income']
df = pd.read_csv(SRC); df['y'] = (df.label != 'white').astype(int); df['addr_code'] = df.address.astype('category').cat.codes
y = df.y.values; groups = df.addr_code.values; yr = df.year.values; fam = df.label.values; idx = np.arange(len(df)); X = df[TOPO].values
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def c2st(a, b, seed=0, cap=20000):
    rng = np.random.default_rng(seed); a = a if len(a) <= cap else rng.choice(a, cap, replace=False); b = b if len(b) <= cap else rng.choice(b, cap, replace=False)
    t = np.r_[np.zeros(len(a)), np.ones(len(b))]; k = int(min(3, len(a), len(b)))
    p = cross_val_predict(LGBMClassifier(n_estimators=100, num_leaves=31, learning_rate=0.1, n_jobs=1, random_state=seed, verbose=-1), X[np.r_[a, b]], t, cv=StratifiedKFold(k, shuffle=True, random_state=seed), method='predict_proba')[:, 1]
    return float(roc_auc_score(t, p))
rows = []
def add(tag, group, status, ref_label, a, b):
    r = {'test': tag, 'group': group, 'status': status, 'reference': ref_label, 'n_ref': len(a), 'n_test': len(b)}
    for j, c in enumerate(TOPO): r['ks_' + c] = float(ks_2samp(X[a, j], X[b, j]).statistic); r['med_ref_' + c] = float(np.median(X[a, j])); r['med_test_' + c] = float(np.median(X[b, j]))
    r['ks_mean'] = float(np.mean([r['ks_' + c] for c in TOPO])); r['ks_max'] = float(np.max([r['ks_' + c] for c in TOPO])); r['c2st_auc'] = c2st(a, b)
    rows.append(r); log(tag, group, status, len(a), len(b), round(r['ks_mean'], 3), round(r['c2st_auc'], 3)); pd.DataFrame(rows).to_csv(OUT + '/combined_drift.csv', index=False)
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
log('EXP5 DONE')
