#!/bin/bash
# Clean-room reproduction check: fresh clone, fresh virtual environment, regenerated tables and rerun experiments
# compared with the committed results.
# Usage: scripts/cleanroom_check.sh <path-to-BitcoinHeistData.csv> <empty-work-directory> [quick]
#   quick = only regenerate the tables and figures from the committed result files (about one minute);
#   without it, 06_combined_drift.py and 04_overlap_isolation.py are also rerun on the raw data (about 15 minutes).
set -e
DATA=$(realpath "$1"); CR=$(realpath "$2"); MODE=${3:-full}
cd "$CR" && rm -rf repo venv fig_check res_check
git clone -q https://github.com/adeilhamfajri/bitcoinheist-leakage-audit.git repo && cd repo && git log --oneline | head -1
python3 -m venv "$CR/venv" && . "$CR/venv/bin/activate" && pip install -q -r requirements.txt && python --version
python src/make_tables_figures.py results "$CR/fig_check" > /dev/null
diff -q figures/tables.md "$CR/fig_check/tables.md" && echo "tables.md: identical"
[ "$MODE" = quick ] && exit 0
mkdir -p "$CR/res_check"
python src/06_combined_drift.py "$DATA" "$CR/res_check" > "$CR/log06.txt" 2>&1
python src/04_overlap_isolation.py "$DATA" "$CR/res_check" > "$CR/log04.txt" 2>&1
python - "$CR/res_check" <<'PY'
import sys, json, pandas as pd
out = sys.argv[1]
for f in ('combined_drift.csv', 'inject.csv', 'purge_groups.csv'):
    a = pd.read_csv('results/' + f); b = pd.read_csv(out + '/' + f); print(f + ':', 'identical' if a.equals(b) else 'DIFFERENT')
a = json.load(open('results/inject_bootstrap.json')); b = json.load(open(out + '/inject_bootstrap.json'))
print('inject_bootstrap.json:', 'identical' if json.dumps(a) == json.dumps(b) else 'DIFFERENT')
PY
