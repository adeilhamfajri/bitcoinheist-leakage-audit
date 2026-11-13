"""Second-revision experiments for the BitcoinHeist leakage-aware evaluation.
Usage: python src/05_second_revision_experiments.py <path-to-BitcoinHeistData.csv> <outdir> [stages]
R5  feature drift between periods (Kolmogorov-Smirnov statistics and a classifier two-sample test)
R1  combined protocol for all five classifiers, with cluster-bootstrap intervals and paired model comparisons
R4  withheld-family protocol with address-level bootstrap replicates of the family recall
R2  validation-calibrated operating point under the random split (reference for operational measures)
R3  five further repeated splits (seeds 5-9) for the random and address-disjoint protocols
Operating point: a record is flagged when its score is strictly greater than the 99th percentile of the scores of the white
validation records, so that the validation false-positive rate cannot exceed 1% even when many scores are tied."""
import sys, os, time, json, warnings
import numpy as np, pandas as pd
from scipy.stats import ks_2samp
from sklearn.model_selection import StratifiedShuffleSplit, GroupShuffleSplit, cross_val_predict, StratifiedKFold
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
ONLY = sys.argv[3].split(',') if len(sys.argv) > 3 else ['R5', 'R1', 'R4', 'R2', 'R3']
TOPO = ['length', 'weight', 'count', 'looped', 'neighbors', 'income']; TIME = ['year', 'day']
FS = {'all': TIME + TOPO, 'notime': TOPO}
df = pd.read_csv(SRC); df['y'] = (df.label != 'white').astype(int)
for c in TOPO: df['l_' + c] = np.log1p(df[c])
df['addr_code'] = df.address.astype('category').cat.codes
y = df.y.values; groups = df.addr_code.values; yr = df.year.values; fam = df.label.values; idx = np.arange(len(df))
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)
def xgb(seed): return XGBClassifier(n_estimators=200, max_depth=8, learning_rate=0.1, tree_method='hist', n_jobs=2, random_state=seed, verbosity=0)
def lgbm(seed): return LGBMClassifier(n_estimators=300, num_leaves=63, learning_rate=0.05, n_jobs=2, random_state=seed, verbose=-1)
def models(seed):
    return {'LR': make_pipeline(StandardScaler(), LogisticRegression(max_iter=300, C=1.0)), 'DT': DecisionTreeClassifier(min_samples_leaf=5, random_state=seed),
            'RF': RandomForestClassifier(n_estimators=100, min_samples_leaf=2, max_samples=200000, n_jobs=2, random_state=seed), 'XGB': xgb(seed), 'LGBM': lgbm(seed)}
ALL = ['LR', 'DT', 'RF', 'XGB', 'LGBM']
def feats(fs, name): return [('l_' + c if (c in TOPO and name == 'LR') else c) for c in FS[fs]]
def prep(scores, yt):
    o = np.argsort(-scores, kind='stable'); s = scores[o]; last = np.r_[np.nonzero(np.diff(s))[0], len(s) - 1]
    return o, yt[o].astype(float), last
def wap(ys, ws, last):
    tp = np.cumsum(ws * ys); tot = np.cumsum(ws); tpg = tp[last]; rec = tpg / max(tp[-1], 1e-12)
    return float(np.sum(np.diff(rec, prepend=0.0) * (tpg / np.maximum(tot[last], 1e-12))))
def pci(a):
    a = np.asarray(a, float); a = a[~np.isnan(a)]
    return (float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))) if len(a) else (np.nan, np.nan)
fam_rows = df[df.y == 1].label.value_counts(); BIG = [k for k, v in fam_rows.items() if v >= 200]

