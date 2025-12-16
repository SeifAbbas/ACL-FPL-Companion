"""
Knowledge Graph Query Module for FPL Graph-RAG Assistant
Handles all Neo4j queries with baseline and semantic retrieval modes.
"""

from neo4j import GraphDatabase
from difflib import get_close_matches
from .config import Config

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    HuggingFaceEmbeddings = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_search_aliases(db_code):
    """Expands position code to aliases for flexible matching."""
    code = db_code.upper()
    alias_map = {
        "GKP": ["GKP", "GK", "Goalkeeper", "Goalie", "Keeper"],
        "DEF": ["DEF", "DF", "Defender", "Back", "CB", "LB", "RB"],
        "MID": ["MID", "MF", "Midfielder", "Wing", "Winger"],
        "FWD": ["FWD", "FW", "Forward", "Striker", "Attacker", "ST"]
    }
    return alias_map.get(code, [code])


def resolve_position(session, raw_pos):
    """Converts user position input to database-compatible aliases."""
    if not raw_pos:
        return []
    
    raw = str(raw_pos).strip().lower()

    manual_map = {
        "goal": "GKP", "keep": "GKP", "gk": "GKP",
        "def": "DEF", "back": "DEF", "cb": "DEF", "lb": "DEF", "rb": "DEF",
        "mid": "MID", "wing": "MID", "central": "MID",
        "forw": "FWD", "strik": "FWD", "attac": "FWD", "st": "FWD"
    }

    for key, code in manual_map.items():
        if key in raw:
            return get_search_aliases(code)

    result = session.run("MATCH (p:Position) RETURN p.name AS name")
    db_positions = [r["name"] for r in result]

    for pos in db_positions:
        if raw == pos.lower():
            return get_search_aliases(pos)

    for pos in db_positions:
        if (pos.lower() in raw and len(pos) > 2) or (raw in pos.lower() and len(raw) > 2):
            return get_search_aliases(pos)

    return [raw_pos]


def resolve_team(session, raw_name):
    """Resolves user team input to exact database team name."""
    if not raw_name:
        return None
    
    raw_name = raw_name.strip()
    raw_lower = raw_name.lower()

    cypher_query = """
    MATCH (t:Team)
    WHERE toLower(t.name) = $raw 
       OR toLower(t.name) CONTAINS $raw
       OR all(term IN split($raw, ' ') WHERE toLower(t.name) CONTAINS term)
    RETURN t.name AS Name 
    LIMIT 1
    """
    result = session.run(cypher_query, {"raw": raw_lower})
    record = result.single()

    if record:
        return record["Name"]

    result = session.run("MATCH (t:Team) RETURN t.name AS name")
    db_teams = [r["name"] for r in result]

    matches = get_close_matches(raw_name, db_teams, n=1, cutoff=0.6)
    return matches[0] if matches else raw_name


def resolve_player_names_semantic(session, raw_names, embedder, index_name):
    """
    SEMANTIC MODE ONLY: Resolves messy player names using vector similarity.
    This is what makes semantic mode different from baseline.
    """
    cleaned_names = []

    for name in raw_names:
        vector = embedder.embed_query(name)

        # Vector search only - this is the key difference from baseline
        query = f"""
        CALL db.index.vector.queryNodes('{index_name}', 10, $vec)
        YIELD node, score
        WHERE score > 0.70
        RETURN node.player_name AS Name
        ORDER BY score DESC
        LIMIT 1
        """

        result = session.run(query, {"vec": vector})
        record = result.single()

        if record and record["Name"]:
            cleaned_names.append(record["Name"])
        else:
            cleaned_names.append(name)

    return cleaned_names


# =============================================================================
# MAIN QUERY FUNCTION
# =============================================================================

