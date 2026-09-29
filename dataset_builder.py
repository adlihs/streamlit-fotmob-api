from __future__ import annotations

from typing import Any
import time
import pandas as pd
from flatten import flatten_json


def _walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk(value)


def extract_players(team_payload: Any) -> pd.DataFrame:
    rows = []
    seen = set()
    for item in _walk(team_payload):
        if not isinstance(item, dict):
            continue
        player_id = item.get("id")
        if not isinstance(player_id, int):
            continue
        marker = str(item.get("type", "")).lower()
        keys = " ".join(str(k).lower() for k in item.keys())
        if not any(x in marker or x in keys for x in ("player", "squad", "position", "shirt")):
            continue
        if player_id in seen:
            continue
        seen.add(player_id)
        rows.append({
            "player_id": player_id,
            "name": item.get("name") or item.get("shortName") or item.get("playerName"),
            "position": item.get("position") or item.get("role"),
            "shirt_number": item.get("shirtNumber") or item.get("shirt"),
        })
    return pd.DataFrame(rows)


def fetch_team_dataset(client, team_id: int, ccode3: str = "",
                       include_market_values: bool = True,
                       max_players: int = 100, delay: float = 0.25):
    """
    Build a team dataset using /teams to discover the squad and
    /playerData?id=<player_id> as the canonical player-detail endpoint.

    playerMatches is intentionally NOT used here. It is a separate endpoint
    for match history and can be queried independently from Endpoint Explorer.
    """
    team_params = {"id": team_id}
    if ccode3:
        team_params["ccode3"] = ccode3

    team_payload = client.get("/api/data/teams", team_params)
    players = extract_players(team_payload)

    if players.empty:
        raise ValueError(
            "No se encontraron jugadores en la respuesta de /teams. "
            "Revisa el teamId o la estructura devuelta por FotMob."
        )

    players = players.head(max_players).copy()
    player_rows = []

    for row in players.itertuples(index=False):
        pid = int(row.player_id)

        # Canonical player endpoint:
        # https://www.fotmob.com/api/data/playerData?id=<player_id>
        params = {"id": pid}
        if include_market_values:
            params["includeMarketValues"] = True

        payload = client.get("/api/data/playerData", params)
        flat = flatten_json(payload)
        flat["player_id"] = pid
        flat["team_id"] = team_id
        player_rows.append(flat)

        time.sleep(delay)

    players_out = players.reset_index(drop=True)
    player_data = pd.DataFrame(player_rows)
    team_frame = pd.DataFrame([flatten_json(team_payload)])

    return {
        "team": team_frame,
        "players": players_out,
        "player_data": player_data,
    }
