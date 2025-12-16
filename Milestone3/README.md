# FPL Graph-RAG Assistant 🎯⚽

A **Graph-RAG (Retrieval Augmented Generation)** powered Fantasy Premier League assistant that combines Knowledge Graphs with Large Language Models to answer FPL questions naturally.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Supported Queries](#supported-queries)
- [Technical Details](#technical-details)

---

## Overview

This project implements a conversational AI assistant for Fantasy Premier League (FPL) data from seasons **2021-22** and **2022-23**. It uses:

- **Neo4j Knowledge Graph** - Stores players, teams, fixtures, and performance data
- **Vector Embeddings** - Enables semantic search for typo-tolerant queries
- **Multiple LLMs** - Groq, OpenAI, Gemini, and Cerebras for response generation
- **Streamlit UI** - Interactive chat interface with configuration options

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER QUESTION                          │
│                 "Compare Salah and Haaland"                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  1. INTENT PARSER (intent_parser.py)                        │
│     • Classifies intent: "Compare_Players"                  │
│     • Extracts entities: {Player: ["Salah", "Haaland"]}    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. KNOWLEDGE GRAPH (knowledge_graph.py)                    │
│     ┌────────────┐           ┌────────────┐                │
│     │  BASELINE  │    OR     │  SEMANTIC  │                │
│     │   Cypher   │           │  Vectors   │                │
│     └────────────┘           └────────────┘                │
│                    Neo4j Database                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. RESPONSE GENERATOR (response_generator.py)              │
│     Groq | OpenAI | Gemini | Cerebras                       │
│     Context + Persona + Task → Natural Language             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  4. STREAMLIT UI (app.py)                                   │
│     Chat interface + Metrics + Debug info                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### 🎯 12 Query Intents

| Intent            | Description                          | Example                     |
| ----------------- | ------------------------------------ | --------------------------- |
| Player_Stats      | Individual player statistics         | "Salah stats"               |
| Compare_Players   | Compare multiple players             | "Compare Salah and Haaland" |
| Top_Ranked        | Leaderboards by metric/position      | "Top 10 scorers"            |
| Team_Stats        | Team performance summary             | "Arsenal performance"       |
| Squad_List        | Team roster                          | "Liverpool players"         |
| Gameweek_Schedule | Fixtures in a gameweek               | "GW 10 fixtures"            |
| Gameweek_Analysis | Gameweek performance analysis        | "Analyze gameweek 15"       |
| Head_to_Head      | Historical matchups                  | "Arsenal vs Liverpool h2h"  |
| Similar_Players   | Find similar players (vector search) | "Players like Salah"        |
| Captaincy_Pick    | Captain recommendations              | "Who should I captain?"     |
| Underlying_Stats  | ICT index and advanced metrics       | "Haaland threat rating"     |
| Bonus_Points      | BPS analysis                         | "Who got bonus points?"     |

### 🔍 Two Retrieval Modes

- **Baseline**: Exact text matching with Cypher queries
- **Semantic**: Vector similarity search (handles typos like "firmno" → "Firmino")

### 🤖 Four LLM Options

| Provider | Model            | Speed        | Cost |
| -------- | ---------------- | ------------ | ---- |
| Groq     | Llama 3.3 70B    | ⚡ Fast      | Free |
| Cerebras | Llama 3.3 70B    | ⚡⚡ Fastest | Free |
| Google   | Gemini 2.0 Flash | ⚡ Fast      | Free |
| OpenAI   | GPT-4o           | 🐢 Slower    | Paid |

### 📊 Two Embedding Models

- **Model A (MiniLM)**: 384 dimensions, faster
- **Model B (MPNet)**: 768 dimensions, more accurate

---

## Installation

### Prerequisites

- Python 3.9+
- Neo4j Database (local or Aura)
- API keys for at least one LLM

### Step 1: Clone and Setup

```bash
cd Milestone3
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
```

### Step 2: Install Dependencies

```bash
pip install streamlit neo4j python-dotenv groq openai google-genai cerebras-cloud-sdk langchain-huggingface sentence-transformers
```

### Step 3: Configure Environment

Create a `.env` file in the project root:

```env
# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# LLM API Keys (add at least one)
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
CEREBRAS_API_KEY=your_cerebras_key
```

### Step 4: Initialize Database

```bash
python initialize_vectors.py
```

⚠️ **Only run this once!** It creates nodes, relationships, and vector indexes.

### Step 5: Run the App

```bash
streamlit run app.py
```

---

## Configuration

### Getting API Keys

| Provider | URL                         | Notes                        |
| -------- | --------------------------- | ---------------------------- |
| Groq     | https://console.groq.com    | Free tier available          |
| Cerebras | https://cloud.cerebras.ai   | Free tier, fastest inference |
| Google   | https://aistudio.google.com | Free tier available          |
| OpenAI   | https://platform.openai.com | Paid, best quality           |

### Neo4j Setup

1. Download Neo4j Desktop or use Neo4j Aura (cloud)
2. Create a new database
3. Copy the connection URI and password to `.env`

---

## Usage

### Basic Queries

```
"Salah stats"
"Top 5 defenders"
"Arsenal performance"
"Compare Salah and Haaland"
```

### Advanced Queries

```
"Players similar to Haaland" (requires Semantic mode)
"Who should I captain this week?"
"Arsenal vs Liverpool head to head"
"Gameweek 20 fixtures in 2022-23"
```

### Handling Typos

Switch to **Semantic** mode in the sidebar:

```
"firmno stats" → Finds "Roberto Firmino"
"sallah goals" → Finds "Mohamed Salah"
```

---

## Project Structure

```
Milestone3/
├── app.py                    # Streamlit UI
├── initialize_vectors.py     # Database initialization (run once)
├── .env                      # Environment variables
├── backend/
│   ├── __init__.py
│   ├── config.py            # Configuration and LLM clients
│   ├── intent_parser.py     # Intent classification
│   ├── knowledge_graph.py   # Neo4j queries (12 intents)
│   └── response_generator.py # LLM response generation
├── README.md
├── COMPLETE_GUIDE.md        # Testing guide
└── PRESENTATION_GUIDE.md    # Presentation instructions
```

---

## Supported Queries

### Player Statistics

- "Salah stats"
- "How did Haaland perform in 2022-23?"
- "Mohamed Salah goals and assists"

### Comparisons

- "Compare Salah and Haaland"
- "Salah vs Kane vs Son"

### Rankings

- "Top 10 scorers"
- "Best goalkeepers"
- "Top defenders by clean sheets"

### Team Analysis

- "Arsenal performance"
- "Manchester City stats in 2022-23"
- "Liverpool players"

### Fixtures

- "Gameweek 10 fixtures"
- "GW 15 matches in 2022-23"

### Head-to-Head

- "Arsenal vs Liverpool h2h"
- "Man City against Chelsea history"

### Recommendations

- "Who should I captain?"
- "Players similar to Salah"

---

## Technical Details

### Intent Classification

Uses Groq LLM with JSON mode for structured output:

```python
{
    "intent": "Player_Stats",
    "entities": {
        "Player": ["Salah"],
        "Season": "2022-23"
    }
}
```

### Vector Search

Player embeddings are created from:

```
"Player: Mohamed Salah. Position: MID. Total Fantasy Points: 234."
```

Two indexes:

- `player_idx_a`: MiniLM embeddings (384d)
- `player_idx_b`: MPNet embeddings (768d)

### Prompt Structure

```
[SYSTEM CONTEXT]
- Limited to FPL data from 2021-22 and 2022-23

[CONTEXT]
Retrieved Database Info: {...}

[INSTRUCTIONS]
- Answer using ONLY the retrieved info
- Be specific with numbers
```

---

## Troubleshooting

### "No data found"

- Check if Neo4j is running
- Verify the season exists (only 2021-22 and 2022-23)
- Check player name spelling

### "Intent: General_Chat" for valid queries

- The LLM may have misclassified - try rephrasing
- Add explicit keywords like "stats", "goals", "compare"

### Slow response times

- Switch to Groq or Cerebras (faster)
- Baseline mode is faster than Semantic

### Vector search not working

- Ensure `initialize_vectors.py` was run
- Check that embedding model is installed

---

## License

This project is for educational purposes (CSEN 903 - Advanced Computational Lab).

---

## Acknowledgments

- Fantasy Premier League for the data
- Neo4j for the graph database
- Groq, OpenAI, Google, and Cerebras for LLM APIs
