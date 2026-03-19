import streamlit as st
import requests
from typing import List, Dict, Any
import time

# --- Page Config ---
st.set_page_config(
    page_title="FastAPI Documentation RAG",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"

# --- Session State Initialization ---
if 'query_input' not in st.session_state:
    st.session_state.query_input = ""
if 'expander_open' not in st.session_state:
    st.session_state.expander_open = True
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'current_result' not in st.session_state:
    st.session_state.current_result = None

def query_rag_api(query: str, top_n: int = 5) -> Dict[str, Any]:
    try:
        with st.spinner("Searching FastAPI documentation..."):
            response = requests.post(
                f"{API_BASE_URL}/query",
                json={"query": query, "top_n": top_n},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def display_sources(sources: List[Dict[str, Any]]):
    if not sources:
        return
    st.subheader("📖 Sources")
    for i, source in enumerate(sources, 1):
        with st.expander(f"Source {i}: {source.get('id', 'Unknown')}", expanded=False):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**Source:** {source.get('source', 'Unknown')}")
                st.markdown(f"**Breadcrumb:** {source.get('breadcrumb', 'Unknown')}")
            with col2:
                similarity = source.get('similarity', 0.0)
                color = "🟢" if similarity >= 0.75 else "🟡" if similarity >= 0.35 else "🔴"
                st.markdown(f"**Similarity:** {color} {similarity:.3f}")
            with col3:
                source_path = source.get('source', '').replace('\\', '/')
                github_url = f"https://github.com/fastapi/fastapi/blob/master/docs/en/{source_path}"
                st.markdown(f"[🔗 View on GitHub]({github_url})")
            st.markdown("---")

@st.fragment
def input_section():
    """Optimized fragment with forced expander collapse."""
    
    # Use a form to handle the clear button properly
    with st.form("query_form"):
        # The text area will now show the example text immediately
        query = st.text_area(
            "Enter your question about FastAPI:",
            placeholder="e.g., How do I create a FastAPI application...",
            height=120,
            value=st.session_state.query_input
        )
        
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            submitted = st.form_submit_button("🔍 Search", type="primary", use_container_width=True)
        with c2:
            cleared = st.form_submit_button("🗑️ Clear", use_container_width=True)
        
        if submitted and query.strip():
            # Also collapse on search click
            st.session_state.expander_open = False
            st.session_state.query_input = query  # Update the stored input
            handle_search(query)
            st.rerun() # Force result to show and expander to hide
        
        if cleared:
            st.session_state.query_input = ""
            st.session_state.current_result = None
            st.rerun()

    # Force expander state update by using a unique key that changes when needed
    expander_key = f"expander_{int(st.session_state.expander_open)}"
    
    with st.expander("💡 Example Questions", expanded=st.session_state.expander_open, key=expander_key):
        example_questions = [
            "How do I create a simple FastAPI application?",
            "What is dependency injection in FastAPI?",
            "How do I add authentication to my FastAPI app?",
            "How do I handle file uploads in FastAPI?",
            "What is the difference between Query and Path parameters?",
            "How do I test my FastAPI application?"
        ]
        
        cols = st.columns(2)
        for idx, example in enumerate(example_questions):
            # When the button is clicked:
            if cols[idx % 2].button(example, key=f"ex_{idx}", use_container_width=True):
                # 1. Set the input text (not the widget key)
                st.session_state.query_input = example
                # 2. Keep expander open so user can see more examples
                st.session_state.expander_open = True
                # 3. Rerun to update the text input
                st.rerun()

def handle_search(query_text: str):
    start_time = time.time()
    # Pull top_n from the sidebar slider key
    top_n = st.session_state.get('top_n_slider', 5)
    result = query_rag_api(query_text.strip(), top_n)
    end_time = time.time()
    
    if result:
        result['response_time'] = end_time - start_time
        st.session_state.current_result = result
        st.session_state.query_history.append({
            'query': query_text,
            'answer': result.get('answer', ''),
            'timestamp': time.time(),
            'sources_count': len(result.get('sources', []))
        })

def main():
    st.title("📚 FastAPI Documentation RAG")
    st.markdown("Ask questions about FastAPI and get intelligent answers with source citations.")

    with st.sidebar:
        st.header("⚙️ Configuration")
        st.text_input("API Base URL", value=API_BASE_URL, disabled=True)
        st.slider("Number of Sources", 5, 50, 10, key="top_n_slider")
        
        st.markdown("---")
        st.header("ℹ️ Model Information")
        st.info("Embedding model: text-embedding-004\n\nVector Search: Vertex AI\n\nLLM: Gemini 2.5 Flash")
        
        if st.button("Clear History"):
            st.session_state.query_history = []
            st.rerun()

    # Optimized Input Fragment
    input_section()

    # --- Results Display ---
    if st.session_state.current_result:
        res = st.session_state.current_result
        st.markdown("---")
        st.header("🤖 Answer")
        st.markdown(res.get('answer', 'No answer received.'))
        
        # Restored Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Docs Retrieved", res.get('documents_retrieved', 0))
        m2.metric("Context Length", res.get('context_length', 0))
        m3.metric("Tokens Used", res.get('tokens_used', 0))
        m4.metric("Time", f"{res.get('response_time', 0):.2f}s")
        
        st.caption(f"Model: {res.get('model', 'Unknown')}")
        
        display_sources(res.get('sources', []))

    # --- History Section ---
    if st.session_state.query_history:
        st.markdown("---")
        st.header("📜 Recent Queries")
        for item in reversed(st.session_state.query_history[-5:]):
            with st.expander(f"Q: {item['query'][:70]}..."):
                st.write(item['answer'])

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #666; font-size: 0.8em;'>FastAPI Documentation RAG System | Powered by Vertex AI & Gemini</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()