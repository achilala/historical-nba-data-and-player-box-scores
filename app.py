import streamlit as st
import pandas as pd
import plotly.express as px
import kagglehub
from pathlib import Path

st.set_page_config(
    page_title="NBA Analytics Dashboard",
    page_icon="🏀",
    layout="wide",
)

DATASET_PATH = Path(kagglehub.dataset_download("eoinamoore/historical-nba-data-and-player-box-scores"))

REGULAR_SEASON_TYPES = {"Regular Season", "Pre Season"}
PLAYOFFS_TYPES = {"Playoffs", "Play-in Tournament"}

PLAYER_STAT_COLS = {
    "PTS": "Points",
    "REB": "Rebounds",
    "AST": "Assists",
    "STL": "Steals",
    "BLK": "Blocks",
    "TOV": "Turnovers",
    "FG%": "Field Goal %",
    "3P%": "Three Point %",
    "FT%": "Free Throw %",
    "MIN": "Minutes",
}

TEAM_STAT_COLS = {
    "PTS": "Points",
    "OPP_PTS": "Opp Points",
    "DIFF": "Point Diff",
    "REB": "Rebounds",
    "AST": "Assists",
    "STL": "Steals",
    "BLK": "Blocks",
    "TOV": "Turnovers",
    "FG%": "Field Goal %",
    "3P%": "Three Point %",
    "WIN%": "Win Pct",
}


def add_season(df: pd.DataFrame) -> pd.DataFrame:
    dt = pd.to_datetime(df["gameDateTimeEst"], errors="coerce")
    df["season"] = dt.dt.year + (dt.dt.month >= 10).astype(int)
    return df


PLAYER_NUMERIC_COLS = [
    "numMinutes", "points", "assists", "blocks", "steals", "turnovers",
    "fieldGoalsMade", "fieldGoalsAttempted", "fieldGoalsPercentage",
    "threePointersMade", "threePointersAttempted", "threePointersPercentage",
    "freeThrowsMade", "freeThrowsAttempted", "freeThrowsPercentage",
    "reboundsDefensive", "reboundsOffensive", "reboundsTotal",
    "foulsPersonal", "plusMinusPoints",
]

TEAM_NUMERIC_COLS = [
    "teamScore", "opponentScore", "assists", "blocks", "steals",
    "fieldGoalsMade", "fieldGoalsAttempted", "fieldGoalsPercentage",
    "threePointersMade", "threePointersAttempted", "threePointersPercentage",
    "freeThrowsMade", "freeThrowsAttempted", "freeThrowsPercentage",
    "reboundsDefensive", "reboundsOffensive", "reboundsTotal",
    "foulsPersonal", "turnovers", "numMinutes",
]


@st.cache_data(show_spinner="Loading player stats...")
def load_player_stats() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH / "PlayerStatistics.csv", low_memory=False)
    for col in PLAYER_NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = add_season(df)
    df["playerName"] = df["firstName"] + " " + df["lastName"]
    df["teamName"] = df["playerteamCity"] + " " + df["playerteamName"]
    return df


@st.cache_data(show_spinner="Loading team stats...")
def load_team_stats() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH / "TeamStatistics.csv", low_memory=False)
    for col in TEAM_NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = add_season(df)
    df["teamFullName"] = df["teamCity"] + " " + df["teamName"]
    return df


@st.cache_data(show_spinner="Loading games...")
def load_games() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH / "Games.csv", usecols=["gameId", "gameType"])
    return df.set_index("gameId")


@st.cache_data(show_spinner="Loading advanced stats...")
def load_team_advanced() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH / "TeamStatisticsAdvanced.csv")
    df = add_season(df)
    df["teamFullName"] = df["teamCity"] + " " + df["teamName"]
    return df


def season_label(s: int) -> str:
    return f"{s - 1}-{str(s)[-2:]}"


