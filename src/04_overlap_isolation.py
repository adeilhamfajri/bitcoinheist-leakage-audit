"""Paired tests that isolate the effect of address overlap (leakage channel L1).
Usage: python src/04_overlap_isolation.py <path-to-BitcoinHeistData.csv> <outdir>
E7  leak-injection test: starting from an address-disjoint split, about half of the records of every repeated test
    address are moved into the training partition. A clean model (training partition only) and a leaky model
    (training partition plus the moved records) are scored on the same remaining test records.
E8  decomposition of the address-purge effect: full and purged models of the random split are scored separately on
    ransomware test records whose address is seen or unseen in the full training partition."""
import sys, time, json, warnings
import numpy as np, pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit, GroupShuffleSplit
from sklearn.metrics import average_precision_score
from xgboost import XGBClassifier
warnings.filterwarnings('ignore')
SRC, OUT = sys.argv[1], sys.argv[2]
TOPO = ['length', 'weight', 'count', 'looped', 'neighbors', 'income']; TIME = ['year', 'day']
FS = {'all': TIME + TOPO, 'notime': TOPO}
df = pd.read_csv(SRC); df['y'] = (df.label != 'white').astype(int)
df['addr_code'] = df.address.astype('category').cat.codes
y = df.y.values; groups = df.addr_code.values; idx = np.arange(len(df))
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def xgb(seed): return XGBClassifier(n_estimators=200, max_depth=8, learning_rate=0.1, tree_method='hist', n_jobs=2, random_state=seed, verbosity=0)
def prep(scores, yt):
    o = np.argsort(-scores, kind='stable'); s = scores[o]; last = np.r_[np.nonzero(np.diff(s))[0], len(s) - 1]
    return o, yt[o].astype(float), last
def wap(ys, ws, last):
    tp = np.cumsum(ws * ys); tot = np.cumsum(ws); tpg = tp[last]; rec = tpg / tp[-1]
    return float(np.sum(np.diff(rec, prepend=0.0) * (tpg / np.maximum(tot[last], 1e-12))))
def boot_diff(te, pa, pb, n_boot=1000, seed=12345):
    """Cluster bootstrap over addresses for AP(pa) - AP(pb) on the records te."""
    yt = y[te]; u, inv = np.unique(groups[te], return_inverse=True); A = len(u); rng = np.random.default_rng(seed)
    Pa, Pb = prep(pa, yt), prep(pb, yt); d = np.zeros(n_boot)
    for b in range(n_boot):
        w = np.bincount(rng.integers(0, A, A), minlength=A)[inv].astype(float)
        d[b] = wap(Pa[1], w[Pa[0]], Pa[2]) - wap(Pb[1], w[Pb[0]], Pb[2])
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
def group_ap(yt, p, mask):
    """AP of the positives selected by mask against all negatives."""
    keep = mask | (yt == 0); return float(average_precision_score(yt[keep], p[keep]))

