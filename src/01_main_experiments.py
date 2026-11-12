"""Leakage-aware evaluation of ransomware address detection on BitcoinHeist.
Usage: python src/01_main_experiments.py <path-to-BitcoinHeistData.csv> <outdir>
Note: zeroday.csv written by this script calibrates thresholds on test records and is superseded by
zeroday_val.csv from 03_revision_experiments.py; it is not used in the paper."""
import sys, json, time, glob, warnings
import numpy as np, pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit, GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (average_precision_score, roc_auc_score, f1_score,
    precision_score, recall_score, matthews_corrcoef, accuracy_score)
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
warnings.filterwarnings('ignore')
SRC, OUT = sys.argv[1], sys.argv[2]
SEEDS = [0, 1, 2]
TOPO = ['length', 'weight', 'count', 'looped', 'neighbors', 'income']
TIME = ['year', 'day']
df = pd.read_csv(SRC)
df['y'] = (df.label != 'white').astype(int)
df['addr_code'] = df.address.astype('category').cat.codes
for c in ('weight', 'income', 'count', 'looped', 'neighbors', 'length'):
    df['l_' + c] = np.log1p(df[c])
LOGF = ['l_' + c for c in TOPO]
y = df.y.values; groups = df.addr_code.values
def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)

# ---------- E0: dataset audit ----------
o = {'rows': len(df), 'uniq_addr': int(df.address.nunique()), 'ransom_rows': int(y.sum()),
     'white_rows': int((1 - y).sum()), 'families': int(df[df.y == 1].label.nunique())}
vc = df.address.value_counts(); rep = vc[vc > 1]
o['addr_repeated'] = int(len(rep)); o['rows_of_repeated_addr'] = int(rep.sum()); o['max_rep'] = int(vc.max())
g = df.groupby('addr_code').agg(ny=('y', 'nunique'), nl=('label', 'nunique'), y=('y', 'max'))
o['uniq_ransom_addr'] = int((g.y == 1).sum()); o['addr_mixed_binary'] = int((g.ny > 1).sum()); o['addr_multi_label'] = int((g.nl > 1).sum())
rv = df[df.y == 1].address.value_counts()
o['ransom_rows_in_repeated_addr'] = int(rv[rv > 1].sum()); o['ransom_addr_repeated'] = int((rv > 1).sum())
wv = df[df.y == 0].address.value_counts(); o['white_rows_in_repeated_addr'] = int(wv[wv > 1].sum())
o['dup_full_rows'] = int(df.duplicated(subset=['address'] + TIME + TOPO + ['label']).sum())
o['year_table'] = pd.crosstab(df.year, df.y).rename(columns={0: 'white', 1: 'ransom'}).reset_index().to_dict('records')
o['family_rows'] = df[df.y == 1].label.value_counts().to_dict()
o['family_addr'] = df[df.y == 1].groupby('label').address.nunique().to_dict()
json.dump(o, open(OUT + '/e0.json', 'w'), indent=1); log('E0 done', o['rows'], o['uniq_addr'])

# ---------- models ----------
def models(seed):
    return {
     'LR': make_pipeline(StandardScaler(), LogisticRegression(max_iter=300, C=1.0)),
     'DT': DecisionTreeClassifier(min_samples_leaf=5, random_state=seed),
     'RF': RandomForestClassifier(n_estimators=100, min_samples_leaf=2, max_samples=200000, n_jobs=2, random_state=seed),
     'XGB': XGBClassifier(n_estimators=200, max_depth=8, learning_rate=0.1, tree_method='hist', n_jobs=2, random_state=seed, verbosity=0),
     'LGBM': LGBMClassifier(n_estimators=300, num_leaves=63, learning_rate=0.05, n_jobs=2, random_state=seed, verbose=-1),
    }
def feats(fs, name):
    base = {'all': TIME + TOPO, 'notime': TOPO, 'addr': ['addr_code'] + TIME + TOPO}[fs]
    if name == 'LR':
        base = [('l_' + c if c in TOPO else c) for c in base]
    return base
def metrics(yt, p):
    yh = (p >= 0.5).astype(int)
    return {'pr_auc': average_precision_score(yt, p), 'roc_auc': roc_auc_score(yt, p), 'f1': f1_score(yt, yh, zero_division=0),
            'precision': precision_score(yt, yh, zero_division=0), 'recall': recall_score(yt, yh), 'mcc': matthews_corrcoef(yt, yh)}
def split(kind, seed):
    idx = np.arange(len(df))
    if kind == 'random':
        tr, te = next(StratifiedShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y))
    elif kind == 'address':
        tr, te = next(GroupShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y, groups))
    elif kind == 'temporal':
        tr, te = idx[df.year.values <= 2015], idx[df.year.values >= 2016]
    return tr, te

