"""Extra analyses: rolling-origin temporal evaluation and class-weighting robustness (XGBoost)."""
import sys, time, json, warnings
import numpy as np, pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit, GroupShuffleSplit
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score, precision_score, recall_score, matthews_corrcoef
from xgboost import XGBClassifier
warnings.filterwarnings('ignore')
SRC, OUT = sys.argv[1], sys.argv[2]
TOPO = ['length', 'weight', 'count', 'looped', 'neighbors', 'income']; TIME = ['year', 'day']
FS = {'all': TIME + TOPO, 'notime': TOPO}
df = pd.read_csv(SRC); df['y'] = (df.label != 'white').astype(int); y = df.y.values; yr = df.year.values
groups = df.address.astype('category').cat.codes.values
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def xgb(seed=0, spw=1.0): return XGBClassifier(n_estimators=200, max_depth=8, learning_rate=0.1, tree_method='hist', n_jobs=2, random_state=seed, verbosity=0, scale_pos_weight=spw)
def met(yt, p):
    yh = (p >= 0.5).astype(int)
    return {'pr_auc': average_precision_score(yt, p), 'roc_auc': roc_auc_score(yt, p), 'f1': f1_score(yt, yh, zero_division=0),
            'precision': precision_score(yt, yh, zero_division=0), 'recall': recall_score(yt, yh), 'mcc': matthews_corrcoef(yt, yh)}
idx = np.arange(len(df))
# ---- rolling origin: train on years <= N, test on year N+1; reference = random-split model scored on the same test year
roll = []
SEEDS = [0, 1, 2]
ref_pred = {}
for seed in SEEDS:
    tr, te = next(StratifiedShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y))
    for fs, f in FS.items():
        p = xgb(seed).fit(df.iloc[tr][f], y[tr]).predict_proba(df.iloc[te][f])[:, 1]; ref_pred[(seed, fs)] = (te, p)
    log('reference random split', seed)
for N in range(2011, 2017):
    T = N + 1; tr = idx[yr <= N]; te = idx[yr == T]
    for fs, f in FS.items():
        for seed in SEEDS:
            p = xgb(seed).fit(df.iloc[tr][f], y[tr]).predict_proba(df.iloc[te][f])[:, 1]
            rte, rp = ref_pred[(seed, fs)]; mk = yr[rte] == T
            roll.append({'train_until': N, 'test_year': T, 'fs': fs, 'seed': seed, 'n_train': len(tr), 'pos_train': int(y[tr].sum()), 'n_test': len(te), 'pos_test': int(y[te].sum()),
                         'base_rate': float(y[te].mean()), **{'roll_' + k: v for k, v in met(y[te], p).items()},
                         'ref_pr_auc': average_precision_score(y[rte][mk], rp[mk]), 'ref_recall': recall_score(y[rte][mk], (rp[mk] >= 0.5).astype(int))})
        log('rolling', N, fs, round(np.mean([r['roll_pr_auc'] for r in roll[-3:]]), 4), 'ref', round(np.mean([r['ref_pr_auc'] for r in roll[-3:]]), 4))
        pd.DataFrame(roll).to_csv(OUT + '/rolling.csv', index=False)
# ---- class weighting robustness
w = []
for seed in SEEDS:
    splits = {'random': next(StratifiedShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y)),
              'address': next(GroupShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y, groups)),
              'temporal': (idx[yr <= 2015], idx[yr >= 2016])}
    for kind, (tr, te) in splits.items():
        spw = float((y[tr] == 0).sum() / (y[tr] == 1).sum())
        for fs, f in FS.items():
            p = xgb(seed, spw).fit(df.iloc[tr][f], y[tr]).predict_proba(df.iloc[te][f])[:, 1]
            w.append({'split': kind, 'fs': fs, 'seed': seed, 'spw': spw, **met(y[te], p)}); log('weighted', seed, kind, fs, round(w[-1]['pr_auc'], 4), round(w[-1]['recall'], 3), round(w[-1]['precision'], 3))
            pd.DataFrame(w).to_csv(OUT + '/weighted.csv', index=False)
log('EXTRA DONE')
