import time
from neo4j import GraphDatabase
# Ensure you run this from the root folder: python initialize_vectors.py
from backend.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, embedding_model_a, embedding_model_b

def create_dual_indices():
    if not embedding_model_a or not embedding_model_b:
        print("❌ Error: One or both embedding models failed to load.")
        return

    # 1. Detect Dimensions
    DIM_A = len(embedding_model_a.embed_query("test")) # Usually 384
    DIM_B = len(embedding_model_b.embed_query("test")) # Usually 768
    print(f"📏 Detected Dimensions -> Model A: {DIM_A} | Model B: {DIM_B}")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # 2. Define Index Queries
    queries = [
        # Index A (MiniLM)
        f"CREATE VECTOR INDEX player_index_a IF NOT EXISTS FOR (n:Player) ON (n.embedding_a) OPTIONS {{indexConfig: {{`vector.dimensions`: {DIM_A}, `vector.similarity_function`: 'cosine'}}}}",
        f"CREATE VECTOR INDEX team_index_a IF NOT EXISTS FOR (n:Team) ON (n.embedding_a) OPTIONS {{indexConfig: {{`vector.dimensions`: {DIM_A}, `vector.similarity_function`: 'cosine'}}}}",
        
        # Index B (MPNet)
        f"CREATE VECTOR INDEX player_index_b IF NOT EXISTS FOR (n:Player) ON (n.embedding_b) OPTIONS {{indexConfig: {{`vector.dimensions`: {DIM_B}, `vector.similarity_function`: 'cosine'}}}}",
        f"CREATE VECTOR INDEX team_index_b IF NOT EXISTS FOR (n:Team) ON (n.embedding_b) OPTIONS {{indexConfig: {{`vector.dimensions`: {DIM_B}, `vector.similarity_function`: 'cosine'}}}}"
    ]

    # 3. Define Update Logic (Void procedures)
    update_player = """
    MATCH (p:Player {player_name: $name})
    CALL db.create.setNodeVectorProperty(p, 'embedding_a', $vec_a)
    CALL db.create.setNodeVectorProperty(p, 'embedding_b', $vec_b)
    """
    
    update_team = """
    MATCH (t:Team {name: $name})
    CALL db.create.setNodeVectorProperty(t, 'embedding_a', $vec_a)
    CALL db.create.setNodeVectorProperty(t, 'embedding_b', $vec_b)
    """

    with driver.session() as session:
        # Step A: Create Indexes
        print("🏗️  Creating Dual Vector Indexes...")
        for q in queries:
            session.run(q)
        
        # Step B: Process Players
        print("⏳ Processing Players (This may take a while)...")
        players = [r["name"] for r in session.run("MATCH (p:Player) RETURN p.player_name as name")]
        count = 0
        for name in players:
            vec_a = embedding_model_a.embed_query(name)
            vec_b = embedding_model_b.embed_query(name)
            session.run(update_player, name=name, vec_a=vec_a, vec_b=vec_b)
            count += 1
            if count % 100 == 0: print(f"   ...processed {count} players")
            
        # Step C: Process Teams
        print("⏳ Processing Teams...")
        teams = [r["name"] for r in session.run("MATCH (t:Team) RETURN t.name as name")]
        for name in teams:
            vec_a = embedding_model_a.embed_query(name)
            vec_b = embedding_model_b.embed_query(name)
            session.run(update_team, name=name, vec_a=vec_a, vec_b=vec_b)

    driver.close()
    print("✅ SUCCESS! Database is now Dual-Core Ready (Two Models Installed).")

if __name__ == "__main__":
    create_dual_indices()