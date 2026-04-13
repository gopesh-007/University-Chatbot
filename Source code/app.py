import streamlit as st
import google.generativeai as genai
import json
import os
from datetime import datetime
import pytz
from database import init_database, get_course_data, save_chat, get_or_create_user_session
import time
from streamlit.components.v1 import html

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

# Particle animation for background
def particle_animation():
    return """
    <style>
        body {
            overflow: hidden;
        }
        #particles-js {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: -1;
        }
    </style>
    <div id="particles-js"></div>
    <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
    <script>
        particlesJS("particles-js", {
            "particles": {
                "number": {
                    "value": 80,
                    "density": {
                        "enable": true,
                        "value_area": 800
                    }
                },
                "color": {
                    "value": "#4a90e2"
                },
                "shape": {
                    "type": "circle",
                    "stroke": {
                        "width": 0,
                        "color": "#000000"
                    },
                    "polygon": {
                        "nb_sides": 5
                    }
                },
                "opacity": {
                    "value": 0.5,
                    "random": false,
                    "anim": {
                        "enable": false,
                        "speed": 1,
                        "opacity_min": 0.1,
                        "sync": false
                    }
                },
                "size": {
                    "value": 3,
                    "random": true,
                    "anim": {
                        "enable": false,
                        "speed": 40,
                        "size_min": 0.1,
                        "sync": false
                    }
                },
                "line_linked": {
                    "enable": true,
                    "distance": 150,
                    "color": "#4a90e2",
                    "opacity": 0.4,
                    "width": 1
                },
                "move": {
                    "enable": true,
                    "speed": 2,
                    "direction": "none",
                    "random": false,
                    "straight": false,
                    "out_mode": "out",
                    "bounce": false,
                    "attract": {
                        "enable": false,
                        "rotateX": 600,
                        "rotateY": 1200
                    }
                }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {
                    "onhover": {
                        "enable": true,
                        "mode": "grab"
                    },
                    "onclick": {
                        "enable": true,
                        "mode": "push"
                    },
                    "resize": true
                },
                "modes": {
                    "grab": {
                        "distance": 140,
                        "line_linked": {
                            "opacity": 1
                        }
                    },
                    "bubble": {
                        "distance": 400,
                        "size": 40,
                        "duration": 2,
                        "opacity": 8,
                        "speed": 3
                    },
                    "repulse": {
                        "distance": 200,
                        "duration": 0.4
                    },
                    "push": {
                        "particles_nb": 4
                    },
                    "remove": {
                        "particles_nb": 2
                    }
                }
            },
            "retina_detect": true
        });
    </script>
    """

# Add the particle animation to the page
html(particle_animation(), height=0)