def game_type_filter(df: pd.DataFrame, game_type: str) -> pd.DataFrame:
    if game_type == "Regular Season":
        return df[df["gameType"].isin(REGULAR_SEASON_TYPES)]
    elif game_type == "Playoffs":
        return df[df["gameType"].isin(PLAYOFFS_TYPES)]
    return df


# --- Player Stats Tab ---
def player_stats_tab():
    player_df = load_player_stats()

    seasons = sorted(player_df["season"].dropna().unique().astype(int), reverse=True)
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        season = st.selectbox(
            "Season",
            seasons,
            index=0,
            format_func=season_label,
        )
    with col2:
        game_type = st.selectbox(
            "Season Type",
            ["Regular Season", "Playoffs", "All"],
        )
    with col3:
        min_gp = st.number_input("Min Games Played", min_value=1, value=10)

    df = player_df[player_df["season"] == season].copy()
    df = game_type_filter(df, game_type)

    agg = (
        df.groupby(["personId", "playerName", "teamName"])
        .agg(
            GP=("gameId", "count"),
            MIN=("numMinutes", "mean"),
            PTS=("points", "mean"),
            REB=("reboundsTotal", "mean"),
            AST=("assists", "mean"),
            STL=("steals", "mean"),
            BLK=("blocks", "mean"),
            TOV=("turnovers", "mean"),
            FG_made=("fieldGoalsMade", "sum"),
            FG_att=("fieldGoalsAttempted", "sum"),
            ThreeP_made=("threePointersMade", "sum"),
            ThreeP_att=("threePointersAttempted", "sum"),
            FT_made=("freeThrowsMade", "sum"),
            FT_att=("freeThrowsAttempted", "sum"),
        )
        .reset_index()
    )

    agg = agg[agg["GP"] >= min_gp].copy()
    agg["FG%"] = (agg["FG_made"].astype(float) / agg["FG_att"].astype(float).where(agg["FG_att"] > 0) * 100).round(1)
    agg["3P%"] = (agg["ThreeP_made"].astype(float) / agg["ThreeP_att"].astype(float).where(agg["ThreeP_att"] > 0) * 100).round(1)
    agg["FT%"] = (agg["FT_made"].astype(float) / agg["FT_att"].astype(float).where(agg["FT_att"] > 0) * 100).round(1)
    for col in ["MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV"]:
        agg[col] = pd.to_numeric(agg[col], errors="coerce").round(1)

    display = agg[["playerName", "teamName", "GP", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "FG%", "3P%", "FT%"]].rename(
        columns={"playerName": "Player", "teamName": "Team"}
    )

    st.subheader(f"Player Stats — {season_label(season)} {game_type}")
    sort_col = st.selectbox("Sort by", list(PLAYER_STAT_COLS.keys()), index=0, key="player_sort")
    display = display.sort_values(sort_col, ascending=False).reset_index(drop=True)
    display.index += 1

    st.dataframe(display, use_container_width=True, height=420)

    st.divider()
    st.subheader(f"Top 15 — {PLAYER_STAT_COLS[sort_col]}")
    top = display.head(15)
    fig = px.bar(
        top,
        x="Player",
        y=sort_col,
        color=sort_col,
        color_continuous_scale="Blues",
        text=sort_col,
        labels={sort_col: PLAYER_STAT_COLS[sort_col]},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, coloraxis_showscale=False, xaxis_tickangle=-30, height=420)
    st.plotly_chart(fig, use_container_width=True)


