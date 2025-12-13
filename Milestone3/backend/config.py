import os
from dotenv import load_dotenv
from groq import Groq
from langchain_huggingface import HuggingFaceEmbeddings

# 1. Load Environment Variables
load_dotenv()

# 2. Neo4j Credentials
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

# 3. LLM Config (Groq)
API_KEY = os.getenv("LLM_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile" # Use a high-quality model

try:
    groq_client = Groq(api_key=API_KEY)
except Exception as e:
    groq_client = None
    print(f"⚠️ Groq Client Error: {e}")

# 4. DUAL EMBEDDING MODELS (Requirement: Compare 2 Models)
print("⏳ Loading Embedding Model A (MiniLM - Fast)...")
try:
    embedding_model_a = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    print("✅ Model A Loaded.")
except Exception as e:
    embedding_model_a = None
    print(f"❌ Failed to load Model A: {e}")

print("⏳ Loading Embedding Model B (MPNet - Accurate)...")
try:
    embedding_model_b = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")
    print("✅ Model B Loaded.")
except Exception as e:
    embedding_model_b = None
    print(f"❌ Failed to load Model B: {e}")