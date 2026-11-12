"""Revision experiments for the BitcoinHeist leakage-aware evaluation.
Usage: python src/03_revision_experiments.py <path-to-BitcoinHeistData.csv> <outdir> [stages]
E5  leave-one-family-out with a threshold calibrated on a separate validation set
E6  combined protocol: temporal + address-disjoint + (naturally) unseen families, rolling origins
E2  paired address-purge test with cluster bootstrap; E3 paired calendar-feature test
E4  bootstrap confidence intervals for the temporal and rolling-origin protocols
E1  two further seeds for the main experiment"""
import sys, time, json, warnings
import numpy as np, pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit, GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (average_precision_score, roc_auc_score, f1_score, precision_score, recall_score, matthews_corrcoef)
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
warnings.filterwarnings('ignore')
SRC, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3].split(',') if len(sys.argv) > 3 else ['E5', 'E6', 'E2', 'E4', 'E1']
TOPO = ['length', 'weight', 'count', 'looped', 'neighbors', 'income']; TIME = ['year', 'day']
FS = {'all': TIME + TOPO, 'notime': TOPO}
df = pd.read_csv(SRC); df['y'] = (df.label != 'white').astype(int)
for c in TOPO: df['l_' + c] = np.log1p(df[c])
df['addr_code'] = df.address.astype('category').cat.codes
y = df.y.values; groups = df.addr_code.values; yr = df.year.values; fam = df.label.values; idx = np.arange(len(df))
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def xgb(seed): return XGBClassifier(n_estimators=200, max_depth=8, learning_rate=0.1, tree_method='hist', n_jobs=2, random_state=seed, verbosity=0)
def lgbm(seed): return LGBMClassifier(n_estimators=300, num_leaves=63, learning_rate=0.05, n_jobs=2, random_state=seed, verbose=-1)
MK = {'XGB': xgb, 'LGBM': lgbm}
def prep(scores, yt):
    o = np.argsort(-scores, kind='stable'); s = scores[o]; last = np.r_[np.nonzero(np.diff(s))[0], len(s) - 1]
    return o, yt[o].astype(float), last
def wap(ys, ws, last):
    tp = np.cumsum(ws * ys); tot = np.cumsum(ws); tpg = tp[last]; rec = tpg / tp[-1]
    return float(np.sum(np.diff(rec, prepend=0.0) * (tpg / np.maximum(tot[last], 1e-12))))
def boot(te, preds, n_boot=1000, seed=12345):
    """Cluster bootstrap over addresses; preds = dict name -> scores on te. Returns array [n_boot, len(preds)+1] (last col = positive rate)."""
    yt = y[te]; u, inv = np.unique(groups[te], return_inverse=True); A = len(u); rng = np.random.default_rng(seed)
    P = {k: prep(v, yt) for k, v in preds.items()}; out = np.zeros((n_boot, len(preds) + 1))
    for b in range(n_boot):
        w = np.bincount(rng.integers(0, A, A), minlength=A)[inv].astype(float)
        for j, (k, (o, ys, last)) in enumerate(P.items()): out[b, j] = wap(ys, w[o], last)
        out[b, -1] = (w * yt).sum() / w.sum()
    return out
def ci(a): return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))
fam_rows = df[df.y == 1].label.value_counts(); BIG = [k for k, v in fam_rows.items() if v >= 200]
SEEDS5 = [0, 1, 2, 3, 4]

