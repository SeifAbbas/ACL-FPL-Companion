from neo4j import GraphDatabase
from backend.config import Config

def verify_player(session, name, expected_nodes=1, should_have_both_seasons=True):
    print(f"\n🔍 Inspecting: '{name}'")
    
    # 1. Check Node Count
    query_nodes = "MATCH (p:Player {player_name: $name}) RETURN p, elementId(p) as id"
    nodes = list(session.run(query_nodes, name=name))
    
    count = len(nodes)
    status = "✅ PASS" if count == expected_nodes else "❌ FAIL"
    print(f"   Nodes Found: {count} | Expected: {expected_nodes} -> {status}")

    if count == 0:
        return

    # 2. Check Seasons & Teams for each node found
    for record in nodes:
        node_id = record["id"]
        
        # Query history for this specific node
        query_history = """
        MATCH (p)-[:PLAYED_IN]->(f:Fixture)
        WHERE elementId(p) = $id
        RETURN collect(distinct f.season) as seasons, count(f) as total_matches, collect(distinct p.text_representation) as text
        """
        history = session.run(query_history, id=node_id).single()
        
        seasons = sorted(history["seasons"])
        matches = history["total_matches"]
        
        # Verify Seasons
        has_21 = "2021-22" in seasons
        has_22 = "2022-23" in seasons
        season_status = "✅ Both Seasons" if (has_21 and has_22) else f"⚠️ {seasons}"
        
        if not should_have_both_seasons:
             # Some players might only genuinely play in one season
             season_status = f"ℹ️  Active in: {seasons}"

        print(f"   - Internal ID: {node_id}")
        print(f"     Seasons: {seasons} ({season_status})")
        print(f"     Total Matches Linked: {matches}")

def main():
    print("🚀 Starting Graph Integrity Check...")
    driver = GraphDatabase.driver(Config.NEO4J_URI, auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD))

    with driver.session() as session:
        # TEST GROUP 1: Should be MERGED (1 Node, Both Seasons)
        print("\n--- 🧪 GROUP 1: MERGED PLAYERS (Expected: 1 Node) ---")
        verify_player(session, "Eberechi Eze")
        verify_player(session, "Mohamed Naser El Sayed Elneny") # Check exact name in CSV if this fails
        verify_player(session, "Ben Davies") 

        # TEST GROUP 2: Should be SEPARATE (Distinct Names)
        print("\n--- 🧪 GROUP 2: SEPARATE ENTITIES (Expected: Distinct Nodes) ---")
        # We check them individually to ensure they exist independently
        verify_player(session, "Mathias Jensen")
        verify_player(session, "Mathias Jorgensen")
        verify_player(session, "Kyle Walker")
        verify_player(session, "Kyle Walker-Peters")

    driver.close()
    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    main()