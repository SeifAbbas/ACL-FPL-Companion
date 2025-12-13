# ⚽ FPL Intelligent Assistant (GraphRAG) - Milestone 3

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
```
