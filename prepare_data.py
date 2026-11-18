"""Join the Fairfax County tables into one row per sale.

Run from the project root, after fetch_data.py has finished:

    python prepare_data.py

It reads the six CSV files in data/ and writes data/fairfax_joined.csv.

What this script does: joins on the parcel ID, gives columns plain names,
turns text into numbers and dates, and adds flag columns.

What this script does NOT do: it removes no sale. Every row of
fairfax_sales.csv is in the output, also $0 sales, transfers, and sales of
parcels with no house record. Which sales to keep is a decision for the
analysis step, and the flag columns are there to make that choice easy.
"""

import time
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data")
OUT_FILE = DATA_DIR / "fairfax_joined.csv"

SQFT_PER_ACRE = 43560


def read_table(file_name):
    """Read one downloaded file with every column as text.

    Why text: the parcel ID has leading zeros and spaces inside it
    ("0311 20  0020"). If pandas guessed the types, IDs and zip codes could
    be changed. Numbers are converted later, column by column.
    """
    return pd.read_csv(DATA_DIR / file_name, dtype=str, keep_default_na=False)


def to_number(text_column):
    """Turn a text column into numbers. Empty or unreadable becomes missing."""
    return pd.to_numeric(text_column.str.strip(), errors="coerce")


def to_whole_number(text_column):
    """Like to_number, but for counts and years, so 1987 is not shown as 1987.0."""
    return to_number(text_column).round().astype("Int64")


def tidy_text(text_column):
    """Cut spaces at both ends. The county pads some labels with a trailing space."""
    return text_column.str.strip()


def first_row_per_parcel(table, count_name):
    """Keep the row with the lowest OBJECTID for each parcel, and count the rows.

    Why: the legal and parcel tables should have one row per parcel. If the
    county ever has two, a plain join would silently copy the sale. The
    count column shows where that happened.
    """
    table = table.assign(_order=to_number(table["OBJECTID"])).sort_values("_order")
    counts = table.groupby("PARID").size().rename(count_name)
    first = table.drop_duplicates("PARID", keep="first").drop(columns="_order")
    return first.merge(counts, on="PARID")


def prepare_sales(sales):
    """One row per recorded sale. Nothing is removed here."""
    out = pd.DataFrame({
        "sale_id": to_whole_number(sales["OBJECTID"]),
        "parcel_id": sales["PARID"],
        "sale_date": pd.to_datetime(sales["SALEDT"], format="%Y-%m-%d", errors="coerce"),
        "price": to_number(sales["PRICE"]),
        "sale_label": tidy_text(sales["SALEVAL_DESC"]),
    })
    out["sale_year"] = out["sale_date"].dt.year.astype("Int64")
    # Same parcel, date, price, and label more than once. Flagged, not removed.
    same = ["parcel_id", "sale_date", "price", "sale_label"]
    out["copies_of_this_sale"] = out.groupby(same, dropna=False)["sale_id"].transform("size")
    return out


def prepare_dwelling(dwelling):
    """One row per parcel from the dwelling table (the house as it is today).

    A parcel can have several dwelling rows. Join choice: I keep the row
    with the largest living area (ties: lowest OBJECTID) as the main house,
    and I keep the number of rows and the total living area of all rows, so
    the choice can be changed later.
    """
    table = pd.DataFrame({
        "parcel_id": dwelling["PARID"],
        "_order": to_number(dwelling["OBJECTID"]),
        "living_area_sqft": to_number(dwelling["SFLA"]),
        "year_built": to_whole_number(dwelling["YRBLT"]),
        "effective_year": to_whole_number(dwelling["EFFYR"]),
        "remodel_year": to_whole_number(dwelling["YRREMOD"]),
        "bedrooms": to_whole_number(dwelling["RMBED"]),
        "full_baths": to_whole_number(dwelling["FIXBATH"]),
        "half_baths": to_whole_number(dwelling["FIXHALF"]),
        "style": tidy_text(dwelling["STYLE_DESC"]),
        "grade": tidy_text(dwelling["GRADE_DESC"]),
        "condition": tidy_text(dwelling["CDU_DESC"]),
        "basement": tidy_text(dwelling["BSMT_DESC"]),
        "rec_room_sqft": to_number(dwelling["RECROMAREA"]),
    })
    groups = table.groupby("parcel_id")
    per_parcel = pd.DataFrame({
        "dwelling_rows": groups.size(),
        # min_count=1: if no row has an area, the total stays missing, not 0.
        "living_area_all_dwellings": groups["living_area_sqft"].sum(min_count=1),
    }).reset_index()
    # Largest living area first. Missing areas go last, so they are not picked
    # over a row that has an area.
    main = (table.sort_values(["living_area_sqft", "_order"],
                              ascending=[False, True], na_position="last")
            .drop_duplicates("parcel_id", keep="first")
            .drop(columns="_order"))
    return main.merge(per_parcel, on="parcel_id")


