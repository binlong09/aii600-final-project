"""Apply my filters to the joined sales and keep the rows I will model.

Run from the project root, after prepare_data.py:

    python select_sales.py

It reads data/fairfax_joined.csv and writes data/fairfax_selected.csv.
It prints one line per rule: rows before, rows removed, rows after.

Each rule is one small function, applied in the order of RULES below.
The reasons for each rule are in decisions.md (entries dated 2026-11-18).
"""

import time
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data")
IN_FILE = DATA_DIR / "fairfax_joined.csv"
OUT_FILE = DATA_DIR / "fairfax_selected.csv"

# My choices. See decisions.md, entries dated 2026-11-18. Change them here only
# together with a new decisions.md entry.
START_DATE = "2020-01-01"                       # rule 1: first sale date kept
KEPT_TYPES = ["single_family", "townhouse"]     # rule 2: property types kept
KEPT_LABEL = "Valid and verified sale"          # rule 3: the county's label kept
MIN_PRICE = 50_000                              # rule 4: lowest price kept
MAX_PRICE = 5_000_000                           # rule 4: highest price kept
PLACEHOLDER_YEARS = [1700, 1730, 2100]          # rule 5: year built values that mean "unknown"
DUPLICATE_KEYS = ["parcel_id", "sale_date", "price", "sale_label"]  # rule 6
MIN_LIVING_AREA = 400                           # rule 8: smallest living area kept, in square feet


def read_joined():
    """Read the joined table. IDs and zips stay text so nothing is reformatted."""
    return pd.read_csv(IN_FILE, dtype={"parcel_id": str, "zip": str},
                       parse_dates=["sale_date"], low_memory=False)


def keep_recent_years(sales):
    """Rule 1. Older sales come from a different market, so I start in 2020."""
    return sales[sales["sale_date"] >= START_DATE]


def keep_house_types(sales):
    """Rule 2. I am looking for a detached house or a townhouse, not a condo."""
    return sales[sales["property_type"].isin(KEPT_TYPES)]


def keep_market_sales(sales):
    """Rule 3. Only sales the county checked and calls a market sale."""
    return sales[sales["sale_label"] == KEPT_LABEL]


def keep_plausible_prices(sales):
    """Rule 4. A price outside these limits is not a normal house sale."""
    return sales[(sales["price"] >= MIN_PRICE) & (sales["price"] <= MAX_PRICE)]


def blank_placeholder_years(sales):
    """Rule 5, first part. The county writes 1700, 1730 or 2100 when the
    year built is unknown. Those are not real years, so they become missing."""
    out = sales.copy()
    out["year_built"] = out["year_built"].mask(out["year_built"].isin(PLACEHOLDER_YEARS))
    return out


def keep_complete_details(sales):
    """Rule 5. The model needs size, age, bedrooms and zip for every row.

    Only these four fields are checked. Full baths, lot size and grade may
    still be missing after this rule.
    """
    sales = blank_placeholder_years(sales)
    has_area = sales["living_area_sqft"] > 0   # False for missing and for 0
    complete = (has_area & sales["year_built"].notna()
                & sales["bedrooms"].notna() & sales["zip"].notna())
    return sales[complete]


def drop_exact_copies(sales):
    """Rule 6. The same sale recorded twice would count twice. Keep one copy.

    Which copy: the one with the lowest sale_id. The copies are equal in
    parcel, date, price and label, so the choice does not change the data.
    """
    return sales.sort_values("sale_id").drop_duplicates(DUPLICATE_KEYS, keep="first")


def drop_sales_of_a_different_house(sales):
    """Rule 7. The county describes the house as it is today.

    If the sale year is before the year built, the sale was land or an
    unfinished house. If it is before the remodel year, the buyer paid for
    the older version. Same-year sales are kept. No remodel year means no
    known remodel, so the row is kept.
    """
    before_built = sales["sale_year"] < sales["year_built"]
    before_remodel = sales["sale_year"] < sales["remodel_year"]   # False if missing
    return sales[~(before_built | before_remodel)]


def drop_tiny_living_area(sales):
    """Rule 8. A living area under 400 square feet is a recording error.

    One house was recorded at 4 square feet and sold for $1,700,100. That
    gives $425,025 per square foot and would distort its zip code's median.
    """
    return sales[sales["living_area_sqft"] >= MIN_LIVING_AREA]


def drop_same_day_price_conflicts(sales):
    """Rule 9. Same house, same day, two different prices: drop both rows.

    I cannot tell which price is the real one. Exact copies are already gone
    after rule 6, so any parcel and date seen twice here has two prices.
    """
    conflict = sales.duplicated(["parcel_id", "sale_date"], keep=False)
    return sales[~conflict]


# The order matters for the printed counts, not for the final rows, except
# rule 6 (it runs after rule 3, so all copies have the same label by then)
# and rule 9 (it runs after rule 6, so exact copies are already gone).
RULES = [
    ("1 years: from " + START_DATE, keep_recent_years),
    ("2 types: " + " and ".join(KEPT_TYPES), keep_house_types),
    ("3 label: " + KEPT_LABEL, keep_market_sales),
    (f"4 price: {MIN_PRICE:,} to {MAX_PRICE:,}", keep_plausible_prices),
    ("5 details: area, year built, bedrooms, zip", keep_complete_details),
    ("6 exact copies: keep one", drop_exact_copies),
    ("7 sale before built or remodel year", drop_sales_of_a_different_house),
    (f"8 living area under {MIN_LIVING_AREA} sq ft", drop_tiny_living_area),
    ("9 same house and day, two prices: drop both", drop_same_day_price_conflicts),
]


def apply_rules(sales):
    """Apply every rule in order and print the waterfall."""
    print(f"{'rule':<46}{'before':>10}{'removed':>10}{'after':>10}")
    for name, rule in RULES:
        before = len(sales)
        sales = rule(sales)
        print(f"{name:<46}{before:>10,}{before - len(sales):>10,}{len(sales):>10,}")
    return sales


def main():
    start = time.time()
    selected = apply_rules(read_joined()).sort_values(["sale_date", "sale_id"])
    selected.to_csv(OUT_FILE, index=False, lineterminator="\n", date_format="%Y-%m-%d")
    print(f"Wrote {OUT_FILE}: {len(selected):,} sales, {time.time() - start:.0f} seconds")


if __name__ == "__main__":
    main()