# --- Team Stats Tab ---
def team_stats_tab():
    team_df = load_team_stats()
    games_df = load_games()
    adv_df = load_team_advanced()

    # Join gameType onto team stats
    team_df = team_df.join(games_df, on="gameId")

    seasons = sorted(team_df["season"].dropna().unique().astype(int), reverse=True)
    col1, col2 = st.columns([2, 2])
    with col1:
        season = st.selectbox("Season", seasons, index=0, format_func=season_label, key="team_season")
    with col2:
        game_type = st.selectbox("Season Type", ["Regular Season", "Playoffs", "All"], key="team_gt")

    df = team_df[team_df["season"] == season].copy()
    df = game_type_filter(df, game_type)

    agg = (
        df.groupby(["teamId", "teamFullName"])
        .agg(
            GP=("gameId", "count"),
            W=("win", "sum"),
            PTS=("teamScore", "mean"),
            OPP_PTS=("opponentScore", "mean"),
            REB=("reboundsTotal", "mean"),
            AST=("assists", "mean"),
            STL=("steals", "mean"),
            BLK=("blocks", "mean"),
            TOV=("turnovers", "mean"),
            FG_made=("fieldGoalsMade", "sum"),
            FG_att=("fieldGoalsAttempted", "sum"),
            ThreeP_made=("threePointersMade", "sum"),
            ThreeP_att=("threePointersAttempted", "sum"),
        )
        .reset_index()
    )

    agg["L"] = agg["GP"] - agg["W"]
    agg["WIN%"] = (agg["W"] / agg["GP"] * 100).round(1)
    agg["DIFF"] = (agg["PTS"] - agg["OPP_PTS"]).round(1)
    agg["FG%"] = (agg["FG_made"].astype(float) / agg["FG_att"].astype(float).where(agg["FG_att"] > 0) * 100).round(1)
    agg["3P%"] = (agg["ThreeP_made"].astype(float) / agg["ThreeP_att"].astype(float).where(agg["ThreeP_att"] > 0) * 100).round(1)
    for col in ["PTS", "OPP_PTS", "REB", "AST", "STL", "BLK", "TOV"]:
        agg[col] = agg[col].round(1)

    display = agg[["teamFullName", "GP", "W", "L", "WIN%", "PTS", "OPP_PTS", "DIFF", "REB", "AST", "STL", "BLK", "TOV", "FG%", "3P%"]].rename(
        columns={"teamFullName": "Team"}
    )

    st.subheader(f"Team Stats — {season_label(season)} {game_type}")
    sort_col = st.selectbox("Sort by", list(TEAM_STAT_COLS.keys()), index=0, key="team_sort")
    ascending = sort_col == "TOV"
    display = display.sort_values(sort_col, ascending=ascending).reset_index(drop=True)
    display.index += 1
    st.dataframe(display, use_container_width=True, height=420)

    st.divider()

    # Scatter: Offense vs Defense
    adv = adv_df[adv_df["season"] == season].copy()
    adv_gt = game_type_filter(adv, game_type) if "gameType" in adv.columns else adv
    if not adv_gt.empty and {"offRating", "defRating"}.issubset(adv_gt.columns):
        adv_agg = (
            adv_gt.groupby(["teamId", "teamFullName"])
            .agg(offRating=("offRating", "mean"), defRating=("defRating", "mean"), netRating=("netRating", "mean"))
            .reset_index()
        )
        st.subheader("Offensive vs Defensive Rating")
        adv_agg["offRating"] = adv_agg["offRating"].round(1)
        adv_agg["defRating"] = adv_agg["defRating"].round(1)
        fig = px.scatter(
            adv_agg,
            x="offRating",
            y="defRating",
            text="teamFullName",
            color="netRating",
            color_continuous_scale="RdYlGn",
            labels={"offRating": "Offensive Rating", "defRating": "Defensive Rating (lower=better)", "netRating": "Net Rating"},
            title="Better offence → right | Better defence → bottom",
        )
        fig.update_traces(textposition="top center", marker_size=10)
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Fallback: PTS vs OPP_PTS bar chart
        st.subheader("Points For vs Against")
        fig = px.bar(
            display.head(30),
            x="Team",
            y=["PTS", "OPP_PTS"],
            barmode="group",
            labels={"value": "Points per Game", "variable": ""},
            color_discrete_map={"PTS": "#1d428a", "OPP_PTS": "#c8102e"},
        )
        fig.update_layout(xaxis_tickangle=-30, height=420)
        st.plotly_chart(fig, use_container_width=True)


