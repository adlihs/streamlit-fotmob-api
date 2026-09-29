# streamlit-fotmob-api

Streamlit Data Explorer for FotMob internal API endpoints.

## Features

- Query configured FotMob endpoints.
- Dynamic parameter forms.
- JSON response inspection.
- Automatic conversion of nested record lists into pandas DataFrames.
- CSV and Parquet export.
- Retry handling for transient HTTP errors and rate limiting.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\\Scripts\\activate`.

## Endpoints

- `/api/data/search/suggest`
- `/api/data/allLeagues`
- `/api/data/matches`
- `/api/data/leagues`
- `/api/data/leagueseasondeepstats`
- `/api/data/teams`
- `/api/data/playerData`
- `/api/data/playerMatches`
- `/api/data/matchDetails`
- `/api/data/ltc`
- `/api/data/heatmap/match/{matchId}/heatmaps`
- `/api/data/transfers`
- `/api/data/tvlistings`
- `/api/data/audio-matches`
- `/api/data/dataproviders`

## Disclaimer

FotMob does not publish a complete official public specification for these internal endpoints. They may change without notice. Use responsibly and respect FotMob's terms and applicable rate limits.