if 'E5' in ONLY:
    rows = []
    for seed in SEEDS5:
        tr, te = next(GroupShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y, groups))
        a, b = next(GroupShuffleSplit(1, test_size=0.2, random_state=seed).split(tr, y[tr], groups[tr])); fit, val = tr[a], tr[b]
        Xte = df.iloc[te][TOPO]; Xval = df.iloc[val][TOPO]; wte = y[te] == 0; wval = y[val] == 0
        base = lgbm(seed).fit(df.iloc[fit][TOPO], y[fit]); pb = base.predict_proba(Xte)[:, 1]; thr_b = np.quantile(base.predict_proba(Xval)[:, 1][wval], 0.99)
        fpr_b = float((pb[wte] >= thr_b).mean())
        for k in BIG:
            keep = fit[fam[fit] != k]; m = lgbm(seed).fit(df.iloc[keep][TOPO], y[keep]); p = m.predict_proba(Xte)[:, 1]
            thr = np.quantile(m.predict_proba(Xval)[:, 1][wval], 0.99); mk = fam[te] == k
            rows.append({'seed': seed, 'family': k, 'n_total': int(fam_rows[k]), 'n_fit': int((fam[fit] == k).sum()), 'n_val': int((fam[val] == k).sum()), 'n_test': int(mk.sum()),
                         'recall_known': float((pb[mk] >= thr_b).mean()), 'recall_zero_day': float((p[mk] >= thr).mean()), 'fpr_known': fpr_b, 'fpr_zero_day': float((p[wte] >= thr).mean()),
                         'ap_known': average_precision_score(np.r_[np.ones(mk.sum()), np.zeros(wte.sum())], np.r_[pb[mk], pb[wte]]),
                         'ap_zero_day': average_precision_score(np.r_[np.ones(mk.sum()), np.zeros(wte.sum())], np.r_[p[mk], p[wte]])})
            log('E5', seed, k, round(rows[-1]['recall_known'], 3), round(rows[-1]['recall_zero_day'], 3), round(fpr_b, 4), round(rows[-1]['fpr_zero_day'], 4))
            pd.DataFrame(rows).to_csv(OUT + '/zeroday_val.csv', index=False)

if 'E6' in ONLY:
    rows = []; famrows = []
    settings = [(B, [B + 1], f'{B+1}') for B in range(2011, 2017)] + [(2015, [2016, 2017, 2018], '2016-2018')]
    for B, tys, tag in settings:
        hist = idx[yr <= B]; te0 = idx[np.isin(yr, tys)]; seen = np.isin(groups[te0], np.unique(groups[hist])); te = te0[~seen]
        known_fams = set(fam[hist][y[hist] == 1]); emerging = np.array([(f not in known_fams) for f in fam[te]]) & (y[te] == 1); cont = (y[te] == 1) & ~emerging; wte = y[te] == 0
        for seed in [0, 1, 2]:
            a, b = next(GroupShuffleSplit(1, test_size=0.2, random_state=seed).split(hist, y[hist], groups[hist])); fit, val = hist[a], hist[b]; wval = y[val] == 0
            for mname, mk_ in MK.items():
                for fs, f in FS.items():
                    m = mk_(seed).fit(df.iloc[fit][f], y[fit]); p = m.predict_proba(df.iloc[te][f])[:, 1]; thr = np.quantile(m.predict_proba(df.iloc[val][f])[:, 1][wval], 0.99); hit = p >= thr
                    r = {'boundary': B, 'test': tag, 'seed': seed, 'model': mname, 'fs': fs, 'n_test': len(te), 'n_removed_seen': int(seen.sum()), 'pos_removed_seen': int((seen & (y[te0] == 1)).sum()),
                         'pos_fit': int(y[fit].sum()), 'pos_test': int(y[te].sum()), 'n_emerging': int(emerging.sum()), 'n_continuing': int(cont.sum()), 'base_rate': float(y[te].mean()),
                         'pr_auc': average_precision_score(y[te], p) if y[te].sum() else np.nan, 'roc_auc': roc_auc_score(y[te], p) if y[te].sum() else np.nan,
                         'fpr': float(hit[wte].mean()), 'recall': float(hit[y[te] == 1].mean()) if y[te].sum() else np.nan,
                         'recall_emerging': float(hit[emerging].mean()) if emerging.sum() else np.nan, 'recall_continuing': float(hit[cont].mean()) if cont.sum() else np.nan,
                         'precision': float((hit & (y[te] == 1)).sum() / max(hit.sum(), 1))}
                    rows.append(r)
                    for k in np.unique(fam[te][y[te] == 1]):
                        mk = fam[te] == k
                        famrows.append({'boundary': B, 'test': tag, 'seed': seed, 'model': mname, 'fs': fs, 'family': k, 'status': 'continuing' if k in known_fams else 'emerging', 'n_test': int(mk.sum()), 'recall': float(hit[mk].mean())})
            log('E6', tag, seed, {k: round(v, 3) if isinstance(v, float) else v for k, v in rows[-1].items() if k in ('pr_auc', 'fpr', 'recall_emerging', 'recall_continuing', 'n_emerging', 'n_continuing')})
            pd.DataFrame(rows).to_csv(OUT + '/combined.csv', index=False); pd.DataFrame(famrows).to_csv(OUT + '/combined_family.csv', index=False)