rows = []; seenrows = []
def run(kind, seed, fs, names):
    tr, te = split(kind, seed)
    tr_addr = set(groups[tr]); seen = np.fromiter((a in tr_addr for a in groups[te]), bool, len(te))
    info = {'n_train': len(tr), 'n_test': len(te), 'pos_test': int(y[te].sum()),
            'test_rows_seen_addr': float(seen.mean()), 'test_pos_seen_addr': float(seen[y[te] == 1].mean())}
    ms = models(seed)
    for name in names:
        f = feats(fs, name); t0 = time.time()
        m = ms[name].fit(df.iloc[tr][f], y[tr]); p = m.predict_proba(df.iloc[te][f])[:, 1]
        r = {'split': kind, 'seed': seed, 'fs': fs, 'model': name, **metrics(y[te], p), **info, 'sec': time.time() - t0}
        rows.append(r); log(kind, seed, fs, name, round(r['pr_auc'], 4), round(r['f1'], 4), int(r['sec']))
        if kind == 'random':
            pos = y[te] == 1; yh = p >= 0.5
            for tag, msk in (('seen', seen), ('unseen', ~seen)):
                mm = pos & msk
                seenrows.append({'seed': seed, 'fs': fs, 'model': name, 'group': tag, 'n_pos': int(mm.sum()),
                                 'recall': float(yh[mm].mean()) if mm.sum() else np.nan})
        pd.DataFrame(rows).to_csv(OUT + '/main.csv', index=False); pd.DataFrame(seenrows).to_csv(OUT + '/seen.csv', index=False)

ALL = ['LR', 'DT', 'RF', 'XGB', 'LGBM']
for fs in ('all', 'notime'):
    for seed in SEEDS:
        run('random', seed, fs, ALL); run('address', seed, fs, ALL)
    for seed in SEEDS:  # temporal split is deterministic; seeds vary the learners only
        run('temporal', seed, fs, ALL if seed == 0 else ['RF', 'XGB', 'LGBM', 'DT'])
for seed in SEEDS:
    run('random', seed, 'addr', ['RF', 'XGB']); run('address', seed, 'addr', ['RF', 'XGB'])
log('main done')

# ---------- zero-day: leave-one-family-out (address-disjoint, no time features) ----------
fam = df.label.values; big = [k for k, v in o['family_rows'].items() if v >= 200]
z = []
def lgbm(seed): return LGBMClassifier(n_estimators=300, num_leaves=63, learning_rate=0.05, n_jobs=2, random_state=seed, verbose=-1)
for seed in SEEDS:
    tr, te = split('address', seed); Xte = df.iloc[te][TOPO]; white_te = y[te] == 0
    base = lgbm(seed).fit(df.iloc[tr][TOPO], y[tr]); pb = base.predict_proba(Xte)[:, 1]
    thr_b = np.quantile(pb[white_te], 0.99)
    for k in big:
        keep = tr[fam[tr] != k]
        m = lgbm(seed).fit(df.iloc[keep][TOPO], y[keep]); p = m.predict_proba(Xte)[:, 1]
        thr = np.quantile(p[white_te], 0.99); mk = fam[te] == k
        z.append({'seed': seed, 'family': k, 'n_test': int(mk.sum()), 'recall_known': float((pb[mk] >= thr_b).mean()),
                  'recall_zero_day': float((p[mk] >= thr).mean()),
                  'ap_known': average_precision_score(np.r_[np.ones(mk.sum()), np.zeros(white_te.sum())], np.r_[pb[mk], pb[white_te]]),
                  'ap_zero_day': average_precision_score(np.r_[np.ones(mk.sum()), np.zeros(white_te.sum())], np.r_[p[mk], p[white_te]])})
        log('zero-day', seed, k, z[-1]['recall_known'], z[-1]['recall_zero_day'])
        pd.DataFrame(z).to_csv(OUT + '/zeroday.csv', index=False)

# ---------- family attribution on ransomware rows (families >= 50 rows) ----------
rr = df[(df.y == 1) & df.label.isin([k for k, v in o['family_rows'].items() if v >= 50])].reset_index(drop=True)
yy = rr.label.astype('category').cat.codes.values; a = []
for seed in SEEDS:
    for kind in ('random', 'address'):
        idx = np.arange(len(rr))
        if kind == 'random': tr, te = next(StratifiedShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, yy))
        else: tr, te = next(GroupShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, yy, rr.addr_code.values))
        for fs, f in (('all', TIME + TOPO), ('notime', TOPO)):
            for name, m in (('RF', RandomForestClassifier(n_estimators=200, n_jobs=2, random_state=seed)),
                            ('LGBM', LGBMClassifier(n_estimators=200, n_jobs=2, random_state=seed, verbose=-1))):
                m.fit(rr.iloc[tr][f], yy[tr]); ph = m.predict(rr.iloc[te][f])
                a.append({'seed': seed, 'split': kind, 'fs': fs, 'model': name, 'acc': accuracy_score(yy[te], ph),
                          'macro_f1': f1_score(yy[te], ph, average='macro', zero_division=0), 'n_classes': int(len(np.unique(yy)))})
pd.DataFrame(a).to_csv(OUT + '/attrib.csv', index=False)
log('ALL DONE')
