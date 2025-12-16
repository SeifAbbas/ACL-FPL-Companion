# FPL Graph-RAG Assistant - Complete Testing Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [All 12 Intents with Test Prompts](#all-12-intents-with-test-prompts)
3. [Baseline vs Semantic Comparison](#baseline-vs-semantic-comparison)
4. [Embedding Model Comparison](#embedding-model-comparison)
5. [LLM Comparison (4 Models)](#llm-comparison-4-models)
6. [Metrics Collection Guide](#metrics-collection-guide)
7. [Error Analysis](#error-analysis)
8. [Code Explanation](#code-explanation)

---

## Quick Start

### 1. Start the Application

```bash
cd Milestone3
streamlit run app.py
```

### 2. Configure Settings (Sidebar)

- **Retrieval Strategy**: Start with "Semantic" (handles typos)
- **Embedding Model**: Model A (faster) or Model B (more accurate)
- **LLM Model**: Choose from available models

### 3. Test a Query

Type: `Salah stats` and press Enter

---

## All 12 Intents with Test Prompts

### 1. Player_Stats

**Purpose**: Get statistics for a specific player

| Test Query                 | Expected Result                  |
| -------------------------- | -------------------------------- |
| `Salah stats`              | Points, goals, assists for Salah |
| `Haaland goals in 2022-23` | Goal count for Haaland           |
| `How did Kane perform?`    | Kane's performance summary       |
| `Mohamed Salah statistics` | Full name recognition            |
| `saka`                     | Just player name should work     |

**Cypher Pattern**:

```cypher
MATCH (p:Player) WHERE toLower(p.player_name) CONTAINS toLower($name)
MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
RETURN p.player_name, sum(r.goals_scored), sum(r.total_points)
```

---

### 2. Compare_Players

**Purpose**: Side-by-side comparison of multiple players

| Test Query                         | Expected Result               |
| ---------------------------------- | ----------------------------- |
| `Compare Salah and Haaland`        | Both players' stats           |
| `Salah vs Kane`                    | Head-to-head comparison       |
| `Compare Salah, Haaland, and Kane` | Three-way comparison          |
| `Who is better, Son or Saka?`      | Comparison framed as question |

---

### 3. Top_Ranked

**Purpose**: Leaderboards by metric or position

| Test Query                | Expected Result               |
| ------------------------- | ----------------------------- |
| `Top scorers`             | Top 10 by goals               |
| `Top 10 defenders`        | Best defenders by points      |
| `Best goalkeepers`        | GKP rankings                  |
| `Most assists in 2022-23` | Assist leaders                |
| `Top strikers`            | FWD rankings (alias handling) |
| `Highest points`          | Overall top performers        |

**Position Aliases**:

- Goalkeeper: GKP, GK, Keeper, Goalie
- Defender: DEF, Back, CB, LB, RB
- Midfielder: MID, Wing, Winger
- Forward: FWD, Striker, Attacker

---

### 4. Team_Stats

**Purpose**: Team performance summary (W/D/L, Goals, GD)

| Test Query                         | Expected Result               |
| ---------------------------------- | ----------------------------- |
| `Arsenal performance`              | P38 W26 D6 L6 GF88 GA43 GD+45 |
| `How did Liverpool do in 2022-23?` | Liverpool season stats        |
| `Manchester City stats`            | City's record                 |
| `Chelsea record`                   | Chelsea W/D/L                 |

**Expected Arsenal 2022-23**:

- Played: 38, Wins: 26, Draws: 6, Losses: 6
- Goals For: 88, Goals Against: 43, GD: +45

---

### 5. Squad_List

**Purpose**: List players from a team

| Test Query             | Expected Result              |
| ---------------------- | ---------------------------- |
| `Arsenal players`      | Arsenal squad with positions |
| `Liverpool squad`      | Liverpool roster             |
| `Chelsea midfielders`  | Position-filtered list       |
| `Who plays for Spurs?` | Tottenham players            |

---

### 6. Gameweek_Schedule

**Purpose**: Fixtures in a specific gameweek

| Test Query                        | Expected Result   |
| --------------------------------- | ----------------- |
| `Gameweek 10 fixtures`            | All GW10 matches  |
| `GW 15 matches`                   | GW15 fixture list |
| `Fixtures in week 20 of 2022-23`  | Season-specific   |
| `What matches are in gameweek 5?` | Question format   |

---

### 7. Gameweek_Analysis

**Purpose**: Performance analysis for a gameweek

| Test Query                          | Expected Result       |
| ----------------------------------- | --------------------- |
| `Analyze gameweek 10`               | Top performers, goals |
| `GW 15 review`                      | Summary of GW15       |
| `Who performed best in gameweek 5?` | Top scorers           |
| `Gameweek 20 summary`               | GW20 analysis         |

---

### 8. Head_to_Head

**Purpose**: Historical matches between two teams

| Test Query                             | Expected Result          |
| -------------------------------------- | ------------------------ |
| `Arsenal vs Liverpool h2h`             | All matches between them |
| `Man City against Chelsea`             | City vs Chelsea history  |
| `Liverpool versus United head to head` | Derby history            |
| `Spurs vs Arsenal`                     | North London derby       |

**Trigger Keywords**: "vs", "versus", "h2h", "head to head", "against"

---

### 9. Similar_Players ⚠️ Requires Semantic Mode

**Purpose**: Find players with similar profiles using vector search

| Test Query                 | Expected Result     |
| -------------------------- | ------------------- |
| `Players similar to Salah` | Similar MID players |
| `Alternatives to Haaland`  | Similar FWD players |
| `Who is like Kane?`        | Kane alternatives   |
| `Find players like Saka`   | Similar profiles    |

**Note**: This ONLY works in Semantic mode because it uses vector embeddings.

---

### 10. Underlying_Stats

**Purpose**: ICT index and advanced metrics

| Test Query                        | Expected Result               |
| --------------------------------- | ----------------------------- |
| `Salah's ICT stats`               | Influence, Creativity, Threat |
| `Haaland threat rating`           | Threat metric                 |
| `Show me Kane's underlying stats` | Full ICT breakdown            |
| `Creativity leaders`              | Top creative players          |

---

### 11. Captaincy_Pick

**Purpose**: Captain recommendations based on form

| Test Query                  | Expected Result          |
| --------------------------- | ------------------------ |
| `Who should I captain?`     | Top picks by recent form |
| `Best captain pick`         | Recommendations          |
| `Captain suggestions`       | Form-based picks         |
| `Who to captain this week?` | Top performers           |

**Logic**: Analyzes last 5 gameweeks, filters players with 60+ minutes and 3+ matches.

---

### 12. Bonus_Points

**Purpose**: BPS (Bonus Points System) analysis

| Test Query                      | Expected Result      |
| ------------------------------- | -------------------- |
| `Who got bonus points?`         | Top BPS earners      |
| `BPS leaders`                   | Bonus point rankings |
| `Bonus points in gameweek 10`   | GW-specific BPS      |
| `Show bonus point distribution` | BPS breakdown        |

---

## Baseline vs Semantic Comparison

### What's the Difference?

| Aspect        | Baseline              | Semantic            |
| ------------- | --------------------- | ------------------- |
| Matching      | Exact text (CONTAINS) | Vector similarity   |
| Typo handling | ❌ Fails              | ✅ Works            |
| Speed         | Faster                | Slower              |
| Use case      | Known exact names     | Fuzzy/unknown names |

### Test These Queries in Both Modes:

| Query          | Baseline Result | Semantic Result    |
| -------------- | --------------- | ------------------ |
| `Salah stats`  | ✅ Works        | ✅ Works           |
| `firmno stats` | ❌ No data      | ✅ Finds Firmino   |
| `sallah goals` | ❌ No data      | ✅ Finds Salah     |
| `haalnd`       | ❌ No data      | ✅ Finds Haaland   |
| `KDB stats`    | ❌ May fail     | ✅ Finds De Bruyne |

### How to Test:

1. Set **Retrieval Strategy** to "Baseline"
2. Type: `firmno stats`
3. Note: Should return empty or error
4. Switch to **"Semantic"**
5. Type same query: `firmno stats`
6. Note: Should find "Roberto Firmino"

---

## Embedding Model Comparison

### Model A vs Model B

| Property   | Model A (MiniLM) | Model B (MPNet) |
| ---------- | ---------------- | --------------- |
| Dimensions | 384              | 768             |
| Speed      | ⚡ Faster        | 🐢 Slower       |
| Accuracy   | Good             | Better          |
| Memory     | Lower            | Higher          |

### Test Queries for Comparison:

Run each query with Model A, then Model B:

1. `firmno stats` - Typo handling
2. `Mohamed Elneny statistics` - Full name
3. `Players similar to Haaland` - Vector search quality
4. `KDB goals` - Abbreviation handling

### Record These Metrics:

- Response time (shown in UI)
- Whether correct player was found
- Similarity scores (in Similar_Players)

---

## LLM Comparison (4 Models)

### Available Models

| Model            | Provider | Speed        | Quality   | Cost |
| ---------------- | -------- | ------------ | --------- | ---- |
| Llama 3.3 70B    | Groq     | ⚡ Fast      | Good      | Free |
| Llama 3.3 70B    | Cerebras | ⚡⚡ Fastest | Good      | Free |
| Gemini 2.0 Flash | Google   | ⚡ Fast      | Good      | Free |
| GPT-4o           | OpenAI   | 🐢 Slower    | Excellent | Paid |

### Test Queries for Each LLM:

| Query Type     | Query                        |
| -------------- | ---------------------------- |
| Simple fact    | `Salah goals in 2022-23`     |
| Comparison     | `Compare Salah and Haaland`  |
| Recommendation | `Who should I captain?`      |
| Analysis       | `Arsenal vs Liverpool h2h`   |
| Creative       | `Summarize Haaland's season` |

### What to Observe:

- **Response time** (LLM Gen metric)
- **Response quality** (accuracy, detail)
- **Tone** (conversational vs formal)
- **Hallucinations** (making up facts)

---

## Metrics Collection Guide

### Quantitative Metrics (From UI)

| Metric       | Where to Find   | What It Measures   |
| ------------ | --------------- | ------------------ |
| Total Time   | Top of response | End-to-end latency |
| Graph Search | Metrics row     | Neo4j query time   |
| LLM Gen      | Metrics row     | LLM response time  |

### Qualitative Metrics (Your Judgment)

| Metric       | Scale | Criteria                 |
| ------------ | ----- | ------------------------ |
| Accuracy     | 1-5   | Did it answer correctly? |
| Relevance    | 1-5   | Was the answer on-topic? |
| Naturalness  | 1-5   | Does it sound human?     |
| Completeness | 1-5   | Was anything missing?    |

### Data Collection Spreadsheet

Create a spreadsheet with these columns:

```
| Query | Intent | Mode | Emb Model | LLM | Total Time | Graph Time | LLM Time | Accuracy | Notes |
```

### Sample Filled Row:

```
| Salah stats | Player_Stats | Semantic | Model A | Groq | 2.1s | 1.3s | 0.8s | 5 | Correct goals/assists |
```

---

## Error Analysis

### Common Errors and Fixes

#### 1. Intent Misclassification

**Symptom**: "Salah stats" → General_Chat
**Cause**: LLM didn't recognize player name
**Fix**: The code has override logic that checks entities

#### 2. Empty Results

**Symptom**: "No data found"
**Causes**:

- Typo in baseline mode
- Invalid season (only 2021-22, 2022-23)
- Player didn't exist that season

#### 3. Wrong Player Found

**Symptom**: Asked for "Jack" but got wrong Jack
**Cause**: Multiple players with same name
**Fix**: Use full name or add team context

#### 4. Head-to-Head Not Triggered

**Symptom**: "Arsenal Liverpool" → General_Chat
**Fix**: Add keywords like "vs", "h2h", "against"

#### 5. Similar_Players Fails

**Symptom**: "Similar Players requires semantic mode"
**Fix**: Switch to Semantic retrieval mode

### Document 2-3 Errors for Presentation

For each error, record:

1. The query that failed
2. What happened
3. Why it happened
4. How you fixed it (or couldn't)

---

## Code Explanation

### config.py

```python
# Loads API keys from .env file
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

# Creates LLM clients
groq_client = Groq(api_key=Config.GROQ_API_KEY)
cerebras_client = Cerebras(api_key=Config.CEREBRAS_API_KEY)

# Returns available LLMs (only those with valid keys)
def get_available_llms():
    available = []
    if groq_client: available.append(Config.MODEL_GROQ)
    if cerebras_client: available.append(Config.MODEL_CEREBRAS)
    ...
```

### intent_parser.py

```python
# System prompt defines all 12 intents
system_prompt = """
1. "Player_Stats": Statistics of a specific player
2. "Compare_Players": Comparison between players
...
"""

# LLM returns JSON with intent + entities
{
    "intent": "Player_Stats",
    "entities": {"Player": ["Salah"]}
}
```

### knowledge_graph.py

```python
# Main function handles all 12 intents
def query_knowledge_graph(structured_data, retrieval_mode, model_choice):

    # Override misclassified intents
    if intent == "General_Chat" and entities.get("Player"):
        intent = "Player_Stats"

    # Semantic mode: resolve typos using vectors
    if retrieval_mode == "semantic":
        params["names"] = resolve_player_names_semantic(...)

    # Execute intent-specific Cypher query
    if intent == "Player_Stats":
        query = "MATCH (p:Player) WHERE ..."
```

### response_generator.py

```python
# Selects persona based on intent
persona_map = {
    "Player_Stats": "You are an expert FPL Analyst",
    "Team_Stats": "You are a Football Pundit",
    ...
}

# Calls appropriate LLM based on selection
if target_model == Config.MODEL_CEREBRAS:
    completion = cerebras_client.chat.completions.create(...)
```

### app.py

```python
# Sidebar configuration
retrieval_mode = st.radio("Search Mode:", ["baseline", "semantic"])
selected_model = st.selectbox("Choose LLM:", available_llms)

# Processing pipeline
intent_data = parse_user_intent(prompt)           # Step 1
kg_result = query_knowledge_graph(intent_data)    # Step 2
answer = generate_natural_language_answer(...)    # Step 3
```

---

## Quick Reference Card

### Must-Test Queries

1. `Salah stats` - Basic player stats
2. `Compare Salah and Haaland` - Comparison
3. `Top 10 scorers` - Rankings
4. `Arsenal performance` - Team stats (should show 26 wins)
5. `Arsenal vs Liverpool h2h` - Head to head
6. `firmno stats` (Semantic only) - Typo handling
7. `Players similar to Salah` (Semantic only) - Vector search
8. `Who should I captain?` - Recommendations

### Settings Combinations to Test

1. Baseline + Model A + Groq
2. Semantic + Model A + Groq
3. Semantic + Model B + Groq
4. Semantic + Model A + Cerebras
5. Semantic + Model A + Gemini
6. Semantic + Model A + OpenAI (if available)

### Expected Times

- Baseline queries: 1-2 seconds
- Semantic queries: 2-4 seconds
- LLM generation: 0.5-2 seconds (varies by model)

---

Good luck with your testing! 🎯
