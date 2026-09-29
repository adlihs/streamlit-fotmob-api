# streamlit-fotmob-api

Streamlit Data Explorer + Dataset Builder for FotMob internal API endpoints.

## Features

- Query 15 configured FotMob endpoints.
- Dynamic parameter forms and JSON inspection.
- Automatic conversion of nested record lists into pandas DataFrames.
- CSV and Parquet export.
- **Dataset Builder:** team → squad → playerData → playerMatches.
- Separate relational tables: `team`, `players`, `player_data`, `player_matches`.
- ZIP export containing CSV and Parquet versions of all generated tables.
- Retry handling for transient HTTP errors and rate limiting.
- Heatmap endpoint path parameters are handled automatically.

## Dataset Builder

Enter a FotMob `teamId`, optionally set `ccode3`, choose the maximum number of players and the number of player-match pages to retrieve.

Generated tables keep explicit keys for later joins:

| Table | Main key |
|---|---|
| `team` | `team_id` |
| `players` | `player_id` |
| `player_data` | `player_id`, `team_id` |
| `player_matches` | `player_id`, `team_id` |

The output can be loaded into pandas, Polars, DuckDB or a data warehouse.

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
