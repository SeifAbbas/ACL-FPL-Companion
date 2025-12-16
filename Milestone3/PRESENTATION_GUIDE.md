# FPL Graph-RAG Presentation Guide

## ⚠️ CRITICAL RULES

| Rule                          | Consequence    |
| ----------------------------- | -------------- |
| Total time: **18-22 minutes** | Required       |
| 19+ minutes late              | **ZERO grade** |
| 15-18 minutes late            | 30% deduction  |
| 10-14 minutes late            | 15% deduction  |

---

## Team Member Assignments

| Member   | Component           | Slides | Q&A Topics                               |
| -------- | ------------------- | ------ | ---------------------------------------- |
| Person 1 | Input Preprocessing | 3      | Intent classification, entity extraction |
| Person 2 | Graph Retrieval     | 4-5    | Cypher queries, baseline vs semantic     |
| Person 3 | LLM Layer           | 6-7    | Prompt structure, 4 LLM comparison       |
| Person 4 | UI + Demo           | 2, 8-9 | Integration, live demo                   |

---

## Slide-by-Slide Script

### Slide 1: Title (0 seconds - Just display)

```
FPL Graph-RAG Assistant
Milestone 3

Team Members:
- [Name 1] - Input Preprocessing
- [Name 2] - Graph Retrieval
- [Name 3] - LLM Layer
- [Name 4] - UI & Integration

Course: CSEN 903
Date: [Date]
```

**DO NOT** add introduction, motivation, or problem statement.

---

### Slide 2: System Architecture (2 min - Person 4)

**Visual**: Flow diagram showing all 4 components

```
User Question
     │
     ▼
┌────────────────────┐
│  Intent Parser     │ ◄── Groq LLM
│  (intent_parser.py)│
└────────────────────┘
     │
     ▼
┌────────────────────┐
│  Knowledge Graph   │ ◄── Neo4j + Vectors
│  (knowledge_graph) │
│  Baseline/Semantic │
└────────────────────┘
     │
     ▼
┌────────────────────┐
│  Response Generator│ ◄── 4 LLMs Available
│  (response_gen.py) │
└────────────────────┘
     │
     ▼
   Answer
```

**Script**:

> "Our system has four components. When a user asks a question, the Intent Parser classifies what they want and extracts entities. The Knowledge Graph layer queries Neo4j using either baseline text matching or semantic vector search. The Response Generator uses one of four LLMs to create a natural language answer. Let me hand over to [Person 1] for the preprocessing details."

---

### Slide 3: Input Preprocessing (2 min - Person 1)

**Left side - Intent List**:

```
12 Supported Intents:
1. Player_Stats       7. Gameweek_Analysis
2. Compare_Players    8. Head_to_Head
3. Top_Ranked         9. Similar_Players
4. Team_Stats        10. Captaincy_Pick
5. Squad_List        11. Underlying_Stats
6. Gameweek_Schedule 12. Bonus_Points
```

**Right side - Example**:

```
Input: "Compare Salah and Haaland"

Output:
{
  "intent": "Compare_Players",
  "entities": {
    "Player": ["Salah", "Haaland"]
  }
}
```

**Script**:

> "For intent classification, we use Groq's Llama model with JSON mode. The model classifies queries into one of 12 intents. Entity extraction identifies players, teams, seasons, gameweeks, positions, and metrics. Here's an example: 'Compare Salah and Haaland' becomes Compare_Players intent with both player names extracted."

---

### Slide 4: Graph Retrieval - Baseline (2-3 min - Person 2)

**Title**: Baseline Retrieval: Cypher Queries

**Show 3 query examples**:

**Query 1 - Player Stats**:

```cypher
MATCH (p:Player)
WHERE toLower(p.player_name) CONTAINS toLower($name)
MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
RETURN p.player_name, sum(r.goals_scored) AS Goals
```

**Query 2 - Top Ranked**:

```cypher
MATCH (p:Player)-[:PLAYS_AS]->(pos:Position)
WHERE pos.name = $position
RETURN p.player_name, sum(r.total_points) AS Points
ORDER BY Points DESC LIMIT 10
```

**Query 3 - Team Stats**:

```cypher
// Calculates W/D/L using player goals and fixture context
// Complex logic to determine which players belong to which team
```

**Script**:

> "Baseline uses 12 Cypher query templates with exact text matching. Player Stats uses CONTAINS for name matching. Top Ranked filters by position and sorts by the requested metric. Team Stats is our most complex query - it calculates wins, draws, losses by analyzing which players scored for which team in each fixture."

---

### Slide 5: Graph Retrieval - Semantic (2-3 min - Person 2)

**Title**: Semantic Retrieval: Vector Search

**Left side**:

```
Embedding Approach: Node Embeddings

Text format for each player:
"Player: Mohamed Salah. Position: MID.
 Total Fantasy Points: 234."

Vector Search Query:
CALL db.index.vector.queryNodes(
  'player_idx_a', 10, $queryVector
)
YIELD node, score
WHERE score > 0.7
```

