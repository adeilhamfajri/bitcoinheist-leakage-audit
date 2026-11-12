"""Loads every result file and computes the statistics quoted in the manuscript. Imported by build5.py; run directly to print them."""
import sys, os, json
import numpy as np, pandas as pd
from scipy import stats
RES = sys.argv[1] if len(sys.argv) > 1 else '../exp/full'
def rd(f):
    p = os.path.join(RES, f)
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
e0 = json.load(open(RES + '/e0.json'))
M = pd.concat([rd('main.csv'), rd('main_extra.csv')], ignore_index=True)
SE = pd.concat([rd('seen.csv'), rd('seen_extra.csv')], ignore_index=True)
A = rd('attrib.csv'); RO = rd('rolling.csv'); WG = rd('weighted.csv')
ZV = rd('zeroday_val.csv'); CB = rd('combined.csv'); CF = rd('combined_family.csv'); PU = rd('purge.csv'); RC = rd('rolling_ci.csv')
BT = json.load(open(RES + '/bootstrap.json')) if os.path.exists(RES + '/bootstrap.json') else {}
INJ = rd('inject.csv'); PGG = rd('purge_groups.csv')
IB = json.load(open(RES + '/inject_bootstrap.json')) if os.path.exists(RES + '/inject_bootstrap.json') else {}
MODELS = ['LR', 'DT', 'RF', 'XGB', 'LGBM']; best = 'XGB'
def sel(split, fs, model): return M[(M.split == split) & (M.fs == fs) & (M.model == model)]
def m(split, fs, model, metric='pr_auc'): return sel(split, fs, model)[metric].mean()
def sd(split, fs, model, metric='pr_auc'): return sel(split, fs, model)[metric].std(ddof=1)
def nseed(split, fs, model): return sel(split, fs, model).seed.nunique()
def acc(split, fs, model):
    g = sel(split, fs, model); tp = g.recall * g.pos_test; fp = np.where(g.precision > 0, tp * (1 / g.precision.replace(0, np.nan) - 1), 0.0)
    return float(((g.n_test - (g.pos_test - tp) - np.nan_to_num(fp)) / g.n_test).mean())
def sr(fs, model, grp, col='recall'): return SE[(SE.fs == fs) & (SE.model == model) & (SE.group == grp)][col].mean()
def srsd(fs, model, grp): return SE[(SE.fs == fs) & (SE.model == model) & (SE.group == grp)].recall.std(ddof=1)
def wg(split, fs, k): return WG[(WG.split == split) & (WG.fs == fs)][k].mean()
def at(split, fs, metric): return A[(A.split == split) & (A.fs == fs) & (A.model == 'RF')][metric].mean()

N = {}
gr = M[M.split == 'random']; N['pi_random'] = float((gr.pos_test / gr.n_test).mean()); N['maj'] = 1 - N['pi_random']
ga = M[M.split == 'address'].drop_duplicates(['seed']); N['pi_addr_min'] = float((ga.pos_test / ga.n_test).min()); N['pi_addr_max'] = float((ga.pos_test / ga.n_test).max())
N['n_test_addr_min'] = int(ga.n_test.min()); N['n_test_addr_max'] = int(ga.n_test.max())
gt = M[M.split == 'temporal']; N['pi_temp'] = float((gt.pos_test / gt.n_test).mean()); N['n_test_temp'] = int(gt.n_test.iloc[0]); N['pos_test_temp'] = int(gt.pos_test.iloc[0]); N['n_train_temp'] = int(gt.n_train.iloc[0])
info = M.groupby('split')[['test_pos_seen_addr', 'test_rows_seen_addr']].mean()
N['pos_seen'] = float(info.loc['random', 'test_pos_seen_addr']); N['rows_seen'] = float(info.loc['random', 'test_rows_seen_addr'])
N['temp_pos_seen'] = float(info.loc['temporal', 'test_pos_seen_addr']); N['temp_rows_seen'] = float(info.loc['temporal', 'test_rows_seen_addr'])
# Welch test random vs address-disjoint, best model, both feature sets
for fs in ('all', 'notime'):
    a, b = sel('random', fs, best).pr_auc.values, sel('address', fs, best).pr_auc.values
    t = stats.ttest_ind(a, b, equal_var=False); N[f'welch_{fs}'] = {'diff': float(a.mean() - b.mean()), 't': float(t.statistic), 'p': float(t.pvalue), 'n': (len(a), len(b)), 'sd_r': float(a.std(ddof=1)), 'sd_a': float(b.std(ddof=1))}
# paired purge test
if len(PU):
    for fs in ('all', 'notime'):
        d = (PU[f'ap_full_{fs}'] - PU[f'ap_purged_{fs}']).values; t = stats.ttest_rel(PU[f'ap_full_{fs}'], PU[f'ap_purged_{fs}'])
        se = d.std(ddof=1) / np.sqrt(len(d)); tc = stats.t.ppf(0.975, len(d) - 1)
        N[f'purge_{fs}'] = {'mean': float(d.mean()), 'sd': float(d.std(ddof=1)), 'ci': (float(d.mean() - tc * se), float(d.mean() + tc * se)), 't': float(t.statistic), 'p': float(t.pvalue), 'n': len(d),
                            'full': float(PU[f'ap_full_{fs}'].mean()), 'purged': float(PU[f'ap_purged_{fs}'].mean()), 'wilcoxon_p': float(stats.wilcoxon(d).pvalue)}
    N['purged_share'] = float((PU.n_purged / PU.n_train).mean()); N['purged_pos_share'] = float((PU.pos_purged / PU.pos_train).mean()); N['n_purged'] = float(PU.n_purged.mean()); N['pos_purged'] = float(PU.pos_purged.mean())
