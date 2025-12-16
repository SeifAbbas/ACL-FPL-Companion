import os
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from google import genai
from cerebras.cloud.sdk import Cerebras

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
    CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

    # ---------------------------------------------------------
    # 3. Model Names (YOUR ORIGINAL WORKING MODEL)
    # ---------------------------------------------------------
    MODEL_GROQ = "llama-3.3-70b-versatile"
    MODEL_OPENAI = "gpt-oss-20b"
    MODEL_GEMINI = "gemini-2.5-flash"
    MODEL_CEREBRAS = "gpt-oss-120b"

    # ---------------------------------------------------------
    # 4. Embedding Model Names
    # ---------------------------------------------------------
    EMBEDDING_MODEL_A = "all-MiniLM-L6-v2"
    EMBEDDING_MODEL_B = "all-mpnet-base-v2"

    # ---------------------------------------------------------
    # 5. Validation Logic
    # ---------------------------------------------------------
    @staticmethod
    def validate():
        if not Config.NEO4J_URI or not Config.NEO4J_PASSWORD:
            raise ValueError("❌ CRITICAL ERROR: Missing Neo4j credentials in .env file.")

        missing_keys = []
        if not Config.GROQ_API_KEY: missing_keys.append("GROQ_API_KEY")
        if not Config.OPENAI_API_KEY: missing_keys.append("OPENAI_API_KEY")
        if not Config.GOOGLE_API_KEY: missing_keys.append("GOOGLE_API_KEY")
        if not Config.CEREBRAS_API_KEY: missing_keys.append("CEREBRAS_API_KEY")


        if missing_keys:
            print(f"⚠️  WARNING: Missing API keys: {', '.join(missing_keys)}")
        else:
            print("✅ Configuration Loaded.")


# Create client instances
groq_client = Groq(api_key=Config.GROQ_API_KEY) if Config.GROQ_API_KEY else None
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
gemini_client = genai.Client(api_key=Config.GOOGLE_API_KEY) if Config.GOOGLE_API_KEY else None
cerebras_client = Cerebras(api_key=Config.CEREBRAS_API_KEY) if Config.CEREBRAS_API_KEY else None




def get_available_llms():
    """Returns list of available LLM model names."""
    available = []
    if groq_client:
        available.append(Config.MODEL_GROQ)
    if openai_client:
        available.append(Config.MODEL_OPENAI)
    if gemini_client:
        available.append(Config.MODEL_GEMINI)
    if cerebras_client:
        available.append(Config.MODEL_CEREBRAS)
    return available if available else [Config.MODEL_GROQ]


# Validate on load
Config.validate()