**Right side - Model Comparison**:

| Property   | Model A (MiniLM) | Model B (MPNet) |
| ---------- | ---------------- | --------------- |
| Dimensions | 384              | 768             |
| Speed      | ⚡ Faster        | 🐢 Slower       |
| Accuracy   | Good             | Better          |

**Script**:

> "Semantic retrieval embeds each player as a text description, then stores the vector in Neo4j. When a user makes a typo like 'firmno', we embed the query and find similar vectors. Model A uses MiniLM with 384 dimensions - faster but less accurate. Model B uses MPNet with 768 dimensions - slower but handles edge cases better."

---

### Slide 6: LLM Layer - Prompt Structure (2 min - Person 3)

**Title**: LLM Prompt Construction

**Show prompt structure**:

```
┌─────────────────────────────────────┐
│         SYSTEM PERSONA              │
│ "You are an expert FPL Analyst..."  │
└─────────────────────────────────────┘
              +
┌─────────────────────────────────────┐
│            CONTEXT                  │
│ Retrieved Data from Knowledge Graph │
│ [{Player: "Salah", Points: 234}]    │
└─────────────────────────────────────┘
              +
┌─────────────────────────────────────┐
│             TASK                    │
│ "Answer using ONLY provided data.   │
│  Be specific with numbers."         │
└─────────────────────────────────────┘
```

**Script**:

> "Our prompt has three parts. First, a dynamic persona that changes based on intent - Player Stats uses 'FPL Analyst', Team Stats uses 'Football Pundit'. Second, the context containing actual data from Neo4j. Third, strict instructions to use only the provided data. This structure prevents hallucination by grounding the LLM in real database results."

---

### Slide 7: LLM Comparison (2 min - Person 3)

**Title**: 4 LLM Models Compared

| Model            | Provider | Avg Time | Quality   | Cost |
| ---------------- | -------- | -------- | --------- | ---- |
| Llama 3.3 70B    | Groq     | ~0.8s    | Good      | Free |
| Llama 3.3 70B    | Cerebras | ~0.5s    | Good      | Free |
| Gemini 2.0 Flash | Google   | ~1.0s    | Good      | Free |
| GPT-4o           | OpenAI   | ~2.5s    | Excellent | Paid |

**Observations**:

```
Cerebras: Fastest inference, good for demos
Groq: Good balance of speed and quality
Gemini: Occasionally verbose responses
OpenAI: Best quality but slowest and costs money
```

**Script**:

> "We compared four LLMs. Cerebras is fastest at 0.5 seconds - they specialize in inference speed. Groq is our default - fast and free. Gemini works well but can be verbose. OpenAI GPT-4o gives the best quality responses but costs money and is 3-5x slower. For demos, we recommend Cerebras or Groq."

---

### Slide 8: Error Analysis (2 min - Person 1 or 3)

**Title**: Challenges & Solutions

**Left - Problems Found**:

```
1. Intent Misclassification
   - "Salah stats" → General_Chat
   - Fix: Override logic checks entities

2. Typos in Baseline Mode
   - "firmno" → No results
   - Fix: Use Semantic mode

3. Team Stats Calculation
   - Wrong W/D/L numbers
   - Fix: Count fixtures with majority rule
```

**Right - Remaining Limitations**:

```
• Only 2021-22 and 2022-23 seasons
• Player transfers not fully tracked
• Some complex queries slow (3-5s)
• Typos in team names less robust
```

**Script**:

> "We encountered three main challenges. First, the LLM sometimes misclassified queries - we added override logic to check if entities exist. Second, baseline mode can't handle typos - semantic mode with vectors solves this. Third, calculating team statistics required complex logic to determine which players belong to which team. Remaining limitations include only having two seasons of data."

---

### Slide 9: Live Demo (30 sec intro, then demo)

**Title**: Live Demonstration

**Queries to demonstrate**:

```
1. "Salah stats" - Basic query
2. "firmno stats" - Typo handling (Semantic)
3. "Compare Salah and Haaland" - Comparison
4. "Arsenal performance" - Team stats
5. "Who should I captain?" - Recommendation
6. Switch LLM: Groq → Cerebras
```

**Script before demo**:

> "Now I'll demonstrate the system live. I'll show basic queries, typo handling with semantic search, comparisons, team stats, and then switch between LLMs to show the flexibility."

---

## Live Demo Script (4-5 min - Person 4)

### Step 1: Show the Interface

- Point to sidebar: "Configuration panel"
- Point to chat: "Main conversation area"

### Step 2: Basic Query

```
Type: Salah stats
```

- Wait for response
- Click "Under the Hood"
- Show: Intent, Cypher Query, Raw Data

> "The system correctly identified Player_Stats intent, ran the Cypher query, and generated a natural response."

### Step 3: Typo Handling

- **First**: Set mode to "Baseline"

```
Type: firmno stats
```

> "In baseline mode, typos fail because it's exact matching."

