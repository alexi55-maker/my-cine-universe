import streamlit as st
import requests
import sqlite3
import random
import pandas as pd

# 1. Configuration - აუცილებელია layout="wide" მთლიანი ეკრანისთვის
st.set_page_config(page_title="CineBook Universe", layout="wide", initial_sidebar_state="expanded")

API_KEY = "976001f454c4d2d5a392e8bbad9237d1"

# --- 2. Database Functions ---
def init_db():
    conn = sqlite3.connect('universe.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, xp INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS articles (author TEXT, title TEXT, content TEXT, category TEXT)')
    conn.commit()
    conn.close()

def update_xp(username, amount):
    conn = sqlite3.connect('universe.db')
    c = conn.cursor()
    c.execute("UPDATE users SET xp = xp + ? WHERE username = ?", (amount, username))
    conn.commit()
    conn.close()

init_db()

# --- 3. CSS for Full Screen & Styling ---
st.markdown("""
    <style>
    /* აშორებს ზედმეტ სივრცეებს გვერდებიდან და ზემოდან */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    
    .stApp { background-color: #0a0e14; color: white; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { background-color: #111827 !important; min-width: 280px !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: #1f2937 !important; border: 2px solid #3b82f6 !important;
        border-radius: 10px !important; margin-bottom: 10px !important; padding: 12px !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label p { color: white !important; font-size: 18px !important; font-weight: 800; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    
    /* Content Cards */
    .game-card { background: #1f2937; padding: 25px; border-radius: 15px; border: 1px solid #3b82f6; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. Helper Functions ---
def get_tmdb(path, params={}):
    params['api_key'] = API_KEY
    return requests.get(f"https://api.themoviedb.org/3/{path}", params=params).json()

def get_books(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10"
    try: return requests.get(url).json().get('items', [])
    except: return []

# --- 5. Logic & Navigation ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

q = st.query_params
if "id" in q:
    # --- Detail Page ---
    if st.button("⬅️ Back to Universe"): st.query_params.clear(); st.rerun()
    m_type = q.get("type", "movie")
    
    if m_type in ["movie", "tv"]:
        data = get_tmdb(f"{m_type}/{q['id']}")
        col1, col2 = st.columns([1, 2])
        with col1:
            if data.get('poster_path'): st.image(f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}", use_container_width=True)
        with col2:
            st.title(data.get('title') or data.get('name'))
            st.write(data.get('overview'))
            st.slider("Rate this story", 1, 5, 3, key=f"rate_{q['id']}")
            if st.button("Save Rating"):
                if st.session_state.logged_in: 
                    update_xp(st.session_state.username, 5)
                    st.success("Points added to your profile!")
    elif m_type == "book":
        st.title("Book Details")
        st.info("Book detail view is under construction, but you can read it in the Library!")

else:
    # --- Sidebar Navigation ---
    page = st.sidebar.radio("", ["🏠 Home", "📺 Series", "📚 Books", "✍️ Articles", "🎮 Games", "👤 Profile"])

    if page == "🏠 Home":
        st.title("🍿 Trending Movies")
        res = get_tmdb("movie/popular").get('results', [])[:12]
        cols = st.columns(6) # 6 სვეტი მთლიან ეკრანზე გადასანაწილებლად
        for i, m in enumerate(res):
            with cols[i%6]:
                st.image(f"https://image.tmdb.org/t/p/w500{m['poster_path']}", use_container_width=True)
                if st.button("Details", key=f"m_{m['id']}"):
                    st.query_params.id, st.query_params.type = m['id'], "movie"; st.rerun()

    elif page == "📺 Series":
        st.title("📺 Top Series")
        res = get_tmdb("tv/popular").get('results', [])[:12]
        cols = st.columns(6)
        for i, s in enumerate(res):
            with cols[i%6]:
                st.image(f"https://image.tmdb.org/t/p/w500{s['poster_path']}", use_container_width=True)
                if st.button("Details", key=f"s_{s['id']}"):
                    st.query_params.id, st.query_params.type = s['id'], "tv"; st.rerun()

    elif page == "📚 Books":
        st.title("📚 Library Highlights")
        books = get_books("subject:fiction")
        cols = st.columns(5)
        for i, b in enumerate(books):
            with cols[i%5]:
                img = b['volumeInfo'].get('imageLinks', {}).get('thumbnail')
                if img: st.image(img, use_container_width=True)
                st.caption(b['volumeInfo'].get('title')[:35])

    elif page == "🎮 Games":
        st.title("🎮 Arcade & Games")
        if not st.session_state.logged_in:
            st.warning("Please Login in Profile to play games!")
        else:
            game = st.selectbox("Select a Game to Start:", ["Choose...", "Blind Date", "Character Match", "Movie Quiz"])
            
            if game == "Blind Date":
                st.subheader("Guess the Movie Plot")
                if 'bm' not in st.session_state:
                    st.session_state.bm = random.choice(get_tmdb("movie/top_rated").get('results', []))
                m = st.session_state.bm
                st.info(f"Plot: {m['overview'][:250]}...")
                guess = st.text_input("Title:")
                if st.button("Check"):
                    if guess.lower() in m['title'].lower() and guess != "":
                        st.success("Perfect! +15 XP"); update_xp(st.session_state.username, 15)
                    else:
                        st.error(f"It was: {m['title']}")
                        st.image(f"https://image.tmdb.org/t/p/w500{m['poster_path']}", width=200)
                if st.button("New Game"): del st.session_state.bm; st.rerun()

            elif game == "Character Match":
                st.subheader("Legendary Soulmate Quiz")
                with st.form("c_match"):
                    q1 = st.radio("Your Vibe:", ["Dark & Mysterious", "Noble & Brave", "Independent & Smart"])
                    if st.form_submit_button("Reveal My Character"):
                        res = {"Dark & Mysterious": ["Batman", "https://image.tmdb.org/t/p/w500/86pUjm97wU6nzCs7YjQnZnJvI7P.jpg"],
                               "Noble & Brave": ["Aragorn", "https://image.tmdb.org/t/p/w500/7cn96S7997v6U8690v7ny986UN.jpg"]}
                        char = res.get(q1, ["Elizabeth Bennet", "https://image.tmdb.org/t/p/w500/pA2fUnf2tD7q2j5w1P7C1v5EAn9.jpg"])
                        st.header(char[0]); st.image(char[1], width=300)
                        update_xp(st.session_state.username, 10)

    elif page == "✍️ Articles":
        st.title("✍️ Writing Studio")
        # Articles logic stays here...

    elif page == "👤 Profile":
        st.title("👤 Your Identity")
        if not st.session_state.logged_in:
            u = st.text_input("New Username:")
            if st.button("Create Account"):
                conn = sqlite3.connect('universe.db')
                conn.execute("INSERT OR IGNORE INTO users (username, xp) VALUES (?, 0)", (u,))
                conn.commit(); conn.close()
                st.session_state.logged_in = True; st.session_state.username = u; st.rerun()
        else:
            conn = sqlite3.connect('universe.db')
            xp = conn.execute("SELECT xp FROM users WHERE username=?", (st.session_state.username,)).fetchone()[0]
            st.header(f"Welcome back, {st.session_state.username}!")
            st.metric("Current XP", f"{xp} points")
            
            st.write("---")
            st.subheader("🏆 Global Leaderboard")
            leaders = pd.read_sql_query("SELECT username, xp FROM users ORDER BY xp DESC LIMIT 5", conn)
            st.table(leaders)
            conn.close()
            if st.button("Logout"): st.session_state.logged_in = False; st.rerun()