# ---------------- R5: feature drift between periods ----------------
if 'R5' in ONLY:
    rows = []
    def c2st(a, b, seed=0, cap=20000):
        """Classifier two-sample test: cross-validated ROC-AUC of a model that separates sample a from sample b (0.5 = indistinguishable)."""
        rng = np.random.default_rng(seed); a = a if len(a) <= cap else rng.choice(a, cap, replace=False); b = b if len(b) <= cap else rng.choice(b, cap, replace=False)
        X = df.iloc[np.r_[a, b]][TOPO].values; t = np.r_[np.zeros(len(a)), np.ones(len(b))]
        p = cross_val_predict(LGBMClassifier(n_estimators=100, num_leaves=31, learning_rate=0.1, n_jobs=2, random_state=seed, verbose=-1), X, t, cv=StratifiedKFold(3, shuffle=True, random_state=seed), method='predict_proba')[:, 1]
        return float(roc_auc_score(t, p))
    def add(kind, la, lb, a, b):
        if len(a) < 100 or len(b) < 100: return
        r = {'kind': kind, 'a': la, 'b': lb, 'n_a': len(a), 'n_b': len(b)}
        for c in TOPO:
            r['ks_' + c] = float(ks_2samp(df[c].values[a], df[c].values[b]).statistic); r['med_a_' + c] = float(np.median(df[c].values[a])); r['med_b_' + c] = float(np.median(df[c].values[b]))
        r['ks_mean'] = float(np.mean([r['ks_' + c] for c in TOPO])); r['ks_max'] = float(np.max([r['ks_' + c] for c in TOPO])); r['c2st_auc'] = c2st(a, b)
        rows.append(r); log('R5', kind, la, lb, len(a), len(b), round(r['ks_mean'], 3), round(r['c2st_auc'], 3)); pd.DataFrame(rows).to_csv(OUT + '/drift.csv', index=False)
    for N in range(2011, 2018):                                                   # white records, consecutive years
        add('white_consecutive', f'white {N}', f'white {N+1}', idx[(y == 0) & (yr == N)], idx[(y == 0) & (yr == N + 1)])
    for k in fam_rows.index:                                                      # same family, consecutive years
        for N in range(2011, 2018):
            add('family_consecutive', f'{k} {N}', f'{k} {N+1}', idx[(fam == k) & (yr == N)], idx[(fam == k) & (yr == N + 1)])
    for N in range(2011, 2017):                                                   # emerging families against all earlier ransomware
        prior = idx[(y == 1) & (yr <= N)]; known = set(fam[prior])
        for k in fam_rows.index:
            if k in known: continue
            add('emerging_vs_prior', f'ransomware <= {N}', f'{k} {N+1}', prior, idx[(fam == k) & (yr == N + 1)])
        cont = idx[(y == 1) & (yr == N + 1) & np.isin(fam, list(known))]
        add('continuing_vs_prior', f'ransomware <= {N}', f'continuing {N+1}', prior, cont)
        add('ransomware_consecutive', f'ransomware {N}', f'ransomware {N+1}', idx[(y == 1) & (yr == N)], idx[(y == 1) & (yr == N + 1)])
    for N in range(2011, 2019):                                                   # context: ransomware against white in the same year
        add('ransomware_vs_white', f'white {N}', f'ransomware {N}', idx[(y == 0) & (yr == N)], idx[(y == 1) & (yr == N)])

