# RaceLab — Singapore Grand Prix prediction lab

A historical pre-weekend forecast for the **Singapore Grand Prix on October 5, 2025**, with an **as-of cutoff of October 2, 2025**. It learns from earlier driver/team results, then simulates finishing orders. The target and cutoff were selected during reconstruction to fit the owner's October 2025 project date; they are not proof of a prediction published in 2025.

## Project history

The original project was completed in programming club in **October 2025**, according to the project owner's recollection. The original files were lost. This repository contains a new implementation reconstructed with AI assistance in **September 2026**, and its commits record the actual reconstruction/upload dates. It is not a recovery of the original source or an exact copy of the reel's code.

## Run locally

Requires Python 3.9 or later. No external packages, API keys, or network access are needed.

```sh
python3 app.py
```

Open http://127.0.0.1:8000. For a second project running at the same time, use `python3 app.py --port 8001`. The server binds only to your computer.

1. Click **Run analysis** to evaluate the historical dataset.
2. Edit the JSON input or load your own JSON file.
3. Inspect metrics, the results table and model notes.
4. Export the complete result as JSON.

## Historical dataset and cutoff

`example.json` includes rounds 1–17 of the 2025 championship: Australia through Azerbaijan (September 21). There are 339 recorded driver results. **No Singapore result, practice, qualifying, grid, or later race is included.** The retrieval script requests only those round endpoints, rather than downloading the full season and retaining later results.

Sources: [Jolpica-F1](https://github.com/jolpica/jolpica-f1), [results endpoint documentation](https://github.com/jolpica/jolpica-f1/blob/main/docs/endpoints/results.md), and [official 2025 calendar](https://www.formula1.com/en/racing/2025). Each race carries its source URL. Retrieval time and SHA-256 fingerprints are in `DATA_PROVENANCE.json`.

These are current historical database records, not a preserved October 2025 database snapshot. Later retrospective corrections to earlier results cannot be ruled out. This project enforces event-date exclusion and past-only features; it does not claim perfect historical data-vintage reproduction. The target entrant list is carried forward from Azerbaijan, an explicit modeling assumption.

## Input contract

- `as_of`: ISO date before the target race. Historical races must be strictly earlier.
- `target`: race name, ISO date, round and circuit.
- `races`: 8–100 complete races in ascending date order, all before the cutoff and target round. Each contains `name`, `date`, `round`, and `results` (driver ID, team ID, unique integer finish).
- `entrants`: 3–30 unique driver IDs with names and teams. Target finish, grid, practice and points fields are rejected.
- `simulations`: 100–50,000; `seed`: integer.

## Method and limits

Features are the driver's mean finish over the previous five starts, constructor mean finish over the previous ten car results, and driver's podium rate over the previous five starts. A driver with no prior history uses neutral values. Three races initialize the rolling history. For each training race, features are derived only from races before that race; no current-race result enters its features.

Ridge regression uses a fixed penalty of 2 and standardization fitted on training rows only. Whole race groups are held out chronologically. During validation, feature history updates after each earlier completed race, while fitted coefficients remain fixed. The final forecast refits on all allowed historical rows. A recent-form baseline is reported alongside model MAE.

Monte Carlo simulations add independent Gaussian noise to finishing scores, with scale estimated from held-out errors. Win/podium frequencies depend on this approximation; they are not calibrated betting odds. Sampling standard error is not total model uncertainty. Circuit effects, weather, pit stops and retirements are not explicitly modeled. There is no live data feed or actual race-outcome comparison for the target.

The local server accepts JSON up to 1 MB, validates input, and does not persist imported data. `engine.py` owns temporal validation and features; `models.py` owns the numerical solver. `test_engine.py` tests date exclusions, feature leakage, chronological holdout and probability conservation.

## Verify

```sh
python3 -m unittest -v
```

## API

`POST /api/run` accepts the same JSON as the editor and returns `metrics`, `series`, `rows`, and `details`. Errors return HTTP 400 with an `error` message. This is a local educational server, not an Internet-facing production service.

## Historical availability of the method

Ridge regression was published by Hoerl and Kennard in 1970 ([original paper](https://doi.org/10.1080/00401706.1970.10488634)). This reconstruction fits coefficients from the supplied historical data; it does not use a pretrained modern foundation model. The implementation uses only Python 3.9 standard-library functionality.
