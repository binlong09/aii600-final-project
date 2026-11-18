"""Functions for the house offer analysis. analysis.ipynb imports this file.

Two methods give a "fair price" for a house:

- the rule of thumb (baseline): the zip code's median price per square foot
  times the house's square feet,
- the model: a linear regression on the log of the sale price.

Both get low and high estimates the same way, from how far their fair
prices were from real prices on training sales. The offer is a low estimate.

Every choice in this file is written down in decisions.md.
"""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

DATA_FILE = Path("data") / "fairfax_selected.csv"
# The file select_sales.py wrote on 2026-11-18. If the file changes, every
# number in the notebook can change, so the notebook stops when this differs.
EXPECTED_SHA256 = "822756ecb502bc589e8ec9b02c3426a2f01861bfe04e70818876e59bffc6c3d5"

# My choices. See decisions.md, entries dated 2026-11-18.
CUTOFF = "2026-03-01"          # sales on or after this date are test sales
WINDOW_START = "2025-03-01"    # both methods learn from this date up to the cutoff
MIN_ZIP_SALES = 30             # a zip code with fewer window sales is not used alone
OFFER_LEVELS = [0.05, 0.10, 0.25]                  # comfort levels I compare
ALL_LEVELS = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90]  # cut points I read off
CLOSE_FROM = 0.95              # an offer from 95% to 100% of the price is "close"
POOLED_ZIP = "small zips"      # the name of the group of small zip codes


# ---------------------------------------------------------------- data

def file_sha256(path):
    """Hash a file, to check it is the same file I analysed."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_sales(path=DATA_FILE, expected_sha256=EXPECTED_SHA256):
    """Read the selected sales. Stop if the file is not the expected one."""
    found = file_sha256(path)
    if found != expected_sha256:
        raise RuntimeError(
            f"{path} is not the file this analysis was made with.\n"
            f"  expected SHA-256 {expected_sha256}\n"
            f"  found    SHA-256 {found}\n"
            "Rebuild it with prepare_data.py and select_sales.py, or update "
            "the hash in house_model.py and data/README.md.")
    # Zip codes and parcel IDs stay text, so nothing is reformatted.
    sales = pd.read_csv(path, dtype={"parcel_id": str, "zip": str},
                        parse_dates=["sale_date"], low_memory=False)
    return add_helper_columns(sales)


def add_helper_columns(sales):
    """Add the columns both methods need. Each is known on the sale date."""
    out = sales.copy()
    out["price_per_sqft"] = out["price"] / out["living_area_sqft"]
    out["age"] = out["sale_year"] - out["year_built"]
    return out


def split_by_date(sales, cutoff=CUTOFF):
    """Older sales train, newer sales test. No random draw, so no seed."""
    is_test = sales["sale_date"] >= cutoff
    return sales[~is_test], sales[is_test]


def training_window(train, start=WINDOW_START):
    """The recent training sales both methods learn from.

    Why not all years: prices rose about 35% from 2020 to 2025. Old sales
    would pull every estimate down.
    """
    return train[train["sale_date"] >= start]


def error_spread_by_size(sales, groups=5):
    """Why log price: compare the error spread of two very simple models.

    One predicts the price in dollars from the living area. The other
    predicts the log of the price from the log of the living area. The
    table shows the spread of their errors for small to large houses.
    """
    area = sales["living_area_sqft"].astype(float)
    in_dollars = sm.OLS(sales["price"], sm.add_constant(area)).fit()
    in_logs = sm.OLS(np.log(sales["price"]), sm.add_constant(np.log(area))).fit()
    fifth = pd.qcut(area, groups)
    table = pd.DataFrame({
        "sales": area.groupby(fifth, observed=True).size(),
        "error_spread_dollars": in_dollars.resid.groupby(fifth, observed=True).std(),
        "error_spread_log": in_logs.resid.groupby(fifth, observed=True).std(),
    })
    return table.rename_axis("living_area_sqft")


# ---------------------------------------------------------------- baseline

def fit_zip_medians(window, min_sales=MIN_ZIP_SALES):
    """Median price per square foot for each zip code, from the window.

    A zip code with few sales has a shaky median, so it is left out here
    and its houses get the county-wide median instead.
    """
    by_zip = window.groupby("zip")["price_per_sqft"].agg(["median", "size"])
    enough = by_zip[by_zip["size"] >= min_sales]
    return {"zip_median": enough["median"],
            "zip_sales": by_zip["size"],
            "county_median": window["price_per_sqft"].median()}


def baseline_fair_price(houses, medians):
    """Rule of thumb: the zip code's median price per square foot times square feet."""
    per_sqft = houses["zip"].map(medians["zip_median"]).fillna(medians["county_median"])
    return per_sqft * houses["living_area_sqft"]