REF = {}
if 'E2' in ONLY:
    rows = []; bt = {}
    for seed in range(10):
        tr, te = next(StratifiedShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y)); purge = np.isin(groups[tr], np.unique(groups[te])); trp = tr[~purge]
        r = {'seed': seed, 'n_train': len(tr), 'n_purged': int(purge.sum()), 'pos_train': int(y[tr].sum()), 'pos_purged': int(y[tr][purge].sum())}; preds = {}
        for fs, f in FS.items():
            pf = xgb(seed).fit(df.iloc[tr][f], y[tr]).predict_proba(df.iloc[te][f])[:, 1]; pp = xgb(seed).fit(df.iloc[trp][f], y[trp]).predict_proba(df.iloc[te][f])[:, 1]
            r[f'ap_full_{fs}'] = average_precision_score(y[te], pf); r[f'ap_purged_{fs}'] = average_precision_score(y[te], pp); preds[f'full_{fs}'] = pf; preds[f'purged_{fs}'] = pp
        rows.append(r); log('E2', seed, {k: round(v, 4) for k, v in r.items() if k.startswith('ap_')}, r['n_purged'], r['pos_purged']); pd.DataFrame(rows).to_csv(OUT + '/purge.csv', index=False)
        if seed == 0:
            o, ys, last = prep(preds['full_all'], y[te]); assert abs(wap(ys, np.ones(len(te)), last) - r['ap_full_all']) < 1e-9
            Bm = boot(te, preds, 1000); names = list(preds); col = {k: j for j, k in enumerate(names)}
            d = {'n_boot': 1000}
            for k in names: d[k] = {'point': r['ap_' + k], 'ci': ci(Bm[:, col[k]])}
            for nm, (a_, b_) in {'purge_effect_all': ('full_all', 'purged_all'), 'purge_effect_notime': ('full_notime', 'purged_notime'), 'calendar_effect_full': ('full_all', 'full_notime'), 'calendar_effect_purged': ('purged_all', 'purged_notime')}.items():
                dd = Bm[:, col[a_]] - Bm[:, col[b_]]; d[nm] = {'point': r['ap_' + a_] - r['ap_' + b_], 'ci': ci(dd), 'p_two_sided': float(2 * min((dd <= 0).mean(), (dd >= 0).mean()))}
            d['base_rate'] = {'point': float(y[te].mean()), 'ci': ci(Bm[:, -1])}; bt['random_seed0'] = d; json.dump(bt, open(OUT + '/bootstrap.json', 'w'), indent=1); log('E2 bootstrap', d['purge_effect_all'], d['calendar_effect_full'])
            REF = {'te': te, 'all': preds['full_all'], 'notime': preds['full_notime']}

