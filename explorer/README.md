# DDI Explorer

An interactive Streamlit dashboard for exploring the Plan C drug–drug interaction
study results in `results/ddi_study/`.

## Quick start (fresh machine)

```bash
pip install -r explorer/requirements.txt
python explorer/fetch_data.py        # downloads the 151 MB signals parquet from the GitHub Release
python explorer/build_db.py          # one-time, ~2 min, builds results/ddi_study/ddi.db
python -m streamlit run explorer/app.py
```

Opens at `http://localhost:8501`. (Use `python -m streamlit` — the `streamlit`
script isn't on PATH on this machine.)

The large signals table (`phase1_signals.csv`, 650 MB) is **not** in git. It is
published as a compressed Parquet (~151 MB) on a GitHub Release and pulled by
`fetch_data.py`. `build_db.py` automatically prefers the Parquet if present and
falls back to the CSV otherwise.

## What's inside

| Page | Feature |
|------|---------|
| Overview | Headline stats + pipeline figures |
| Drug Pair | All reactions for a pair, ROR table, **2×2 contingency visualizer** |
| Drug Profile | A drug's top partner drugs and reactions |
| Reaction | Which pairs signal for a given reaction |
| Leaderboard | Global sortable/filterable signal table (absolute ROR vs robust CI lower bound) |
| Network | Ego interaction network around a focus drug |
| Heatmap | Partner × reaction signal-intensity heatmap |
| Volcano | ROR vs evidence scatter + ROR distribution |
| Predictions | Top-500 novel predictions, flagged against known DrugBank DDIs |
| Model | Cross-validation metrics, ROC, Precision@k |
| Similarity | Tanimoto fingerprint similarity + **live model scoring** of any pair |
| Audit | FAERS → DrugBank canonicalization audit |

Every table has a **Download CSV** button (autocomplete search is built into the pickers).

## Setup

From the **project root** (`c:\Users\mkbox\Documents\Cursor`):

```bash
pip install -r explorer/requirements.txt
```

## 1. Build the database (one-time, ~1–2 min)

This streams the 650 MB signals CSV into an indexed SQLite file
(`results/ddi_study/ddi.db`):

```bash
python explorer/build_db.py
```

Quick rebuild of just the small tables (skips the big signals load):

```bash
python explorer/build_db.py --skip-signals
```

## 2. Run the app

```bash
python -m streamlit run explorer/app.py
```

It opens at `http://localhost:8501`. (Use `python -m streamlit` because the
`streamlit` script isn't on PATH on this machine.)

## Optional data

- **Known DrugBank DDIs** (`data/drugbank_all_drug_drug_interactions.csv`): if present,
  the Predictions and Drug Pair pages flag whether a pair is already documented.
- **Fingerprints** (`phase2_fingerprints.npz`) and **model** (`best_model.pt`): required
  for the Similarity page (Tanimoto + live scoring). The rest of the app works without them.

## Publishing / updating the signals data (maintainer)

The signals Parquet is distributed as a **GitHub Release asset** (free, up to 2 GB
per file, no LFS quota). To (re)publish it:

1. Regenerate the Parquet from the CSV if needed:

   ```bash
   python -c "import pyarrow.csv as c, pyarrow.parquet as p; p.write_table(c.read_csv('results/ddi_study/phase1_signals.csv'), 'results/ddi_study/phase1_signals.zstd.parquet', compression='zstd')"
   ```

2. Create the release and upload the asset (tag `data-v1`).

   With the GitHub CLI:

   ```bash
   gh release create data-v1 results/ddi_study/phase1_signals.zstd.parquet \
     --title "DDI signals data v1" --notes "Compressed Phase 1 signals (8,962,225 rows)."
   ```

   Or via the web UI: repo → **Releases** → **Draft a new release** → tag `data-v1`
   → attach `phase1_signals.zstd.parquet` → publish.

3. If you change the file, update `SHA256`, `SIZE`, and `TAG` in `fetch_data.py`.

The download URL `fetch_data.py` expects is:
`https://github.com/stephluooo/WI-SP26-DSC-Capstone/releases/download/data-v1/phase1_signals.zstd.parquet`

## Notes / hosting

- `ddi.db` (≈1.9 GB) and the large `phase1_signals.*` files are git-ignored.
  Rebuild `ddi.db` with `build_db.py` on any machine that has the Parquet (or CSV).
- This is a **local** app. To host it publicly, run the same command on a server
  (e.g. an EC2/Lightsail instance or Streamlit Community Cloud) with the result files
  and `ddi.db` present, and expose port 8501 behind a reverse proxy.
