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
