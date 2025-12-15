import time
from difflib import SequenceMatcher
from neo4j import GraphDatabase
from langchain_huggingface import HuggingFaceEmbeddings
from backend.config import Config

# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------
MODEL_NAME_A = Config.EMBEDDING_MODEL_A
MODEL_NAME_B = Config.EMBEDDING_MODEL_B
BATCH_SIZE = 500

class GraphInitializer:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI, 
            auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def run_cypher(self, query, params=None):
        with self.driver.session() as session:
            return list(session.run(query, params or {}))

    # ----------------------------------------------------------------------
    # STEP 1: EXACT MERGE (The "Eze" Fix)
    # ----------------------------------------------------------------------
    def repair_exact_duplicates(self):
        print("\n🔧 STEP 1: Checking for Exact Duplicates...")
        
        check_query = """
        MATCH (p:Player)
        WITH p.player_name AS name, count(p) AS count
        WHERE count > 1
        RETURN count(name) as duplicate_count
        """
        result = self.run_cypher(check_query)
        dupe_count = result[0]["duplicate_count"] if result else 0

        if dupe_count == 0:
            print("   ✅ No exact duplicates found.")
            return

        print(f"   ⚠️  Found {dupe_count} exact duplicates. Merging...")
        
        # FIXED: Added 'WITH master, duplicate' between operations
        merge_query = """
        MATCH (p:Player)
        WITH p.player_name AS name, collect(p) AS nodes
        WHERE size(nodes) > 1
        CALL (nodes) {
            WITH head(nodes) AS master, tail(nodes) AS duplicates
            UNWIND duplicates AS duplicate
            
            // 1. Position
            OPTIONAL MATCH (duplicate)-[r_pos:PLAYS_AS]->(pos)
            FOREACH (_ IN CASE WHEN r_pos IS NOT NULL THEN [1] ELSE [] END | 
                MERGE (master)-[:PLAYS_AS]->(pos) DELETE r_pos
            )
            
            WITH master, duplicate
            
            // 2. Team
            OPTIONAL MATCH (duplicate)-[r_team:PLAYS_FOR]->(t)
            FOREACH (_ IN CASE WHEN r_team IS NOT NULL THEN [1] ELSE [] END | 
                MERGE (master)-[:PLAYS_FOR]->(t) DELETE r_team
            )
            
            WITH master, duplicate

            // 3. History
            OPTIONAL MATCH (duplicate)-[r_played:PLAYED_IN]->(f)
            FOREACH (_ IN CASE WHEN r_played IS NOT NULL THEN [1] ELSE [] END | 
                MERGE (master)-[new_r:PLAYED_IN]->(f) SET new_r = properties(r_played) DELETE r_played
            )
            
            // 4. Cleanup
            WITH duplicate
            DETACH DELETE duplicate
        }
        RETURN count(*) as processed
        """
        self.run_cypher(merge_query)
        print("   ✅ Exact Merge Complete.")

    # ----------------------------------------------------------------------
    # STEP 2: SMART ALIAS REPAIR (The "Walker" Safety Check)
    # ----------------------------------------------------------------------
    def repair_aliases_safely(self):
        print("\n🔧 STEP 2: Checking for Aliases (Temporal Check)...")
        
        query = """
        MATCH (p:Player)-[:PLAYED_IN]->(f:Fixture)
        RETURN p.player_name as name, collect(distinct f.season) as seasons
        """
        data = self.run_cypher(query)
        
        all_names_query = "MATCH (p:Player) RETURN p.player_name as name"
        all_names_res = self.run_cypher(all_names_query)
        player_seasons = {row["name"]: set(row["seasons"]) for row in data}
        for r in all_names_res:
            if r["name"] not in player_seasons: player_seasons[r["name"]] = set()

        names = sorted(player_seasons.keys(), key=len)
        aliases = []
        
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                n1 = names[i]
                n2 = names[j]
                
                if abs(len(n1) - len(n2)) > 15: continue
                if n1[0] != n2[0]: continue 

                is_name_match = False
                if (n1 in n2) and len(n1) > 4: is_name_match = True
                elif SequenceMatcher(None, n1, n2).ratio() > 0.88: is_name_match = True
                
                if is_name_match:
                    s1 = player_seasons[n1]
                    s2 = player_seasons[n2]
                    intersection = s1.intersection(s2)
                    
                    if not intersection:
                        aliases.append((n1, n2))
                    else:
                        print(f"   🛡️  Skipped: '{n1}' vs '{n2}' (Both active in {intersection})")

        if not aliases:
            print("   ✅ No aliases found.")
        else:
            print(f"   ⚠️  Found {len(aliases)} safe aliases. Merging...")
            self._execute_merge(aliases)

    def _execute_merge(self, aliases):
        # FIXED: Added 'WITH keep, remove' between operations
        merge_query = """
        MATCH (keep:Player {player_name: $keep})
        MATCH (remove:Player {player_name: $remove})
        CALL (keep, remove) {
            // 1. Position
            OPTIONAL MATCH (remove)-[r_pos:PLAYS_AS]->(pos)
            FOREACH (_ IN CASE WHEN r_pos IS NOT NULL THEN [1] ELSE [] END | 
                MERGE (keep)-[:PLAYS_AS]->(pos) DELETE r_pos
            )

            WITH keep, remove

            // 2. Team
            OPTIONAL MATCH (remove)-[r_team:PLAYS_FOR]->(t)
            FOREACH (_ IN CASE WHEN r_team IS NOT NULL THEN [1] ELSE [] END | 
                MERGE (keep)-[:PLAYS_FOR]->(t) DELETE r_team
            )

            WITH keep, remove

            // 3. History
            OPTIONAL MATCH (remove)-[r_played:PLAYED_IN]->(f)
            FOREACH (_ IN CASE WHEN r_played IS NOT NULL THEN [1] ELSE [] END | 
                MERGE (keep)-[new_r:PLAYED_IN]->(f) SET new_r = properties(r_played) DELETE r_played
            )

            // 4. Cleanup
            WITH remove
            DETACH DELETE remove
        }
        RETURN count(*)
        """
        with self.driver.session() as session:
            for keep, remove in aliases:
                try:
                    session.run(merge_query, keep=keep, remove=remove)
                except Exception:
                    pass
            print(f"   ✅ Merged {len(aliases)} alias pairs.")

    # ----------------------------------------------------------------------
    # STEP 3: EMBEDDING GENERATION
    # ----------------------------------------------------------------------
    def generate_embeddings(self):
        print("\n🧠 STEP 3: Generating Embeddings...")
        hf_a = HuggingFaceEmbeddings(model_name=MODEL_NAME_A)
        dim_a = len(hf_a.embed_query("test"))
        hf_b = HuggingFaceEmbeddings(model_name=MODEL_NAME_B)
        dim_b = len(hf_b.embed_query("test"))

        self._setup_indexes(dim_a, dim_b)

        print("   ...Fetching Player Data...")
        query = """
        MATCH (p:Player)
        OPTIONAL MATCH (p)-[:PLAYS_AS]->(pos:Position)
        OPTIONAL MATCH (p)-[r:PLAYED_IN]->()
        WITH p, pos.name AS position, sum(r.total_points) AS total_points
        RETURN elementId(p) AS internal_id, p.player_name AS name, position, total_points
        """
        players = self.run_cypher(query)
        total = len(players)
        print(f"   ...Found {total} unique players.")

        batch = []
        with self.driver.session() as session:
            for record in players:
                text = f"Player: {record['name']}. Position: {record['position'] or 'Unknown'}. Total Fantasy Points: {int(record['total_points'] or 0)}."
                batch.append({
                    "id": record["internal_id"],
                    "text": text,
                    "vec_a": hf_a.embed_query(text),
                    "vec_b": hf_b.embed_query(text)
                })

                if len(batch) >= BATCH_SIZE:
                    self._write_batch(session, batch)
                    batch = []
            if batch:
                self._write_batch(session, batch)
        
        print("\n✅ SUCCESS: Knowledge Graph is fully initialized and vector-ready.")

    def _setup_indexes(self, dim_a, dim_b):
        print("   ...Refreshing Indexes...")
        with self.driver.session() as session:
            for idx in ["player_idx_a", "player_idx_b", "player_embeddings", "team_embeddings"]:
                session.run(f"DROP INDEX {idx} IF EXISTS")
            session.run(f"CREATE VECTOR INDEX player_idx_a IF NOT EXISTS FOR (n:Player) ON (n.embedding_a) OPTIONS {{ indexConfig: {{ `vector.dimensions`: {dim_a}, `vector.similarity_function`: 'cosine' }} }}")
            session.run(f"CREATE VECTOR INDEX player_idx_b IF NOT EXISTS FOR (n:Player) ON (n.embedding_b) OPTIONS {{ indexConfig: {{ `vector.dimensions`: {dim_b}, `vector.similarity_function`: 'cosine' }} }}")

    def _write_batch(self, session, batch):
        query = """
        UNWIND $batch AS row
        MATCH (p) WHERE elementId(p) = row.id
        SET p.text_representation = row.text, p.embedding_a = row.vec_a, p.embedding_b = row.vec_b
        """
        session.run(query, batch=batch)

def main():
    Config.validate()
    init = GraphInitializer()
    try:
        init.repair_exact_duplicates()  # Step 1
        init.repair_aliases_safely()    # Step 2
        init.generate_embeddings()      # Step 3
    finally:
        init.close()

if __name__ == "__main__":
    main()
