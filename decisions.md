# Decisions

This file is the history of the project. Append an entry when a choice changes the work: the quantity, the data, the split, the model, the loss, or the action. Leave old entries in place. A later entry can reverse an earlier one. If a result depends on a random draw, record the seed under Why. The split entry records the cutoff date, or the seed and the fraction. The pull request that merges the code names this entry.

## YYYY-MM-DD: short title

- Decision. What you chose.
- Why. The evidence.
- Alternative. What you rejected.
- Revisit. What would change the choice.

## 2026-11-18: The decision is the most I should offer for a house near Reston

- Decision. I study one choice: for a listed house within about 20 miles of Reston, Virginia, what is the most I should offer? I estimate the sale price in dollars with a low, middle, and high estimate. My offer is the low estimate at my comfort level. I compare my model with the rule buyers use, the zip code's median price per square foot times square feet, by how many held-out houses each would have won at the same comfort level without overpaying more often.
- Why. I am house hunting now, so I can judge the results myself. Fairfax County publishes individual sales with property details. A test query on 2026-11-18 found about 96,000 sales since January 2020 labeled "Valid and verified sale", with the latest in September 2026. Overpaying is the costlier mistake for me. A 10% comfort level means a dollar overpaid counts 9 times as much as a dollar offered too low (0.90 divided by 0.10 is 9).
- Alternative. Why this, not that. I rejected predicting aircraft icing at altitude from pilot reports and weather balloons. I am house hunting now, so I can judge the house results myself. I could not check icing results against my own experience.
- Revisit. I would change the question if the county data cannot be joined into enough clean sales with square feet, year built, and zip code to fit and test a model. I would first add nearby counties before changing the decision itself.

## 2026-11-18: Data source is Fairfax County public records, Fairfax only

- Decision. I use the Fairfax County open data tables from the Department of Tax Administration: sales, dwelling details, address and zip, land use, lot size, and assessed values. They join by parcel ID. I downloaded sales from January 2015 onward on 2026-11-18, with every county sale label kept. I do not republish the files. `data/README.md` gives the download command and a SHA-256 for each file.
- Why. Fairfax contains Reston. The download has 350,708 recorded transfers since 2015, and 173,472 of them carry the county label "Valid and verified sale". The county disclaimer reserves all rights and allows copies for internal or personal use, so I do not create a `data` release.
- Alternative. Why this, not that. I rejected adding Loudoun County now. I found parcel layers for Loudoun but no county download with sale prices, and two counties record house details differently. I also rejected paid data aggregators, because I could not share how to rebuild the data.
- Revisit. I would add Loudoun if I find a public source with sale prices and house details. Until then the model covers the Fairfax part of my 20 miles, not Sterling or Ashburn.

## 2026-11-18: Which sales I keep

- Decision. I keep sales from January 2020 to September 2026, single family houses and townhouses only, with the county label "Valid and verified sale", and a price from $50,000 to $5,000,000. I drop sales with no living area, year built, bedrooms, or zip code, and I treat the placeholder years 1700, 1730, and 2100 as missing. I keep one copy of exact duplicate rows. I drop sales dated before the year built or before the recorded remodel year, and I keep sales in the same year. The baseline is a common rule of thumb, the zip code's median price per square foot times square feet, and it uses the same sales.
- Why. Since 2020 there are 44,009 valid single family sales and 27,751 valid townhouse sales, enough to fit and test a model. The county label is the county's own definition of a market sale, so I do not have to invent one. Of all valid home sales since 2015, 4 are under $50,000 (three at $0, one at $7,000) and 126 are over $5,000,000. A $0 price has no logarithm, and I am not shopping for a $5,000,000 house. The limits are round numbers I fixed before fitting any model. The county describes each house as it is today, so a sale before the year built or the remodel year has the wrong house attached: 487 and 683 valid sales since 2020.
- Alternative. Why this, not that. (1) I rejected keeping 2015 to 2019. Prices then are far from today's, and older sales are more likely to have a house that changed since. I can still train on fewer years in the model step, but not on more. (2) I rejected condos. Their price depends on monthly fees, floor, and building, which the data does not have, and 37,271 of 37,314 valid condo sales have no lot size. (3) I rejected adding "Handyman special" sales (3,963). They are real prices for houses in poor condition, but a listing does not come with that label, so I could not use it for a house I am looking at. (4) I rejected dropping same-year remodel sales (3,410). Many are likely houses renovated and then sold, which the county describes correctly.
- Revisit. I would widen the years if the model needs more sales per zip code. I would add condos if I start shopping for one. I would rethink the remodel rule if the residuals show that same-year remodel sales are priced very differently.

## 2026-11-18: Two more cleaning rules for recording errors

- Decision. I drop sales with a living area under 400 square feet (2 rows). I drop both rows when the same house has two different prices on the same day (3 pairs, 6 rows). This leaves 70,306 sales: single family houses and townhouses in Fairfax County, January 2020 to September 2026.
- Why. One house was recorded at 4 square feet and sold for $1,700,100, which is $425,025 per square foot. That is a recording error, and it would distort the median price per square foot of its zip code. For the same-day pairs, for example $632,500 and $600,000 for one Reston house on 2022-03-28, I cannot tell which price is real.
- Alternative. Why this, not that. I rejected keeping these rows, because the baseline is built from price per square foot and one wrong area can move a zip code's median. For the pairs, I rejected keeping the higher or the lower price, because I have no reason to prefer one.
- Revisit. I would change the 400 square feet limit if I find real small houses being dropped. Only one such sale exists now, at 336 square feet.
