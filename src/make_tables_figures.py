"""Regenerates every result table and every figure of the paper from the result files.
Usage: python make_tables_figures.py <results-dir> <out-dir>
Writes <out-dir>/f1.png ... f5.png (Figs. 1-5) and <out-dir>/tables.md (Tables V-XV and the statistics quoted in the text)."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msstats import *
def f3(x): return f'{x:.3f}'.replace('-', '−')
def sg(x, d=4): return f'{0:.{d}f}' if round(x, d) == 0 else f'{x:+.{d}f}'.replace('-', '−')
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
em_ok = cty[cty.n_emerging > 0]; co_ok = cty[cty.n_continuing > 0]      # every group that has at least one positive test record
ENS = ['RF', 'XGB', 'LGBM']
def ci3(c, f=f3): return f'{f(c[0])}–{f(c[1])}'
def vci(v, c, f=f3): return f'{f(v)} ({f(c[0])}–{f(c[1])})'
def v95(v, c, f=f3): return f'{f(v)} (95% CI {f(c[0])}–{f(c[1])})'

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
    # Fig. 5: combined protocol, recall for emerging and continuing families against the realized FPR, three tree ensembles,
    # pooled-bootstrap intervals; marker fill encodes the size of the group, tick labels give the number of records per group
    from matplotlib.lines import Line2D; plt.rcParams['mathtext.fontset'] = 'stix'
    CAL = '#b3261e'      # calibrated FPR (dashed, red) against realized FPR (solid, black)
    fig, axs = plt.subplots(3, 1, figsize=(3.4, 5.6), sharex=True, sharey=True); xs = np.arange(len(YEARS))
    for ax, mo in zip(axs, ENS):
        ax.axhline(0.01, color=CAL, lw=1.0, ls=(0, (4, 2)), zorder=1)
        for off, col, ncol, c, mk, ms_ in ((-0.18, 'recall_emerging', 'n_emerging', COL[1], '^', 6.0), (0.18, 'recall_continuing', 'n_continuing', COL[0], 'o', 5.2)):
            for i, t_ in enumerate(YEARS):
                nn = cb(t_, mo, 'notime', ncol)
                if nn <= 0: continue
                v = cb(t_, mo, 'notime', col); lo, hi = cci(t_, mo, 'notime', col); big = nn >= 100
                ax.errorbar(i + off, v, yerr=[[max(v - lo, 0)], [max(hi - v, 0)]], fmt=mk, ms=ms_, color=c, ecolor=c, elinewidth=1.1, capsize=2.6,
                            mfc=c if big else 'white', mec=c, mew=1.1, zorder=3)
        ax.hlines([cb(t_, mo, 'notime', 'fpr') for t_ in YEARS], xs - 0.44, xs + 0.44, color=INK, lw=1.7, zorder=2)
        ax.text(0.02, 0.86, mo, transform=ax.transAxes, fontsize=10, fontweight='bold'); grid(ax); ax.set_xticks(xs); ax.set_ylim(-0.012, 0.33); ax.set_yticks([0, 0.1, 0.2, 0.3])
        ax.tick_params(axis='y', labelsize=9)
    lab_ = [f"{t_}\n{n(cb(t_, best, 'notime', 'n_emerging')) if cb(t_, best, 'notime', 'n_emerging') > 0 else '–'}\n{n(cb(t_, best, 'notime', 'n_continuing'))}" for t_ in YEARS]
    axs[2].set_xticklabels(lab_, fontsize=8.2, linespacing=1.2)
    for yy, tx, cc in ((-0.085, 'Year', INK), (-0.172, '$n_\\mathrm{E}$', COL[1]), (-0.262, '$n_\\mathrm{C}$', COL[0])):
        axs[2].text(-0.15, yy, tx, transform=axs[2].transAxes, fontsize=8.2, ha='left', va='top', color=cc)
    axs[1].set_ylabel('Recall at the calibrated threshold', fontsize=9.5)
    hd = [Line2D([], [], marker='^', color=COL[1], ls='none', ms=6.0), Line2D([], [], marker='o', color=COL[0], ls='none', ms=5.2),
          Line2D([], [], marker='o', color='#555555', mfc='white', ls='none', ms=5.2), Line2D([], [], color=INK, lw=1.7), Line2D([], [], color=CAL, lw=1.0, ls=(0, (4, 2)))]
    fig.legend(hd, ['Emerging families (triangles)', 'Continuing families (circles)', 'Open marker: fewer than 100 records', 'Realized false-positive rate', 'Calibrated false-positive rate (1%)'],
               frameon=False, ncol=1, loc='upper center', fontsize=8.6, bbox_to_anchor=(0.56, 1.0), labelspacing=0.25)
    fig.tight_layout(rect=(0, 0, 1, 0.865)); fig.savefig(FIG + 'f5.png', dpi=300); plt.close(fig)


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
    T['prauc'] = dict(cap='PR-AUC (Mean ± SD over Repetitions) by Classifier, Feature Set, and Split', header=['Model / features', 'Random', 'Address-disjoint', 'Temporal'], rows=rows6, widths=[1300, 1200, 1200, 1200],
                      note=f'All = eight numeric attributes; Topo. = six topological features. Random and address-disjoint: {WORD[nseed("random", "all", best)]} splits. Temporal = training on 2011–2015 and testing on 2016–2018, {WORD[nseed("temporal", "all", "RF")]} model seeds. Expected PR-AUC of a random ranking: {f3(pi_R)} (random and address-disjoint splits) and {f3(pi_T)} (temporal split). Under the temporal split the partition is fixed and only the model seed varies; logistic regression and XGBoost, which does not subsample, are deterministic there.')
    def mrow(s_, k): return [k, f3(acc(s_, 'all', k))] + [f3(m(s_, 'all', k, c)) for c in ('precision', 'recall', 'f1', 'mcc', 'pr_auc', 'roc_auc')]
    f1_rand = 2 * pi_R * 0.5 / (pi_R + 0.5); f1_rand_T = 2 * pi_T * 0.5 / (pi_T + 0.5)
    rows7 = [['*Random split*'] + [''] * 7, ['Majority', f3(maj), '–', '0.000', '0.000', '0.000', f3(pi_R), '0.500'], ['Random', '0.500', f3(pi_R), '0.500', f3(f1_rand), '0.000', f3(pi_R), '0.500']] + [mrow('random', k) for k in MODELS]
    rows7 += [['*Address-disjoint split*'] + [''] * 7] + [mrow('address', k) for k in MODELS]
    rows7 += [['*Temporal split*'] + [''] * 7, ['Majority', f3(1 - pi_T), '–', '0.000', '0.000', '0.000', f3(pi_T), '0.500'], ['Random', '0.500', f3(pi_T), '0.500', f3(f1_rand_T), '0.000', f3(pi_T), '0.500']] + [mrow('temporal', k) for k in MODELS]
    T['metrics'] = dict(cap='All Metrics for All Classifiers under the Main Protocols (All Features, Mean over Repetitions)', header=['Model', 'Acc.', 'Prec.', 'Rec.', 'F1', 'MCC', 'PR-AUC', 'ROC-AUC'], rows=rows7,
                        widths=[1040, 560, 560, 560, 560, 560, 580, 580], opts=dict(sz=16),
                        note='Acc. = accuracy; Prec. = precision; Rec. = recall. Precision, recall, F1, and MCC are computed at a threshold of 0.5. Majority = every record labeled white; Random = uniform random scores (expected values). The baselines of the address-disjoint split equal those of the random split to three decimals.')
    IJ, IJt, PGa, PGb = N['inject_all'], N['inject_notime'], N['purge_all'], N['purge_notime']
    def cis(d, lo, hi): return f'{sg(d, 3)} ({sg(lo, 3)} to {sg(hi, 3)})'
    def pp(p): return '< 0.001' if p < 0.001 else f'{p:.2f}'
    T['overlap'] = dict(cap='Paired Tests of the Effect of Address Overlap on PR-AUC (XGB, Ten Splits)', header=['Features', 'With overlap', 'Without overlap', 'Difference (95% CI)', '*p*'], widths=[1000, 680, 760, 1860, 700], opts=dict(sz=16), rows=[
        ['*Leak injection: same-address records added to the training partition of an address-disjoint split*', '', '', '', ''],
        ['All', f3(IJ['leaky']), f3(IJ['clean']), cis(IJ['mean'], *IJ['ci']), pp(IJ['p'])],
        ['Topological', f3(IJt['leaky']), f3(IJt['clean']), cis(IJt['mean'], *IJt['ci']), pp(IJt['p'])],
        ['*Address purge: same-address records deleted from the training partition of a random split*', '', '', '', ''],
        ['All', f3(PGa['full']), f3(PGa['purged']), cis(PGa['mean'], *PGa['ci']), pp(PGa['p'])],
        ['Topological', f3(PGb['full']), f3(PGb['purged']), cis(PGb['mean'], *PGb['ci']), pp(PGb['p'])]],
        note=f'Both models of a pair are scored on identical test records. Leak injection changes only the overlap: the address-disjoint training records are kept and the same-address records are added, so the difference measures the effect of overlap ({WORD[IJt["n"]]} splits for the topological features). Address purge changes the overlap and the training population at the same time, because the deletion removes most repeated-address ransomware records from training; its difference is therefore not a measure of leakage. Difference = with overlap minus without, averaged over the splits; the 95% CI is the *t*-interval of the mean paired difference, so it describes the variation between splits; paired *t*-test.')
    rows8 = [[fam(k), n(v.n_total), n(v.n_fit + v.n_val), n(v.n_test), f3(v.recall_known) + '\n(' + ci3(zci(k, 'known')) + ')', f3(v.recall_zero_day) + '\n(' + ci3(zci(k, 'withheld')) + ')'] for k, v in zf.iterrows()]
    rows8 += [['Pooled, Eq. (2)', n(zf.n_total.sum()), n(zf.n_fit.sum() + zf.n_val.sum()), n(zf.n_test.sum()), f3(zk) + '\n(' + ci3(N['z_pool_known_ci']) + ')', f3(zz) + '\n(' + ci3(N['z_pool_zero_ci']) + ')'],
              ['Macro average', '–', '–', '–', f3(N['z_macro_known']) + '\n(' + ci3(N['z_macro_known_ci']) + ')', f3(N['z_macro_zero']) + '\n(' + ci3(N['z_macro_zero_ci']) + ')']]
    T['withheld'] = dict(cap='Withheld-Family Protocol: Records per Family and Recall (95% CI) at a Validation-Calibrated 1% FPR', header=['Family', 'Total', 'Train', 'Test', 'Recall, known', 'Recall, withheld'], rows=rows8,
                         widths=[1130, 570, 570, 570, 1080, 1080], opts=dict(sz=16),
                         note=f'Total = ransomware records of the family in the complete dataset; Train, Test = mean number in the training partition (fitting and validation parts, divided 80%/20% by address) and in the test partition over {WORD[N["z_seeds"]]} address-disjoint splits. Every test partition also contains about {n(N["z_white_test"])} white records, which determine the realized FPR. Known = family present in the fitting part; Withheld = family removed from it. Recall is the mean over the splits; the 95% CI is the percentile interval of the address-level bootstrap replicates pooled over the splits.')
    rows9 = []
    for t_ in YEARS + [FIX]:
        r_, ra_ = ct.loc[t_], ca.loc[t_]
        rows9.append([t_.replace('-', '–'), n(r_.n_emerging), n(r_.n_continuing), f3(r_.base_rate), f3(ra_.pr_auc), f3(r_.pr_auc), pct(r_.fpr, 2).replace('%', ''), f3(r_.recall_emerging) if r_.n_emerging > 0 else '–', f3(r_.recall_continuing) if r_.n_continuing > 0 else '–'])
    T['combined'] = dict(cap=f'Combined Temporal, Address-Disjoint, and Emerging-Family Protocol ({best})', header=['Test', '*n*~E~', '*n*~C~', 'π', 'PR-AUC all', 'PR-AUC topo.', 'FPR (%)', '*R*~E~', '*R*~C~'], rows=rows9,
                         widths=[820, 560, 540, 460, 560, 560, 500, 500, 500], opts=dict(sz=16),
                         note='Training on all years before the test period; test records restricted to addresses unseen in training. *n*~E~, *n*~C~ = ransomware test records of emerging and continuing families; π = positive rate of the test partition. FPR, *R*~E~, and *R*~C~ = realized false-positive rate and recall on emerging and continuing families for the topological model at the threshold calibrated to 1% FPR on validation data. Means over three seeds; confidence intervals are given in Table XII and Fig. 5.')
    # combined protocol across classifiers (fixed boundary, topological features) with pooled-bootstrap intervals
    rowsm = []; nE6 = cpooled(best, 'notime', 'emerging', YEARS)[1]; nC6 = cpooled(best, 'notime', 'continuing', YEARS)[1]
    def c2(v, c_, f=f3, sc=1.0): return f(v * sc) + '\n(' + f(c_[0] * sc) + '–' + f(c_[1] * sc) + ')'
    rowsm.append([f'*(a) Training on 2011–2015, test on 2016–2018 ({n(ct.loc[FIX].n_emerging)} emerging-family and {n(ct.loc[FIX].n_continuing)} continuing-family records)*', '', '', '', ''])
    for k in MODELS:
        rowsm.append([k] + [c2(cb(FIX, k, 'notime', mt), cci(FIX, k, 'notime', mt)) for mt in ('pr_auc', 'recall_emerging', 'recall_continuing')] + [c2(cb(FIX, k, 'notime', 'fpr'), cci(FIX, k, 'notime', 'fpr'), f2, 100)])
    rowsm.append([f'*(b) Pooled over the six yearly origins, test years 2012–2017 ({n(nE6)} emerging-family and {n(nC6)} continuing-family records)*', '', '', '', ''])
    for k in MODELS:
        fp6 = cpooled_fpr(k, 'notime', YEARS)
        rowsm.append([k, '–', c2(cpooled(k, 'notime', 'emerging', YEARS)[0], cpooled_ci(k, 'notime', 'emerging', YEARS)), c2(cpooled(k, 'notime', 'continuing', YEARS)[0], cpooled_ci(k, 'notime', 'continuing', YEARS)), c2(fp6[0], fp6[1], f2, 100)])
    T['models'] = dict(cap='Combined Protocol for All Classifiers (Topological Features)', header=['Model', 'PR-AUC', 'Emerging recall', 'Continuing recall', 'FPR (%)'], rows=rowsm,
                       widths=[620, 1095, 1095, 1095, 1095], opts=dict(sz=16),
                       note=f'Emerging recall, continuing recall = recall on emerging-family and continuing-family records (*R*~E~ and *R*~C~ of Table X) at the threshold calibrated to 1% FPR on validation data; FPR = realized false-positive rate on the test partition. Values are means over three seeds, with the 95% CI of the address-level bootstrap pooled over the seeds in parentheses. Panel (a): fixed boundary, positive rate {f3(ct.loc[FIX].base_rate)}. Panel (b): detected records of the six test years divided by all records of the group, and false alerts divided by all white test records; PR-AUC is not pooled, because the positive rate differs between the years (Table X).')
    # family-level recall and feature drift under the combined protocol
    rowsf = []; g = DR[DR.test.isin(YEARS) & DR.status.isin(['emerging', 'continuing']) & (DR.n_test >= 100)]
    for _, d_ in g.iterrows():
        cf_ = cfam(d_.test, best, 'notime', d_.group)
        rowsf.append([d_.test, fam(d_.group), 'E' if d_.status == 'emerging' else 'C', n(d_.n_test), f3(cf_['recall']) + '\n(' + ci3(cf_['ci']) + ')', f3(d_.ks_mean), f3(d_.c2st_auc) + '\n(' + ci3((d_.c2st_lo, d_.c2st_hi)) + ')'])
    T['families'] = dict(cap=f'Combined Protocol by Family: Recall of {best} (95% CI) and Feature Drift Relative to the Training Data', header=['Test', 'Family', 'Type', '*n*', 'Recall (95% CI)', 'KS', 'AUC (95% CI)'], rows=rowsf,
                         widths=[420, 1120, 450, 480, 1030, 470, 1030], opts=dict(sz=16, left=2),
                         note='Families with at least 100 test records. E = emerging, C = continuing; *n* = test records with an address unseen in training. Drift is measured between the test records and their reference in the training years (the same family for C, all ransomware for E): KS = Kolmogorov–Smirnov statistic averaged over the six topological features; AUC = ROC-AUC of a classifier two-sample test that separates test from reference records (0.5 = indistinguishable), with three-fold cross-validation in which all records of an address fall into the same fold; the 95% CI is a cluster bootstrap over addresses of the out-of-fold scores.')
    # operational measures at the validation-calibrated operating point
    rowso = []
    def orow(k, src, fs):
        o = opst(src, k, fs, FIX)
        return [k, f2(o['alerts_per_1000']), f2(o['fp_per_1000']), f3(o['precision']), f3(o['recall']), f1d(o['false_per_true']), n(o['alerts']) + ' (' + n(o['tp']) + ')']
    o_r0, o_c0 = opst('random', best, 'all'), opst('combined', best, 'all', FIX)
    for lab_, src, fs, o_ in (('*Random split, all features*', 'random', 'all', o_r0), ('*Combined protocol 2016–2018, all features*', 'combined', 'all', o_c0), ('*Combined protocol 2016–2018, topological features*', 'combined', 'notime', o_c0)):
        rowso.append([lab_ + f' ({n(o_["n_test"])} test records, {n(o_["n_pos"])} ransomware)'] + [''] * 6); rowso += [orow(k, src, fs) for k in ENS]
    T['operational'] = dict(cap='Operational Measures at the Threshold Calibrated to a 1% FPR on Validation Data', header=['Model', 'Alerts per 1,000', 'False alerts per 1,000', 'Precision', 'Recall', 'False alerts per true alert', 'Alerts per split (true alerts)'], rows=rowso,
                            widths=[570, 580, 640, 800, 600, 640, 1170], opts=dict(sz=16),
                            note='Denominator of the per-1,000 measures = all test records of the protocol (white and ransomware). Alerts = test records scored above the threshold; false alerts = white records among them (false positives); true alerts = ransomware records among them. Precision = true alerts / alerts; recall = true alerts / ransomware test records. All rates and ratios are computed from the counts summed over three seeds before rounding; the last column gives the mean number of alerts per split, with the true alerts in parentheses.')
    rowsw = []
    for fs, fl in (('all', 'All'), ('notime', 'Topo.')):
        for s_, sl in (('random', 'Random'), ('address', 'Address'), ('temporal', 'Temporal')):
            rowsw.append([f'{fl} / {sl}', f3(m3(s_, fs)), f3(wg(s_, fs, 'pr_auc')), f3(wg(s_, fs, 'precision')), f3(wg(s_, fs, 'recall'))])
    T['weighting'] = dict(cap=f'{best} with Class Weighting', header=['Features / split', 'PR-AUC (unw.)', 'PR-AUC (w.)', 'Prec. (w.)', 'Recall (w.)'], rows=rowsw, widths=[1400, 950, 900, 800, 850],
                          note='unw. = unweighted model; w. = positive class weighted by the ratio of negative to positive training records. Both columns are means over the same three seeds; Tables VI and VII report ten splits for the random and address-disjoint protocols.')
    # sensitivity of the uncertainty estimates
    def srow(label, d, f=f3, sc=1.0):
        lo_, hi_ = d['pooled_ci']; inc = [c_ for c_ in d['cis']]; fs_ = (lambda v: f'{v * sc:.4f}') if sc == 1.0 else (lambda v: f'{v * sc:.1f}')
        def rg(a, b): return f(a * sc) + (' to ' if a < 0 or b < 0 else '–') + f(b * sc)
        return [label, str(d['k']), f(d['mean'] * sc) + '\n(' + rg(lo_, hi_) + ')', fs_(d['sd_between']), fs_(d['se_within']), rg(min(c_[0] for c_ in inc), max(c_[1] for c_ in inc))]
    def f1s(v): return sg(v, 1)
    def f4(v): return sg(v, 4)
    SENS = [('Withheld family, known (LGBM)', z_sens('known'), f3), ('Withheld family, withheld (LGBM)', z_sens('withheld'), f3),
            ('Combined 2016–2018, PR-AUC (XGB)', c_sens(FIX, best, 'notime', 'pr_auc'), f3), ('Combined 2016–2018, *R*~E~ (XGB)', c_sens(FIX, best, 'notime', 'recall_emerging'), f3),
            ('Combined 2014, *R*~E~ (XGB)', c_sens('2014', best, 'notime', 'recall_emerging'), f3), ('Combined 2017, *R*~C~ (XGB)', c_sens('2017', best, 'notime', 'recall_continuing'), f3),
            ('ΔPR-AUC × 10^3^, RF − XGB, 2016–2018', c_sens(FIX, 'RF', 'notime', 'pr_auc', minus=(best, 'notime')), f1s), ('ΔPR-AUC × 10^3^, LGBM − XGB, 2016–2018', c_sens(FIX, 'LGBM', 'notime', 'pr_auc', minus=(best, 'notime')), f1s)]
    T['sens_raw'] = SENS
    T['sensitivity'] = dict(cap='Between-Repetition Variation and Sampling Uncertainty of Key Estimates (Topological Features)', header=['Estimate', '*k*', 'Mean (pooled 95% CI)', 'SD between', 'SE within', 'Per-repetition 95% CIs'], rows=[srow(a, b, f, 1000.0 if f is f1s else 1.0) for a, b, f in SENS],
                            widths=[1330, 230, 1130, 640, 600, 1070], opts=dict(sz=16, left=1),
                            note='*k* = number of repetitions (address-disjoint splits for the withheld-family protocol, seeds for the combined protocol). SD between = standard deviation of the point estimates over the repetitions; SE within = mean standard deviation of the address-level bootstrap replicates within one repetition; per-repetition 95% CIs = lowest lower and highest upper limit of the intervals computed separately for each repetition. Δ = paired difference on identical resamples, given in units of 0.001.')
    return T

if __name__ == '__main__':
    OUTDIR = sys.argv[2].rstrip('/') + '/'; figures(OUTDIR)
    plain = lambda t: re.sub(r'[*~]', '', str(t)).replace('\n', ' ')
    with open(OUTDIR + 'tables.md', 'w', encoding='utf8') as f:
        for num, key in (('V', 'audit'), ('VI', 'prauc'), ('VII', 'metrics'), ('VIII', 'overlap'), ('IX', 'withheld'), ('X', 'combined'), ('XI', 'models'), ('XII', 'families'), ('XIII', 'operational'), ('XIV', 'weighting'), ('XV', 'sensitivity')):
            t = tables()[key]; f.write(f'### Table {num}. {plain(t["cap"])}\n\n| ' + ' | '.join(plain(h) for h in t['header']) + ' |\n|' + '---|' * len(t['header']) + '\n')
            for r in t['rows']: f.write('| ' + ' | '.join(plain(c) for c in r) + ' |\n')
            f.write('\n' + (plain(t['note']) + '\n\n' if t.get('note') else ''))
        f.write('### Statistics quoted in the text\n\n```\n' + json.dumps({k: v for k, v in N.items()}, indent=1, default=str) + '\n```\n')
    print('written', OUTDIR)