- **Then**: Switch to "Semantic"

```
Type: firmno stats
```

> "Semantic mode uses vectors to find 'Roberto Firmino' despite the typo."

### Step 4: Comparison

```
Type: Compare Salah and Haaland
```

> "For comparisons, both players' stats are retrieved and compared."

### Step 5: Team Stats

```
Type: Arsenal performance
```

> "Team stats shows wins, draws, losses, goal difference. Arsenal had 26 wins in 2022-23."

### Step 6: Switch LLM

- Change dropdown from Groq to Cerebras

```
Type: Top 5 scorers
```

> "Notice Cerebras is faster. Same data, different LLM for generation."

### Step 7: Show Metrics

- Point to Total Time, Graph Search, LLM Gen
  > "These metrics help us compare performance across configurations."

---

## Q&A Preparation

### Questions for Person 1 (Input Preprocessing)

**Q: Why use LLM for intent classification instead of rules?**

> "LLMs handle variations naturally. Rule-based would need hundreds of if-else statements for edge cases like 'how many goals did Salah score' vs 'Salah goal count' vs 'goals for Salah'."

**Q: What happens if entity extraction fails?**

> "We have override logic in knowledge_graph.py. If entities are found but intent is General_Chat, we correct it based on which entities exist."

**Q: Show me the intent classification code.**

> Open intent_parser.py, show system_prompt and groq_client.chat.completions.create()

---

### Questions for Person 2 (Graph Retrieval)

**Q: Why node embeddings instead of edge embeddings?**

> "Our primary search target is player names. Node embeddings let us embed the whole player identity - name, position, total points - in one vector."

**Q: How does vector search handle typos?**

> "Similar words have similar embeddings. 'firmno' and 'firmino' produce similar vectors because they share characters and context."

**Q: Show me a Cypher query.**

> Open knowledge_graph.py, scroll to Player_Stats or Team_Stats section.

---

### Questions for Person 3 (LLM Layer)

**Q: Why change persona based on intent?**

> "Different contexts need different expertise. A comparison needs analytical tone, a captain recommendation needs advisory tone. This improves response quality."

**Q: How do you prevent hallucination?**

> "We explicitly tell the LLM to use ONLY the provided context. If data is missing, admit it rather than make things up. The KG data grounds every response."

**Q: Why is Cerebras faster than Groq?**

> "Cerebras built custom hardware optimized for neural network inference. Their WSE chip runs the full model without memory bottlenecks."

---

### Questions for Person 4 (UI + Integration)

**Q: How do the components communicate?**

> "app.py orchestrates everything. It calls parse_user_intent() which returns a dict, passes that to query_knowledge_graph() which returns data, then to generate_natural_language_answer() for the final response."

**Q: What if Neo4j is down?**

> "The try-except in knowledge_graph.py catches database errors and returns a user-friendly message instead of crashing."

**Q: Why Streamlit?**

> "It's Python-native, requires no frontend knowledge, and creates interactive UIs quickly. Perfect for prototyping ML applications."

---

## Timing Checklist

| Section             | Target        | Actual | Presenter  |
| ------------------- | ------------- | ------ | ---------- |
| Architecture        | 2 min         | \_\_\_ | Person 4   |
| Input Preprocessing | 2 min         | \_\_\_ | Person 1   |
| Graph - Baseline    | 2-3 min       | \_\_\_ | Person 2   |
| Graph - Semantic    | 2-3 min       | \_\_\_ | Person 2   |
| LLM - Prompts       | 2 min         | \_\_\_ | Person 3   |
| LLM - Comparison    | 2 min         | \_\_\_ | Person 3   |
| Error Analysis      | 2 min         | \_\_\_ | Person 1/3 |
| Live Demo           | 4-5 min       | \_\_\_ | Person 4   |
| **TOTAL**           | **18-22 min** | \_\_\_ |            |

---

## Day-Before Checklist

- [ ] All API keys working (test each LLM)
- [ ] Neo4j database running
- [ ] `streamlit run app.py` works
- [ ] Each person practiced their slides
- [ ] Backup screenshots saved
- [ ] Know room location and time slot

## 30-Minutes-Before Checklist

- [ ] Arrive at location
- [ ] Connect to projector
- [ ] Open slides
- [ ] Start `streamlit run app.py`
- [ ] Open backup screenshots folder
- [ ] Test one query to warm up the system

---

## What NOT To Do

❌ Don't explain basic concepts (Graph-RAG, Neo4j, LLMs)
❌ Don't add introduction/motivation slides
❌ Don't show code line-by-line
❌ Don't have one person present everything
❌ Don't go over 22 minutes
❌ Don't use pre-recorded video for demo
❌ Don't panic if demo fails (use backup screenshots)

---

## Backup Plan

If the live demo fails:

1. Stay calm
2. Say: "Let me show you from our backup documentation"
3. Open backup folder with screenshots
4. Walk through the same queries using images
5. Explain what WOULD happen

---

Good luck! 🎯⚽
