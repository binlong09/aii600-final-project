# Data

The files the notebook reads are not committed. When the terms let you republish them, they are assets on the GitHub release tagged `data`. The release is public. When the terms let you download the files but not republish them, do not create that release. Write the command that downloads them from the source, and say what it needs (an account, a key in `.env`, a path).

`OWNER/REPO` is your fork, the form `username/aii600-final-project`. In the clone, once:

```bash
gh repo set-default OWNER/REPO
```

Create the release from the project root, after the files are in this folder:

```bash
gh release create data data/your-file.csv --repo OWNER/REPO --title "Data" --notes "See data/README.md"
```

Add every file the notebook reads. When a file changes:

```bash
gh release upload data data/your-file.csv --repo OWNER/REPO --clobber
```

On another machine:

```bash
gh release download data --dir data --repo OWNER/REPO
```

Record a SHA-256 for each file. Replacing a file with `--clobber` does not show up in git, so update the hash in the same commit:

```bash
shasum -a 256 data/your-file.csv
```

## This project

- Source. Fairfax County, Virginia open data, tables from the Department of Tax Administration, served at `https://services1.arcgis.com/ioennV6PpG5Xodq0/ArcGIS/rest/services`. The county disclaimer (https://www.fairfaxcounty.gov/maps/disclaimer) reserves all rights and allows copies for internal or personal use. It does not clearly allow republishing, so there is no `data` release. I thank Fairfax County for making the tables public.
- Download. From the project root, with the packages in `requirements.txt` installed:

```bash
python fetch_data.py
python prepare_data.py
python select_sales.py
```

`fetch_data.py` downloads the six county tables below (about 16 minutes, no account or key needed). `prepare_data.py` joins them into one row per sale, `data/fairfax_joined.csv`, and removes nothing. `select_sales.py` applies the filters in `decisions.md` and writes `data/fairfax_selected.csv`, which the notebook reads.

- The county edits these tables. A download on another day can differ from mine, and then the hashes below will not match. My download is from 2026-11-18. The county last edited the sales table on 2026-09-20.

| File | Rows | SHA-256 |
|---|---|---|
| `fairfax_sales.csv` | 350,708 | `6ad7dcec5186a72e77bdbcff27c600fc92ec0c954211fe403dc7ac24e0e9ffff` |
| `fairfax_dwelling.csv` | 340,666 | `542ba5103c65520ab35d33fb89d3ab98b49d72dfd7a87807aba805662588c612` |
| `fairfax_legal.csv` | 369,750 | `7bb8b7854ef6b6619eab1599ab7d888f867660c1dba40498646054d2f7a9fabc` |
| `fairfax_parcel.csv` | 370,561 | `28d3784278793935fed2d66ad5172bd7cdfd7ff14bfb4e90a8a9cc45905e7294` |
| `fairfax_land.csv` | 372,190 | `043819fe366a2a845c8aaf1946b0310006c3dc71f2686911e0b574b88aad54c2` |
| `fairfax_assessed.csv` | 369,441 | `6f7e22b2476f7738b4f406e9cfca9922c60f0bd9154b829d45468f2162bef263` |

The two files the scripts build from those six, for the same download:

| File | Rows | SHA-256 |
|---|---|---|
| `fairfax_joined.csv` | 350,708 | `d9c9849221456abfb81584892ce8c0bf79bc41393584ecde6057bd352b7b4f88` |
| `fairfax_selected.csv` | 70,306 | `822756ecb502bc589e8ec9b02c3426a2f01861bfe04e70818876e59bffc6c3d5` |

- Unit of observation. In `fairfax_sales.csv`, one row is one recorded transfer of one parcel: parcel ID, sale date, price, and the county's label for the sale. The other tables have one or more rows per parcel and describe the property as it is today.
- Sample size and time span. 350,708 transfers from 2015-01-05 to 2026-09-17. 173,472 carry the label "Valid and verified sale". The filters in `decisions.md` reduce this to 70,306 sales of single family houses and townhouses, 2020-01-02 to 2026-09-15, which the notebook uses.