if 'E4' in ONLY:
    bt = json.load(open(OUT + '/bootstrap.json')) if 'E2' in ONLY else {}
    tr, te = idx[yr <= 2015], idx[yr >= 2016]; preds = {fs: xgb(0).fit(df.iloc[tr][f], y[tr]).predict_proba(df.iloc[te][f])[:, 1] for fs, f in FS.items()}
    Bm = boot(te, preds, 1000); d = {fs: {'point': average_precision_score(y[te], preds[fs]), 'ci': ci(Bm[:, j]), 'lift_ci': ci(Bm[:, j] / Bm[:, -1])} for j, fs in enumerate(preds)}
    d['base_rate'] = {'point': float(y[te].mean()), 'ci': ci(Bm[:, -1])}; bt['temporal'] = d; log('E4 temporal', d)
    roll = []
    for N in range(2011, 2017):
        T = N + 1; tr = idx[yr <= N]; te = idx[yr == T]; preds = {fs: xgb(0).fit(df.iloc[tr][f], y[tr]).predict_proba(df.iloc[te][f])[:, 1] for fs, f in FS.items()}
        Bm = boot(te, preds, 500)
        if REF:
            mk = yr[REF['te']] == T; rte = REF['te'][mk]; rp = {fs: REF[fs][mk] for fs in FS}; Br = boot(rte, rp, 500)
        for j, fs in enumerate(preds):
            r = {'test_year': T, 'fs': fs, 'roll': average_precision_score(y[te], preds[fs]), 'roll_lo': ci(Bm[:, j])[0], 'roll_hi': ci(Bm[:, j])[1], 'base': float(y[te].mean())}
            if REF: r.update({'ref': average_precision_score(y[rte], rp[fs]), 'ref_lo': ci(Br[:, j])[0], 'ref_hi': ci(Br[:, j])[1]})
            roll.append(r)
        log('E4 rolling', T, roll[-2:]); pd.DataFrame(roll).to_csv(OUT + '/rolling_ci.csv', index=False)
    json.dump(bt, open(OUT + '/bootstrap.json', 'w'), indent=1)

if 'E1' in ONLY:
    def models(seed):
        return {'LR': make_pipeline(StandardScaler(), LogisticRegression(max_iter=300, C=1.0)), 'DT': DecisionTreeClassifier(min_samples_leaf=5, random_state=seed),
                'RF': RandomForestClassifier(n_estimators=100, min_samples_leaf=2, max_samples=200000, n_jobs=2, random_state=seed), 'XGB': xgb(seed), 'LGBM': lgbm(seed)}
    def feats(fs, name): return [('l_' + c if (c in TOPO and name == 'LR') else c) for c in FS[fs]]
    def met(yt, p):
        yh = (p >= 0.5).astype(int)
        return {'pr_auc': average_precision_score(yt, p), 'roc_auc': roc_auc_score(yt, p), 'f1': f1_score(yt, yh, zero_division=0), 'precision': precision_score(yt, yh, zero_division=0), 'recall': recall_score(yt, yh), 'mcc': matthews_corrcoef(yt, yh)}
    rows = []; seenrows = []
    def run(kind, seed, fs, names):
        if kind == 'random': tr, te = next(StratifiedShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y))
        elif kind == 'address': tr, te = next(GroupShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y, groups))
        else: tr, te = idx[yr <= 2015], idx[yr >= 2016]
        seen = np.isin(groups[te], np.unique(groups[tr])); info = {'n_train': len(tr), 'n_test': len(te), 'pos_test': int(y[te].sum()), 'test_rows_seen_addr': float(seen.mean()), 'test_pos_seen_addr': float(seen[y[te] == 1].mean())}
        ms = models(seed)
        for name in names:
            f = feats(fs, name); t0 = time.time(); p = ms[name].fit(df.iloc[tr][f], y[tr]).predict_proba(df.iloc[te][f])[:, 1]
            rows.append({'split': kind, 'seed': seed, 'fs': fs, 'model': name, **met(y[te], p), **info, 'sec': time.time() - t0}); log('E1', kind, seed, fs, name, round(rows[-1]['pr_auc'], 4))
            if kind == 'random':
                pos = y[te] == 1; yh = p >= 0.5
                for tag, msk in (('seen', seen), ('unseen', ~seen)):
                    mm = pos & msk; seenrows.append({'seed': seed, 'fs': fs, 'model': name, 'group': tag, 'n_pos': int(mm.sum()), 'recall': float(yh[mm].mean()) if mm.sum() else np.nan})
            pd.DataFrame(rows).to_csv(OUT + '/main_extra.csv', index=False); pd.DataFrame(seenrows).to_csv(OUT + '/seen_extra.csv', index=False)
    ALL = ['LR', 'DT', 'RF', 'XGB', 'LGBM']
    for seed in (3, 4):
        for fs in ('all', 'notime'):
            run('random', seed, fs, ALL); run('address', seed, fs, ALL); run('temporal', seed, fs, ['DT', 'RF', 'XGB', 'LGBM'])
log('EXP2 DONE')
