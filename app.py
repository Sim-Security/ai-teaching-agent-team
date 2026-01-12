"""
AI Teaching Agent Team - Streamlit Application

A multi-agent teaching system built with LangChain, LangGraph, and LangSmith.
Each agent specializes in a different aspect of creating educational content.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="👨‍🏫 AI Teaching Agent Team",
    page_icon="👨‍🏫",
    layout="centered",
)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------

if 'openrouter_api_key' not in st.session_state:
    st.session_state['openrouter_api_key'] = os.getenv('OPENROUTER_API_KEY', '')
if 'composio_api_key' not in st.session_state:
    st.session_state['composio_api_key'] = os.getenv('COMPOSIO_API_KEY', '')
if 'composio_user_id' not in st.session_state:
    st.session_state['composio_user_id'] = os.getenv('COMPOSIO_USER_ID', 'default')
if 'composio_mcp_config_id' not in st.session_state:
    st.session_state['composio_mcp_config_id'] = os.getenv('COMPOSIO_MCP_CONFIG_ID', '')
if 'langsmith_api_key' not in st.session_state:
    st.session_state['langsmith_api_key'] = os.getenv('LANGSMITH_API_KEY', '')
if 'serpapi_api_key' not in st.session_state:
    st.session_state['serpapi_api_key'] = os.getenv('SERPAPI_API_KEY', '')
if 'topic' not in st.session_state:
    st.session_state['topic'] = ''
if 'use_test_model' not in st.session_state:
    st.session_state['use_test_model'] = True
if 'use_production_search' not in st.session_state:
    st.session_state['use_production_search'] = False

# Model options
MODELS = {
    "🧪 Gemini 2.0 Flash (Free)": "google/gemini-2.0-flash-exp:free",
    "🚀 Grok 4.1 Fast (Production)": "x-ai/grok-4.1-fast",
    "💎 Claude 3.5 Sonnet": "anthropic/claude-3.5-sonnet",
    "🧠 GPT-4o": "openai/gpt-4o",
    "⚡ GPT-4o Mini": "openai/gpt-4o-mini",
}

# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------

with st.sidebar:
    st.title("⚙️ Configuration")
    
    st.subheader("🔑 API Keys")
    
    st.session_state['openrouter_api_key'] = st.text_input(
        "OpenRouter API Key",
        value=st.session_state['openrouter_api_key'],
        type="password",
        help="Get your key at https://openrouter.ai/keys"
    ).strip()
    
    st.session_state['composio_api_key'] = st.text_input(
        "Composio API Key",
        value=st.session_state['composio_api_key'],
        type="password",
        help="Get your key at https://composio.ai"
    ).strip()
    
    st.session_state['langsmith_api_key'] = st.text_input(
        "LangSmith API Key (Optional)",
        value=st.session_state['langsmith_api_key'],
        type="password",
        help="Get your key at https://smith.langchain.com"
    ).strip()
    
    st.divider()
    
    st.subheader("🤖 Model Selection")
    
    selected_model = st.selectbox(
        "Choose Model",
        options=list(MODELS.keys()),
        index=0,
        help="Free tier available for testing"
    )
    model_id = MODELS[selected_model]
    
    st.caption(f"Model ID: `{model_id}`")
    
    st.divider()
    
    st.subheader("🔍 Search Configuration")
    
    st.session_state['use_production_search'] = st.toggle(
        "Use SerpAPI (Production)",
        value=st.session_state['use_production_search'],
        help="Toggle off for DuckDuckGo (free)"
    )
    
    if st.session_state['use_production_search']:
        st.session_state['serpapi_api_key'] = st.text_input(
            "SerpAPI Key",
            value=st.session_state['serpapi_api_key'],
            type="password",
        ).strip()
    
    st.divider()
    
    # LangSmith info
    if st.session_state['langsmith_api_key']:
        st.success("✅ LangSmith tracing enabled")
        st.caption("View traces at [smith.langchain.com](https://smith.langchain.com)")
    else:
        st.info("💡 Add LangSmith key for observability")

# -----------------------------------------------------------------------------
# Main UI
# -----------------------------------------------------------------------------

st.title("👨‍🏫 AI Teaching Agent Team")
st.markdown("*Powered by LangGraph & LangSmith*")

st.markdown("""
Enter a topic to generate a complete learning package including:
- 📚 **Knowledge Base** - Comprehensive overview from first principles
- 🗺️ **Learning Roadmap** - Structured path from beginner to expert
- 📖 **Curated Resources** - Tutorials, docs, courses, and more
- ✍️ **Practice Materials** - Exercises, quizzes, and projects
""")

# Validate required API keys
missing_keys = []
if not st.session_state['openrouter_api_key']:
    missing_keys.append("OpenRouter")
if not st.session_state['composio_api_key']:
    missing_keys.append("Composio")

if missing_keys:
    st.error(f"⚠️ Please enter your {' and '.join(missing_keys)} API key(s) in the sidebar.")
    st.stop()

# Topic input
topic = st.text_input(
    "🎯 What topic do you want to learn?",
    placeholder="e.g., LangGraph, Machine Learning, Kubernetes, etc.",
    value=st.session_state['topic']
)
st.session_state['topic'] = topic

# Start button
if st.button("🚀 Generate Learning Package", type="primary", use_container_width=True):
    if not topic:
        st.error("Please enter a topic.")
        st.stop()
    
    # Configure LangSmith
    if st.session_state['langsmith_api_key']:
        os.environ['LANGSMITH_TRACING'] = 'true'
        os.environ['LANGSMITH_API_KEY'] = st.session_state['langsmith_api_key']
        os.environ['LANGSMITH_PROJECT'] = 'ai-teaching-agent-team'
    
    try:
        # Import LangChain components
        from langchain_openai import ChatOpenAI
        from src.graph import create_teaching_graph
        from src.tools.google_docs import get_google_docs_tools
        from src.tools.search import get_search_tool
        from src.state import create_initial_state
        
        # Initialize LLM with OpenRouter
        llm = ChatOpenAI(
            model=model_id,
            api_key=st.session_state['openrouter_api_key'],
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/ai-teaching-agent-team",
                "X-Title": "AI Teaching Agent Team"
            }
        )
        
        # Initialize tools
        with st.spinner("🔧 Initializing tools..."):
            # Use MCP if config ID provided (recommended for reliable execution)
            mcp_config_id = st.session_state.get('composio_mcp_config_id', '')
            google_docs_tools = get_google_docs_tools(
                st.session_state['composio_api_key'],
                user_id=st.session_state['composio_user_id'],
                mcp_config_id=mcp_config_id if mcp_config_id else None
            )
            search_tool = get_search_tool(
                use_production=st.session_state['use_production_search'],
                serpapi_key=st.session_state['serpapi_api_key']
            )
        
        # Debug: Show loaded tools
        if google_docs_tools:
            st.success(f"✅ Loaded {len(google_docs_tools)} Google Docs tool(s): {[t.name for t in google_docs_tools]}")
        else:
            st.warning("⚠️ No Google Docs tools loaded. Documents won't be created.")
        
        # Create the graph
        with st.spinner("🔨 Building agent graph..."):
            graph = create_teaching_graph(llm, google_docs_tools, search_tool)
        
        # Initialize state
        initial_state = create_initial_state(topic)
        
        # Execute the graph with progress indicators
        st.markdown("---")
        st.subheader("📊 Agent Progress")
        
        progress_placeholder = st.empty()
        results_container = st.container()
        
        # Track agent execution
        agent_status = {
            "professor": "⏳ Waiting...",
            "academic_advisor": "⏳ Waiting...",
            "research_librarian": "⏳ Waiting...",
            "teaching_assistant": "⏳ Waiting...",
        }
        
        def update_progress():
            with progress_placeholder.container():
                cols = st.columns(4)
                agents = list(agent_status.keys())
                names = ["Professor", "Advisor", "Librarian", "TA"]
                for i, (agent, name) in enumerate(zip(agents, names)):
                    with cols[i]:
                        st.markdown(f"**{name}**")
                        st.markdown(agent_status[agent])
        
        update_progress()
        
        # Stream execution
        final_state = None
        
        for event in graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                if node_name in agent_status:
                    agent_status[node_name] = "🔄 Running..."
                    update_progress()
                    
                    # Mark as complete when done
                    agent_status[node_name] = "✅ Complete"
                    update_progress()
                    
                    # Store output - properly merge google_doc_links
                    if final_state is None:
                        final_state = dict(initial_state)
                    
                    # Merge google_doc_links instead of overwriting
                    if "google_doc_links" in node_output and node_output["google_doc_links"]:
                        current_links = final_state.get("google_doc_links", {})
                        current_links.update(node_output["google_doc_links"])
                        node_output["google_doc_links"] = current_links
                    
                    final_state.update(node_output)
        
        # Debug: Print final google_doc_links
        
        # Display results
        st.markdown("---")
        st.subheader("📋 Results")
        
        # Google Doc links
        if final_state and final_state.get("google_doc_links"):
            st.markdown("### 🔗 Google Doc Links")
            links = final_state["google_doc_links"]
            for agent, link in links.items():
                agent_name = agent.replace("_", " ").title()
                st.markdown(f"- **{agent_name}**: [{link}]({link})")
        
        # Expandable sections for each output
        if final_state:
            with st.expander("📚 Knowledge Base (Professor)", expanded=False):
                st.markdown(final_state.get("knowledge_base", "Not generated"))
            
            with st.expander("🗺️ Learning Roadmap (Academic Advisor)", expanded=False):
                st.markdown(final_state.get("roadmap", "Not generated"))
            
            with st.expander("📖 Learning Resources (Research Librarian)", expanded=False):
                st.markdown(final_state.get("resources", "Not generated"))
            
            with st.expander("✍️ Practice Materials (Teaching Assistant)", expanded=False):
                st.markdown(final_state.get("practice_materials", "Not generated"))
        
        # LangSmith link
        if st.session_state['langsmith_api_key']:
            st.info("📊 View detailed traces at [smith.langchain.com](https://smith.langchain.com)")
        
        st.success("✅ Learning package generated successfully!")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.exception(e)

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.markdown("---")
st.markdown("### 👥 About the Agents")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **🧑‍🏫 Professor**
    - Creates comprehensive knowledge bases
    - Explains concepts from first principles
    - Covers terminology and core principles
    
    **🧑‍🎓 Academic Advisor**
    - Designs structured learning roadmaps
    - Sets progressive milestones
    - Estimates time commitments
    """)

with col2:
    st.markdown("""
    **📚 Research Librarian**
    - Curates high-quality resources
    - Finds tutorials, courses, and docs
    - Rates resources by difficulty
    
    **✏️ Teaching Assistant**  
    - Creates practice exercises
    - Develops quizzes and projects
    - Provides detailed solutions
    """)

st.caption("Built with LangChain, LangGraph, and LangSmith | [View on GitHub](https://github.com/Sim-Security/ai-teaching-agent-team)")