def query_knowledge_graph(structured_data, retrieval_mode="baseline", model_choice="A"):
    """
    Main entry point for querying the Knowledge Graph.
    
    BASELINE: Uses exact text matching - typos will fail
    SEMANTIC: Uses vector search to find similar names - handles typos
    """
    intent = structured_data.get("intent")
    entities = structured_data.get("entities", {})
    user_query = str(structured_data.get("user_query", "")).lower()

    # ==========================================================================
    # INTENT OVERRIDE: Fix common misclassifications
    # ==========================================================================
    if intent == "General_Chat":
        if entities.get("Player"):
            intent = "Player_Stats"
        elif entities.get("Team"):
            intent = "Team_Stats"
        elif entities.get("Position") or entities.get("Metric"):
            intent = "Top_Ranked"

    # Head-to-Head detection
    if any(p in user_query for p in ["h2h", " vs ", "versus", "head to head", "against"]):
        team_list = entities.get("Team", [])
        if isinstance(team_list, str):
            team_list = [team_list]
        if len(team_list) >= 2:
            intent = "Head_to_Head"

    # ==========================================================================
    # INPUT SANITIZATION
    # ==========================================================================
    names = entities.get("Player", [])
    if isinstance(names, str):
        names = [names]
    names = [n.strip() for n in names if n]

    team_names = entities.get("Team", [])
    if isinstance(team_names, str):
        team_names = [team_names]
    team_names = [t.strip() for t in team_names if t]

    # ==========================================================================
    # MODEL SELECTION
    # ==========================================================================
    if model_choice == "B":
        active_model = Config.EMBEDDING_MODEL_B
        active_index = "player_idx_b"
    else:
        active_model = Config.EMBEDDING_MODEL_A
        active_index = "player_idx_a"

    # ==========================================================================
    # SEASON AND FILTERS
    # ==========================================================================
    target_season = entities.get("Season")
    target_gw = entities.get("Gameweek")
    target_metric = entities.get("Metric", "total_points")
    raw_pos = entities.get("Position")

    if target_season:
        target_season = str(target_season).strip()
        if "21" in target_season:
            target_season = "2021-22"
        elif "22" in target_season or "23" in target_season:
            target_season = "2022-23"
    else:
        target_season = "2022-23"

    base_filters = []
    base_filters.append(
        "EXISTS { MATCH (f)<-[:HAS_FIXTURE]-(:Gameweek)<-[:HAS_GW]-(s:Season) "
        "WHERE s.season_name CONTAINS $season }"
    )

    if target_gw:
        base_filters.append(
            "EXISTS { MATCH (f)<-[:HAS_FIXTURE]-(gw:Gameweek) "
            "WHERE toString(gw.GW_number) = toString($gw) OR gw.GW_number = toInteger($gw) }"
        )

    params = {"season": target_season, "gw": target_gw}
    executed_cypher = "No Query Executed"

    # ==========================================================================
    # DATABASE CONNECTION
    # ==========================================================================
    driver = GraphDatabase.driver(
        Config.NEO4J_URI,
        auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD)
    )

    try:
        with driver.session() as session:
            
            # ==================================================================
            # KEY DIFFERENCE: BASELINE vs SEMANTIC
            # ==================================================================
            # SEMANTIC: Pre-resolve names using vector search (handles typos)
            # BASELINE: Use names exactly as provided (typos will fail)
            
            if retrieval_mode == "semantic" and names and HuggingFaceEmbeddings:
                embedder = HuggingFaceEmbeddings(model_name=active_model)
                params["names"] = resolve_player_names_semantic(
                    session, names, embedder, active_index
                )
            else:
                # BASELINE: Use raw names without any correction
                params["names"] = names

            # Resolve teams (both modes do this)
            clean_teams = []
            for t in team_names:
                resolved = resolve_team(session, t)
                if resolved:
                    clean_teams.append(resolved)
            params["team_names"] = clean_teams

            # Resolve position aliases
            params["aliases"] = resolve_position(session, raw_pos)

            # ==================================================================
            # INTENT 1: PLAYER_STATS
            # ==================================================================
            if intent == "Player_Stats":
                filter_clause = " AND ".join(base_filters) if base_filters else "1=1"
                
                # Simple CONTAINS matching - typos will fail in baseline mode
                query = f"""
                UNWIND $names AS search_name
                
                MATCH (p:Player)
                WHERE toLower(p.player_name) CONTAINS toLower(search_name)
                
                MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
                WHERE ({filter_clause}) AND r.minutes > 0
                
                WITH p, 
                     count(r) AS Matches, 
                     sum(r.total_points) AS Points, 
                     sum(r.goals_scored) AS Goals, 
                     sum(r.assists) AS Assists,
                     sum(r.minutes) AS Minutes
                
                ORDER BY Matches DESC
                LIMIT 1
                
                RETURN p.player_name AS Player, Points, Goals, Assists, Matches, Minutes
                """

                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 2: COMPARE_PLAYERS
            # ==================================================================
            elif intent == "Compare_Players":
                filter_clause = " AND ".join(base_filters) if base_filters else "1=1"
                
                query = f"""
                UNWIND $names AS search_name
                MATCH (p:Player) 
                WHERE toLower(p.player_name) CONTAINS toLower(search_name)
                
                MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
                WHERE ({filter_clause}) AND r.minutes > 0
                
                RETURN 
                    p.player_name AS Name,
                    sum(r.total_points) AS Points,
                    sum(r.goals_scored) AS Goals,
                    sum(r.assists) AS Assists,
                    count(r) AS Matches,
                    sum(r.minutes) AS Minutes,
                    round(toFloat(sum(r.total_points)) / count(r), 2) AS PointsPerGame
                ORDER BY Points DESC
                """

                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 3: TOP_RANKED
            # ==================================================================
            elif intent == "Top_Ranked":
                filter_clause = " AND ".join(base_filters) if base_filters else "1=1"

                sort_clause = "ORDER BY Points DESC"
                is_keeper_query = params["aliases"] and "GKP" in params["aliases"]

                if target_metric:
                    tm = target_metric.lower()
                    if "goal" in tm and not is_keeper_query:
                        sort_clause = "ORDER BY Goals DESC"
                    elif "assist" in tm:
                        sort_clause = "ORDER BY Assists DESC"
                    elif "clean" in tm:
                        sort_clause = "ORDER BY CleanSheets DESC"
                    elif "save" in tm:
                        sort_clause = "ORDER BY Saves DESC"

                pos_filter = ""
                if params["aliases"]:
                    pos_filter = """
                    WHERE any(alias IN $aliases WHERE 
                        toLower(pos.name) = toLower(alias) OR 
                        toLower(pos.name) CONTAINS toLower(alias) OR 
                        toLower(alias) CONTAINS toLower(pos.name)
                    )
                    """

                query = f"""
                MATCH (p:Player)-[:PLAYS_AS]->(pos:Position)
                {pos_filter}
                
                MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
                WHERE ({filter_clause}) AND r.minutes > 0
                
                WITH p, pos,
                     count(r) AS Matches,
                     sum(r.total_points) AS Points,
                     sum(r.goals_scored) AS Goals,
                     sum(r.assists) AS Assists,
                     sum(r.clean_sheets) AS CleanSheets,
                     sum(r.saves) AS Saves
                
                RETURN 
                    p.player_name AS Player,
                    pos.name AS Position,
                    Matches, Points, Goals, Assists, CleanSheets
                {sort_clause}
                LIMIT 10
                """

                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 4: TEAM_STATS
            # ==================================================================
            elif intent == "Team_Stats":
                target_season = params.get("season", "2022-23")
                
                query = """
                UNWIND $team_names AS t_name
                MATCH (t:Team) WHERE toLower(t.name) CONTAINS toLower(t_name)
                
                // Find all fixtures for this team in the season
                MATCH (s:Season) WHERE s.season_name = $season OR s.season_name CONTAINS $season
                MATCH (s)-[:HAS_GW]->(gw:Gameweek)-[:HAS_FIXTURE]->(f:Fixture)
                
                // Get fixtures where our team played
                MATCH (f)-[:HAS_HOME_TEAM]->(home:Team)
                MATCH (f)-[:HAS_AWAY_TEAM]->(away:Team)
                WHERE home = t OR away = t
                
                // Get all players who played in this fixture with their stats
                MATCH (p:Player)-[r:PLAYED_IN]->(f)
                WHERE r.minutes > 0
                
                // For each player, count how many fixtures they have with our team
                WITH t, f, home, away, p, r
                OPTIONAL MATCH (p)-[:PLAYED_IN]->(:Fixture)-[:HAS_HOME_TEAM|HAS_AWAY_TEAM]->(t)
                WITH t, f, home, away, p, r, count(*) AS player_team_fixtures
                
                // Count player's total fixtures in the season
                OPTIONAL MATCH (p)-[:PLAYED_IN]->(any_f:Fixture)<-[:HAS_FIXTURE]-(:Gameweek)<-[:HAS_GW]-(s2:Season)
                WHERE s2.season_name CONTAINS $season
                WITH t, f, home, away, p, r, player_team_fixtures, count(DISTINCT any_f) AS player_total_fixtures
                
                // Player belongs to our team if majority of their fixtures involve our team
                // (handles transfers - player belongs to team they played most for)
                WITH t, f, home, away, r,
                     CASE WHEN player_team_fixtures >= player_total_fixtures * 0.5 THEN true ELSE false END AS is_my_player
                
                // Aggregate goals at fixture level
                WITH t, f,
                     sum(CASE WHEN is_my_player THEN r.goals_scored ELSE 0 END) AS my_goals,
                     sum(CASE WHEN NOT is_my_player THEN r.goals_scored ELSE 0 END) AS opp_goals,
                     sum(CASE WHEN is_my_player THEN r.own_goals ELSE 0 END) AS my_own_goals,
                     sum(CASE WHEN NOT is_my_player THEN r.own_goals ELSE 0 END) AS opp_own_goals
                
                // Goals For = my goals + opponent own goals
                // Goals Against = opponent goals + my own goals  
                WITH t, f,
                     my_goals + opp_own_goals AS GF,
                     opp_goals + my_own_goals AS GA
                
                // Calculate results per fixture
                WITH t,
                     CASE WHEN GF > GA THEN 1 ELSE 0 END AS Win,
                     CASE WHEN GF = GA THEN 1 ELSE 0 END AS Draw,
                     CASE WHEN GF < GA THEN 1 ELSE 0 END AS Loss,
                     CASE WHEN GA = 0 THEN 1 ELSE 0 END AS CleanSheet,
                     GF, GA
                
                // Aggregate across all fixtures
                RETURN
                    t.name AS Team,
                    count(*) AS Played,
                    sum(Win) AS W,
                    sum(Draw) AS D,
                    sum(Loss) AS L,
                    sum(GF) AS GoalsFor,
                    sum(GA) AS GoalsAgainst,
                    sum(GF) - sum(GA) AS GD,
                    sum(CleanSheet) AS CS
                ORDER BY W DESC, GD DESC
                """
                
                params["season"] = target_season
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 5: SQUAD_LIST
            # ==================================================================
            elif intent == "Squad_List":
                query = """
                UNWIND $team_names AS t_name
                MATCH (t:Team) WHERE toLower(t.name) CONTAINS toLower(t_name)
                MATCH (t)<-[:HAS_HOME_TEAM|HAS_AWAY_TEAM]-(f:Fixture)<-[r:PLAYED_IN]-(p:Player)
                MATCH (p)-[:PLAYS_AS]->(pos:Position)
                
                WITH DISTINCT p, t, pos, sum(r.total_points) AS TotalPoints
                ORDER BY TotalPoints DESC
                
                RETURN 
                    t.name AS Team, 
                    p.player_name AS Player,
                    pos.name AS Position,
                    TotalPoints
                LIMIT 20
                """

                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 6: GAMEWEEK_SCHEDULE
            # ==================================================================
            elif intent == "Gameweek_Schedule":
                query = """
                MATCH (s:Season) WHERE s.season_name CONTAINS $season
                MATCH (s)-[:HAS_GW]->(gw:Gameweek)
                WHERE toString(gw.GW_number) = toString($gw) OR gw.GW_number = toInteger($gw)
                
                MATCH (gw)-[:HAS_FIXTURE]->(f:Fixture)
                MATCH (f)-[:HAS_HOME_TEAM]->(h:Team)
                MATCH (f)-[:HAS_AWAY_TEAM]->(a:Team)
                
                RETURN 
                    gw.GW_number AS Gameweek,
                    f.kickoff_time AS Date,
                    h.name AS Home,
                    a.name AS Away
                ORDER BY f.kickoff_time ASC
                """

                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 7: GAMEWEEK_ANALYSIS
            # ==================================================================
            elif intent == "Gameweek_Analysis":
                query = """
                MATCH (s:Season) WHERE s.season_name CONTAINS $season
                MATCH (s)-[:HAS_GW]->(gw:Gameweek)
                WHERE toString(gw.GW_number) = toString($gw)
                
                MATCH (gw)-[:HAS_FIXTURE]->(f:Fixture)
                MATCH (p:Player)-[r:PLAYED_IN]->(f)
                WHERE r.minutes > 0
                
                WITH gw.GW_number AS Gameweek,
                     count(DISTINCT f) AS FixturesPlayed,
                     sum(r.goals_scored) AS TotalGoals,
                     p.player_name AS Player,
                     sum(r.total_points) AS PlayerPoints
                
                ORDER BY PlayerPoints DESC
                LIMIT 10
                
                RETURN Gameweek, FixturesPlayed, TotalGoals, Player, PlayerPoints
                """

                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 8: HEAD_TO_HEAD
            # ==================================================================
            elif intent == "Head_to_Head":
                params["season"] = None  # Query all seasons for H2H

                query = """
                WITH $team_names AS teams
                WHERE size(teams) >= 2
                WITH teams[0] AS team1_name, teams[1] AS team2_name
                
                MATCH (t1:Team) WHERE toLower(t1.name) CONTAINS toLower(team1_name)
                MATCH (t2:Team) WHERE toLower(t2.name) CONTAINS toLower(team2_name)
                
                MATCH (s:Season)-[:HAS_GW]->(gw:Gameweek)-[:HAS_FIXTURE]->(f:Fixture)
                MATCH (f)-[:HAS_HOME_TEAM]->(h:Team)
                MATCH (f)-[:HAS_AWAY_TEAM]->(a:Team)
                WHERE (h = t1 AND a = t2) OR (h = t2 AND a = t1)
                
                MATCH (p:Player)-[r:PLAYED_IN]->(f)
                WHERE r.minutes > 0
                
                WITH s, gw, f, h, a,
                     sum(r.goals_scored) AS TotalGoals,
                     collect(CASE WHEN r.goals_scored > 0 
                             THEN {player: p.player_name, goals: r.goals_scored} 
                             ELSE NULL END) AS AllScorers
                
                RETURN 
                    s.season_name AS Season,
                    gw.GW_number AS Gameweek,
                    f.kickoff_time AS Kickoff,
                    h.name AS Home,
                    a.name AS Away,
                    TotalGoals,
                    [scorer IN AllScorers WHERE scorer IS NOT NULL] AS GoalScorers
                ORDER BY f.kickoff_time ASC
                """

                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 9: SIMILAR_PLAYERS (Requires Semantic Mode)
            # ==================================================================
            elif intent == "Similar_Players":
                if retrieval_mode != "semantic" or not HuggingFaceEmbeddings:
                    return {
                        "data": "Similar Players requires semantic mode. Please enable it in the sidebar.",
                        "cypher": "N/A - Requires Vector Index"
                    }

                if not params["names"]:
                    return {"data": "Please specify a player name.", "cypher": "N/A"}

                target_name = params["names"][0]
                emb_field = "embedding_a" if model_choice == "A" else "embedding_b"
                
                query = f"""
                MATCH (target:Player)
                WHERE toLower(target.player_name) CONTAINS toLower($target_name)
                
                WITH target, target.{emb_field} AS targetVec
                WHERE targetVec IS NOT NULL
                
                CALL db.index.vector.queryNodes('{active_index}', 10, targetVec)
                YIELD node AS similar, score
                
                WHERE similar.player_name <> target.player_name AND score > 0.7
                
                MATCH (similar)-[:PLAYS_AS]->(pos:Position)
                OPTIONAL MATCH (similar)-[r:PLAYED_IN]->(f:Fixture)
                
                RETURN 
                    similar.player_name AS Player,
                    pos.name AS Position,
                    round(score, 3) AS Similarity,
                    sum(r.total_points) AS Points
                ORDER BY Similarity DESC
                LIMIT 5
                """

                params["target_name"] = target_name
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 10: UNDERLYING_STATS
            # ==================================================================
            elif intent == "Underlying_Stats":
                filter_clause = " AND ".join(base_filters) if base_filters else "1=1"
                
                query = f"""
                UNWIND $names AS search_name
                MATCH (p:Player)
                WHERE toLower(p.player_name) CONTAINS toLower(search_name)
                
                MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
                WHERE ({filter_clause}) AND r.minutes > 0
                
                RETURN 
                    p.player_name AS Player,
                    count(r) AS Matches,
                    round(avg(toFloat(r.ict_index)), 2) AS AvgICT,
                    round(avg(toFloat(r.influence)), 2) AS AvgInfluence,
                    round(avg(toFloat(r.creativity)), 2) AS AvgCreativity,
                    round(avg(toFloat(r.threat)), 2) AS AvgThreat,
                    sum(r.total_points) AS TotalPoints
                ORDER BY AvgICT DESC
                """

                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 11: CAPTAINCY_PICK
            # ==================================================================
            elif intent == "Captaincy_Pick":
                query = """
                MATCH (s:Season) WHERE s.season_name = $season
                MATCH (s)-[:HAS_GW]->(gw:Gameweek)-[:HAS_FIXTURE]->(f:Fixture)
                
                WITH max(gw.GW_number) AS latestGW
                
                MATCH (s:Season)-[:HAS_GW]->(gw:Gameweek)-[:HAS_FIXTURE]->(f:Fixture)
                WHERE s.season_name = $season AND gw.GW_number > (latestGW - 5)
                
                MATCH (p:Player)-[r:PLAYED_IN]->(f)
                WHERE r.minutes >= 60
                
                MATCH (p)-[:PLAYS_AS]->(pos:Position)
                
                WITH p, pos,
                     count(r) AS RecentMatches,
                     sum(r.total_points) AS RecentPoints,
                     avg(r.total_points) AS AvgPoints,
                     sum(r.goals_scored) AS Goals,
                     sum(r.assists) AS Assists
                
                WHERE RecentMatches >= 3
                
                RETURN 
                    p.player_name AS Player,
                    pos.name AS Position,
                    RecentMatches,
                    RecentPoints,
                    round(AvgPoints, 2) AS PointsPerGame,
                    Goals,
                    Assists
                ORDER BY AvgPoints DESC
                LIMIT 10
                """

                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # INTENT 12: BONUS_POINTS
            # ==================================================================
            elif intent == "Bonus_Points":
                filter_clause = " AND ".join(base_filters) if base_filters else "1=1"
                
                query = f"""
                MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
                WHERE ({filter_clause}) AND r.bonus > 0
                
                MATCH (f)-[:HAS_HOME_TEAM]->(h:Team)
                MATCH (f)-[:HAS_AWAY_TEAM]->(a:Team)
                
                RETURN 
                    p.player_name AS Player,
                    r.bonus AS BonusPoints,
                    r.bps AS BPS,
                    h.name + ' vs ' + a.name AS Match,
                    r.total_points AS TotalPoints
                ORDER BY r.bonus DESC, r.bps DESC
                LIMIT 20
                """

                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # ==================================================================
            # FALLBACK: GENERAL_CHAT
            # ==================================================================
            else:
                return {
                    "data": "This appears to be a general conversation. No database query was executed.",
                    "cypher": "N/A - General Chat"
                }

    except Exception as e:
        return {
            "data": f"Database Error: {str(e)}",
            "cypher": executed_cypher
        }

    finally:
        driver.close()