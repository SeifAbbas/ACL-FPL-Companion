import json
from .config import groq_client, MODEL_NAME

def parse_user_intent(user_input):
    """
    Analyzes user input to determine the Intent and Entities.
    """
    
    system_prompt = """
    You are an AI that extracts structured data from football (FPL) queries.
    
    Step 1: Identify the INTENT from this list:
    1. "Player_Stats": Specific player output (goals, assists, points).
    2. "Compare_Players": Compare two or more players side-by-side.
    3. "Top_Ranked": Best/Top players (filtering by position/stat).
    4. "Fixture_Query": Specific team's matches ("Who do Arsenal play?").
    5. "Gameweek_Schedule": General GW fixtures ("What games are in GW 12?").
    6. "Player_Form": Recent performance/history (last 3 games).
    7. "Injury_Query": Availability/minutes played/chance of playing.
    8. "Recommendation": Advice on who to pick/captain/bench.
    9. "Team_Stats": Team performance/goals/wins.
    10. "Squad_List": Asking for players in a specific team ("List Arsenal attackers").
    11. "General_Chat": Non-football greetings or nonsense.

    Step 2: Extract ENTITIES:
    - "Player": List of player names
    - "Team": List of team names
    - "Season": e.g., "2023-24"
    - "Gameweek": e.g., "12"
    - "Position": e.g., "Defender", "FWD", "Goalie"
    - "Metric": e.g., "goals", "points", "creativity", "price"

    OUTPUT FORMAT: Return ONLY valid JSON.
    Example: {"intent": "Gameweek_Schedule", "entities": {"Gameweek": "12"}}
    """

    try:
        completion = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)

    except Exception as e:
        print(f"Intent Parser Error: {e}")
        return {"intent": "General_Chat", "entities": {}}