# ---------------- E7: leak injection on the address-disjoint split ----------------
rows = []; bt = {}
for seed in range(10):
    tr, te = next(GroupShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y, groups))
    rng = np.random.default_rng(1000 + seed); o = rng.permutation(len(te)); t = pd.DataFrame({'i': te[o], 'g': groups[te][o]})
    rank = t.groupby('g').cumcount().values; cnt = t.groupby('g').g.transform('size').values
    move = rank < (cnt // 2)                      # singletons stay; a repeated address keeps at least one record in the test partition
    Mv = t.i.values[move]; Tp = t.i.values[~move]; seen = (cnt[~move] >= 2); yt = y[Tp]; pos = yt == 1
    trl = np.r_[tr, Mv]
    for fs, f in FS.items():
        if fs == 'notime' and seed >= 5: continue
        pc = xgb(seed).fit(df.iloc[tr][f], y[tr]).predict_proba(df.iloc[Tp][f])[:, 1]
        pl = xgb(seed).fit(df.iloc[trl][f], y[trl]).predict_proba(df.iloc[Tp][f])[:, 1]
        r = {'seed': seed, 'fs': fs, 'n_train': len(tr), 'n_moved': len(Mv), 'pos_train': int(y[tr].sum()), 'pos_moved': int(y[Mv].sum()), 'n_test': len(Tp), 'pos_test': int(pos.sum()),
             'pos_test_seen': int((pos & seen).sum()), 'rows_test_seen': int(seen.sum()),
             'ap_clean': average_precision_score(yt, pc), 'ap_leaky': average_precision_score(yt, pl),
             'ap_clean_seen': group_ap(yt, pc, pos & seen), 'ap_leaky_seen': group_ap(yt, pl, pos & seen), 'ap_clean_unseen': group_ap(yt, pc, pos & ~seen), 'ap_leaky_unseen': group_ap(yt, pl, pos & ~seen),
             'rec_clean_seen': float((pc[pos & seen] >= 0.5).mean()), 'rec_leaky_seen': float((pl[pos & seen] >= 0.5).mean()),
             'rec_clean_unseen': float((pc[pos & ~seen] >= 0.5).mean()), 'rec_leaky_unseen': float((pl[pos & ~seen] >= 0.5).mean())}
        rows.append(r); log('E7', seed, fs, {k: round(v, 4) for k, v in r.items() if k.startswith(('ap_', 'rec_'))}, r['pos_moved'], r['pos_test_seen'])
        pd.DataFrame(rows).to_csv(OUT + '/inject.csv', index=False)
        if seed == 0:
            lo, hi = boot_diff(Tp, pl, pc); bt[fs] = {'point': r['ap_leaky'] - r['ap_clean'], 'ci': (lo, hi)}; json.dump(bt, open(OUT + '/inject_bootstrap.json', 'w'), indent=1); log('E7 bootstrap', fs, bt[fs])

# ---------------- E8: where does the purge effect come from? ----------------
rows = []
for seed in range(3):
    tr, te = next(StratifiedShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y)); purge = np.isin(groups[tr], np.unique(groups[te])); trp = tr[~purge]
    seen = np.isin(groups[te], np.unique(groups[tr])); yt = y[te]; pos = yt == 1; f = FS['all']
    # share of repeated-address ransomware records (repeated in the complete dataset) before and after the purge
    cnt_all = np.bincount(groups)[groups]; rep = cnt_all >= 2
    pf = xgb(seed).fit(df.iloc[tr][f], y[tr]).predict_proba(df.iloc[te][f])[:, 1]; pp = xgb(seed).fit(df.iloc[trp][f], y[trp]).predict_proba(df.iloc[te][f])[:, 1]
    r = {'seed': seed, 'pos_train': int(y[tr].sum()), 'pos_train_purged': int(y[trp].sum()), 'pos_train_repeated': int((y[tr] == 1)[rep[tr]].sum()), 'pos_train_purged_repeated': int((y[trp] == 1)[rep[trp]].sum()),
         'pos_test_seen': int((pos & seen).sum()), 'pos_test_unseen': int((pos & ~seen).sum()),
         'ap_full': average_precision_score(yt, pf), 'ap_purged': average_precision_score(yt, pp),
         'ap_full_seen': group_ap(yt, pf, pos & seen), 'ap_purged_seen': group_ap(yt, pp, pos & seen), 'ap_full_unseen': group_ap(yt, pf, pos & ~seen), 'ap_purged_unseen': group_ap(yt, pp, pos & ~seen),
         'rec_full_seen': float((pf[pos & seen] >= 0.5).mean()), 'rec_purged_seen': float((pp[pos & seen] >= 0.5).mean()), 'rec_full_unseen': float((pf[pos & ~seen] >= 0.5).mean()), 'rec_purged_unseen': float((pp[pos & ~seen] >= 0.5).mean())}
    rows.append(r); log('E8', seed, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}); pd.DataFrame(rows).to_csv(OUT + '/purge_groups.csv', index=False)
log('EXP3 DONE')
