"""
FPL Intelligent Assistant - Streamlit UI
Graph-RAG powered Fantasy Premier League assistant.
"""

import streamlit as st
import time

from backend.config import Config, get_available_llms
from backend.intent_parser import parse_user_intent
from backend.knowledge_graph import query_knowledge_graph
from backend.response_generator import generate_natural_language_answer, get_model_display_name


# Page config
st.set_page_config(
    page_title="FPL Assistant (GraphRAG)",
    page_icon="⚽",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. Retrieval Strategy
    st.subheader("1. Retrieval Strategy")
    retrieval_mode = st.radio(
        "Search Mode:",
        ["baseline", "semantic"],
        captions=["Exact Text Match (typos fail)", "AI Vector Search (handles typos)"],
        index=1
    )
    
    # 2. Embedding Model (only for semantic)
    model_choice = "A"
    if retrieval_mode == "semantic":
        st.subheader("2. Embedding Model")
        emb_model = st.selectbox(
            "Choose Model:",
            ["Model A (MiniLM - Fast)", "Model B (MPNet - Accurate)"]
        )
        model_choice = "A" if "MiniLM" in emb_model else "B"
    
    st.divider()
    
    # 3. LLM Selection
    st.subheader("3. LLM Model")
    available_llms = get_available_llms()
    selected_model = st.selectbox(
        "Choose LLM:",
        available_llms,
        format_func=get_model_display_name,
        index=0
    )
    
    st.divider()
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main interface
st.title("⚽ FPL Intelligent Assistant")
st.caption("Seasons: 2021-22 & 2022-23 | Baseline vs Semantic Retrieval")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "debug" in message:
            with st.expander("🛠️ Under the Hood"):
                st.json(message["debug"])

# Chat input
if prompt := st.chat_input("Ask about FPL (e.g., 'Salah stats', 'Top scorers')"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    start_total = time.time()
    
    with st.status("🧠 Processing...", expanded=False) as status:
        
        # 1. Intent Parsing
        t0 = time.time()
        intent_data = parse_user_intent(prompt)
        t_intent = time.time() - t0
        status.write(f"Intent detected: {intent_data['intent']}")
        
        # 2. Graph Retrieval
        status.update(label=f"🔍 Searching Graph ({retrieval_mode})...", state="running")
        t0 = time.time()
        kg_result = query_knowledge_graph(
            intent_data, 
            retrieval_mode=retrieval_mode, 
            model_choice=model_choice
        )
        t_graph = time.time() - t0
        
        raw_data = kg_result.get("data", "[]")
        cypher_query = kg_result.get("cypher", "No query")
        
        # 3. Answer Generation
        status.update(label="📝 Generating Answer...", state="running")
        t0 = time.time()
        final_answer = generate_natural_language_answer(
            prompt, 
            intent_data, 
            raw_data, 
            model_name=selected_model
        )
        t_llm = time.time() - t0
        
        status.update(label="✅ Complete!", state="complete", expanded=False)

    end_total = time.time()
    total_time = end_total - start_total

    # Display response
    with st.chat_message("assistant"):
        st.markdown(final_answer)
        
        # Metrics
        cols = st.columns(4)
        cols[0].metric("Total Time", f"{total_time:.2f}s")
        cols[1].metric("Graph Search", f"{t_graph:.2f}s")
        cols[2].metric("LLM Gen", f"{t_llm:.2f}s")
        cols[3].metric("Active Brain", f"Model {model_choice}")

        debug_info = {
            "1_Intent": intent_data,
            "2_Cypher": cypher_query,
            "3_Raw_Data": raw_data,
            "4_Performance": {
                "Total": f"{total_time:.4f}s",
                "Graph": f"{t_graph:.4f}s",
                "LLM": f"{t_llm:.4f}s"
            }
        }
        
        with st.expander("🛠️ Under the Hood"):
            st.markdown("**Cypher Query:**")
            st.code(cypher_query, language="cypher")
            st.markdown("**Raw Data:**")
            st.text(raw_data)

    st.session_state.messages.append({
        "role": "assistant", 
        "content": final_answer,
        "debug": debug_info
    })