# leak-injection test on the address-disjoint split, and decomposition of the purge effect
if len(INJ):
    for fs in ('all', 'notime'):
        g = INJ[INJ.fs == fs]; d = (g.ap_leaky - g.ap_clean).values; t = stats.ttest_rel(g.ap_leaky, g.ap_clean); se = d.std(ddof=1) / np.sqrt(len(d)); tc = stats.t.ppf(0.975, len(d) - 1)
        N[f'inject_{fs}'] = {'mean': float(d.mean()), 'sd': float(d.std(ddof=1)), 'ci': (float(d.mean() - tc * se), float(d.mean() + tc * se)), 't': float(t.statistic), 'p': float(t.pvalue), 'n': len(d),
                             'clean': float(g.ap_clean.mean()), 'leaky': float(g.ap_leaky.mean()), 'd_seen': float((g.ap_leaky_seen - g.ap_clean_seen).mean()), 'd_unseen': float((g.ap_leaky_unseen - g.ap_clean_unseen).mean()),
                             'p_seen': float(stats.ttest_rel(g.ap_leaky_seen, g.ap_clean_seen).pvalue), 'p_unseen': float(stats.ttest_rel(g.ap_leaky_unseen, g.ap_clean_unseen).pvalue),
                             **{k: float(g[k].mean()) for k in ('ap_clean_seen', 'ap_leaky_seen', 'ap_clean_unseen', 'ap_leaky_unseen', 'rec_clean_seen', 'rec_leaky_seen', 'rec_clean_unseen', 'rec_leaky_unseen')}}
    g = INJ[INJ.fs == 'all']; N['inj_pos_moved'] = float(g.pos_moved.mean()); N['inj_n_moved'] = float(g.n_moved.mean()); N['inj_pos_moved_share'] = float((g.pos_moved / g.pos_train).mean()); N['inj_pos_test_seen_share'] = float((g.pos_test_seen / g.pos_test).mean())
    N['inj_pos_test'] = float(g.pos_test.mean()); N['inj_pos_test_seen'] = float(g.pos_test_seen.mean())
if len(PGG):
    N['pg'] = {k: float(PGG[k].mean()) for k in PGG.columns if k != 'seed'}; N['pg']['n'] = len(PGG)
# zero-day with validation-calibrated threshold
if len(ZV):
    ZV['tp_k'] = ZV.recall_known * ZV.n_test; ZV['tp_z'] = ZV.recall_zero_day * ZV.n_test
    zf = ZV.groupby('family')[['n_total', 'n_fit', 'n_val', 'n_test', 'recall_known', 'recall_zero_day', 'ap_known', 'ap_zero_day']].mean().sort_values('n_total', ascending=False)
    N['z_pool_known'] = float(ZV.tp_k.sum() / ZV.n_test.sum()); N['z_pool_zero'] = float(ZV.tp_z.sum() / ZV.n_test.sum())
    N['z_macro_known'] = float(zf.recall_known.mean()); N['z_macro_zero'] = float(zf.recall_zero_day.mean())
    ps = ZV.groupby('seed')[['tp_k', 'tp_z', 'n_test']].sum(); N['z_pool_known_sd'] = float((ps.tp_k / ps.n_test).std(ddof=1)); N['z_pool_zero_sd'] = float((ps.tp_z / ps.n_test).std(ddof=1))
    fs_ = ZV.drop_duplicates('seed'); N['z_fpr_known'] = (float(fs_.fpr_known.min()), float(fs_.fpr_known.max())); N['z_fpr_zero'] = (float(ZV.fpr_zero_day.min()), float(ZV.fpr_zero_day.max())); N['z_seeds'] = int(ZV.seed.nunique())
    t = stats.ttest_rel(ps.tp_k / ps.n_test, ps.tp_z / ps.n_test); N['z_paired_p'] = float(t.pvalue)
else: zf = pd.DataFrame()
# combined protocol
def cb(tag, model, fs, col): return CB[(CB.test == tag) & (CB.model == model) & (CB.fs == fs)][col].mean()
TAGS = list(dict.fromkeys(CB.test)) if len(CB) else []

if __name__ == '__main__':
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40); pd.set_option('display.float_format', lambda v: f'{v:.4f}')
    print('seeds per cell', {(s, f): nseed(s, f, best) for s in ('random', 'address', 'temporal') for f in ('all', 'notime')})
    print(M.groupby(['fs', 'split', 'model']).pr_auc.agg(['mean', 'std', 'count']).unstack('split').to_string())
    for k, v in N.items(): print(k, v)
    if len(zf): print(zf.to_string())
    if len(CB):
        g = CB.groupby(['test', 'model', 'fs'])[['n_test', 'n_removed_seen', 'pos_removed_seen', 'pos_fit', 'pos_test', 'n_emerging', 'n_continuing', 'base_rate', 'pr_auc', 'roc_auc', 'fpr', 'recall', 'recall_emerging', 'recall_continuing', 'precision']].mean()
        print(g.to_string()); print(CB.groupby(['test', 'model', 'fs'])[['pr_auc', 'recall_emerging', 'recall_continuing', 'fpr']].std().to_string())
        print(CF[(CF.model == 'XGB') & (CF.fs == 'notime')].groupby(['test', 'status', 'family'])[['n_test', 'recall']].mean().to_string())
    if len(PU): print(PU.to_string())
    if len(INJ): print(INJ.to_string())
    if len(PGG): print(PGG.T.to_string())
    if IB: print(IB)
    if BT: print(json.dumps(BT, indent=1))
    if len(RC): print(RC.to_string())
