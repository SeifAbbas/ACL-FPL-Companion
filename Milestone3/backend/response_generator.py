from .config import groq_client, MODEL_NAME

def generate_natural_language_answer(user_query, structured_data, kg_data):
    """
    Generates a response using the LLM, grounded in the Neo4j data.
    Args:
        user_query (str): The user's original question.
        structured_data (dict): The output from the intent parser.
        kg_data (str/list): The raw data retrieved from Neo4j.
    """
    
    # 1. Prepare Context
    if not kg_data or kg_data == "[]" or "No specific query" in str(kg_data):
        context_block = "No direct data was found in the database. Rely on general knowledge but mention the missing data."
    else:
        context_block = f"Retrieved Database Info:\n{kg_data}"

    # 2. Extract Intent for Persona Switching
    intent = structured_data.get("intent", "General_Chat")
    
    # 3. Dynamic Persona
    if intent == "Player_Stats":
        system_persona = "You are an expert FPL Analyst. Use the retrieved stats to answer precisely."
    elif intent == "Team_Stats":
        system_persona = "You are a Football Pundit. Summarize the team's performance based on the data."
    elif intent == "Recommendation":
        system_persona = "You are a Fantasy Premier League Manager / Coach. Give advice based on the data."
    else:
        system_persona = "You are a helpful FPL Assistant."

    # 4. Construct Prompt
    prompt = f"""
    [CONTEXT]
    The user asked: "{user_query}"
    
    {context_block}
    
    [INSTRUCTIONS]
    - Answer the question using ONLY the retrieved info above.
    - If the retrieved info contains the answer, be specific (numbers, names).
    - If the retrieved info is empty or irrelevant, admit you don't know based on the database.
    - Keep it short and conversational.
    """

    # 5. Call LLM
    try:
        completion = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_persona},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"⚠️ LLM Error: {str(e)}"