# ---------------- R1: combined protocol, five classifiers, bootstrap intervals, paired comparisons ----------------
if 'R1' in ONLY:
    rows = []; famrows = []; BR = {}; done = set()
    if os.path.exists(OUT + '/combined5_boot.npz') and os.path.exists(OUT + '/combined5.csv'):      # resume: keep every (test period, seed) whose bootstrap is complete
        z = np.load(OUT + '/combined5_boot.npz'); BR = {k: z[k] for k in z.files}; done = {(k.split('|')[0], int(k.split('|')[1])) for k in BR}
        rows = [r for r in pd.read_csv(OUT + '/combined5.csv', dtype={'test': str}).to_dict('records') if (r['test'], int(r['seed'])) in done]
        famrows = [r for r in pd.read_csv(OUT + '/combined5_family.csv', dtype={'test': str}).to_dict('records') if (r['test'], int(r['seed'])) in done]
        log('R1 resume', sorted(done))
    settings = [(B, [B + 1], f'{B+1}') for B in range(2011, 2017)] + [(2015, [2016, 2017, 2018], '2016-2018')]
    for B, tys, tag in settings:
        hist = idx[yr <= B]; te0 = idx[np.isin(yr, tys)]; seen = np.isin(groups[te0], np.unique(groups[hist])); te = te0[~seen]; yt = y[te]
        known_fams = set(fam[hist][y[hist] == 1]); pos = yt == 1; emerging = np.array([(f not in known_fams) for f in fam[te]]) & pos; cont = pos & ~emerging; wte = yt == 0
        for seed in [0, 1, 2]:
            if (tag, seed) in done: continue
            a, b = next(GroupShuffleSplit(1, test_size=0.2, random_state=seed).split(hist, y[hist], groups[hist])); fit, val = hist[a], hist[b]; wval = y[val] == 0
            ms = {fs: models(seed) for fs in FS}; P = {}; Hh = {}
            for mname in ALL:
                for fs in FS:
                    f = feats(fs, mname); m = ms[fs][mname].fit(df.iloc[fit][f], y[fit]); p = m.predict_proba(df.iloc[te][f])[:, 1]; thr = np.quantile(m.predict_proba(df.iloc[val][f])[:, 1][wval], 0.99); hit = p > thr
                    P[(mname, fs)] = p; Hh[(mname, fs)] = hit
                    rows.append({'boundary': B, 'test': tag, 'seed': seed, 'model': mname, 'fs': fs, 'n_test': len(te), 'n_white_test': int(wte.sum()), 'n_removed_seen': int(seen.sum()), 'pos_removed_seen': int((seen & (y[te0] == 1)).sum()),
                                 'pos_fit': int(y[fit].sum()), 'pos_test': int(pos.sum()), 'n_emerging': int(emerging.sum()), 'n_continuing': int(cont.sum()), 'base_rate': float(yt.mean()),
                                 'pr_auc': average_precision_score(yt, p) if pos.sum() else np.nan, 'roc_auc': roc_auc_score(yt, p) if pos.sum() else np.nan, 'threshold': float(thr), 'n_at_threshold': int((p == thr).sum()),
                                 'alerts': int(hit.sum()), 'tp': int((hit & pos).sum()), 'fp': int((hit & wte).sum()),
                                 'fpr': float(hit[wte].mean()), 'recall': float(hit[pos].mean()) if pos.sum() else np.nan,
                                 'recall_emerging': float(hit[emerging].mean()) if emerging.sum() else np.nan, 'recall_continuing': float(hit[cont].mean()) if cont.sum() else np.nan,
                                 'precision': float((hit & pos).sum() / max(hit.sum(), 1))})
                    for k in np.unique(fam[te][pos]):
                        mk = fam[te] == k
                        famrows.append({'boundary': B, 'test': tag, 'seed': seed, 'model': mname, 'fs': fs, 'family': k, 'status': 'continuing' if k in known_fams else 'emerging', 'n_test': int(mk.sum()), 'n_addr': int(len(np.unique(groups[te][mk]))), 'recall': float(hit[mk].mean())})
            log('R1', tag, seed, {k: round(v, 3) if isinstance(v, float) else v for k, v in rows[-2].items() if k in ('model', 'fs', 'pr_auc', 'fpr', 'recall_emerging', 'recall_continuing')})
            pd.DataFrame(rows).to_csv(OUT + '/combined5.csv', index=False); pd.DataFrame(famrows).to_csv(OUT + '/combined5_family.csv', index=False)
            # cluster bootstrap over test addresses (500 resamples per seed; replicates are stored so that seeds can be pooled and models compared on identical resamples)
            nb = 500; u, inv = np.unique(groups[te], return_inverse=True); A = len(u); rng = np.random.default_rng(12345 + seed)
            PR = {k: prep(v, yt) for k, v in P.items()}; keys = list(P); MET = ['pr_auc', 'fpr', 'recall', 'recall_emerging', 'recall_continuing', 'precision', 'lift', 'fp_per_1000', 'alerts_per_1000']
            R = {k: {mt: np.full(nb, np.nan) for mt in MET} for k in keys}; fams = [k for k in np.unique(fam[te][pos]) if (fam[te] == k).sum() >= 30]; FM = {k: fam[te] == k for k in fams}
            RFm = {(k, f_): np.full(nb, np.nan) for k in keys for f_ in fams}; e_f = emerging.astype(float); c_f = cont.astype(float); p_f = pos.astype(float); w_f = wte.astype(float)
            for bi in range(nb):
                w = np.bincount(rng.integers(0, A, A), minlength=A)[inv].astype(float); wE = (w * e_f).sum(); wC = (w * c_f).sum(); wP = (w * p_f).sum(); wW = (w * w_f).sum(); wT = w.sum()
                for k in keys:
                    o, ys, last = PR[k]; ap = wap(ys, w[o], last); wh = w * Hh[k]; tp = (wh * p_f).sum(); fp = (wh * w_f).sum(); r = R[k]
                    r['pr_auc'][bi] = ap; r['lift'][bi] = ap / (wP / wT) if wP > 0 else np.nan; r['fpr'][bi] = fp / wW; r['recall'][bi] = tp / wP if wP > 0 else np.nan
                    r['recall_emerging'][bi] = (wh * e_f).sum() / wE if wE > 0 else np.nan; r['recall_continuing'][bi] = (wh * c_f).sum() / wC if wC > 0 else np.nan
                    r['precision'][bi] = tp / (tp + fp) if (tp + fp) > 0 else np.nan; r['fp_per_1000'][bi] = 1000 * fp / wT; r['alerts_per_1000'][bi] = 1000 * (tp + fp) / wT
                    for f_ in fams:
                        d = w[FM[f_]].sum(); RFm[(k, f_)][bi] = wh[FM[f_]].sum() / d if d > 0 else np.nan
            for k in keys:
                for mt in MET: BR[f'{tag}|{seed}|{k[0]}|{k[1]}|{mt}'] = R[k][mt]
                for f_ in fams: BR[f'{tag}|{seed}|{k[0]}|{k[1]}|fam|{f_}'] = RFm[(k, f_)]
            np.savez_compressed(OUT + '/combined5_boot.npz', **BR); log('R1 bootstrap', tag, seed, nb)

