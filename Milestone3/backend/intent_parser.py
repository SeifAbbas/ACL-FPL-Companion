import json
import re
from .config import groq_client, Config


def parse_user_intent(user_input):
    """
    Analyzes user input to determine the Intent and Entities.
    Returns dict with: intent, entities, user_query
    """
    
    system_prompt = """
You are an AI that extracts structured data from Fantasy Premier League (FPL) queries.

CRITICAL: If a query mentions ANY player name (like Salah, Haaland, Kane, Firmino, etc.) or asks about stats/goals/assists/points, it is NEVER "General_Chat". Only use General_Chat for greetings like "hello" or "hi" with no football content.

Step 1: Identify the INTENT from this list:
1. "Player_Stats": Statistics of a specific player (goals, assists, points, matches). USE THIS if any player name is mentioned.
2. "Compare_Players": Comparison between two or more players.
3. "Top_Ranked": Ranked lists of best players by a metric or position.
4. "Head_to_Head": Direct comparison between two teams (e.g., "Arsenal vs Liverpool").
5. "Gameweek_Schedule": List of fixtures in a specific gameweek.
6. "Gameweek_Analysis": Analysis of a gameweek including top performers.
7. "Team_Stats": Aggregated statistics of a team.
8. "Squad_List": List of players from a specific team.
9. "Similar_Players": Finding players with similar attributes.
10. "Captaincy_Pick": Advice on who to captain.
11. "Underlying_Stats": ICT index, threat, creativity queries.
12. "Bonus_Points": Queries about bonus points (BPS).
13. "General_Chat": ONLY for greetings with NO football content (e.g., "hello", "hi", "thanks").

Step 2: Extract ENTITIES exactly as typed (DO NOT correct spelling):
- "Player": List of player names exactly as user typed them
- "Team": List of team names exactly as user typed them  
- "Season": Use format "2021-22" or "2022-23"
- "Gameweek": e.g. "12"
- "Position": e.g. "Defender", "Midfielder", "Forward", "GKP"
- "Metric": e.g. "goals", "points", "assists", "clean sheets"

OUTPUT: Return ONLY valid JSON.
Example: {"intent": "Player_Stats", "entities": {"Player": ["Salah"], "Season": "2022-23"}}
"""
    
    try:
        completion = groq_client.chat.completions.create(
            model=Config.MODEL_GROQ,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content.strip()
        
        # Clean markdown backticks if present
        if "```" in content:
            match = re.search(r"```(?:json)?(.*?)```", content, re.DOTALL)
            if match:
                content = match.group(1).strip()

        parsed = json.loads(content)
        
        # Ensure required fields exist
        if "intent" not in parsed:
            parsed["intent"] = "General_Chat"
        if "entities" not in parsed:
            parsed["entities"] = {}
        
        # Pass through original query for downstream processing
        parsed["user_query"] = user_input

        return parsed

    except Exception as e:
        print(f"Intent Parser Error: {e}")
        return {"intent": "General_Chat", "entities": {}, "user_query": user_input}