# --- Player Profile Tab ---
def player_profile_tab():
    player_df = load_player_stats()

    all_players = (
        player_df[["personId", "playerName"]]
        .drop_duplicates()
        .sort_values("playerName")
    )

    selected = st.selectbox(
        "Search player",
        all_players["playerName"].tolist(),
        index=all_players["playerName"].tolist().index("LeBron James")
        if "LeBron James" in all_players["playerName"].tolist()
        else 0,
    )

    pid = all_players[all_players["playerName"] == selected]["personId"].iloc[0]
    df = player_df[player_df["personId"] == pid].copy()

    career = (
        df.groupby("season")
        .agg(
            GP=("gameId", "count"),
            Team=("teamName", lambda x: x.mode()[0] if len(x) > 0 else ""),
            MIN=("numMinutes", "mean"),
            PTS=("points", "mean"),
            REB=("reboundsTotal", "mean"),
            AST=("assists", "mean"),
            STL=("steals", "mean"),
            BLK=("blocks", "mean"),
            TOV=("turnovers", "mean"),
            FG_made=("fieldGoalsMade", "sum"),
            FG_att=("fieldGoalsAttempted", "sum"),
        )
        .reset_index()
        .sort_values("season")
    )
    career["FG%"] = (career["FG_made"].astype(float) / career["FG_att"].astype(float).where(career["FG_att"] > 0) * 100).round(1)
    for col in ["MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV"]:
        career[col] = pd.to_numeric(career[col], errors="coerce").round(1)
    career["season"] = career["season"].astype(int)
    career["Season"] = career["season"].apply(season_label)

    st.subheader(f"{selected} — Career Stats")

    display = career[["Season", "Team", "GP", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "FG%"]]
    st.dataframe(display.set_index("Season"), use_container_width=True)

    st.divider()
    stat = st.selectbox("Chart stat", ["PTS", "REB", "AST", "STL", "BLK", "TOV", "MIN", "FG%"], key="profile_stat")
    fig = px.line(
        career,
        x="Season",
        y=stat,
        markers=True,
        labels={stat: PLAYER_STAT_COLS.get(stat, stat), "Season": "Season"},
        title=f"{selected} — {PLAYER_STAT_COLS.get(stat, stat)} per Game",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Game Log")

    col1, col2 = st.columns([2, 2])
    with col1:
        log_game_type = st.selectbox(
            "Season Type",
            ["Regular Season", "Playoffs", "All"],
            key="profile_log_gt",
        )

    available_seasons = sorted(
        game_type_filter(df, log_game_type)["season"].dropna().unique().astype(int),
        reverse=True,
    )
    with col2:
        log_season = st.selectbox(
            "Season",
            available_seasons,
            format_func=season_label,
            key="profile_log_season",
        )

    log_df = df[df["season"] == log_season].copy()
    log_df = game_type_filter(log_df, log_game_type)
    log_df = log_df.sort_values("gameDateTimeEst")

    log_df["Date"] = pd.to_datetime(log_df["gameDateTimeEst"], errors="coerce").dt.strftime("%Y-%m-%d")
    log_df["Opponent"] = log_df["opponentteamCity"] + " " + log_df["opponentteamName"]
    log_df["H/A"] = log_df["home"].map({1: "H", 0: "A", True: "H", False: "A"})
    log_df["W/L"] = pd.to_numeric(log_df["win"], errors="coerce").map({1: "W", 0: "L", 1.0: "W", 0.0: "L"})
    log_df["FG%"] = (
        log_df["fieldGoalsMade"].astype(float)
        / log_df["fieldGoalsAttempted"].astype(float).where(log_df["fieldGoalsAttempted"] > 0)
        * 100
    ).round(1)
    log_df["Game"] = range(1, len(log_df) + 1)

    log_display = log_df[["Game", "Date", "W/L", "H/A", "Opponent", "numMinutes", "points", "reboundsTotal", "assists", "steals", "blocks", "turnovers", "FG%", "plusMinusPoints"]].rename(columns={
        "numMinutes": "MIN",
        "points": "PTS",
        "reboundsTotal": "REB",
        "assists": "AST",
        "steals": "STL",
        "blocks": "BLK",
        "turnovers": "TOV",
        "plusMinusPoints": "+/-",
    })
    for col in ["MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV"]:
        log_display[col] = pd.to_numeric(log_display[col], errors="coerce").round(1)

    if log_display.empty:
        st.info("No games found for this selection.")
    else:
        st.dataframe(log_display.set_index("Game"), use_container_width=True, height=300)

        stat_map = {"PTS": "points", "REB": "reboundsTotal", "AST": "assists", "STL": "steals", "BLK": "blocks", "TOV": "turnovers", "MIN": "numMinutes", "FG%": "FG%"}
        log_stat = st.selectbox("Chart stat", list(stat_map.keys()), key="profile_log_stat")
        plot_col = stat_map[log_stat] if log_stat != "FG%" else "FG%"

        rolling = log_df[plot_col].expanding().mean().round(1)
        fig2 = px.scatter(
            log_df,
            x="Game",
            y=plot_col,
            labels={plot_col: PLAYER_STAT_COLS.get(log_stat, log_stat), "Game": "Game #"},
            title=f"{selected} — {PLAYER_STAT_COLS.get(log_stat, log_stat)}, {season_label(log_season)} {log_game_type} (game by game)",
        )
        fig2.add_scatter(
            x=log_df["Game"],
            y=rolling,
            mode="lines",
            name="Season avg",
            line=dict(color="orange", width=2, dash="dot"),
        )
        fig2.update_traces(marker_size=7, selector=dict(mode="markers"))
        fig2.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)


