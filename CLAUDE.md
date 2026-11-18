# CLAUDE.md

Working rules for AI sessions on this repo. Read this first, every session.
Also read README.md, CHECKLIST.md, decisions.md, PROPOSAL.md, and the course
lab (https://vsokolov.org/labs/final-project-lab.html). If this file conflicts
with the starter repo's rules, the repo wins, and the student is told.

## Who decides

The student is solo, is responsible for everything on main, and must defend
every choice in a live 3-minute talk. The student decides. The AI advises and builds.

1. Before each step, say in plain words: what we are about to do, why it
   matters, and what comes after it.
2. At the start of each step, give all real choices for that step in one batch
   (data source, area, time range, property types, filters, baseline, features,
   split, model, comfort level, offer rule). For each: 2 to 3 options, the
   tradeoff, and a recommendation with the reason. Wait for answers. Do not
   pick. If a new choice comes up mid-step, stop and ask. After the student
   chooses, write the decisions.md entries in the student's words and show
   them. decisions.md is append-only. Never rewrite an old entry.
3. Every decisions.md entry has a "why this, not that" line: the rejected
   alternative and the reason. It goes in the Alternative bullet of the repo's
   entry format (Decision, Why, Alternative, Revisit).
4. After each step, give a short recap: what we did, what the result means,
   and what a classmate or the professor might ask, with a short answer.
   Append these questions and answers to STUDY_NOTES.md (gitignored).
5. Explain any stats or ML idea literally, with a small worked example using
   real numbers. No summation notation: write formulas term by term. Plain
   words beat jargon (English stats terms are not the student's first language).
6. Do not write code the student has not agreed to. Keep functions small and
   comment the "why".
7. Small mechanical tasks (installing packages, fixing a bug, formatting) do
   not need approval. Just report them.
8. Never push to GitHub without the student's OK.
9. Keep this file up to date when decisions change.
10. Keep a running record in STUDY_NOTES.md so the student understands every
    step and can build the slide deck from it. Three sections there:
    "Project log" (dated, plain words: what was decided or found, why, and
    which slide it feeds), "Talk plan" (the slide mapping below), and the
    question-and-answer sections. Add to the log after every decision, every
    result, and every question the student asks. Never leave it for later.

## Writing style for submitted files

PROPOSAL.md, decisions.md, README, slides: plain, short sentences, first
person, no em dashes (use commas, colons, or periods), no grand framing, no
superlatives.

## Project plan (starting plan, each item is confirmed with the student when reached)

The student is searching for a house within about 20 miles of Reston, VA, and
wants to spot houses priced below what they are worth.

- Decision: for a listed house, what is the most I should offer? A listing is
  "undervalued" when its asking price is below the model's low estimate of the
  sale price.
- Hypothesis: a model using size, age, lot, location, property type, and sale
  date predicts sale prices better than a common rule of thumb: the area's
  median price per square foot times the house's square feet. Call it "a
  common rule of thumb", never "the rule buyers use" (changed 2026-11-18:
  there is no evidence most buyers decide this way).
- Data: past home sales with property details. Start with Fairfax County.
  Adding nearby counties (such as Loudoun) is the student's decision after
  seeing the counts.
- Baseline: zip code median price per square foot, from training sales only,
  times square feet. County tax assessment as a second baseline is an option
  to show.
- Model: linear regression on the log of sale price. Show why log and not raw
  dollars, using the data.
- Low and high estimates: from the spread of the model's errors on training
  data. Quantile regression is an alternative to show.
- Split: by time, never random. Older sales train, the most recent months
  test. How the model handles the sale date (price drift) is a decision.
- No leakage: every number the baseline or model uses (zip medians, scaling,
  error spread, offer rule) comes from training sales only. No feature that
  already contains the sale price, such as an assessment made after the sale.
  Test months are scored once, at the end.
- Offer rule: the student would rather pass on a good deal than overpay.
  Comfort level: at most a 10% chance of paying more than the sale price. The
  offer is the model's 10% low estimate. Show 5%, 10%, and 25% side by side.
- Decision units (changed 2026-11-18, see decisions.md "How I score offers"):
  on held-out sales, for each comfort level, the share overpaid, the average
  dollars overpaid, and the share of close offers (95% to 100% of the sale
  price). "Share won" was dropped: it was the same event as overpaid. Same
  for the baseline at the same comfort levels. This simplifies real bidding:
  say so wherever results appear.
- No cost for losing a house: that cost is close to zero for the student, and
  a rule built on it would say never buy. Record as the rejected alternative.
- Known limit, stated wherever results appear: a flagged house may be cheap
  for a reason the data cannot see (condition, layout, road noise). More sales
  of the same kind do not fix that. The model is a screening tool for which
  houses to visit. It does not replace an inspection or an agent.
- Margin of safety, stated wherever results appear: offering the low estimate
  leaves a buffer for unseen problems. But flagged houses are more likely than
  average to have such problems, because the problem may be why the price is low.
- Step 3 must also include, each explained with numbers first: a calibration
  check (do 80% ranges hold about 80% of held-out prices, is the 10% low
  estimate above the sale price about 10% of the time), a Beta range with a
  uniform prior on the share of houses won (show counts, say why Beta fits),
  and a note separating noise (few sales in a zip) from bias (things the data
  cannot see).
- Step 4, after Step 3 and with the student's OK: the student types in a few
  live listings. Show low, middle, high estimates and which are flagged. A
  demo for the talk, not part of the held-out score.

## Talk plan (agreed 2026-11-18, build after Step 3)

The repo fixes the deck: title slide plus exactly four slides, three minutes,
no added slides. The student's ideas map onto them like this:

- Title: one spoken sentence on the question (house hunting near Reston, what
  is the most I should offer). No separate proposal slide.
- Action: "Offer the model's low estimate. Visit listings priced below it."
  Example table with two live listings: asking price, rule of thumb value,
  model low / middle / high, verdict.
- Reason: the held-out score only (share won, share overpaid, average dollars
  overpaid, model vs rule of thumb at the same comfort level). Must match the
  notebook exactly.
- Risk: one number (chance and size of overpaying) plus the limit that a
  flagged house may be cheap for a reason the data cannot see. The student's
  own house visit can be a one-sentence example here.
- Value: what being less wrong is worth in dollars.
- Data, methods, and statistics stay in analysis.ipynb and in Q&A prep.
- Wording: the model "flags" a house, it never "proves" anything.
- The two live listings are picked by a fixed rule BEFORE seeing the model's
  verdict (rule still to be chosen by the student), typed in by hand, shown
  as a plain table, not a Zillow screenshot.
- No class vote. Q&A comes after the three minutes and has no slide.

## Deadlines

- Real deadline: final presentation Dec 9, 2026. Push to main by 7:00 pm
  Eastern. Talk is 7:30 to 10:15 pm. presentation.html has a title slide plus
  four slides: action, reason, risk with a number, value of being less wrong.
  CHECKLIST.md is ticked in the final commit.
- Proposal (Oct 28) and preliminary results (Nov 18) are soft per the
  professor. The student wants the proposal pushed the week of Nov 16 for
  early feedback. A late push still gets a comment, and the issue says it was late.
- If data is republished, the repo says the `data` release exists by Nov 18.

## Repo rules that are easy to miss

- Solo student may commit to main. No force-push to main.
- Data files, secrets, fitted weights stay out of git. Each data file needs a
  SHA-256 in data/README.md, and the notebook checks it.
- requirements.txt lists only packages the notebook imports, pinned, for the
  interpreter in .python-version (3.13.18). No pip freeze dump.
- Notebook on main is run top to bottom with outputs saved. Plots in fig/,
  including fig/layers.png (diagram: data, model, prediction, decision).
- Shared functions go in .py files the notebook imports.
- The split entry in decisions.md records the cutoff date.
- CHECKLIST.md wants the loss or profit as a formula, and why the loss picks
  the offer rule. The comfort level has to be tied to a written loss.
- README needs the student's name and GitHub username under "Who", and one
  line on AI tool use.
- Render presentation.qmd once, in the commit that is presented.
- The collaborator invite to VadimSokolov (sent 2026-11-14) expires 2026-11-21
  if not accepted. Resend it then.

## Environment and data notes

- Windows, PowerShell. Virtual env in .venv (gitignored). Quarto 1.11.9.
- Fairfax County open data, verified with test queries on 2026-11-18. Tables
  join on PARID. Base URL:
  https://services1.arcgis.com/ioennV6PpG5Xodq0/ArcGIS/rest/services
  - Sales: OpenData_A5/FeatureServer/1 (PARID, SALEDT, PRICE, SALEVAL_DESC)
  - Dwelling: OpenData_A7/FeatureServer/2 (style, year built, beds, baths, SFLA)
  - Legal description: OpenData_A7/FeatureServer/1 (address, zip, acres)
- The county GIS disclaimer grants reproduction for internal or personal use
  only. Republishing is not clearly allowed.

## Status

- 2026-11-14: fork created, Issues on, invite sent.
- 2026-11-18: project changed from aircraft icing to house offers near Reston.
  Earlier local drafts were discarded before any commit. Proposal and first
  decisions.md entry in progress.
- 2026-11-18: Step 2 choices made (see decisions.md): Fairfax only; sales
  2020-01 to 2026-09; single family and townhouse; label "Valid and verified
  sale"; price $50,000 to $5,000,000; drop missing living area, year built,
  bedrooms, zip; one copy of exact duplicates; drop sales before year built
  or remodel year. Pipeline: fetch_data.py, prepare_data.py (join only),
  select_sales.py (filters), then the notebook reads data/fairfax_selected.csv.
- The student asked for build work to be delegated to a subagent while the
  main session orchestrates and answers questions.
- 2026-11-18: two more rules: drop living area under 400 sq ft, drop both rows
  of same-house same-day price conflicts. Final: 70,306 sales in
  data/fairfax_selected.csv. Step 2 pushed. Next is Step 3. Open items for
  Step 3: 1,213 townhouses have no lot size; September 2026 is a partial
  month; 754 resales within a year (possible flips); 11 zips have fewer than
  100 sales; assessed values exist for tax year 2026 only.
- 2026-11-18: Step 3 core done and pushed for the preliminary checkpoint.
  house_model.py holds the functions, analysis.ipynb runs top to bottom.
  Split cutoff 2026-03-01, both methods learn from 2025-03-01 to 2026-02-28,
  cut points by property type, offer = 10% low estimate. Test (5,816 sales,
  scored once): overpaid model 485 vs rule 541, average dollars over $60,822
  vs $110,308, close offers 509 vs 331, typical miss 6.9% vs 12.6%.
- Still open in Step 3: the calibration check, the Beta range, and the noise
  versus bias note are NOT in the notebook. The functions exist in
  house_model.py. The student asked for time to understand them first
  (does not yet know what a Beta range is). Explain again, slowly, with the
  3-of-10 example, then add after the student's nod. Also open: the student
  is "not sure" about the "assumption I trust least" sentence (draft: flat
  price level inside the 12-month window); whether to show the assessed
  value as a second baseline; the rule for picking live listings (Step 4).
