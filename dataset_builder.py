from __future__ import annotations

from typing import Any
import time
import pandas as pd
from flatten import json_to_frames, flatten_json


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
        # Avoid treating arbitrary entity IDs as players.
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


def _records_from_payload(payload: Any, preferred=("matches", "playerMatches", "games")):
    frames = json_to_frames(payload)
    for key in preferred:
        for frame_key, frame in frames.items():
            if key.lower() in frame_key.lower():
                return frame
    if frames:
        return max(frames.values(), key=len)
    return pd.DataFrame()


def _first_scalar(payload: Any, names):
    for item in _walk(payload):
        if not isinstance(item, dict):
            continue
        for name in names:
            value = item.get(name)
            if value not in (None, "") and not isinstance(value, (dict, list)):
                return value
    return None


def fetch_team_dataset(client, team_id: int, ccode3: str = "", include_market_values: bool = True,
                       include_player_matches: bool = True, max_players: int = 100,
                       max_pages_per_player: int = 5, delay: float = 0.25):
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
    match_frames = []

    for n, row in enumerate(players.itertuples(index=False), start=1):
        pid = int(row.player_id)
        payload = client.get(
            "/api/data/playerData",
            {"id": pid, "includeMarketValues": include_market_values},
        )
        flat = flatten_json(payload)
        flat["player_id"] = pid
        flat["team_id"] = team_id
        player_rows.append(flat)

        if include_player_matches:
            before = None
            seen_signatures = set()
            for page in range(max_pages_per_player):
                params = {"playerId": pid}
                if before:
                    params["before"] = before
                payload_matches = client.get("/api/data/playerMatches", params)
                frame = _records_from_payload(payload_matches)
                if frame.empty:
                    break

                frame = frame.copy()
                frame["player_id"] = pid
                frame["team_id"] = team_id
                frame["page"] = page + 1
                match_frames.append(frame)

                # FotMob may expose a cursor/date under different names.
                next_before = _first_scalar(
                    payload_matches,
                    ("before", "nextBefore", "next", "nextPage", "previous"),
                )
                if not next_before or str(next_before) == str(before):
                    break
                signature = (str(next_before), len(frame))
                if signature in seen_signatures:
                    break
                seen_signatures.add(signature)
                before = next_before
                time.sleep(delay)

        time.sleep(delay)

    players_out = players.reset_index(drop=True)
    player_data = pd.DataFrame(player_rows)
    player_matches = pd.concat(match_frames, ignore_index=True) if match_frames else pd.DataFrame()

    # Remove obvious duplicate match rows when a cursor returns overlapping pages.
    if not player_matches.empty:
        subset = [c for c in ("player_id", "matchId", "match_id", "id") if c in player_matches.columns]
        if subset:
            player_matches = player_matches.drop_duplicates(subset=subset)

    team_frame = pd.DataFrame([flatten_json(team_payload)])
    return {
        "team": team_frame,
        "players": players_out,
        "player_data": player_data,
        "player_matches": player_matches,
    }
