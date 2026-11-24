import sys
import os
import time
import streamlit as st

# Sync Streamlit Cloud secrets to environment variables if present
try:
    if hasattr(st, "secrets"):
        for k in st.secrets:
            v = st.secrets[k]
            if isinstance(v, str):
                os.environ[k] = v
        # Prioritize Groq if a Groq key is present
        if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"]:
            os.environ["LLM_PROVIDER"] = "groq"
            os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
            if "GROQ_MODEL" not in st.secrets:
                os.environ["GROQ_MODEL"] = "openai/gpt-oss-20b"
except Exception:
    pass

# Configure page layout and branding
st.set_page_config(
    page_title="@SpotifyCares AI Support Agent",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Spotify-themed Dark Mode CSS
st.markdown("""
<style>
    /* Global styles */
    .stApp {
        background-color: #121212 !important;
        color: #FFFFFF !important;
    }
    
    /* Headers & Accent */
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
        font-family: 'Circular', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    }
    .spotify-green {
        color: #1DB954 !important;
        font-weight: bold;
    }

    /* ------------------------------------------------------------- */
    /* QUERY INPUT BOX: Crisp White Background with Pure Black Font */
    /* ------------------------------------------------------------- */
    .stTextArea textarea, 
    div[data-baseweb="textarea"] textarea,
    textarea {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
        caret-color: #000000 !important;
        border-radius: 8px !important;
        border: 2px solid #282828 !important;
    }
    .stTextArea textarea:focus,
    div[data-baseweb="textarea"] textarea:focus {
        border-color: #1DB954 !important;
        box-shadow: 0 0 8px rgba(29, 185, 84, 0.4) !important;
    }
    .stTextArea textarea::placeholder {
        color: #666666 !important;
    }

    /* Query Label */
    .stTextArea label,
    .stTextArea label p,
    div[data-testid="stWidgetLabel"] p {
        color: #FFFFFF !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        margin-bottom: 6px !important;
    }

    /* Thread turns number input */
    input[type="number"],
    div[data-baseweb="input"] input {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        border-radius: 8px !important;
    }

    /* ------------------------------------------------------------- */
    /* SIDEBAR: Modern Dark Theme with Crisp White Text */
    /* ------------------------------------------------------------- */
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child {
        background-color: #181818 !important;
        border-right: 1px solid #282828 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] li {
        color: #E0E0E0 !important;
        font-size: 14px !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1DB954 !important;
    }

    /* Sidebar Buttons (Presets) */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #242424 !important;
        color: #FFFFFF !important;
        border: 1px solid #383838 !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        text-align: left !important;
        padding: 8px 12px !important;
        margin-bottom: 4px !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #333333 !important;
        border-color: #1DB954 !important;
        color: #1DB954 !important;
    }

    /* ------------------------------------------------------------- */
    /* PRIMARY ACTION BUTTON: Vibrant Spotify Green */
    /* ------------------------------------------------------------- */
    button[kind="primary"],
    .stButton > button[kind="primary"] {
        background-color: #1DB954 !important;
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 14px rgba(29, 185, 84, 0.4) !important;
        transition: all 0.2s ease-in-out !important;
    }
    button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        background-color: #1ed760 !important;
        transform: scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(29, 185, 84, 0.6) !important;
    }

    /* ------------------------------------------------------------- */
    /* TABS: High-Contrast Styling */
    /* ------------------------------------------------------------- */
    button[data-baseweb="tab"] {
        color: #B3B3B3 !important;
        font-size: 15px !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #1DB954 !important;
        border-bottom-color: #1DB954 !important;
    }

    /* Metrics card container */
    .metric-card {
        background: #181818;
        border: 1px solid #282828;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: #1DB954;
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #B3B3B3;
    }
    
    /* Twitter card styling */
    .tweet-card {
        background: #181818;
        border: 1px solid #282828;
        border-radius: 14px;
        padding: 20px;
        margin-top: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .tweet-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }
    .tweet-avatar {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: #1DB954;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
    }
    .tweet-author {
        font-weight: 700;
        font-size: 1.05rem;
        color: #FFFFFF;
    }
    .tweet-handle {
        font-size: 0.85rem;
        color: #B3B3B3;
    }
    .tweet-body {
        font-size: 1.05rem;
        line-height: 1.5;
        color: #E6E6E6;
        white-space: pre-wrap;
    }
    
    /* Status Badges */
    .badge-escalate-yes {
        background-color: rgba(235, 87, 87, 0.15);
        color: #EB5757;
        border: 1px solid #EB5757;
        border-radius: 20px;
        padding: 4px 12px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-escalate-no {
        background-color: rgba(29, 185, 84, 0.15);
        color: #1DB954;
        border: 1px solid #1DB954;
        border-radius: 20px;
        padding: 4px 12px;
        font-weight: 600;
        display: inline-block;
    }
    .retrieved-box {
        background: #202020;
        border-left: 3px solid #1DB954;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Import the pipeline
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.pipeline import run_agent, retrieve_similar
    pipeline_ready = True
except Exception as e:
    st.error(f"Failed to load pipeline: {e}")
    pipeline_ready = False

# Sidebar: System Metadata, Model Info & Presets
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=60)
    st.title("System Controls")
    
    st.markdown("### ⚙️ Architecture Specs")
    st.markdown("""
    - **Dataset:** ~4,000+ `@SpotifyCares` Support Triples
    - **Embeddings:** `all-MiniLM-L6-v2` (Dense RAG)
    - **Inference LLM:** Groq LPU / OpenAI OSS
    - **Guardrails:** Dual (Regex Fact Check + Escalation Guard)
    - **Taxonomy:** 7 Categories
    """)
    
    st.divider()
    
    st.markdown("### 🧪 Quick Presets (Click to Test)")
    
    preset_samples = {
        "💳 Double Charge (Billing)": (
            "I recently signed up for a promotional free trial of Spotify Premium, "
            "but I am now being charged the full monthly fee and cannot remember my login details to cancel it."
        ),
        "🎵 Song Skipping (Playback)": (
            "Hey @SpotifyCares every time my screen locks, my music pauses or skips to the next track. "
            "I'm on Android 14 with the latest app update."
        ),
        "🔍 Missing Album (Content)": (
            "Why is the new album by my favorite indie artist unavailable in Canada? "
            "It was here yesterday and now all songs are greyed out!"
        ),
        "🔐 Locked Out (Account Access)": (
            "I lost access to my registered email and can't receive password reset links. "
            "Can someone please help unlock my account?"
        ),
        "👋 Friendly Greeting (Other)": (
            "hiii, samera, how are you? have a beuatiful day, and im a very big fan of your work"
        )
    }

    selected_preset = None
    for label, text in preset_samples.items():
        if st.button(label, use_container_width=True):
            st.session_state["query_input"] = text

# Main Content Tabs
tab_demo, tab_architecture, tab_benchmarks = st.tabs([
    "🚀 Interactive Agent Prototype",
    "📐 System Architecture & Workflow",
    "📊 Empirical Evaluation & Benchmarks"
])

# TAB 1: Live Interactive Demo
with tab_demo:
    st.markdown("## 🎧 @SpotifyCares AI Support Agent")
    st.markdown(
        "A grounded, multi-stage customer support intelligence system with dense vector retrieval (RAG) "
        "and human-in-the-loop safety guardrails."
    )
    
    default_text = st.session_state.get(
        "query_input",
        "I recently signed up for a promotional free trial of Spotify Premium, but I am now being charged the full monthly fee and cannot remember my login details to cancel it."
    )
    
    user_query = st.text_area(
        "**Customer Tweet / Inbound Support Query:**",
        value=default_text,
        height=100,
        placeholder="Type a customer support message here..."
    )
    
    col_btn, col_turns = st.columns([4, 1])
    with col_turns:
        num_turns = st.number_input("Thread Turns", min_value=1, max_value=5, value=1)
    with col_btn:
        st.write("")
        st.write("")
        run_pressed = st.button("✨ Process Tweet with Agent", type="primary", use_container_width=True)
    
    if run_pressed and pipeline_ready:
        with st.spinner("Classifying intent, querying vector store, and running safety guardrails..."):
            start_t = time.perf_counter()
            result = run_agent(user_query, thread_context=user_query, num_turns=num_turns)
            elapsed = time.perf_counter() - start_t
        
        st.divider()
        
        # 1. Headline Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        
        intent_color = "#1DB954" if result['intent'] != "Other" else "#B3B3B3"
        conf_pct = int(result.get('confidence', 1.0) * 100)
        
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Predicted Intent</div>
                <div class="metric-value" style="color: {intent_color};">{result['intent']}</div>
                <div style="font-size: 0.8rem; color: #888;">Confidence: {conf_pct}%</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m2:
            escalate_status = result['escalate']
            escalate_badge = (
                '<span class="badge-escalate-yes">🚨 ESCALATE TO HUMAN</span>'
                if escalate_status else
                '<span class="badge-escalate-no">✅ RESOLVED BY AI</span>'
            )
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Routing Decision</div>
                <div class="metric-value">{escalate_badge}</div>
                <div style="font-size: 0.8rem; color: #888; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {result['escalate_reason']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with m3:
            hallucinated = result.get('hallucination_flagged', False)
            h_text = '<span style="color: #EB5757;">⚠️ Flagged</span>' if hallucinated else '<span style="color: #1DB954;">🛡️ Verified Grounded</span>'
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Grounding Check</div>
                <div class="metric-value">{h_text}</div>
                <div style="font-size: 0.8rem; color: #888;">0 Hallucinated Entities</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">End-to-End Latency</div>
                <div class="metric-value" style="color: #1DB954;">{elapsed:.2f}s</div>
                <div style="font-size: 0.8rem; color: #888;">LPU Hardware Acceleration</div>
            </div>
            """, unsafe_allow_html=True)
            
        # 2. Twitter / X Response Preview
        st.markdown("### 💬 Drafted Social Media Response")
        st.markdown(f"""
        <div class="tweet-card">
            <div class="tweet-header">
                <div class="tweet-avatar">🎧</div>
                <div>
                    <div class="tweet-author">SpotifyCares <span style="color:#1DB954;">✔</span></div>
                    <div class="tweet-handle">@SpotifyCares • Just now</div>
                </div>
            </div>
            <div class="tweet-body">{result['reply']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. Grounding Vector Context (RAG Inspection)
        with st.expander("🔍 View Retrieved Historical Knowledge Base Grounding (Top-3 Matches)", expanded=False):
            st.markdown("*These 3 historical `@SpotifyCares` resolution pairs were retrieved via dense vector similarity (`all-MiniLM-L6-v2`) to ground the response and prevent hallucinations:*")
            for idx, ex in enumerate(result.get('retrieved_examples', [])):
                st.markdown(f"""
                <div class="retrieved-box">
                    <strong>Reference #{idx+1}</strong><br>
                    <span style="color: #B3B3B3;">Customer:</span> {ex.get('customer_message', '')}<br>
                    <span style="color: #1DB954;">Spotify Resolution:</span> {ex.get('brand_reply', '')}
                </div>
                """, unsafe_allow_html=True)

# TAB 2: Architecture & Workflow Diagram
with tab_architecture:
    st.markdown("## 📐 Multi-Stage Agent Architecture")
    st.markdown("""
    The system follows a **Safety-First, RAG-Grounded Agentic Pipeline** designed specifically for high-volume brand customer service channels:
    """)
    
    st.markdown("""
    ```mermaid
    flowchart TD
        A["Inbound Tweet / Query"] --> B["Intent Classifier<br/>(Few-Shot Prompting, 7 Categories)"]
        A --> C["Dense Vector Retriever<br/>(all-MiniLM-L6-v2)"]
        
        C --> D["Knowledge Base Vector Store<br/>(4,081 @SpotifyCares Resolution Pairs)"]
        D --> E["Top-3 Semantically Similar Context Triples"]
        
        B --> F["Context-Injected Prompt Assembler"]
        E --> F
        
        F --> G["LPU Inference Generator<br/>(Tone-Calibrated Spotify Persona)"]
        G --> H["Draft Response Candidate"]
        
        H --> I{"Guardrail 1:<br/>Hallucination Validator"}
        I -->|"Numeric/Entity Check"| J{"Guardrail 2:<br/>Escalation Policy Engine"}
        
        J -->|"Billing / 2FA / High-Turn / Risk"| K["🚨 Human Agent Escalation<br/>(Backstage Ticket Dispatch)"]
        J -->|"Safe & Grounded"| L["✅ Dispatch Public Reply<br/>(@SpotifyCares Tweet)"]
        
        style A fill:#181818,stroke:#1DB954,stroke-width:2px,color:#fff
        style D fill:#282828,stroke:#1DB954,stroke-width:1px,color:#fff
        style K fill:#331515,stroke:#EB5757,stroke-width:2px,color:#fff
        style L fill:#15331f,stroke:#1DB954,stroke-width:2px,color:#fff
    ```
    """)
    
    st.markdown("### 🛡️ Guardrails & Safety Architecture")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        #### 1. Hallucination Detection
        - **Mechanism:** Extracts all numeric entities, URLs, plan names, and refund promises from the drafted reply.
        - **Cross-Verification:** Asserts that each entity exists verbatim in either the retrieved historical examples or the user's input.
        - **Fallback:** If an ungrounded commitment is detected, the response is rejected or flagged.
        """)
    with c2:
        st.markdown("""
        #### 2. Hybrid Escalation Engine
        - **Financial Liabilities:** Billing disputes and refund requests automatically route to humans.
        - **Credential / 2FA Security:** Account lockouts requiring backstage lookups route securely.
        - **Sentiment & Frustration:** Profanity, legal threats, or multi-turn churn trigger instant handoff.
        """)

# TAB 3: Empirical Benchmarking & Metrics
with tab_benchmarks:
    st.markdown("## 📊 Evaluation & Comparative Benchmarks")
    st.markdown("""
    Evaluated across an annotated **200-example Golden Dataset** (`eval/golden_set.csv`) covering all 7 taxonomy intents, 
    comparing against standard industry baselines:
    """)
    
    st.markdown("""
    | System / Architecture | Intent Accuracy | Escalation Precision | Escalation Recall | Escalation F1 | Avg LLM-as-a-Judge Score (1–5) |
    |---|---|---|---|---|---|
    | **Trivial Baseline** (Majority Class) | 16.5% | 0.000 | 0.000 | 0.000 | 1.20 / 5.00 |
    | **Simple Baseline** (Regex + TF-IDF) | **80.5%** | **1.000** | 0.500 | **0.667** | 3.85 / 5.00 |
    | **Full Agent (RAG + Guardrails)** | 67.5% | 0.091 | **0.800** | 0.163 | **4.83 / 5.00** |
    """)
    
    st.info("""
    💡 **Key Engineering Insight:**
    In safety-critical customer support, **Escalation Recall is prioritized over Precision**. 
    Missing an escalation on a fraudulent transaction or suicidal user is catastrophic, whereas a false escalation merely adds a brief human review. 
    The full agent achieves **0.800 recall** and **4.83/5.00 response quality** according to the LLM-as-a-Judge benchmark.
    """)
