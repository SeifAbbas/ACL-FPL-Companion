from neo4j import GraphDatabase
from .config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, embedding_model_a, embedding_model_b

def get_position_aliases(pos_text):
    """Maps user input (e.g., 'Goalie') to DB values (e.g., 'GKP', 'Goal')."""
    if not pos_text: return []
    pos_text = str(pos_text).lower()
    if any(x in pos_text for x in ["goal", "gk", "keeper", "gkp"]): return ["GKP", "Goal", "Keep"]
    elif any(x in pos_text for x in ["def", "back", "cb", "lb", "rb"]): return ["DEF", "Def", "Back"]
    elif any(x in pos_text for x in ["mid", "winger"]): return ["MID", "Mid", "Wing"]
    elif any(x in pos_text for x in ["forw", "strik", "attac", "fwd"]): return ["FWD", "Forw", "Strik", "Attac"]
    return [pos_text]

def query_knowledge_graph(structured_data, retrieval_mode="baseline", model_choice="A"):
    """
    Routes user intent to 10+ Cypher templates.
    Supports switching between Baseline (Text) and Semantic (Vector A vs B).
    """
    intent = structured_data.get("intent")
    entities = structured_data.get("entities", {})
    
    # Select the Correct Brain
    if model_choice == "B":
        active_model = embedding_model_b
        active_index = "player_index_b"
    else:
        active_model = embedding_model_a
        active_index = "player_index_a"

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Extract Filters
    target_season = entities.get("Season")
    target_gw = entities.get("Gameweek")
    raw_pos = entities.get("Position")
    target_metric = entities.get("Metric", "total_points")
    
    # Shared Filters
    base_filters = []
    if target_season:
        base_filters.append("EXISTS { MATCH (f)<-[:HAS_FIXTURE]-(:Gameweek)<-[:HAS_GW]-(s:Season) WHERE s.season_name CONTAINS $season }")
    if target_gw:
        base_filters.append("EXISTS { MATCH (f)<-[:HAS_FIXTURE]-(gw:Gameweek) WHERE toString(gw.GW_number) = toString($gw) OR gw.GW_number = toInteger($gw) }")

    params = {"season": target_season, "gw": target_gw, "metric": target_metric}
    executed_cypher = "No Query Executed"

    try:
        with driver.session() as session:
            
            # 1. PLAYER STATS (Supports Semantic Switch)
            if intent == "Player_Stats":
                names = entities.get("Player", [])
                params["names"] = names
                
                if retrieval_mode == "semantic" and names and active_model:
                    # Vector Search Logic
                    query = f"""
                    CALL db.index.vector.queryNodes('{active_index}', 5, $vec)
                    YIELD node AS p, score WHERE score > 0.70
                    MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
                    WHERE {' AND '.join(base_filters) if base_filters else '1=1'}
                    RETURN p.player_name as Player, sum(r.total_points) as Points, sum(r.goals_scored) as Goals, sum(r.assists) as Assists
                    """
                    params["vec"] = active_model.embed_query(names[0])
                else:
                    # Baseline Text Search
                    query = f"""
                    UNWIND $names as search_name
                    MATCH (p:Player) WHERE toLower(p.player_name) CONTAINS toLower(search_name)
                    WITH p ORDER BY length(p.player_name) ASC LIMIT 1
                    MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
                    WHERE {' AND '.join(base_filters) if base_filters else '1=1'}
                    RETURN p.player_name as Player, sum(r.total_points) as Points, sum(r.goals_scored) as Goals, sum(r.assists) as Assists
                    """
                
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # 2. COMPARE PLAYERS
            elif intent == "Compare_Players":
                names = entities.get("Player", [])
                params["names"] = names
                query = f"""
                UNWIND $names as search_name
                MATCH (p:Player) WHERE toLower(p.player_name) CONTAINS toLower(search_name)
                MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
                WHERE {' AND '.join(base_filters) if base_filters else '1=1'}
                RETURN p.player_name as Name, sum(r.total_points) as Points, sum(r.goals_scored) as Goals, sum(r.assists) as Assists
                """
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # 3. TOP RANKED
            elif intent == "Top_Ranked":
                sort_clause = "ORDER BY Points DESC"
                if target_metric and "goal" in target_metric.lower(): sort_clause = "ORDER BY Goals DESC"
                elif target_metric and "assist" in target_metric.lower(): sort_clause = "ORDER BY Assists DESC"
                
                aliases = get_position_aliases(raw_pos)
                params["aliases"] = aliases
                pos_filter = "WHERE any(alias IN $aliases WHERE toLower(pos.name) CONTAINS toLower(alias))" if aliases else ""
                
                query = f"""
                MATCH (p:Player)-[:PLAYS_AS]->(pos:Position)
                {pos_filter}
                MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
                WHERE {' AND '.join(base_filters) if base_filters else '1=1'}
                WITH p, pos, sum(r.total_points) as Points, sum(r.goals_scored) as Goals, sum(r.assists) as Assists
                RETURN p.player_name as Player, pos.name as Pos, Points, Goals, Assists
                {sort_clause} LIMIT 10
                """
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # 4. FIXTURE QUERY (Specific Team)
            elif intent == "Fixture_Query":
                names = entities.get("Team", [])
                params["names"] = names
                query = f"""
                UNWIND $names as search_name
                MATCH (t:Team) WHERE toLower(t.name) CONTAINS toLower(search_name)
                MATCH (t)<-[:HAS_HOME_TEAM|HAS_AWAY_TEAM]-(f:Fixture)
                OPTIONAL MATCH (f)<-[:HAS_FIXTURE]-(gw:Gameweek)
                WHERE ($gw IS NULL OR toString(gw.GW_number) = toString($gw))
                RETURN t.name as Team, gw.GW_number as Gameweek, f.kickoff_time as Date, f.team_h_score as H, f.team_a_score as A
                ORDER BY f.kickoff_time ASC LIMIT 5
                """
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # 5. PLAYER FORM (Last 3 Games)
            elif intent == "Player_Form" or intent == "General_Chat": 
                names = entities.get("Player", [])
                params["names"] = names
                query = f"""
                UNWIND $names as search_name
                MATCH (p:Player) WHERE toLower(p.player_name) CONTAINS toLower(search_name)
                MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
                WITH p, r, f ORDER BY f.kickoff_time DESC LIMIT 3
                RETURN p.player_name as Player, f.kickoff_time as Date, r.total_points as Pts, r.goals_scored as Goals
                """
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}
            
            # 6. INJURY QUERY
            elif intent == "Injury_Query":
                names = entities.get("Player", [])
                params["names"] = names
                query = f"""
                UNWIND $names as search_name
                MATCH (p:Player) WHERE toLower(p.player_name) CONTAINS toLower(search_name)
                MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
                WITH p, r ORDER BY f.kickoff_time DESC LIMIT 1
                RETURN p.player_name, r.minutes as LastMatchMinutes
                """
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # 7. RECOMMENDATION
            elif intent == "Recommendation":
                query = f"""
                MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
                WITH p, avg(r.total_points) as AvgPoints
                WHERE AvgPoints > 5
                RETURN p.player_name, AvgPoints
                ORDER BY AvgPoints DESC LIMIT 5
                """
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # 8. TEAM STATS
            elif intent == "Team_Stats":
                names = entities.get("Team", [])
                params["names"] = names
                query = f"""
                UNWIND $names as search_name
                MATCH (t:Team) WHERE toLower(t.name) CONTAINS toLower(search_name)
                MATCH (t)<-[:HAS_HOME_TEAM|HAS_AWAY_TEAM]-(f:Fixture)
                RETURN t.name as Team, count(f) as Games, sum(f.team_h_score) + sum(f.team_a_score) as Goals
                """
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # 9. GAMEWEEK SCHEDULE
            elif intent == "Gameweek_Schedule":
                query = f"""
                MATCH (f:Fixture)<-[:HAS_FIXTURE]-(gw:Gameweek)
                WHERE toString(gw.GW_number) = toString($gw) OR gw.GW_number = toInteger($gw)
                MATCH (f)-[:HAS_HOME_TEAM]->(h:Team)
                MATCH (f)-[:HAS_AWAY_TEAM]->(a:Team)
                RETURN gw.GW_number as GW, h.name as Home, a.name as Away, f.kickoff_time as Time
                ORDER BY f.kickoff_time ASC
                """
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            # 10. SQUAD LIST
            elif intent == "Squad_List":
                names = entities.get("Team", [])
                params["names"] = names
                query = f"""
                UNWIND $names as search_name
                MATCH (t:Team) WHERE toLower(t.name) CONTAINS toLower(search_name)
                MATCH (t)<-[:HAS_HOME_TEAM|HAS_AWAY_TEAM]-(f:Fixture)<-[:PLAYED_IN]-(p:Player)
                WITH DISTINCT p, t
                RETURN t.name as Team, collect(p.player_name)[..10] as KeyPlayers
                """
                executed_cypher = query
                result = session.run(query, params)
                return {"data": str([dict(r) for r in result]), "cypher": executed_cypher}

            return {"data": "No specific query found.", "cypher": "N/A"}

    except Exception as e:
        return {"data": f"Database Error: {e}", "cypher": executed_cypher}
    finally:
        driver.close()