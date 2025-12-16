"""
Response Generator Module for FPL Graph-RAG Assistant
Generates natural language answers using LLMs, grounded in Knowledge Graph data.
"""

from .config import Config, groq_client, openai_client, gemini_client, cerebras_client


def generate_natural_language_answer(user_query, structured_data, kg_data, model_name=None):
    """
    Generates a response using the LLM, grounded in the Neo4j data.
    
    Args:
        user_query: The user's original question
        structured_data: Output from intent parser
        kg_data: Raw data from Neo4j
        model_name: Which LLM to use
    
    Returns:
        Natural language response string
    """
    
    # Prepare context
    if not kg_data or kg_data == "[]" or "No specific query" in str(kg_data) or "General Chat" in str(kg_data):
        context_block = "No direct data was found in the database. Rely on general knowledge but mention the missing data."
    else:
        context_block = f"Retrieved Database Info:\n{kg_data}"

    # Get intent for persona
    intent = structured_data.get("intent", "General_Chat")
    
    # Dynamic persona based on intent
    persona_map = {
        "Player_Stats": "You are an expert FPL Analyst. Use the retrieved stats to answer precisely.",
        "Compare_Players": "You are an FPL Comparison Expert. Analyze differences objectively.",
        "Top_Ranked": "You are an FPL Rankings Specialist. Present the leaderboard clearly.",
        "Team_Stats": "You are a Football Pundit. Summarize the team's performance.",
        "Head_to_Head": "You are a Match Commentator. Analyze the history between these teams.",
        "Gameweek_Schedule": "You are an FPL Fixture Analyst. Present the schedule clearly.",
        "Gameweek_Analysis": "You are a Gameweek Analyst. Summarize key events and performers.",
        "Similar_Players": "You are an FPL Transfer Advisor. Explain player similarities.",
        "Captaincy_Pick": "You are an FPL Captain Expert. Give captain recommendations.",
        "Underlying_Stats": "You are an Advanced Stats Analyst. Explain ICT metrics.",
        "Bonus_Points": "You are a BPS Expert. Explain bonus point distribution.",
        "Squad_List": "You are a Squad Analyst. Present the team roster.",
        "General_Chat": "You are a helpful FPL Assistant."
    }
    
    system_persona = persona_map.get(intent, "You are a helpful FPL Assistant.")

    # Build prompt
    prompt = f"""
[SYSTEM CONTEXT]
- You are strictly limited to FPL data from seasons 2021-22 and 2022-23.
- Do NOT use external knowledge about matches/players outside this range.

[CONTEXT]
The user asked: "{user_query}"

{context_block}

[INSTRUCTIONS]
- Answer the question using ONLY the retrieved info above.
- If the retrieved info contains the answer, be specific (numbers, names).
- If the retrieved info is empty or irrelevant, admit you don't know based on the database.
- Keep it short and conversational.
"""
    
    target_model = model_name if model_name else Config.MODEL_GROQ
    
    try:
        # Groq (Llama)
        if target_model == Config.MODEL_GROQ and groq_client:
            completion = groq_client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_persona},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return completion.choices[0].message.content
        
        # OpenAI (GPT-4)
        elif target_model == Config.MODEL_OPENAI and openai_client:
            completion = openai_client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_persona},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return completion.choices[0].message.content
        
        # Google Gemini
        elif target_model == Config.MODEL_GEMINI and gemini_client:
            full_prompt = f"{system_persona}\n\n{prompt}"
            response = gemini_client.models.generate_content(
                model=target_model,
                contents=full_prompt
            )
            return response.text
        
        # Cerebras (Llama - Fast Inference)
        elif target_model == Config.MODEL_CEREBRAS and cerebras_client:
            completion = cerebras_client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_persona},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_completion_tokens=500,
                top_p=1
            )
            return completion.choices[0].message.content
        
        # Fallback to Groq
        else:
            if groq_client:
                completion = groq_client.chat.completions.create(
                    model=Config.MODEL_GROQ,
                    messages=[
                        {"role": "system", "content": system_persona},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return f"[Using Groq fallback] {completion.choices[0].message.content}"
            else:
                return f"⚠️ No LLM available for '{target_model}'. Check API keys."
        
    except Exception as e:
        return f"⚠️ LLM Error: {str(e)}"


def get_model_display_name(model_name):
    """Returns human-readable name for UI display."""
    display_names = {
        Config.MODEL_GROQ: "🦙 Llama 3.3 70B V (Groq)",
        Config.MODEL_OPENAI: "🤖 GPT-oss-20b (OpenAI)",
        Config.MODEL_GEMINI: "✨ Gemini 2.5 flash (Google)",
        Config.MODEL_CEREBRAS: "🤖 GPT-oss-120b (Cerebras)"
    }
    return display_names.get(model_name, model_name)