# ---------------- R4: withheld-family protocol with address-level bootstrap of the family recall ----------------
if 'R4' in ONLY:
    rows = []; BOOT = {}
    for seed in [0, 1, 2, 3, 4]:
        tr, te = next(GroupShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y, groups))
        a, b = next(GroupShuffleSplit(1, test_size=0.2, random_state=seed).split(tr, y[tr], groups[tr])); fit, val = tr[a], tr[b]
        Xte = df.iloc[te][TOPO]; Xval = df.iloc[val][TOPO]; wte = y[te] == 0; wval = y[val] == 0
        base = lgbm(seed).fit(df.iloc[fit][TOPO], y[fit]); pb = base.predict_proba(Xte)[:, 1]; thr_b = np.quantile(base.predict_proba(Xval)[:, 1][wval], 0.99); fpr_b = float((pb[wte] > thr_b).mean())
        for k in BIG:
            keep = fit[fam[fit] != k]; m = lgbm(seed).fit(df.iloc[keep][TOPO], y[keep]); p = m.predict_proba(Xte)[:, 1]; thr = np.quantile(m.predict_proba(Xval)[:, 1][wval], 0.99); mk = fam[te] == k
            fk = (pb[mk] > thr_b).astype(float); fz = (p[mk] > thr).astype(float); u, inv = np.unique(groups[te][mk], return_inverse=True); A = len(u)
            sk = np.bincount(inv, weights=fk, minlength=A); sz = np.bincount(inv, weights=fz, minlength=A); nk = np.bincount(inv, minlength=A).astype(float)
            C = np.random.default_rng(777 + seed).multinomial(A, np.full(A, 1.0 / A), size=1000).astype(float); den = C @ nk
            BOOT[f'{seed}|{k}|known'] = (C @ sk) / den; BOOT[f'{seed}|{k}|withheld'] = (C @ sz) / den; BOOT[f'{seed}|{k}|n'] = den; BOOT[f'{seed}|{k}|tpk'] = C @ sk; BOOT[f'{seed}|{k}|tpz'] = C @ sz
            rows.append({'seed': seed, 'family': k, 'n_total': int(fam_rows[k]), 'n_fit': int((fam[fit] == k).sum()), 'n_val': int((fam[val] == k).sum()), 'n_test': int(mk.sum()), 'n_addr_test': int(A), 'n_white_test': int(wte.sum()), 'n_white_val': int(wval.sum()),
                         'recall_known': float(fk.mean()), 'recall_zero_day': float(fz.mean()), 'fpr_known': fpr_b, 'fpr_zero_day': float((p[wte] > thr).mean()),
                         'ap_known': average_precision_score(np.r_[np.ones(mk.sum()), np.zeros(wte.sum())], np.r_[pb[mk], pb[wte]]), 'ap_zero_day': average_precision_score(np.r_[np.ones(mk.sum()), np.zeros(wte.sum())], np.r_[p[mk], p[wte]])})
            log('R4', seed, k, round(rows[-1]['recall_known'], 3), round(rows[-1]['recall_zero_day'], 3), A)
            pd.DataFrame(rows).to_csv(OUT + '/zeroday_val2.csv', index=False); np.savez_compressed(OUT + '/zeroday_boot.npz', **BOOT)

