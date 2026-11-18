# Proposal

## Hypothesis

A model that uses size, age, lot, location, property type, and sale date makes better offers on houses near Reston, Virginia than the rule buyers use: the zip code's median price per square foot times the house's square feet.

The quantity I estimate is the sale price of a house, in dollars, for houses sold in the months after my training data ends. I give a low, a middle, and a high estimate. I will fix the number of test months before I fit any model.

"Better" means this. Both methods make an offer at the same comfort level, for example at most a 10% chance of paying more than the sale price. On held-out sales, the better method would have won more houses without overpaying more often. Winning means my offer is at or above the sale price. This is a simplification of real bidding.

## Data

The source is the Fairfax County open data site, tables from the Department of Tax Administration. Fairfax County contains Reston.

- Unit of observation: one recorded sale of one parcel, with sale date, sale price, and the county's label for the sale (for example "Valid and verified sale" or "Transfer between related parties").
- Property details come from the county's dwelling and legal description tables, joined by parcel ID: living area, year built, bedrooms, bathrooms, style, lot size, and zip code.
- Sample size and time span: the sales table has about 1.44 million records. About 96,000 sales since January 2020 are labeled valid and verified. The latest sales are from September 2026. I will choose the years, property types, and filters in the data step.
- How collected: the county records every deed transfer and its staff label whether the sale reflects market value.

What I measure differs from what the decision needs in three ways. First, the data cannot see condition, layout, or road noise. A house the model flags as cheap may be cheap for one of these reasons. This is bias, and more sales of the same kind do not fix it. Second, the county describes the house as it is today, not as it was on the sale date, so a later renovation can be attached to an older sale. Third, I need the price a listed house will sell for in the future, but I only have past sales. Prices drift over time. Zip codes with few sales add noise, which more data would reduce.

The county's disclaimer reserves all rights and allows copies for internal or personal use. It does not clearly allow republishing. So I will not create a `data` release. `data/README.md` will give the command that downloads the files from the county, and a SHA-256 for each file.

## Decision affected by the model

I am the one who acts. I am searching for a house within about 20 miles of Reston. For a listed house, I decide the most I should offer. My offer is the model's low estimate at my comfort level. I call a listing undervalued when its asking price is below that low estimate, and those are the houses I visit first.

Overpaying is the costlier mistake. I would rather pass on a good deal than overpay. A 10% comfort level means that a dollar overpaid counts 9 times as much as a dollar offered too low (0.90 divided by 0.10 is 9). I give no extra cost to losing a house. I will compare 5%, 10%, and 25% before I fix the level.

The model is a screening tool for which houses to visit. It does not replace an inspection or an agent.
