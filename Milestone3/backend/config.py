import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

class Config:
    # ---------------------------------------------------------
    # 1. Database Credentials
    # ---------------------------------------------------------
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    # ---------------------------------------------------------
    # 2. LLM API Keys
    # ---------------------------------------------------------
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # ---------------------------------------------------------
    # 3. Model Names
    # ---------------------------------------------------------
    MODEL_GROQ = "llama-3.3-70b-versatile"
    
    MODEL_OPENAI = "gpt-4o"
    
    MODEL_GEMINI = "gemini-2.5-flash" 

    # ---------------------------------------------------------
    # 4. Embedding Model Names
    # ---------------------------------------------------------
    # FAST: 384 dimensions. Runs instantly on CPU.
    EMBEDDING_MODEL_A = "all-MiniLM-L6-v2"    
    
    # ACCURATE: 768 dimensions. The "Gold Standard" for stability.
    EMBEDDING_MODEL_B = "all-mpnet-base-v2"   

    # ---------------------------------------------------------
    # 5. Validation Logic
    # ---------------------------------------------------------
    @staticmethod
    def validate():
        """
        Ensures critical environment variables are loaded.
        """
        # Critical: Database must exist
        if not Config.NEO4J_URI or not Config.NEO4J_PASSWORD:
            raise ValueError("❌ CRITICAL ERROR: Missing Neo4j credentials in .env file.")

        # Warning: Check for LLM keys
        missing_keys = []
        if not Config.GROQ_API_KEY: missing_keys.append("GROQ_API_KEY")
        if not Config.OPENAI_API_KEY: missing_keys.append("OPENAI_API_KEY")
        if not Config.GOOGLE_API_KEY: missing_keys.append("GOOGLE_API_KEY")

        if missing_keys:
            print(f"⚠️  WARNING: Missing API keys: {', '.join(missing_keys)}")
        else:
            print("✅ Configuration Loaded.")

# Create Groq client instance (assuming you have GROQ_API_KEY in .env)
groq_client = Groq(api_key=Config.GROQ_API_KEY) if Config.GROQ_API_KEY else None

# Alias for model name (to match your import in intent_parser.py)
MODEL_NAME = Config.MODEL_GROQ

# Optionally call validate on load
Config.validate()