"""Regenerates the train / validation / test record indices of every evaluation protocol.

Usage:  python src/make_splits.py <path-to-BitcoinHeistData.csv> <outdir> [--save]

Indices are 0-based row numbers of BitcoinHeistData.csv as distributed by the UCI Machine Learning
Repository (dataset 526). The script always writes <outdir>/manifest.csv, which lists the size and the
SHA-256 checksum of every index array, so that a regenerated split can be verified against the manifest
shipped in this repository. With --save it also writes one compressed .npz file per split.
All splits are deterministic functions of the file and of the seed."""
import sys, os, hashlib
import numpy as np, pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit, GroupShuffleSplit

SRC, OUT = sys.argv[1], sys.argv[2]
SAVE = '--save' in sys.argv
os.makedirs(OUT, exist_ok=True)
df = pd.read_csv(SRC)
y = (df.label != 'white').astype(int).values
groups = df.address.astype('category').cat.codes.values      # one integer per distinct address
yr = df.year.values
fam = df.label.values
idx = np.arange(len(df))
rows = []

def emit(name, **parts):
    """Record (and optionally save) the index arrays of one split."""
    for part, a in parts.items():
        a = np.asarray(a, dtype=np.int64)
        rows.append({'split': name, 'part': part, 'n_records': len(a), 'n_ransomware': int(y[a].sum()),
                     'sha256': hashlib.sha256(a.tobytes()).hexdigest()})
    if SAVE:
        np.savez_compressed(os.path.join(OUT, name + '.npz'), **{k: np.asarray(v, dtype=np.int32) for k, v in parts.items()})
    print(name, {k: len(v) for k, v in parts.items()}, flush=True)

def random_split(seed):
    return next(StratifiedShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y))

def address_split(seed):
    return next(GroupShuffleSplit(1, test_size=0.3, random_state=seed).split(idx, y, groups))

def fit_val(train, seed):
    """Address-disjoint 80/20 division of a training partition into fitting and validation parts."""
    a, b = next(GroupShuffleSplit(1, test_size=0.2, random_state=seed).split(train, y[train], groups[train]))
    return train[a], train[b]

# 1) Random protocol (seeds 0-9)
for seed in range(10):
    tr, te = random_split(seed)
    purged = tr[~np.isin(groups[tr], np.unique(groups[te]))]          # training records whose address is not in the test partition
    emit(f'random_seed{seed}', train=tr, test=te, train_purged=purged)

# 2) Address-disjoint protocol and 4) withheld-family protocol (seeds 0-4)
big = df[df.label != 'white'].label.value_counts()
big = [k for k, v in big.items() if v >= 200]
for seed in range(5):
    tr, te = address_split(seed)
    fit, val = fit_val(tr, seed)
    emit(f'address_seed{seed}', train=tr, test=te, fit=fit, val=val)
    for k in big:                                                      # fitting part without family k
        emit(f'withheld_{k}_seed{seed}', fit=fit[fam[fit] != k], val=val, test=te)

# 2b) Leak-injection experiment: half of the records of every repeated test address are moved into training (seeds 0-9)
for seed in range(10):
    tr, te = address_split(seed)
    rng = np.random.default_rng(1000 + seed); o = rng.permutation(len(te)); t = pd.DataFrame({'i': te[o], 'g': groups[te][o]})
    rank = t.groupby('g').cumcount().values; cnt = t.groupby('g').g.transform('size').values; move = rank < (cnt // 2)
    emit(f'injection_seed{seed}', train_clean=tr, train_leaky=np.r_[tr, t.i.values[move]], test=t.i.values[~move])

# 3) Temporal protocol and rolling origins
emit('temporal_2011-2015_2016-2018', train=idx[yr <= 2015], test=idx[yr >= 2016])
for N in range(2011, 2017):
    emit(f'rolling_train-to-{N}_test-{N+1}', train=idx[yr <= N], test=idx[yr == N + 1])

# 5) Combined protocol: temporal + address-disjoint, positives divided into emerging and continuing families
settings = [(B, [B + 1], f'{B+1}') for B in range(2011, 2017)] + [(2015, [2016, 2017, 2018], '2016-2018')]
for B, test_years, tag in settings:
    hist = idx[yr <= B]
    te0 = idx[np.isin(yr, test_years)]
    te = te0[~np.isin(groups[te0], np.unique(groups[hist]))]           # drop test records whose address occurs in training
    known = set(fam[hist][y[hist] == 1])
    emerging = te[(y[te] == 1) & ~np.isin(fam[te], list(known))]
    continuing = te[(y[te] == 1) & np.isin(fam[te], list(known))]
    for seed in range(3):
        fit, val = fit_val(hist, seed)
        emit(f'combined_test-{tag}_seed{seed}', fit=fit, val=val, test=te, test_emerging=emerging, test_continuing=continuing)

# 6) Further repetitions of the address-disjoint protocol (seeds 5-9; appended so that the earlier manifest rows keep their order)
for seed in range(5, 10):
    tr, te = address_split(seed)
    emit(f'address_seed{seed}', train=tr, test=te)

pd.DataFrame(rows).to_csv(os.path.join(OUT, 'manifest.csv'), index=False)
print('written', os.path.join(OUT, 'manifest.csv'))
