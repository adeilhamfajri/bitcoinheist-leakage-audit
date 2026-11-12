"""Regenerates every result table and every figure of the paper from the result files.
Usage: python make_tables_figures.py <results-dir> <out-dir>
Writes <out-dir>/f1.png ... f5.png (Figs. 1-5) and <out-dir>/tables.md."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msstats import *
def f3(x): return f'{x:.3f}'.replace('-', '−')
def sg(x, d=4): return f'{x:+.{d}f}'.replace('-', '−')
WORD = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}
def f2(x): return f'{x:.2f}'.replace('-', '−')
def f1d(x): return f'{x:.1f}'
def n(x): return f'{int(round(x)):,}'
def pct(x, d=1): return f'{100*x:.{d}f}%'
def pm(a, b): return f'{a:.3f} ± {b:.3f}'
def rng(lo, hi, f=f3): return f'{f(lo)}–{f(hi)}'
def pv(p): return '*p* < 0.001' if p < 0.001 else f'*p* = {p:.3f}' if p < 0.1 else f'*p* = {p:.2f}'
def fam(k): return re.sub('^(montreal|padua|princeton)', '', k)

# ---------------- derived numbers ----------------
R_all, A_all, T_all = m('random', 'all', best), m('address', 'all', best), m('temporal', 'all', best)
R_top, A_top, T_top = m('random', 'notime', best), m('address', 'notime', best), m('temporal', 'notime', best)
roc_R = m('random', 'all', best, 'roc_auc'); acc_R = acc('random', 'all', best); rec_R = m('random', 'all', best, 'recall'); prec_R = m('random', 'all', best, 'precision')
pi_R, maj, pi_T = N['pi_random'], N['maj'], N['pi_temp']
seenX, unseenX = sr('all', best, 'seen'), sr('all', best, 'unseen')
addr_R, addr_A = m('random', 'addr', best), m('address', 'addr', best)
rep_share = e0['rows_of_repeated_addr'] / e0['rows']; rr_share = e0['ransom_rows_in_repeated_addr'] / e0['ransom_rows']
W_ = N['welch_all']; PG = N['purge_all']; PGt = N['purge_notime']
B0 = BT['random_seed0']; BTm = BT['temporal']
rc = RC.set_index(['fs', 'test_year']); rct = rc.loc['notime']; rca = rc.loc['all']
ro3 = RO.groupby(['fs', 'test_year'])[['roll_pr_auc', 'ref_pr_auc']].mean()
roll_seed_dev = float(max((ro3.loc[fs].roll_pr_auc - rc.loc[fs].roll).abs().max() for fs in ('all', 'notime')))
CX = CB[CB.model == 'XGB']; cbx = CX.groupby(['test', 'fs']).mean(numeric_only=True); cbs = CX.groupby(['test', 'fs']).std(numeric_only=True, ddof=1)
CL = CB[CB.model == 'LGBM']; cbl = CL.groupby(['test', 'fs']).mean(numeric_only=True)
YEARS = [t for t in TAGS if '-' not in t]; FIX = '2016-2018'
ct = cbx.xs('notime', level='fs'); ca = cbx.xs('all', level='fs'); cty = ct.loc[YEARS]; cay = ca.loc[YEARS]
em_ok = cty[cty.n_emerging >= 100]; co_ok = cty[cty.n_continuing >= 100]

# ---------------- figures ----------------
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Liberation Serif', 'Tinos', 'Times New Roman', 'DejaVu Serif'], 'font.size': 9, 'axes.labelsize': 9, 'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': 0.6, 'hatch.linewidth': 0.5, 'errorbar.capsize': 1.8})
COL = ['#2a78d6', '#eb6834', '#1baf7a']; INK = '#0b0b0b'; EK = dict(ecolor=INK, elinewidth=0.7)
def grid(ax): ax.yaxis.grid(True, lw=0.3, color='#cccccc'); ax.set_axisbelow(True)
n_seen = sr('all', best, 'seen', 'n_pos'); n_unseen = sr('all', best, 'unseen', 'n_pos')
def figures(FIG):
    os.makedirs(FIG, exist_ok=True)
    # Fig. 1: records per year
    yt = pd.DataFrame(e0['year_table']); fig, ax = plt.subplots(figsize=(3.4, 2.25)); x = np.arange(len(yt)); w = 0.38
    ax.bar(x - w/2 - 0.02, yt.white.clip(lower=0.5), w, color=COL[0], label='White'); ax.bar(x + w/2 + 0.02, yt.ransom.clip(lower=0.5), w, color=COL[1], hatch='///', edgecolor='white', label='Ransomware')
    ax.set_yscale('log'); ax.set_xticks(x); ax.set_xticklabels(yt.year); ax.set_ylabel('Records (log scale)'); ax.set_xlabel('Year'); grid(ax)
    ax.legend(frameon=False, ncol=2, loc='upper center', bbox_to_anchor=(0.5, 1.17), fontsize=8.5); fig.tight_layout(); fig.savefig(FIG + 'f1.png', dpi=300); plt.close(fig)
    # Fig. 2: PR-AUC per protocol with SD
    fig, axs = plt.subplots(1, 2, figsize=(3.4, 2.35), sharey=True); mods = ['RF', 'XGB', 'LGBM']; sp = ['random', 'address', 'temporal']; lab = ['Random', 'Address-disjoint', 'Temporal']; ht = ['', '///', '...']
    for ax, fs, ttl in zip(axs, ['all', 'notime'], ['(a) All eight features', '(b) Topological only']):
        for j, s_ in enumerate(sp):
            ax.bar(np.arange(3) + (j - 1) * 0.27, [m(s_, fs, mo) for mo in mods], 0.25, yerr=[sd(s_, fs, mo) for mo in mods], error_kw=EK, color=COL[j], hatch=ht[j], edgecolor='white', label=lab[j])
        ax.set_xticks(np.arange(3)); ax.set_xticklabels(mods); ax.set_title(ttl, fontsize=9); ax.set_ylim(0, 0.6); grid(ax)
    axs[0].set_ylabel('PR-AUC'); h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, frameon=False, ncol=3, loc='upper center', fontsize=8, bbox_to_anchor=(0.53, 1.02), columnspacing=0.9, handlelength=1.3, handletextpad=0.4)
    fig.tight_layout(rect=(0, 0, 1, 0.92)); fig.savefig(FIG + 'f2.png', dpi=300); plt.close(fig)
    # Fig. 3: rolling origin with bootstrap intervals
    fig, axs = plt.subplots(1, 2, figsize=(3.4, 2.45), sharey=True)
    for ax, fs, ttl in zip(axs, ['all', 'notime'], ['(a) All eight features', '(b) Topological only']):
        g = rc.loc[fs]; xs = np.arange(len(g))
        ax.bar(xs - 0.2, g.ref, 0.38, yerr=[g.ref - g.ref_lo, g.ref_hi - g.ref], error_kw=EK, color=COL[0], label='Random-split model')
        ax.bar(xs + 0.2, g.roll, 0.38, yerr=[g.roll - g.roll_lo, g.roll_hi - g.roll], error_kw=EK, color=COL[2], hatch='...', edgecolor='white', label='Rolling origin')
        ax.hlines(g.base, xs - 0.42, xs + 0.42, color=INK, lw=1.0, label='Positive rate')
        ax.set_xticks(xs); ax.set_xticklabels([str(v)[2:] for v in g.index]); ax.set_title(ttl, fontsize=9); ax.set_ylim(0, 0.85); grid(ax); ax.set_xlabel('Test year (20xx)')
    axs[0].set_ylabel('PR-AUC'); h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, frameon=False, ncol=3, loc='upper center', fontsize=8, bbox_to_anchor=(0.53, 1.02), columnspacing=0.9, handlelength=1.3, handletextpad=0.4)
    fig.tight_layout(rect=(0, 0, 1, 0.92)); fig.savefig(FIG + 'f3.png', dpi=300); plt.close(fig)
    # Fig. 4: recall for seen and unseen addresses
    fig, ax = plt.subplots(figsize=(3.4, 2.3)); mo4 = ['DT', 'RF', 'XGB', 'LGBM']
    a_ = [sr('all', k, 'seen') for k in mo4]; b_ = [sr('all', k, 'unseen') for k in mo4]
    ax.bar(np.arange(4) - 0.2, a_, 0.38, yerr=[srsd('all', k, 'seen') for k in mo4], error_kw=EK, color=COL[0], label=f'Seen address (n ≈ {n(n_seen)})')
    ax.bar(np.arange(4) + 0.2, b_, 0.38, yerr=[srsd('all', k, 'unseen') for k in mo4], error_kw=EK, color=COL[1], hatch='///', edgecolor='white', label=f'Unseen address (n ≈ {n(n_unseen)})')
    for i, (u, v) in enumerate(zip(a_, b_)):
        ax.text(i - 0.2, u + 0.035, f'{u:.2f}', ha='center', fontsize=8, color=INK); ax.text(i + 0.2, v + 0.035, f'{v:.2f}', ha='center', fontsize=8, color=INK)
    ax.set_xticks(np.arange(4)); ax.set_xticklabels(mo4); ax.set_ylim(0, 0.95); ax.set_ylabel('Ransomware recall'); grid(ax)
    ax.legend(frameon=False, ncol=1, loc='upper right', fontsize=8, borderaxespad=0.1); fig.tight_layout(); fig.savefig(FIG + 'f4.png', dpi=300); plt.close(fig)
    # Fig. 5: combined protocol, recall for emerging and continuing families
    fig, ax = plt.subplots(figsize=(3.4, 2.35)); xs = np.arange(len(YEARS)); sdt = cbs.xs('notime', level='fs').loc[YEARS]
    for off, col, ncol, c, hh, lb in ((-0.2, 'recall_emerging', 'n_emerging', COL[1], '///', 'Emerging families'), (0.2, 'recall_continuing', 'n_continuing', COL[0], '', 'Continuing families')):
        v = cty[col].values; ok = cty[ncol].values >= 100          # groups with fewer than 100 test records are not drawn
        ax.bar(xs[ok] + off, v[ok], 0.38, yerr=np.nan_to_num(sdt[col].values[ok]), error_kw=EK, color=c, hatch=hh, edgecolor='white', label=lb)
    ax.hlines(cty.fpr.values, xs - 0.42, xs + 0.42, color=INK, lw=1.0, label='Realized false-positive rate')
    ax.set_xticks(xs); ax.set_xticklabels(YEARS); ax.set_xlabel('Test year'); ax.set_ylabel('Recall at calibrated threshold'); grid(ax)
    ax.set_ylim(0, max(0.12, float(np.nanmax(cty[['recall_emerging', 'recall_continuing']].values)) * 1.3))
    h, l = ax.get_legend_handles_labels(); o_ = [1, 2, 0] if len(h) == 3 else list(range(len(h)))
    ax.legend([h[i] for i in o_], [l[i] for i in o_], frameon=False, ncol=1, loc='upper left', fontsize=8, borderaxespad=0.1); fig.tight_layout(); fig.savefig(FIG + 'f5.png', dpi=300); plt.close(fig)


# ---------------- tables ----------------
W3 = WG.seed.unique()
def m3(s_, fs, metric='pr_auc'): return M[(M.split == s_) & (M.fs == fs) & (M.model == best) & (M.seed.isin(W3))][metric].mean()
A3 = M[M.fs == 'addr'].seed.unique()
def ma(s_, fs): return M[(M.split == s_) & (M.fs == fs) & (M.model == best) & (M.seed.isin(A3))].pr_auc.mean()
zk, zz = (N.get('z_pool_known'), N.get('z_pool_zero'))
def tables():
    T = {}
    T['audit'] = dict(cap='Audit of the BitcoinHeist Dataset', header=['Property', 'Value'], widths=[3100, 1800], rows=[
        ['Records (address-day pairs)', n(e0['rows'])], ['Distinct addresses', n(e0['uniq_addr'])],
        ['Addresses occurring more than once', n(e0['addr_repeated'])], ['Records of repeated addresses', n(e0['rows_of_repeated_addr']) + ' (' + pct(rep_share) + ')'],
        ['Ransomware records', n(e0['ransom_rows'])], ['Distinct ransomware addresses', n(e0['uniq_ransom_addr'])],
        ['Ransomware records of repeated addresses', n(e0['ransom_rows_in_repeated_addr']) + ' (' + pct(rr_share) + ')'],
        ['Addresses with conflicting labels', str(e0['addr_multi_label'])], ['Missing values; fully duplicated records', '0; ' + str(e0['dup_full_rows'])], ['Ransomware families', str(e0['families'])]])
    rows6 = []
    for fs, fl in (('all', 'All'), ('notime', 'Topo.')):
        for k in MODELS:
            rows6.append([f'{k} / {fl}'] + [(pm(m(s_, fs, k), sd(s_, fs, k)) if nseed(s_, fs, k) > 1 else f3(m(s_, fs, k))) for s_ in ('random', 'address', 'temporal')])
    T['prauc'] = dict(cap='PR-AUC (Mean ± SD over Seeds) by Classifier, Feature Set, and Split', header=['Model / features', 'Random', 'Address-disjoint', 'Temporal'], rows=rows6, widths=[1300, 1200, 1200, 1200],
                      note=f'All = eight numeric attributes; Topo. = six topological features. Temporal = training on 2011–2015 and testing on 2016–2018. Expected PR-AUC of a random ranking: {f3(pi_R)} (random and address-disjoint splits) and {f3(pi_T)} (temporal split). Under the temporal split the partition is fixed and only the model seed varies; logistic regression and XGBoost, which does not subsample, are deterministic there.')
    def mrow(s_, k): return [k, f3(acc(s_, 'all', k))] + [f3(m(s_, 'all', k, c)) for c in ('precision', 'recall', 'f1', 'mcc', 'pr_auc', 'roc_auc')]
    f1_rand = 2 * pi_R * 0.5 / (pi_R + 0.5); f1_rand_T = 2 * pi_T * 0.5 / (pi_T + 0.5)
    rows7 = [['*Random split*'] + [''] * 7, ['Majority', f3(maj), '–', '0.000', '0.000', '0.000', f3(pi_R), '0.500'], ['Random', '0.500', f3(pi_R), '0.500', f3(f1_rand), '0.000', f3(pi_R), '0.500']] + [mrow('random', k) for k in MODELS]
    rows7 += [['*Address-disjoint split*'] + [''] * 7] + [mrow('address', k) for k in MODELS]
    rows7 += [['*Temporal split*'] + [''] * 7, ['Majority', f3(1 - pi_T), '–', '0.000', '0.000', '0.000', f3(pi_T), '0.500'], ['Random', '0.500', f3(pi_T), '0.500', f3(f1_rand_T), '0.000', f3(pi_T), '0.500']] + [mrow('temporal', k) for k in MODELS]
    T['metrics'] = dict(cap='All Metrics for All Classifiers under the Main Protocols (All Features, Mean over Seeds)', header=['Model', 'Acc.', 'Prec.', 'Rec.', 'F1', 'MCC', 'PR-AUC', 'ROC-AUC'], rows=rows7,
                        widths=[1010, 540, 540, 540, 540, 540, 590, 620], opts=dict(sz=15),
                        note='Acc. = accuracy; Prec. = precision; Rec. = recall. Precision, recall, F1, and MCC are computed at a threshold of 0.5. Majority = every record labeled white; Random = uniform random scores (expected values). The baselines of the address-disjoint split equal those of the random split to three decimals.')
    IJ, IJt, PGa, PGb = N['inject_all'], N['inject_notime'], N['purge_all'], N['purge_notime']
    def cis(d, lo, hi): return f'{sg(d, 3)} ({sg(lo, 3)} to {sg(hi, 3)})'
    def pp(p): return '< 0.001' if p < 0.001 else f'{p:.2f}'
    T['overlap'] = dict(cap='Paired Tests of the Effect of Address Overlap on PR-AUC (XGB, Ten Splits)', header=['Experiment / features', 'With overlap', 'Without', 'Difference (95% CI)', '*p*'], widths=[1000, 620, 620, 1960, 700], opts=dict(sz=15), rows=[
        ['Injection / All', f3(IJ['leaky']), f3(IJ['clean']), cis(IJ['mean'], *IJ['ci']), pp(IJ['p'])],
        ['Injection / Topo.', f3(IJt['leaky']), f3(IJt['clean']), cis(IJt['mean'], *IJt['ci']), pp(IJt['p'])],
        ['Purge / All', f3(PGa['full']), f3(PGa['purged']), cis(PGa['mean'], *PGa['ci']), pp(PGa['p'])],
        ['Purge / Topo.', f3(PGb['full']), f3(PGb['purged']), cis(PGb['mean'], *PGb['ci']), pp(PGb['p'])]],
        note=f'Both models of a pair are scored on identical test records. Injection (leak injection): same-address records are added to the training partition of an address-disjoint split, so both models are trained on repeated addresses ({WORD[IJt["n"]]} splits for the topological features). Purge (address purge): same-address records are deleted from the training partition of a random split, which also removes most repeated addresses from training. Difference = with overlap minus without; paired *t*-test.')
    rows8 = [[fam(k), n(v.n_total), n(v.n_fit), n(v.n_val), n(v.n_test), f3(v.recall_known), f3(v.recall_zero_day)] for k, v in zf.iterrows()]
    rows8 += [['Pooled, Eq. (2)', n(zf.n_total.sum()), n(zf.n_fit.sum()), n(zf.n_val.sum()), n(zf.n_test.sum()), f3(zk), f3(zz)], ['Macro average', '', '', '', '', f3(N['z_macro_known']), f3(N['z_macro_zero'])]]
    T['withheld'] = dict(cap='Withheld-Family Protocol: Records per Family and Recall at a Validation-Calibrated 1% FPR', header=['Family', 'Total', 'Fit', 'Val.', 'Test', 'Known', 'Withheld'], rows=rows8,
                         widths=[1180, 620, 600, 580, 580, 660, 700], opts=dict(sz=15),
                         note=f'Total = records in the complete dataset; Fit, Val., Test = mean number of records in the fitting, validation, and test parts over {WORD[N["z_seeds"]]} address-disjoint splits. Known = family present in the fitting part; Withheld = family removed from it.')
    rows9 = []
    for t_ in YEARS + [FIX]:
        r_, ra_ = ct.loc[t_], ca.loc[t_]
        rows9.append([t_.replace('-', '–'), n(r_.n_emerging), n(r_.n_continuing), f3(r_.base_rate), f3(ra_.pr_auc), f3(r_.pr_auc), pct(r_.fpr, 2).replace('%', ''), f3(r_.recall_emerging) if r_.n_emerging > 0 else '–', f3(r_.recall_continuing) if r_.n_continuing > 0 else '–'])
    T['combined'] = dict(cap=f'Combined Temporal, Address-Disjoint, and Emerging-Family Protocol ({best})', header=['Test', '*n*~E~', '*n*~C~', 'π', 'PR-AUC all', 'PR-AUC topo.', 'FPR (%)', '*R*~E~', '*R*~C~'], rows=rows9,
                         widths=[760, 520, 520, 480, 560, 560, 520, 500, 500], opts=dict(sz=15),
                         note='Training on all years before the test period; test records restricted to addresses unseen in training. *n*~E~, *n*~C~ = ransomware test records of emerging and continuing families; π = positive rate of the test partition. FPR, *R*~E~, and *R*~C~ = realized false-positive rate and recall on emerging and continuing families for the topological model at the threshold calibrated to 1% FPR on validation data. Means over three seeds.')
    rowsw = []
    for fs, fl in (('all', 'All'), ('notime', 'Topo.')):
        for s_, sl in (('random', 'Random'), ('address', 'Address'), ('temporal', 'Temporal')):
            rowsw.append([f'{fl} / {sl}', f3(m3(s_, fs)), f3(wg(s_, fs, 'pr_auc')), f3(wg(s_, fs, 'precision')), f3(wg(s_, fs, 'recall'))])
    T['weighting'] = dict(cap=f'{best} with Class Weighting', header=['Features / split', 'PR-AUC (unw.)', 'PR-AUC (w.)', 'Prec. (w.)', 'Recall (w.)'], rows=rowsw, widths=[1400, 950, 900, 800, 850],
                          note='unw. = unweighted model; w. = positive class weighted by the ratio of negative to positive training records. Means over the same three seeds.')
    return T

if __name__ == '__main__':
    OUTDIR = sys.argv[2].rstrip('/') + '/'; figures(OUTDIR)
    plain = lambda t: re.sub(r'[*~]', '', str(t))
    with open(OUTDIR + 'tables.md', 'w', encoding='utf8') as f:
        for num, key in (('V', 'audit'), ('VI', 'prauc'), ('VII', 'metrics'), ('VIII', 'overlap'), ('IX', 'withheld'), ('X', 'combined'), ('XI', 'weighting')):
            t = tables()[key]; f.write(f'### Table {num}. {plain(t["cap"])}\n\n| ' + ' | '.join(plain(h) for h in t['header']) + ' |\n|' + '---|' * len(t['header']) + '\n')
            for r in t['rows']: f.write('| ' + ' | '.join(plain(c) for c in r) + ' |\n')
            f.write('\n' + (plain(t['note']) + '\n\n' if t.get('note') else ''))
        f.write('### Statistics quoted in the text\n\n```\n' + json.dumps({k: v for k, v in N.items()}, indent=1, default=str) + '\n```\n')
    print('written', OUTDIR)