# --- Team History Tab ---
def team_history_tab():
    team_df = load_team_stats()
    games_df = load_games()
    team_df = team_df.join(games_df, on="gameId")
    rs = team_df[team_df["gameType"].isin(REGULAR_SEASON_TYPES)]

    all_teams = sorted(rs["teamFullName"].dropna().unique().tolist())

    defaults = [t for t in ["Los Angeles Lakers", "Boston Celtics", "Chicago Bulls", "Golden State Warriors"] if t in all_teams]
    selected_teams = st.multiselect("Select teams", all_teams, default=defaults[:2])

    if not selected_teams:
        st.info("Select at least one team.")
        return

    df = rs[rs["teamFullName"].isin(selected_teams)]
    history = (
        df.groupby(["teamFullName", "season"])
        .agg(GP=("gameId", "count"), W=("win", "sum"))
        .reset_index()
    )
    history["WIN%"] = (history["W"] / history["GP"] * 100).round(1)
    history["Season"] = history["season"].apply(season_label)

    st.subheader("Win % by Season (Regular Season)")
    fig = px.line(
        history,
        x="Season",
        y="WIN%",
        color="teamFullName",
        markers=True,
        labels={"WIN%": "Win %", "teamFullName": "Team"},
    )
    fig.update_layout(height=480, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Franchise Totals (Regular Season)")
    totals = (
        df.groupby("teamFullName")
        .agg(GP=("gameId", "count"), W=("win", "sum"))
        .reset_index()
    )
    totals["L"] = totals["GP"] - totals["W"]
    totals["WIN%"] = (totals["W"] / totals["GP"] * 100).round(1)
    totals = totals.rename(columns={"teamFullName": "Team"}).set_index("Team")
    st.dataframe(totals, use_container_width=True)


# --- App Layout ---
st.title("🏀 NBA Analytics Dashboard")
st.caption("Historical data from 1946–present | Source: Kaggle — eoinamoore/historical-nba-data-and-player-box-scores")

tab1, tab2, tab3, tab4 = st.tabs(["Player Stats", "Player Profile", "Team Stats", "Team History"])

with tab1:
    player_stats_tab()

with tab2:
    player_profile_tab()

with tab3:
    team_stats_tab()

with tab4:
    team_history_tab()
