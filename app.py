from __future__ import annotations

import io
import zipfile
from datetime import date
import pandas as pd
import streamlit as st
from fotmob_client import FotMobClient, FotMobError
from flatten import json_to_frames, flatten_json
from dataset_builder import fetch_team_dataset

st.set_page_config(page_title="FotMob Data Explorer", page_icon="⚽", layout="wide")
st.title("⚽ FotMob Data Explorer")
st.caption("Explora endpoints individuales o construye datasets relacionales de equipos y jugadores.")

client = FotMobClient()

ENDPOINTS = {
    "Search suggest": {"path": "/api/data/search/suggest", "params": {
        "term": {"type": "text", "default": "", "required": True},
        "hits": {"type": "int", "default": 10}, "lang": {"type": "text", "default": "en"}}},
    "All leagues": {"path": "/api/data/allLeagues", "params": {
        "locale": {"type": "text", "default": "en-US"}, "country": {"type": "text", "default": ""}}},
    "Matches": {"path": "/api/data/matches", "params": {
        "date": {"type": "text", "default": date.today().isoformat(), "required": True},
        "timezone": {"type": "text", "default": "UTC"}, "ccode3": {"type": "text", "default": "USA"}}},
    "League": {"path": "/api/data/leagues", "params": {
        "id": {"type": "int", "default": 47, "required": True},
        "season": {"type": "text", "default": ""}, "ccode3": {"type": "text", "default": "USA"}}},
    "League season deep stats": {"path": "/api/data/leagueseasondeepstats", "params": {
        "id": {"type": "int", "default": 47, "required": True},
        "season": {"type": "text", "default": ""}, "type": {"type": "text", "default": "players"},
        "stat": {"type": "text", "default": ""}, "teamId": {"type": "int", "default": None}}},
    "Team": {"path": "/api/data/teams", "params": {
        "id": {"type": "int", "default": 8456, "required": True},
        "ccode3": {"type": "text", "default": "USA"}}},
    "Player data": {"path": "/api/data/playerData", "params": {
        "id": {"type": "int", "default": 422685, "required": True},
        "includeMarketValues": {"type": "bool", "default": False}}},
    "Player matches": {"path": "/api/data/playerMatches", "params": {
        "playerId": {"type": "int", "default": 422685, "required": True},
        "before": {"type": "text", "default": ""},
        "parentLeagueId": {"type": "int", "default": None}}},
    "Match details": {"path": "/api/data/matchDetails", "params": {
        "matchId": {"type": "int", "default": 0, "required": True}}},
    "Live ticker / commentary": {"path": "/api/data/ltc", "params": {
        "ltcUrl": {"type": "text", "default": "", "required": True},
        "teams": {"type": "text", "default": ""}}},
    "Heatmap": {"path": "/api/data/heatmap/match/{matchId}/heatmaps", "params": {
        "matchId": {"type": "int", "default": 0, "required": True},
        "heatmapUrl": {"type": "text", "default": ""}}},
    "Transfers": {"path": "/api/data/transfers", "params": {
        "teamId": {"type": "int", "default": None}, "leagueId": {"type": "int", "default": None},
        "page": {"type": "int", "default": 1}, "sortBy": {"type": "text", "default": ""},
        "showLoans": {"type": "bool", "default": False}}},
    "TV listings": {"path": "/api/data/tvlistings", "params": {
        "countryCode": {"type": "text", "default": "US"}, "ids": {"type": "text", "default": ""}}},
    "Audio matches": {"path": "/api/data/audio-matches", "params": {}},
    "Data providers": {"path": "/api/data/dataproviders", "params": {}},
}