# ---------------- R2: validation-calibrated operating point under the random split ----------------
if 'R2' in ONLY:
    rows = []
    for seed in [0, 1, 2]:
        tr, te = next(StratifiedShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y)); a, b = next(StratifiedShuffleSplit(1, test_size=0.2, random_state=seed).split(tr, y[tr])); fit, val = tr[a], tr[b]
        yt = y[te]; pos = yt == 1; wte = yt == 0; wval = y[val] == 0; ms = {fs: models(seed) for fs in FS}
        for mname in ALL:
            for fs in FS:
                f = feats(fs, mname); m = ms[fs][mname].fit(df.iloc[fit][f], y[fit]); p = m.predict_proba(df.iloc[te][f])[:, 1]; thr = np.quantile(m.predict_proba(df.iloc[val][f])[:, 1][wval], 0.99); hit = p > thr
                rows.append({'split': 'random', 'seed': seed, 'model': mname, 'fs': fs, 'n_test': len(te), 'pos_test': int(pos.sum()), 'n_white_test': int(wte.sum()), 'base_rate': float(yt.mean()), 'pr_auc': average_precision_score(yt, p), 'threshold': float(thr),
                             'alerts': int(hit.sum()), 'tp': int((hit & pos).sum()), 'fp': int((hit & wte).sum()), 'fpr': float(hit[wte].mean()), 'recall': float(hit[pos].mean()), 'precision': float((hit & pos).sum() / max(hit.sum(), 1))})
                log('R2', seed, mname, fs, round(rows[-1]['fpr'], 4), round(rows[-1]['recall'], 3), round(rows[-1]['precision'], 3)); pd.DataFrame(rows).to_csv(OUT + '/operating_random.csv', index=False)

# ---------------- R3: five further repeated splits for the random and address-disjoint protocols ----------------
if 'R3' in ONLY:
    def met(yt, p):
        yh = (p >= 0.5).astype(int)
        return {'pr_auc': average_precision_score(yt, p), 'roc_auc': roc_auc_score(yt, p), 'f1': f1_score(yt, yh, zero_division=0), 'precision': precision_score(yt, yh, zero_division=0), 'recall': recall_score(yt, yh), 'mcc': matthews_corrcoef(yt, yh)}
    rows = []; seenrows = []
    for seed in (5, 6, 7, 8, 9):
        for fs in ('all', 'notime'):
            for kind in ('random', 'address'):
                tr, te = next(StratifiedShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y)) if kind == 'random' else next(GroupShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y, groups))
                seen = np.isin(groups[te], np.unique(groups[tr])); info = {'n_train': len(tr), 'n_test': len(te), 'pos_test': int(y[te].sum()), 'test_rows_seen_addr': float(seen.mean()), 'test_pos_seen_addr': float(seen[y[te] == 1].mean())}
                ms = models(seed)
                for name in ALL:
                    f = feats(fs, name); t0 = time.time(); p = ms[name].fit(df.iloc[tr][f], y[tr]).predict_proba(df.iloc[te][f])[:, 1]
                    rows.append({'split': kind, 'seed': seed, 'fs': fs, 'model': name, **met(y[te], p), **info, 'sec': time.time() - t0}); log('R3', kind, seed, fs, name, round(rows[-1]['pr_auc'], 4))
                    if kind == 'random':
                        pos = y[te] == 1; yh = p >= 0.5
                        for tag, msk in (('seen', seen), ('unseen', ~seen)):
                            mm = pos & msk; seenrows.append({'seed': seed, 'fs': fs, 'model': name, 'group': tag, 'n_pos': int(mm.sum()), 'recall': float(yh[mm].mean()) if mm.sum() else np.nan})
                    pd.DataFrame(rows).to_csv(OUT + '/main_extra2.csv', index=False); pd.DataFrame(seenrows).to_csv(OUT + '/seen_extra2.csv', index=False)
log('EXP4 DONE')