def prepare_land(land):
    """One row per parcel from the land table: lot size summed over land lines.

    A parcel can have several land lines (for example a homesite line plus
    a second line). Join choice: I add them up. A line gives its size in
    square feet, in acres, or both. I use square feet when it is above 0,
    else acres times 43,560.

    Some parcels (mostly commercial) have the same line number twice with
    different sizes. I cannot tell if that is two pieces of land or two
    versions of one piece. They are added up like the rest, and
    land_line_number_repeats marks those parcels.
    """
    square_feet = to_number(land["SF"])
    acres = to_number(land["ACRES"])
    line_sqft = square_feet.where(square_feet > 0, acres * SQFT_PER_ACRE)
    table = pd.DataFrame({"parcel_id": land["PARID"], "line_number": land["LLINE"],
                          "line_sqft": line_sqft})
    groups = table.groupby("parcel_id")
    out = pd.DataFrame({
        "land_lines": groups.size(),
        # min_count=1: if no line has a size, the total stays missing, not 0.
        "lot_sqft_land_table": groups["line_sqft"].sum(min_count=1),
        "land_line_number_repeats": groups["line_number"].nunique() < groups.size(),
    })
    return out.reset_index()


def prepare_legal(legal):
    """One row per parcel: address, city, zip, and the lot size on the legal record."""
    first = first_row_per_parcel(legal, "legal_rows")
    street = (tidy_text(first["ADRNO"]) + " " + tidy_text(first["ADRSTR"]) + " "
              + tidy_text(first["ADRSUF"]))
    return pd.DataFrame({
        "parcel_id": first["PARID"],
        # Collapse double spaces left by an empty house number or suffix.
        "address": street.str.replace(r"\s+", " ", regex=True).str.strip(),
        "city": tidy_text(first["CITYNAME"]),
        "zip": tidy_zip(first["ZIP1"]),
        "lot_acres_legal": to_number(first["ACRES"]),
        "lot_sqft_legal": to_number(first["SQFT"]),
        "legal_rows": first["legal_rows"],
    })


def tidy_zip(text_column):
    """Keep the zip as text. Only a trailing ".0" from the download is cut off."""
    return text_column.str.strip().str.replace(r"\.0$", "", regex=True)


# The county's land use labels that count as a home type here. Every label
# not in this list is "other". Why a fixed list and not a search for the word
# "condo": the county also has office, medical, retail, and boat slip condos.
# Join choices that can be changed here:
# - "Townhouse in condominium development" counts as townhouse, because the
#   building is a townhouse.
# - "Multiplex in condominium development" counts as condo.
# - Duplex, semidetached, "Two or more Single-family, detached", and rental
#   buildings are "other".
# The full label stays in the land_use column.
PROPERTY_TYPES = {
    "Single-family, Detached": "single_family",
    "Townhouse in ownership development": "townhouse",
    "Townhouse in condominium development": "townhouse",
    "Garden Style condominium (=<4story)": "condo",
    "Multiplex in condominium development": "condo",
    "Medium rise apartments condo(5to8 stry)": "condo",
    "High rise apartments condo(=>9  comm)": "condo",
    "High rise apartments condo(=>9 no comm)": "condo",
}


def property_type(land_use):
    """Sort the county's land use label into four simple groups."""
    return PROPERTY_TYPES.get(land_use, "other")


def prepare_parcel(parcel):
    """One row per parcel: land use, zoning, and the simple property type."""
    first = first_row_per_parcel(parcel, "parcel_rows")
    land_use = tidy_text(first["LUC_DESC"])
    return pd.DataFrame({
        "parcel_id": first["PARID"],
        "land_use": land_use,
        "property_type": land_use.map(property_type),
        "living_units": to_number(first["LIVUNIT"]),
        "zoning": tidy_text(first["ZONING_DESC"]),
        "parcel_rows": first["parcel_rows"],
    })


def assessed_parcels(assessed):
    """Only the list of parcels that have an assessment row.

    Why no values: the assessment was set after most sales, so its dollars
    must not sit next to the sale price until that is decided. Coverage only.
    """
    return pd.DataFrame({"parcel_id": assessed["PARID"].unique(),
                         "has_assessment_row": True})


def join_tables(sales, dwelling, legal, parcel, land, assessed):
    """Left join everything onto the sales, so every sale stays."""
    joined = sales
    for other in [parcel, dwelling, legal, land, assessed]:
        joined = joined.merge(other, on="parcel_id", how="left", validate="many_to_one")
    return joined