def zip_dataframes(frames: dict[str, pd.DataFrame]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for name, df in frames.items():
            safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
            z.writestr(f"{safe}.csv", df.to_csv(index=False))
            try:
                parquet = io.BytesIO()
                df.to_parquet(parquet, index=False, engine="pyarrow")
                z.writestr(f"{safe}.parquet", parquet.getvalue())
            except Exception:
                pass
    return buffer.getvalue()

mode = st.sidebar.radio("Modo", ["Dataset Builder", "Endpoint Explorer"])

if mode == "Dataset Builder":
    st.header("🏗️ Dataset Builder")
    st.write("Construye un dataset a partir de un equipo: equipo → plantilla → /api/data/playerData?id=...")

    with st.form("dataset_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            team_id = st.number_input("Team ID", min_value=1, value=8456, step=1)
        with c2:
            ccode3 = st.text_input("CCODE3", value="USA")
        with c3:
            max_players = st.number_input("Máximo de jugadores", min_value=1, max_value=100, value=30, step=1)

        c4, c5 = st.columns(2)
        with c4:
            include_market = st.checkbox("Incluir market values", value=True)
        with c5:
            delay = st.number_input("Pausa entre jugadores (segundos)", min_value=0.0, max_value=5.0, value=0.25, step=0.05)

        build = st.form_submit_button("🚀 Construir dataset", type="primary")

    if build:
        progress = st.progress(0, text="Iniciando...")
        try:
            # fetch_team_dataset performs the network work; progress is updated by phases.
            progress.progress(10, text="Consultando plantilla del equipo...")
            dataset = fetch_team_dataset(
                client,
                int(team_id),
                ccode3=ccode3.strip(),
                include_market_values=include_market,
                max_players=int(max_players),
                delay=float(delay),
            )
            progress.progress(100, text="Dataset completado")
            st.session_state["dataset"] = dataset
            st.success("Dataset construido correctamente.")
        except (FotMobError, ValueError) as e:
            st.error(str(e))
        except Exception as e:
            st.exception(e)

    dataset = st.session_state.get("dataset")
    if dataset:
        st.subheader("Tablas generadas")
        cols = st.columns(len(dataset))
        for col, (name, df) in zip(cols, dataset.items()):
            with col:
                st.metric(name, f"{len(df):,} filas")

        table_name = st.selectbox("Tabla", list(dataset))
        st.dataframe(dataset[table_name], use_container_width=True, height=500)

        st.download_button(
            "⬇️ Descargar todas las tablas (CSV + Parquet)",
            zip_dataframes(dataset),
            file_name=f"fotmob_team_{team_id}_dataset.zip",
            mime="application/zip",
            use_container_width=True,
        )

        st.caption(
            "El Builder usa /api/data/teams para descubrir la plantilla y /api/data/playerData?id=<player_id> "
            "para obtener los datos de cada jugador. playerMatches queda disponible únicamente en Endpoint Explorer."
        )

else:
    st.header("🔎 Endpoint Explorer")
    st.sidebar.header("Consulta")
    endpoint_name = st.sidebar.selectbox("Endpoint", list(ENDPOINTS))
    spec = ENDPOINTS[endpoint_name]
    st.sidebar.code(spec["path"], language="text")

    params = {}
    for name, cfg in spec["params"].items():
        key = f"{endpoint_name}_{name}"
        if cfg["type"] == "bool":
            value = st.sidebar.checkbox(name, value=bool(cfg["default"]), key=key)
        elif cfg["type"] == "int":
            value = st.sidebar.number_input(name, value=int(cfg["default"] or 0), step=1, key=key)
            if cfg["default"] is None and value == 0:
                value = None
        else:
            value = st.sidebar.text_input(name, value=str(cfg["default"] or ""), key=key)
        params[name] = value

    execute = st.sidebar.button("🚀 Consultar", type="primary", use_container_width=True)
    if "raw" not in st.session_state:
        st.session_state.raw = None
    if "frames" not in st.session_state:
        st.session_state.frames = {}

    if execute:
        clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
        try:
            with st.spinner("Consultando FotMob..."):
                raw = client.get(spec["path"], clean_params)
            st.session_state.raw = raw
            st.session_state.frames = json_to_frames(raw)
            st.success(f"Respuesta recibida. Se detectaron {len(st.session_state.frames)} tabla(s).")
        except FotMobError as e:
            st.error(str(e))
        except Exception as e:
            st.exception(e)

    if st.session_state.raw is None:
        st.info("Selecciona un endpoint, completa sus parámetros y pulsa **Consultar**.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["📊 DataFrames", "🧩 JSON", "🔧 Flatten"])
    with tab1:
        frames = st.session_state.frames
        if not frames:
            st.warning("No se pudo convertir la respuesta en tablas.")
        else:
            selected = st.selectbox("Tabla", list(frames))
            df = frames[selected].copy()
            st.write(f"**{len(df):,} filas × {len(df.columns):,} columnas**")
            st.dataframe(df, use_container_width=True, height=500)
            selected_cols = st.multiselect("Columnas a exportar", list(df.columns), default=list(df.columns))
            export_df = df[selected_cols].copy()
            c1, c2, c3 = st.columns(3)
            with c1:
                st.download_button("⬇️ CSV", export_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="fotmob_data.csv", mime="text/csv", use_container_width=True)
            with c2:
                try:
                    parquet_bytes = export_df.to_parquet(index=False, engine="pyarrow")
                    st.download_button("⬇️ Parquet", parquet_bytes,
                        file_name="fotmob_data.parquet", mime="application/octet-stream", use_container_width=True)
                except Exception as e:
                    st.warning(f"Parquet no disponible: {e}")
            with c3:
                st.metric("Filas", f"{len(export_df):,}")
    with tab2:
        st.json(st.session_state.raw)
    with tab3:
        st.dataframe(pd.DataFrame([flatten_json(st.session_state.raw)]), use_container_width=True)