if not st.session_state.authenticated:
    # Custom login/signup page with animations
    st.markdown("""
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .auth-container {
            animation: fadeIn 0.8s ease-out;
            background: rgba(255, 255, 255, 0.9);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(8px);
            margin: auto;
            max-width: 500px;
        }
        .auth-title {
            color: #4a90e2;
            text-align: center;
            margin-bottom: 1.5rem;
            font-size: 2rem;
        }
        .auth-button {
            background: linear-gradient(45deg, #4a90e2, #8e44ad);
            color: white !important;
            border: none;
            border-radius: 25px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s;
            width: 100%;
            margin-top: 1rem;
        }
        .auth-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(74, 144, 226, 0.4);
        }
        .toggle-auth {
            text-align: center;
            margin-top: 1rem;
            color: #666;
        }
        .toggle-button {
            background: transparent;
            border: none;
            color: #4a90e2;
            cursor: pointer;
            text-decoration: underline;
            font-weight: 600;
        }
        input[type="text"], input[type="password"] {
            border-radius: 25px !important;
            padding: 10px 15px !important;
            border: 1px solid #ddd !important;
            transition: all 0.3s !important;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            border-color: #4a90e2 !important;
            box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            st.markdown('<h1 class="auth-title">\U0001F512 University Course Assistant</h1>', unsafe_allow_html=True)
            
            if st.session_state.signup_mode:
                st.markdown('<h3 style="text-align: center; color: #333;">Create a New Account</h3>', unsafe_allow_html=True)
                new_user = st.text_input("Choose a Username", key="new_user")
                new_pass = st.text_input("Choose a Password", type="password", key="new_pass")
                
                if st.button("Sign Up", key="signup_btn"):
                    if new_user and new_pass:
                        save_user(new_user, new_pass)
                        st.success("Account created! You can now log in.")
                        st.session_state.signup_mode = False
                        st.rerun()
                    else:
                        st.error("Please enter both username and password.")
                
                st.markdown('<div class="toggle-auth">Already have an account? <button class="toggle-button" onclick="window.streamlitSessionState.set({signup_mode: false}); window.streamlitSessionState.rerun()">Login</button></div>', unsafe_allow_html=True)
            else:
                st.markdown('<h3 style="text-align: center; color: #333;">Login to Continue</h3>', unsafe_allow_html=True)
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                
                if st.button("Login", key="login_btn"):
                    if check_login(username, password):
                        st.success("Login successful! \U0001F389")
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                
                st.markdown('<div class="toggle-auth">Don\'t have an account? <button class="toggle-button" onclick="window.streamlitSessionState.set({signup_mode: true}); window.streamlitSessionState.rerun()">Sign Up</button></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# ---------- Application Logic ----------

# Configure Gemini AI
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Initialize database and get user session
init_database()
user_id = get_or_create_user_session()

# Logout button with animation
if st.sidebar.button("Logout \U0001F513"):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.markdown(f"""
    <div style="background: rgba(255,255,255,0.9); padding: 1rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <p style="color: #4a90e2; font-weight: 600; margin-bottom: 0;">\U0001F464 Logged in as:</p>
        <p style="font-size: 1.1rem; font-weight: bold; margin-top: 0;">{st.session_state.username}</p>
    </div>
""", unsafe_allow_html=True)

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
    :root {
        --primary-color: #4a90e2;
        --secondary-color: #8e44ad;
        --accent-color: #2ecc71;
    }
    
    /* Main container */
    .main {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
        color: white;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        border: none;
        height: 42px;
        margin-top: 6%;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(74, 144, 226, 0.4);
    }
    
    /* Input fields */
    .stTextInput>div>div>input {
        border-radius: 25px !important;
        padding: 12px 15px !important;
        border: 1px solid #ddd !important;
        transition: all 0.3s !important;
        height: 42px !important;
    }
    .stTextInput>div>div>input:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        display: flex;
        flex-direction: column;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .user-message {
        background: linear-gradient(135deg, rgba(74, 144, 226, 0.1), rgba(142, 68, 173, 0.1));
        border-left: 4px solid var(--primary-color);
    }
    .bot-message {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(245, 245, 245, 0.9));
        border-left: 4px solid var(--accent-color);
    }
    .timestamp {
        color: #999;
        font-size: 0.8em;
        margin-top: 8px;
        align-self: flex-end;
    }
    
    /* Example questions */
    .example-question {
        background: rgba(255, 255, 255, 0.9);
        padding: 12px 15px;
        margin: 8px 0;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 3px solid var(--primary-color);
    }
    .example-question:hover {
        background: rgba(74, 144, 226, 0.1);
        transform: translateX(5px);
        box-shadow: 0 5px 15px rgba(74, 144, 226, 0.1);
    }
    
    /* Sidebar sections */
    .sidebar-section {
        background: rgba(255, 255, 255, 0.9);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    .sidebar-section:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    .sidebar-header {
        color: var(--primary-color);
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(74, 144, 226, 0.2);
    }
    .sidebar-link {
        display: block;
        padding: 0.5rem 0;
        color: #666;
        text-decoration: none;
        border-radius: 5px;
        transition: all 0.3s;
    }
    .sidebar-link:hover {
        color: var(--primary-color);
        transform: translateX(5px);
    }
    
    /* Title and divider */
    .title-container {
        text-align: center;
        margin-bottom: 2rem;
    }
    .title {
        color: var(--primary-color);
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .divider {
        height: 3px;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border: none;
        border-radius: 3px;
        margin: 0 auto;
        width: 50%;
    }
    
    /* Input container */
    .input-container {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar with enhanced UI
with st.sidebar:
    st.image("./Resources/Logo.png", use_container_width=True)
    st.markdown("""
        <div class="sidebar-section fade-in">
            <div class="sidebar-header">\U0001F44B Welcome!</div>
            <p style="color: #555;">I'm your AI assistant here to guide you through our academic programs and answer all your admission questions.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="sidebar-section fade-in">
            <div class="sidebar-header">\U0001F4AD Quick Questions</div>
    """, unsafe_allow_html=True)
    for question in example_questions:
        if st.button(f"\U0001F539 {question}", key=f"btn_{question}", help="Click to ask this question", use_container_width=True):
            set_question(question)
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="sidebar-section fade-in">
            <div class="sidebar-header">\U0001F517 Quick Links</div>
            <a href="#" class="sidebar-link">\U0001F4DA University Website</a>
            <a href="#" class="sidebar-link">\U0001F393 Admission Portal</a>
            <a href="#" class="sidebar-link">\U0001F464 Student Dashboard</a>
            <a href="#" class="sidebar-link">\U0001F4C3 Course Catalog</a>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="sidebar-section fade-in">
            <div class="sidebar-header">\U0001F4DE Contact Support</div>
            <p style="color: #555;">\U0001F4DE <b>Helpline:</b> 1800-XXX-XXXX</p>
            <p style="color: #555;">\U0001F4E7 <b>Email:</b> admissions@university.edu</p>
            <p style="color: #555;">\U0001F4CD <b>Address:</b> 123 University Ave, Campus City</p>
        </div>
    """, unsafe_allow_html=True)