# ---------------------------------------------------------------- model

def zip_groups(window, min_sales=MIN_ZIP_SALES):
    """The zip codes that get their own level in the model, largest first.

    The largest zip code is the reference: its effect is 0 and the other
    zip effects are measured against it.
    """
    counts = window["zip"].value_counts()
    return list(counts[counts >= min_sales].index)


def build_features(houses, zips):
    """Turn houses into the table of numbers the regression uses.

    One column per term of the model. A zip code that is small or was
    never seen in training goes to the pooled group.
    """
    features = pd.DataFrame({"intercept": 1.0}, index=houses.index)
    features["log_living_area"] = np.log(houses["living_area_sqft"])
    features["townhouse"] = (houses["property_type"] == "townhouse").astype(float)
    features["age"] = houses["age"].astype(float)
    features["bedrooms"] = houses["bedrooms"].astype(float)
    features["full_baths"] = houses["full_baths"].astype(float)
    # The county leaves half baths empty when there is none.
    features["half_baths"] = houses["half_baths"].fillna(0).astype(float)
    # Townhouses in condominium developments have no lot of their own. The
    # log lot is set to 0 for them and the marker column carries the level.
    lot_missing = houses["lot_sqft"].isna()
    features["log_lot"] = np.log(houses["lot_sqft"].where(~lot_missing, 1.0))
    features["lot_missing"] = lot_missing.astype(float)
    zip_group = houses["zip"].where(houses["zip"].isin(zips), POOLED_ZIP)
    for name in zips[1:] + [POOLED_ZIP]:   # zips[0] is the reference
        features["zip_" + name] = (zip_group == name).astype(float)
    return features


def fit_model(window):
    """Fit the regression on log price. Returns the zip list and the fit."""
    zips = zip_groups(window)
    result = sm.OLS(np.log(window["price"]), build_features(window, zips)).fit()
    return {"zips": zips, "result": result}


def model_fair_price(houses, model):
    """The model's middle estimate in dollars: e to the power of the fitted sum."""
    log_price = model["result"].predict(build_features(houses, model["zips"]))
    return np.exp(log_price)


def coefficient_table(model):
    """Every non-zip coefficient with its standard error, and its meaning in percent."""
    result = model["result"]
    table = pd.DataFrame({"coefficient": result.params, "standard_error": result.bse})
    table = table[~table.index.str.startswith("zip_")]
    # For a yes/no or count feature, one more unit multiplies the price by
    # e^coefficient. The two log features are read per 10% instead.
    table["percent_effect"] = 100 * (np.exp(table["coefficient"]) - 1)
    for name in ["log_living_area", "log_lot"]:
        table.loc[name, "percent_effect"] = 100 * (1.10 ** table.loc[name, "coefficient"] - 1)
    table.loc["intercept", "percent_effect"] = np.nan
    return table


def zip_effect_table(model, zips_to_show):
    """Zip effects against the reference zip code, for a few zip codes."""
    result = model["result"]
    rows = []
    for name in zips_to_show:
        column = "zip_" + name
        if name == model["zips"][0]:
            rows.append({"zip": name, "coefficient": 0.0, "standard_error": np.nan})
        elif column in result.params.index:
            rows.append({"zip": name, "coefficient": result.params[column],
                         "standard_error": result.bse[column]})
    table = pd.DataFrame(rows).set_index("zip")
    table["percent_vs_reference"] = 100 * (np.exp(table["coefficient"]) - 1)
    return table


def worked_example(one_house, model):
    """Each term of the model sum for one house: value, coefficient, product.

    `one_house` is a table with a single row.
    """
    values = build_features(one_house, model["zips"]).iloc[0]
    params = model["result"].params
    used = values[values != 0].index
    table = pd.DataFrame({"value": values[used], "coefficient": params[used]})
    table["value_x_coefficient"] = table["value"] * table["coefficient"]
    return table


# ---------------------------------------------------------------- low and high estimates

def fit_cut_points(price, fair_price, property_type, levels=ALL_LEVELS):
    """How far real prices were from the fair price, as ratios, by house type.

    The ratio is real price / fair price. The 10% cut point is the ratio
    that 10% of training sales fall below. Why by type: townhouses are
    more alike than single family houses, so their ratios spread less.
    """
    ratio = price / fair_price
    table = ratio.groupby(property_type).quantile(levels).unstack()
    table.columns = [float(level) for level in table.columns]
    return table


def estimate_at_level(fair_price, property_type, cut_points, level):
    """The price a house falls below with chance `level`, by this method.

    It is the fair price times the cut point for the house's type. Level
    0.10 is my offer. Levels 0.10 and 0.90 are the ends of the 80% range.
    """
    return fair_price * property_type.map(cut_points[level])


