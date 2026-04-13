import streamlit as st
import google.generativeai as genai
import json
import os
from datetime import datetime
import pytz
from database import init_database, get_course_data, save_chat, get_or_create_user_session

# ---------- User Authentication ----------
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def check_login(username, password):
    users = load_users()
    return users.get(username) == password

# State management
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'signup_mode' not in st.session_state:
    st.session_state.signup_mode = False

if not st.session_state.authenticated:
    st.title("\U0001F512 University Course Assistant")

    # Switch between Sign Up and Log In
    if st.session_state.signup_mode:
        st.subheader("Create a New Account")
        new_user = st.text_input("Choose a Username")
        new_pass = st.text_input("Choose a Password", type="password")
        if st.button("Sign Up"):
            if new_user and new_pass:
                save_user(new_user, new_pass)
                st.success("Account created! You can now log in.")
                st.session_state.signup_mode = False
                st.rerun()
            else:
                st.error("Please enter both username and password.")
        if st.button("Already have an account? Login"):
            st.session_state.signup_mode = False
            st.rerun()
    else:
        st.subheader("Login to Continue")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if check_login(username, password):
                st.success("Login successful! \U0001F389")
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password.")
        if st.button("Don't have an account? Sign Up"):
            st.session_state.signup_mode = True
            st.rerun()

    st.stop()

# ---------- Application Logic ----------

# Configure Gemini AI
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Initialize database and get user session
init_database()
user_id = get_or_create_user_session()

# Logout button
if st.sidebar.button("Logout \U0001F513"):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.markdown(f"\U0001F464 Logged in as: **{st.session_state.username}**")

# Load course data
data = {"courses": get_course_data()}

context = f"""
You are a helpful university admission counselor chatbot. You have information about the following courses:

{json.dumps(data, indent=2)}

Key points to remember:
1. Always be polite and professional
2. Provide accurate information about courses based on the data provided
3. Handle general queries and greetings naturally
4. If asked about information not in the data, politely say you can only provide information about the listed courses
5. Keep responses concise but informative
6. Use appropriate emojis to make responses engaging
7. Format responses using markdown for better readability
"""

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""
if 'chat' not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

def get_ai_response(user_input):
    try:
        prompt = f"Context: {context}\n\nUser: {user_input}\n\nResponse:"
        response = st.session_state.chat.send_message(prompt)
        save_chat(user_input, response.text)
        return response.text
    except Exception as e:
        st.error("An error occurred while getting a response from the AI. Please try again.")
        return f"I apologize, but I encountered an error: {str(e)}"

example_questions = [
    "Hi! Can you help me with course information?",
    "What courses do you offer?",
    "Tell me about B.Tech program",
    "What is the fee structure for BCA?",
    "What subjects are taught in B.Sc first semester?",
    "How long is the B.Tech program?",
    "What are the subjects in BCA?",
    "Tell me about admission process",
    "What is the duration of B.Sc?",
    "Can you compare B.Tech and BCA programs?"
]

def set_question(question):
    st.session_state.current_question = question

# UI Styling
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stButton>button { background-color: #000000; color: white; border-radius: 20px; padding: 0.5rem 2rem; border: none; height: 42px; margin-top: 6%; }
    .stTextInput>div>div>input { border-radius: 20px; }
    .chat-message { padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; display: flex; flex-direction: column; }
    .user-message { background-color: #E3F2FD; }
    .bot-message { background-color: #F5F5F5; }
    .timestamp { color: gray; font-size: 0.8em; margin-top: 8px; }
    .example-question { background-color: #f8f9fa; padding: 8px 12px; margin: 4px 0; border-radius: 5px; cursor: pointer; transition: all 0.3s; }
    .example-question:hover { background-color: #e9ecef; transform: translateX(5px); }
    .sidebar-section { background-color: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .sidebar-header { color: #333; font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #f0f0f0; }
    .sidebar-link { display: block; padding: 0.5rem; color: #666; text-decoration: none; border-radius: 5px; transition: all 0.3s; }
    .sidebar-link:hover { background-color: #f8f9fa; color: #0066cc; }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("./Resources/Logo.png", use_container_width=True)
    st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-header">\U0001F44B Welcome!</div>
            <p>I'm here to help you explore our academic programs and answer your questions about admissions.</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-header">\U0001F4AD Example Questions</div>
    """, unsafe_allow_html=True)
    for question in example_questions:
        if st.button(f"\U0001F539 {question}", key=f"btn_{question}", help="Click to ask this question", use_container_width=True):
            set_question(question)
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-header">\U0001F517 Quick Links</div>
            <a href="#" class="sidebar-link">\U0001F4DA University Website</a>
            <a href="#" class="sidebar-link">\U0001F393 Admission Portal</a>
            <a href="#" class="sidebar-link">\U0001F464 Student Dashboard</a>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-header">\U0001F4DE Contact Support</div>
            <p>\U0001F4DE Helpline: 1800-XXX-XXXX</p>
            <p>\U0001F4E7 Email: admissions@university.edu</p>
        </div>
    """, unsafe_allow_html=True)

# Chat interface
st.title("\U0001F393 University Course Assistant")
st.markdown("---")
chat_container = st.container()

for message_data in st.session_state.chat_history:
    with chat_container:
        col1, col2 = st.columns([6, 4])
        if len(message_data) == 3:
            user, bot, timestamp = message_data
        else:
            user, bot = message_data
            timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M')

        with col1:
            st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {user}
                </div>
            """, unsafe_allow_html=True)
            st.caption(timestamp)
        with col2:
            st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>Assistant:</strong>
                    {bot}</div>
            """, unsafe_allow_html=True)
            st.caption(timestamp)

st.markdown("---")
input_col1, input_col2 = st.columns([5, 2])
with input_col1:
    user_input = st.text_input("Ask your question here...", value=st.session_state.current_question, key="input", placeholder="e.g., What courses do you offer?")
with input_col2:
    st.text(" ")
    send_button = st.button("Send📤", use_container_width=True)

if send_button and user_input:
    ai_response = get_ai_response(user_input)
    current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M')
    st.session_state.chat_history.append((user_input, ai_response, current_time))
    st.session_state.current_question = ""
    st.rerun()
