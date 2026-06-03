"""Download the large signals dataset from the GitHub Release.

The 650 MB `phase1_signals.csv` is too big for the git repo, so it is published
as a compressed Parquet (~151 MB) attached to a GitHub Release. This script pulls
it into `results/ddi_study/` so `build_db.py` can use it.

Usage (from project root):

    python explorer/fetch_data.py            # download if missing / outdated
    python explorer/fetch_data.py --force    # re-download even if present
    python explorer/fetch_data.py --url URL  # override the download URL
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results" / "ddi_study"

# --- Release asset metadata -------------------------------------------------
REPO = "stephluooo/WI-SP26-DSC-Capstone"
TAG = "data-v1"
ASSET = "phase1_signals.zstd.parquet"
SHA256 = "e0b2bdfa990ed07a152241a8d1a097c486ce555ced75fdcb4ead1f6b5b71a854"
SIZE = 150_781_250
URL = f"https://github.com/{REPO}/releases/download/{TAG}/{ASSET}"

TARGET = RESULTS_DIR / ASSET


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def already_present(verify: bool) -> bool:
    if not TARGET.exists():
        return False
    if not verify:
        return True
    print("Verifying existing file checksum...")
    return sha256_of(TARGET) == SHA256


def _progress(count: int, block: int, total: int) -> None:
    if total <= 0:
        total = SIZE
    done = min(count * block, total)
    pct = 100 * done / total
    bar = "#" * int(pct // 2)
    sys.stdout.write(f"\r  [{bar:<50}] {pct:5.1f}%  {done/1e6:6.1f}/{total/1e6:.1f} MB")
    sys.stdout.flush()


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch the signals Parquet from the release.")
    ap.add_argument("--url", default=URL, help="Override download URL")
    ap.add_argument("--force", action="store_true", help="Re-download even if present")
    ap.add_argument("--no-verify", action="store_true", help="Skip checksum verification")
    args = ap.parse_args()

    verify = not args.no_verify
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not args.force and already_present(verify):
        print(f"Already have {TARGET.name} ({TARGET.stat().st_size/1e6:.1f} MB). Nothing to do.")
        return 0

    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    print(f"Downloading {args.url}")
    t0 = time.time()
    try:
        urllib.request.urlretrieve(args.url, tmp, reporthook=_progress)
    except Exception as e:  # noqa: BLE001
        print(f"\nDownload failed: {e}")
        print("If the release/tag/asset name differs, pass --url with the correct link.")
        if tmp.exists():
            tmp.unlink()
        return 1
    print(f"\nDownloaded in {time.time()-t0:.0f}s.")

    if verify:
        print("Verifying checksum...")
        got = sha256_of(tmp)
        if got != SHA256:
            print(f"Checksum mismatch!\n  expected {SHA256}\n  got      {got}")
            print("Delete the file and retry, or pass --no-verify if you trust the source.")
            return 1
        print("Checksum OK.")

    tmp.replace(TARGET)
    print(f"Saved -> {TARGET}")
    print("Next: python explorer/build_db.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