def add_flags(joined):
    """Add yes/no columns that describe each sale. Nothing is removed."""
    out = joined.copy()
    # A sale with no row in a table has empty details. Say so explicitly.
    out["has_dwelling_row"] = out["dwelling_rows"].notna()
    out["has_parcel_row"] = out["parcel_rows"].notna()
    out["has_legal_row"] = out["legal_rows"].notna()
    out["has_land_row"] = out["land_lines"].notna()
    out["has_assessment_row"] = out["has_assessment_row"].notna()
    out["several_dwelling_rows"] = out["dwelling_rows"].gt(1).fillna(False)
    out["several_land_lines"] = out["land_lines"].gt(1).fillna(False)
    out["land_line_number_repeats"] = out["land_line_number_repeats"].eq(True)
    # No parcel row means no land use label. That is "other" here, and
    # has_parcel_row tells it apart from a real non-residential label.
    out["property_type"] = out["property_type"].fillna("other")
    # The county describes the house as it is today. A sale before the
    # remodel year sold the older version of the house. A sale before the
    # year built was probably land or a house not finished yet. Only the
    # year is known, so the comparison is by calendar year.
    remodel = out["remodel_year"].where(out["remodel_year"] > 0)
    built = out["year_built"].where(out["year_built"] > 0)
    out["sale_before_remodel"] = (out["sale_year"] < remodel).fillna(False)
    out["sale_in_remodel_year"] = (out["sale_year"] == remodel).fillna(False)
    out["sale_before_built"] = (out["sale_year"] < built).fillna(False)
    return out


def add_lot_size(joined):
    """One lot size column, and a column that says where it came from.

    Join choice: the land table first (summed land lines), then the legal
    record's square feet, then the legal record's acres. The source columns
    stay in the table, so a different order can be used later.
    """
    out = joined.copy()
    legal_from_acres = out["lot_acres_legal"] * SQFT_PER_ACRE
    out["lot_sqft"] = float("nan")
    out["lot_size_source"] = ""
    choices = [("land_table", out["lot_sqft_land_table"]),
               ("legal_sqft", out["lot_sqft_legal"]),
               ("legal_acres", legal_from_acres)]
    for name, values in choices:
        use = out["lot_sqft"].isna() & (values > 0)
        out.loc[use, "lot_sqft"] = values[use]
        out.loc[use, "lot_size_source"] = name
    return out


COLUMN_ORDER = [
    "sale_id", "parcel_id", "sale_date", "sale_year", "price", "sale_label",
    "property_type", "land_use", "living_area_sqft", "year_built",
    "effective_year", "remodel_year", "bedrooms", "full_baths", "half_baths",
    "style", "grade", "condition", "basement", "rec_room_sqft",
    "lot_sqft", "lot_size_source", "address", "city", "zip",
    "living_units", "zoning",
    "sale_before_remodel", "sale_in_remodel_year", "sale_before_built",
    "copies_of_this_sale",
    "has_parcel_row", "has_dwelling_row", "has_legal_row", "has_land_row",
    "has_assessment_row",
    "dwelling_rows", "several_dwelling_rows", "living_area_all_dwellings",
    "land_lines", "several_land_lines", "land_line_number_repeats",
    "lot_sqft_land_table",
    "lot_sqft_legal", "lot_acres_legal", "legal_rows", "parcel_rows",
]


def build_joined_table():
    """Read the six files and return the joined table, one row per sale."""
    sales = prepare_sales(read_table("fairfax_sales.csv"))
    joined = join_tables(
        sales,
        prepare_dwelling(read_table("fairfax_dwelling.csv")),
        prepare_legal(read_table("fairfax_legal.csv")),
        prepare_parcel(read_table("fairfax_parcel.csv")),
        prepare_land(read_table("fairfax_land.csv")),
        assessed_parcels(read_table("fairfax_assessed.csv")),
    )
    joined = add_lot_size(add_flags(joined))
    # The promise of this script: one output row per input sale, no more, no less.
    if len(joined) != len(sales) or not joined["sale_id"].is_unique:
        raise RuntimeError("The join changed the number of sales. Stop and check.")
    return joined[COLUMN_ORDER].sort_values(["sale_date", "sale_id"])


def main():
    start = time.time()
    joined = build_joined_table()
    joined.to_csv(OUT_FILE, index=False, lineterminator="\n")
    print(f"Wrote {OUT_FILE}: {len(joined):,} sales, {joined.shape[1]} columns, "
          f"{time.time() - start:.0f} seconds")


if __name__ == "__main__":
    main()