# Chat interface with enhanced UI
st.markdown("""
    <div class="title-container fade-in">
        <h1 class="title">\U0001F393 University Course Assistant</h1>
        <hr class="divider">
    </div>
""", unsafe_allow_html=True)

chat_container = st.container()

# Display chat history with animations
for i, message_data in enumerate(st.session_state.chat_history):
    with chat_container:
        if len(message_data) == 3:
            user, bot, timestamp = message_data
        else:
            user, bot = message_data
            timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M')
        
        # User message
        st.markdown(f"""
            <div class="chat-message user-message fade-in" style="animation-delay: {i * 0.1}s;">
                <strong style="color: var(--primary-color);">You:</strong> 
                <div style="margin-top: 8px;">{user}</div>
                <div class="timestamp">{timestamp}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Bot message
        st.markdown(f"""
            <div class="chat-message bot-message fade-in" style="animation-delay: {i * 0.1 + 0.2}s;">
                <strong style="color: var(--accent-color);">Assistant:</strong>
                <div style="margin-top: 8px;">{bot}</div>
                <div class="timestamp">{timestamp}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Input area with perfect alignment
input_container = st.container()
with input_container:
    col1, col2 = st.columns([6, 1])  # Adjusted column ratio
    
    with col1:
        user_input = st.text_input(
            "Ask your question here...", 
            value=st.session_state.current_question, 
            key="input", 
            placeholder="e.g., What courses do you offer?",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)  # Vertical alignment helper
        send_button = st.button(
            "Send \U0001F680", 
            use_container_width=True,
            help="Send your question to the assistant"
        )

if send_button and user_input:
    with st.spinner('\U0001F4AC Generating response...'):
        ai_response = get_ai_response(user_input)
        current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M')
        st.session_state.chat_history.append((user_input, ai_response, current_time))
        st.session_state.current_question = ""
        st.rerun()

# Add some JavaScript for smooth scrolling
html("""
<script>
    // Smooth scroll to bottom of chat
    function scrollToBottom() {
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    // Scroll to bottom when page loads
    window.addEventListener('load', function() {
        setTimeout(scrollToBottom, 500);
    });
    
    // Scroll to bottom when new messages are added
    window.streamlitSessionState = window.parent.document.querySelector('iframe').contentWindow.streamlitSessionState;
    window.streamlitSessionState.rerun = function() {
        window.parent.document.querySelector('iframe').contentWindow.streamlit.rerun();
        setTimeout(scrollToBottom, 300);
    }
</script>
""")