<!-- # ⚽ FPL Intelligent Assistant (GraphRAG) - Milestone 3

## 📖 Project Overview

The **FPL Intelligent Assistant** is a Graph Retrieval-Augmented Generation (GraphRAG) system designed to answer complex questions about Fantasy Premier League (FPL). Unlike standard chatbots, this system is grounded in a structured **Neo4j Knowledge Graph**, ensuring answers are factual, strictly schema-compliant, and hallucination-free.

This project implements a **"Dual-Core" Embedding Engine**, allowing real-time switching between distinct vector models to analyze trade-offs between speed and semantic accuracy.

---

## 🚀 Key Features

### 🧠 1. Dual-Core Vector Search (Experimentation)

The system maintains two simultaneous vector indexes for every entity in the graph. Users can toggle between them live in the UI:

- **Model A (MiniLM-L6-v2):** Optimized for ultra-low latency.
- **Model B (MPNet-Base-v2):** Optimized for deep semantic understanding and typo tolerance.

### 🔍 2. Advanced Retrieval Strategies

- **Baseline Retrieval:** Converts natural language to Cypher for exact text matching.
- **Semantic Retrieval:** Uses vector cosine similarity to find entities (e.g., matching "Hland" to "Erling Haaland").
- **Multi-Hop Reasoning:** Can answer complex queries like _"Compare Salah and Haaland"_ or _"Who are the best defenders?"_ by traversing relationships in the graph.

### 📊 3. Quantitative Performance Metrics

The application displays real-time latency metrics for:

- **Intent Parsing Time**
- **Graph Retrieval Time**
- **LLM Generation Time**
  This allows for direct quantitative comparison between different LLMs (Llama-3, Mixtral, etc.) and Embedding models.

### 🛠 4. 10 Distinct Query Capabilities

The Intent Parser is trained to recognize and execute 10 specific templates:

1.  **Player Stats:** _"How many goals did Salah score?"_
2.  **Player Comparison:** _"Compare Saka and Palmer."_
3.  **Top Ranked:** _"Who are the best defenders?"_ (Schema-compliant filtering)
4.  **Fixture Query:** _"Who do Liverpool play next?"_
5.  **Gameweek Schedule:** _"What games are in GW 12?"_
6.  **Player Form:** _"How is Trent playing recently?"_ (Last 3 games)
7.  **Injury/Availability:** _"Is De Bruyne playing?"_
8.  **Team Stats:** _"How many goals has Arsenal scored?"_
9.  **Squad List:** _"List the attackers for Chelsea."_
10. **Recommendation:** _"Who should I buy?"_

---

## 🏗️ System Architecture

The project follows a modular architecture:

1.  **Frontend (Streamlit):** Handles user chat, model configuration, and metric visualization.
2.  **Intent Parser (Groq/Llama-3):** Classifies user prompts into intents and extracts entities (Player, Team, Season).
3.  **Knowledge Graph (Neo4j):** Stores data using the schema: `(Player)-[:PLAYS_AS]->(Position)` and `(Player)-[:PLAYED_IN]->(Fixture)`.
4.  **Response Generator:** Synthesizes the retrieved graph data into a natural language response using dynamic personas (Analyst vs. Pundit).

---

## ⚙️ Installation & Setup (Using `uv`)

This project uses `uv` for blazing fast dependency management and reproducibility.

### Prerequisites

- Python 3.9+
- Neo4j Desktop (Active Database)
- Groq API Key
- **uv** installed (if not, run: `pip install uv`)

### 1. Clone the Repository

```bash
git clone [https://github.com/your-repo/fpl-assistant.git](https://github.com/your-repo/fpl-assistant.git)
cd fpl-assistant
``` -->

````markdown
# ACL FPL Companion - Milestone 3: Graph-RAG Travel Assistant

This project implements an end-to-end Graph-RAG (Retrieval-Augmented Generation) system for the Fantasy Premier League (FPL) domain. It combines a Neo4j Knowledge Graph with Large Language Models (LLMs) to answer user queries, provide recommendations, and analyze player statistics.

## 📂 Project Structure

This project follows a modular, component-based architecture:

```text
Milestone3/
├── app.py                     # Component 4: User Interface (Streamlit)
├── backend/
│   ├── config.py              # Configuration & Secrets Manager
│   ├── preprocessing/         # Component 1: Intent Classification & Entity Extraction
│   ├── retrieval/             # Component 2: Graph Retrieval (Cypher + Vector Search)
│   └── generation/            # Component 3: LLM Integration (Context Construction & Prompting)
└── scripts/                   # Setup scripts (Vector Indexing, Evaluation)
```
````

---

## 🛠️ Installation Instructions (CRITICAL)

**⚠️ IMPORTANT:** This project requires a specific **CPU-optimized** version of PyTorch to keep the installation light (\<300MB) instead of the standard GPU version (\>2GB).

**Please follow these steps exactly in the order listed below.**

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Our package manager).
  - _To install `uv`:_ `pip install uv`

### Step 1: Initialize the Project

Run this command to create the virtual environment (`.venv`) and install the standard project dependencies (LangChain, Neo4j, Streamlit, etc.) defined in `pyproject.toml`.

```bash
uv sync
```

### Step 2: Install CPU PyTorch (The "Hybrid" Step)

You must force-install the CPU version of PyTorch manually using `uv pip`.
**Run this command AFTER Step 1:**

```bash
uv pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)
```

### Step 3: Setup Credentials

1.  Create a file named `.env` in the `Milestone3/` directory.
2.  Add your API keys (Neo4j, Groq, OpenAI, Gemini) following the format below:

<!-- end list -->

```ini
# Neo4j Database
NEO4J_URI=neo4j+ssc://c5d71273.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# LLM API Keys
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here
```

### Step 4: Verify Installation

Activate the environment and run the verification command to ensure the hybrid setup is correct.

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\activate
python -c "import torch; print(f'✅ PyTorch {torch.__version__} Ready!'); from backend.retrieval.graph_client import graph_client; graph_client.verify_connectivity()"
```

**Mac/Linux:**

```bash
source .venv/bin/activate
python -c "import torch; print(f'✅ PyTorch {torch.__version__} Ready!'); from backend.retrieval.graph_client import graph_client; graph_client.verify_connectivity()"
```

---

## 🚀 How to Run

Once installed and verified, make sure your virtual environment is activated, then start the Streamlit Interface:

```bash
streamlit run app.py
```

## ✨ Features

- **Intent Classification:** Intelligently routes queries (Question Answering vs. Recommendations).
- **Hybrid Retrieval:** Combines Cypher queries (Database) with Vector Search (Embeddings).
- **Multi-Model Support:** Compare answers from Groq (Llama), OpenAI (GPT), and Google Gemini.
- **Interactive UI:** Chat interface with transparent context display.

<!-- end list -->

```

```