# ---------------------------------------------------------------- scoring

def typical_miss(fair_price, price):
    """Median distance between the fair price and the real price."""
    miss = (fair_price - price).abs()
    return {"median_miss_dollars": miss.median(),
            "median_miss_percent": 100 * (miss / price).median()}


def score_offers(offer, price):
    """Score offers against recorded sale prices, in the units of my decision.

    Overpaid: the offer is above the sale price. Close: the offer is from
    95% to 100% of the sale price. This simplifies real bidding.
    """
    overpaid = offer > price
    close = (offer >= CLOSE_FROM * price) & (offer <= price)
    dollars_over = (offer - price)[overpaid]
    count = len(price)
    return {
        "sales": count,
        "overpaid_count": int(overpaid.sum()),
        "overpaid_percent": 100 * overpaid.mean(),
        "avg_dollars_over_when_overpaid": dollars_over.mean() if overpaid.any() else 0.0,
        "avg_dollars_over_all_offers": dollars_over.sum() / count,
        "close_count": int(close.sum()),
        "close_percent": 100 * close.mean(),
        "median_offer_percent_of_price": 100 * (offer / price).median(),
    }


def score_method(houses, fair_price, cut_points, levels=OFFER_LEVELS):
    """One row of scores per comfort level, for one method."""
    rows = {}
    for level in levels:
        offer = estimate_at_level(fair_price, houses["property_type"], cut_points, level)
        rows[f"{level:.0%}"] = score_offers(offer, houses["price"])
    return pd.DataFrame(rows).T.rename_axis("comfort_level")


def score_by_group(houses, fair_price, cut_points, groups, level=0.10):
    """The same scores at one comfort level, split by a grouping column."""
    offer = estimate_at_level(fair_price, houses["property_type"], cut_points, level)
    rows = {}
    for name, index in houses.groupby(groups, observed=True).groups.items():
        row = score_offers(offer[index], houses.loc[index, "price"])
        row.update(typical_miss(fair_price[index], houses.loc[index, "price"]))
        rows[name] = row
    return pd.DataFrame(rows).T


def readable_scores(scores):
    """The same scores as text, with the count next to every share."""
    sales = scores["sales"].astype(int)
    return pd.DataFrame({
        "overpaid": [f"{int(n):,} of {s:,} ({p:.1f}%)" for n, s, p in
                     zip(scores["overpaid_count"], sales, scores["overpaid_percent"])],
        "avg $ over, when overpaid": scores["avg_dollars_over_when_overpaid"].map("{:,.0f}".format),
        "avg $ over, all offers": scores["avg_dollars_over_all_offers"].map("{:,.0f}".format),
        "close offers": [f"{int(n):,} of {s:,} ({p:.1f}%)" for n, s, p in
                         zip(scores["close_count"], sales, scores["close_percent"])],
        "median offer, % of price": scores["median_offer_percent_of_price"].map("{:.1f}%".format),
    }, index=scores.index)


# ---------------------------------------------------------------- checks for a later step

def calibration_table(houses, fair_price, cut_points, levels=ALL_LEVELS):
    """How often real prices fell below each estimate. Honest estimates match the level."""
    price = houses["price"]
    rows = {}
    for level in levels:
        estimate = estimate_at_level(fair_price, houses["property_type"], cut_points, level)
        below = price < estimate
        rows[f"{level:.0%}"] = {"below_count": int(below.sum()), "sales": len(price),
                                "below_percent": 100 * below.mean()}
    return pd.DataFrame(rows).T.rename_axis("estimate_level")


def range_coverage(houses, fair_price, cut_points, low=0.10, high=0.90):
    """How often the real price was inside the range from the low to the high estimate."""
    kind = houses["property_type"]
    inside = ((houses["price"] >= estimate_at_level(fair_price, kind, cut_points, low))
              & (houses["price"] <= estimate_at_level(fair_price, kind, cut_points, high)))
    return {"inside_count": int(inside.sum()), "sales": len(inside),
            "inside_percent": 100 * inside.mean()}


def beta_interval(successes, trials, mass=0.90):
    """Range for a true share after seeing `successes` out of `trials`.

    Start from a uniform prior, Beta(1, 1): every share from 0 to 1 is
    equally likely before the data. After the data it is
    Beta(1 + successes, 1 + failures). Returns the middle `mass` of it.
    """
    tail = (1 - mass) / 2
    posterior = stats.beta(1 + successes, 1 + trials - successes)
    return posterior.ppf(tail), posterior.ppf(1 - tail)
