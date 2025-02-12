from google import genai
import streamlit as st
from dotenv import load_dotenv
import os
import shelve
import datetime
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Configure page settings
st.set_page_config(
    page_title="PUMA Chatbot",
    page_icon="🐆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .stChatMessage {
        padding: 1.2rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    [data-testid="stChatMessage"][aria-label*="user"] {
        background-color: #FFD70010;
        border: 1px solid #FFD70030;
    }
    [data-testid="stChatMessage"][aria-label*="assistant"] {
        background-color: #00000008;
        border: 1px solid #00000015;
    }
    .stTextInput input {
        border-radius: 20px;
        padding: 12px 20px;
    }
    .stButton button {
        border-radius: 20px;
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: black;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
    }
    .stButton button:hover {
        transform: scale(1.05);
        background-color: #FFD70030;
    }
    .delete-btn {
        color: red;
        cursor: pointer;
    }
    .sidebar-button {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px;
        border: 1px solid rgba(0,0,0,0.1);
        border-radius: 10px;
        background: white;
    }
    .sidebar-button:hover {
        background: #FFD70020;
    }
    [data-testid="stExpander"] > div {
        transition: all 0.3s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

# App Header
col1, col2 = st.columns([1, 4])
with col1:
    st.image("/Users/shuvamghosh/Desktop/ChatBot2/logo.png", width=80)
with col2:
    st.markdown("<h1 style='margin-top: -20px;'>PUMA CHATBOT</h1>", unsafe_allow_html=True)

# Define user and bot avatars
USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

# Initialize the Google GenAI client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Chat session management
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}

if "current_session" not in st.session_state:
    st.session_state.current_session = None

def generate_image(prompt):
    try:
        response = client.generate_images(
            model="gemini-2.0-flash",  # Or another suitable image model
            prompt=prompt,
            image_generation_usecase=genai.ImageGenerationUsecase.ALTERNATIVES,  # Set the correct usecase
            # Add image_generation_spec if needed
        )
        image_bytes = response.images[0].image_bytes
        image = Image.open(io.BytesIO(image_bytes))
        return image
    except Exception as e:
        st.error(f"Image generation failed: {e}")
        return None


# Function to save and load chat history
def save_chat_sessions():
    with shelve.open("chat_sessions_db") as db:
        db["chat_sessions"] = st.session_state.chat_sessions

def load_chat_sessions():
    with shelve.open("chat_sessions_db") as db:
        return db.get("chat_sessions", {})

# Load chat sessions at startup
if not st.session_state.chat_sessions:
    st.session_state.chat_sessions = load_chat_sessions()

# Add a new chat session
def new_chat():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_id = f"Chat {len(st.session_state.chat_sessions) + 1} - {timestamp}"
    st.session_state.chat_sessions[session_id] = []
    st.session_state.current_session = session_id
    save_chat_sessions()

# Update session names based on first prompt
def update_session_names():
    for session_id, messages in st.session_state.chat_sessions.items():
        if messages and "Asking me: " not in session_id:
            first_user_message = next((msg['content'] for msg in messages if msg['role'] == 'user'), None)
            if first_user_message:
                new_session_id = f"Asking me: {first_user_message[:20]}..."  # Shortened prompt for display
                st.session_state.chat_sessions[new_session_id] = st.session_state.chat_sessions.pop(session_id)
                if st.session_state.current_session == session_id:
                    st.session_state.current_session = new_session_id
                save_chat_sessions()

# Delete a chat session
def delete_chat(session_id):
    if session_id in st.session_state.chat_sessions:
        del st.session_state.chat_sessions[session_id]
        # Reset to the first available session or clear if none
        if st.session_state.chat_sessions:
            st.session_state.current_session = list(st.session_state.chat_sessions.keys())[0]
        else:
            st.session_state.current_session = None
        save_chat_sessions()

# Enhanced Sidebar for ChatGPT-like UX
with st.sidebar:
    st.title("💬PUMA Assistant")
    st.button("✨ New Chat", on_click=new_chat, use_container_width=True)
    st.markdown("---")

    # Update session names dynamically
    update_session_names()

    # Active Chats Section
    with st.expander("🟢 Active Chats", expanded=True):
        for session_id in st.session_state.chat_sessions:
            col1, col2 = st.columns([8, 2])
            with col1:
                if st.button(session_id, key=session_id, help=f"Switch to {session_id}", use_container_width=True):
                    st.session_state.current_session = session_id
            with col2:
                if st.button("❌", key=f"delete-{session_id}", help=f"Delete {session_id}"):
                    delete_chat(session_id)
                    st.experimental_rerun()

    st.markdown("---")

    # Archived Chats Section


    st.markdown(
        """
        <div style="text-align: center; margin-top: 20px;">
            <small>Created by <b>Shuvam Ghosh</b></small>
        </div>
        """, unsafe_allow_html=True
    )

# Display chat messages for the current session
if st.session_state.current_session:
    session_id = st.session_state.current_session
    chat_history = st.session_state.chat_sessions[session_id]

    for message in chat_history:
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Chat input and processing
    if prompt := st.chat_input("Ask PUMA Assistant..."):
        chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            response_placeholder = st.empty()
            full_response = ""
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )
                full_response = response.text
            except Exception as e:
                full_response = f"⚠️ Sorry, I encountered an error: {str(e)}"
            response_placeholder.markdown(full_response)

        chat_history.append({"role": "assistant", "content": full_response})
        st.session_state.chat_sessions[session_id] = chat_history
        save_chat_sessions()
else:
    st.write("Start a new chat to begin!")
