"""Download the Fairfax County real estate tables into data/.

Run from the project root:

    python fetch_data.py

Why a script and not the notebook: the download is slow (about 2,000
requests), and the notebook should only read local files from data/.

Source: Fairfax County open data, Department of Tax Administration tables.
The county allows copies for internal or personal use, so the files are
not republished. Anyone can rebuild them with this script.
"""

import csv
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://services1.arcgis.com/ioennV6PpG5Xodq0/ArcGIS/rest/services"
DATA_DIR = Path("data")

# The county service returns at most 1,000 rows per request.
PAGE_SIZE = 1000

# One entry per table: output file, service path, the columns I keep, and a
# row filter. I keep only columns the analysis can use, to keep files small.
TABLES = [
    {
        "file": "fairfax_sales.csv",
        "path": "OpenData_A5/FeatureServer/1",
        "fields": ["PARID", "SALEDT", "PRICE", "SALEVAL_DESC"],
        # Decision 2026-11-18: download sales since 2015. Every sale label is
        # kept (also transfers and $0 sales), so filters can be chosen later.
        "where": "SALEDT >= DATE '2015-01-01'",
    },
    {
        "file": "fairfax_dwelling.csv",
        "path": "OpenData_A7/FeatureServer/2",
        "fields": ["PARID", "STYLE_DESC", "YRBLT", "EFFYR", "YRREMOD", "RMBED",
                   "FIXBATH", "FIXHALF", "SFLA", "RECROMAREA", "BSMT_DESC",
                   "GRADE_DESC", "CDU_DESC"],
        "where": "1=1",
    },
    {
        "file": "fairfax_legal.csv",
        "path": "OpenData_A7/FeatureServer/1",
        "fields": ["PARID", "ADRNO", "ADRSTR", "ADRSUF", "CITYNAME", "ZIP1",
                   "ACRES", "SQFT"],
        "where": "1=1",
    },
    {
        "file": "fairfax_parcel.csv",
        "path": "OpenData_A6/FeatureServer/1",
        "fields": ["PARID", "LIVUNIT", "LUC_DESC", "ZONING_DESC"],
        "where": "1=1",
    },
    {
        "file": "fairfax_land.csv",
        "path": "OpenData_A6/FeatureServer/3",
        "fields": ["PARID", "LLINE", "SF", "ACRES", "CODE_DESC"],
        "where": "1=1",
    },
    {
        # Decision 2026-11-18: download now, decide in Step 3 whether a fair
        # assessment baseline is possible. The table holds only the current
        # and prior year, so most values were set after the sale.
        "file": "fairfax_assessed.csv",
        "path": "OpenData_A6/FeatureServer/2",
        "fields": ["PARID", "TAXYR", "APRLAND", "APRBLDG", "APRTOT",
                   "PRILAND", "PRIBLDG", "PRITOT"],
        "where": "1=1",
    },
]

# Columns the service sends as milliseconds since 1970. I store plain dates.
DATE_FIELDS = {"SALEDT"}


def fetch_page(path, where, fields, after_id):
    """Get the next rows with OBJECTID above after_id.

    Why page by OBJECTID and not by row offset: the county edits these
    tables, and an offset can skip or repeat rows if the table changes
    during the download. Walking up the ID cannot.
    """
    params = {
        "where": f"({where}) AND OBJECTID > {after_id}",
        "outFields": ",".join(["OBJECTID"] + fields),
        "orderByFields": "OBJECTID",
        "resultRecordCount": PAGE_SIZE,
        "f": "json",
    }
    for attempt in range(5):
        try:
            reply = requests.get(f"{BASE}/{path}/query", params=params, timeout=120)
            body = reply.json()
            if "features" in body:
                return [f["attributes"] for f in body["features"]]
        except (requests.RequestException, ValueError):
            pass
        # The service sometimes times out. Wait longer each time, then retry.
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"No answer from {path} after 5 tries (after_id={after_id})")


def to_date(ms):
    """Turn milliseconds since 1970 into YYYY-MM-DD. Empty stays empty."""
    if ms is None:
        return ""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def clean_cell(name, value):
    """Make one value safe for CSV. Only dates are changed, nothing else."""
    if name in DATE_FIELDS:
        return to_date(value)
    return "" if value is None else value


def download_table(table):
    """Write one table to data/ as CSV and return the number of rows."""
    out_path = DATA_DIR / table["file"]
    columns = ["OBJECTID"] + table["fields"]
    after_id, total = 0, 0
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        while True:
            rows = fetch_page(table["path"], table["where"], table["fields"], after_id)
            if not rows:
                break
            for row in rows:
                writer.writerow([clean_cell(c, row.get(c)) for c in columns])
            after_id = rows[-1]["OBJECTID"]
            total += len(rows)
            if total % 50000 < PAGE_SIZE:
                print(f"  {table['file']}: {total:,} rows so far", flush=True)
    return total


def sha256_of(path):
    """Hash a file so data/README.md and the notebook can check it."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    DATA_DIR.mkdir(exist_ok=True)
    for table in TABLES:
        print(f"Downloading {table['file']} ...", flush=True)
        count = download_table(table)
        digest = sha256_of(DATA_DIR / table["file"])
        print(f"DONE {table['file']}  rows={count:,}  sha256={digest}", flush=True)


if __name__ == "__main__":
    main()
