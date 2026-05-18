# RaceLab — Montreal 2026 race predictor

Forecast finishing order, win probability and podium probability for the **Canadian Grand Prix in Montreal on May 24, 2026**, using a **May 18, 2026 data cutoff**.

## Run

Python 3.9 or later; no external packages or API keys.

```sh
python3 app.py
```

Open http://127.0.0.1:8000 and select **Run analysis**. You can edit or import a dataset and export results as JSON. Use `python3 app.py --port 8001` to choose another port.

## Included data

`example.json` contains all **24 races from 2025** and the **first four races of 2026**: Australia, China, Japan and Miami. The latest included race is Miami on May 3, 2026. No Montreal practice, qualifying, sprint, grid or race results enter the model. The entrant list is carried forward from Miami.

Race results come from [Jolpica-F1](https://github.com/jolpica/jolpica-f1); individual source URLs are included in the dataset. The target date is listed on the [official Canadian GP page](https://www.formula1.com/en/racing/2026/canada). `DATA_PROVENANCE.json` records retrieval time, the cutoff policy and a SHA-256 checksum. These are current historical records, which may include later corrections; the cutoff describes the race dates allowed into the analysis.

## Model

Ridge regression uses three past-only features: a driver's mean finish over five starts, their podium rate over five starts and their constructor's mean finish over ten car results. Three races initialize the history. Standardization is fitted only to the training rows.

Whole races are held out chronologically for evaluation against a recent-form baseline. The model then refits on all permitted results. Seeded Monte Carlo simulations add Gaussian noise based on held-out errors and estimate win and podium frequencies.

The 2026 regulation changes can make 2025 form less representative. New drivers or constructor IDs receive neutral defaults until observations are available; constructor IDs are not merged across name changes. Weather, circuit effects, pit stops and retirements are not explicitly modeled. Simulation probabilities are uncalibrated estimates, not betting odds.

## Dataset format

- `as_of`: ISO cutoff date strictly before the target race.
- `target`: race name, date, circuit, season and round.
- `races`: 8–100 races ordered by date, each with season, round and driver/team finishing positions. All must precede the cutoff and target season/round.
- `entrants`: unique driver IDs, names and teams, without target-race outcomes or weekend features.
- `simulations`: 100–50,000; `seed`: integer.

## Code and checks

`engine.py` handles validation, features and simulations; `models.py` implements ridge regression; `app.py` serves the local interface. `POST /api/run` accepts the dataset JSON and returns metrics, rows and diagnostics. The server binds to your computer and does not save imported data.

```sh
python3 -m unittest -v
```
