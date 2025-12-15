import json
from .config import groq_client, MODEL_NAME

def parse_user_intent(user_input):
    """
    Analyzes user input to determine the Intent and Entities.
    """
    
    system_prompt = """
    You are an AI that extracts structured data from Fantasy Premier League (FPL) queries.
    
    Step 1: Identify the INTENT from this list:
    1. "Player_Stats": Specific player output (goals, assists, points, history).
    2. "Compare_Players": Compare two or more players side-by-side.
    3. "Top_Ranked": Requests for lists of best players (e.g. "top 5 defenders").
    4. "Fixture_Query": Questions about specific matches (e.g. "Who do Arsenal play?").
    5. "Gameweek_Schedule": General schedule (e.g. "fixtures in GW 12").
    6. "Injury_Query": Availability, red flags, or chance of playing.
    7. "Squad_List": Asking for players in a specific team (e.g. "List Arsenal attackers").
    8. "General_Chat": Non-football greetings or off-topic.

    Step 2: Extract ENTITIES:
    - "Player": List of player names (e.g. ["Salah", "Haaland"])
    - "Team": List of team names (e.g. ["Arsenal", "Liverpool"])
    - "Season": The specific season mentioned (Use format: "2021-22" or "2022-23").
    - "Gameweek": e.g. "12"
    - "Position": e.g. "Defender", "Midfielder", "Forward", "GKP"
    - "Metric": e.g. "goals", "points", "clean sheets", "price"

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