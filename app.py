import streamlit as st
import requests

# --- CONFIGURATION ---
BACKEND_URL = "http://127.0.0.1:8000"

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="VeriDoc AI Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE ---
defaults = {
    "token": None,
    "session_id": None,
    "messages": [],
    "file_name": None,
    "user_email": None
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- AUTHENTICATION LOGIC ---
def show_login_signup():
    st.header("Welcome to VeriDoc.ai")
    st.markdown("Your AI-powered assistant for deep-diving into crypto whitepapers. Login or create an account to get started.")

    menu = ["Login", "Sign Up"]
    choice = st.radio("Choose an option", menu, horizontal=True)

    if choice == "Login":
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/auth/login",
                        data={"username": email, "password": password}
                    )
                    if response.status_code == 200:
                        st.session_state.token = response.json().get("access_token")
                        st.session_state.user_email = email
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to login: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

    elif choice == "Sign Up":
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign Up")
            if submitted:
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/auth/signup",
                        json={"email": email, "password": password}
                    )
                    if response.status_code == 200:
                        st.session_state.token = response.json().get("access_token")
                        st.session_state.user_email = email
                        st.success("Account created! You are now logged in.")
                        st.rerun()
                    else:
                        st.error(f"Failed to sign up: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

# --- MAIN APP LOGIC ---
def show_main_app():
    with st.sidebar:
        st.title("VeriDoc.ai")
        st.markdown(f"Welcome, **{st.session_state.user_email}**")
        st.markdown("---")
        uploaded_file = st.file_uploader("Upload a PDF Whitepaper", type="pdf")
        if st.button("Analyze Document"):
            if uploaded_file is not None:
                with st.spinner('Processing document...'):
                    try:
                        files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        headers = {"Authorization": f"Bearer {st.session_state.token}"}
                        response = requests.post(
                            f"{BACKEND_URL}/upload-whitepaper/", files=files, headers=headers
                        )
                        if response.status_code == 200:
                            st.session_state.session_id = response.json().get("session_id")
                            st.session_state.file_name = uploaded_file.name
                            st.session_state.messages = [{
                                "role": "assistant",
                                "content": f"I've analyzed **'{st.session_state.file_name}'**. What would you like to know?"
                            }]
                            st.success("Analysis complete!")
                            st.rerun()
                        else:
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")
            else:
                st.warning("Please upload a PDF file first.")

        st.markdown("---")
        if st.button("Logout"):
            for key in defaults:
                st.session_state[key] = defaults[key]
            st.rerun()

    st.header(f"Chat with VeriDoc about: `{st.session_state.file_name or 'Your Document'}`")

    if st.session_state.session_id:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about tokenomics, technology, risks..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.token}"}
                        response = requests.post(
                            f"{BACKEND_URL}/ask-question/",
                            json={"session_id": st.session_state.session_id, "query": prompt},
                            headers=headers
                        )
                        if response.status_code == 200:
                            answer = response.json().get("answer", "No answer found.")
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        else:
                            st.error(f"API Error: {response.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")
    else:
        st.info("Upload a whitepaper using the sidebar to begin your analysis.")

# --- ROUTER ---
if st.session_state.token:
    show_main_app()
else:
    show_login_signup()
