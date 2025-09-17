import streamlit as st
import requests
import time

# --- CONFIGURATION ---
BACKEND_URL = "http://127.0.0.1:8000"

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="VeriDoc AI Analyst",
    page_icon="🤖",
    layout="wide",
)

# --- STYLES ---
st.markdown("""
<style>
    .stSpinner > div > div {
        border-top-color: #00BFFF;
    }
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #00BFFF;
        background-color: transparent;
        color: #00BFFF;
    }
    .stButton>button:hover {
        border: 1px solid #00BFFF;
        background-color: #00BFFF;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- UI COMPONENTS ---
st.title("🤖 VeriDoc AI Analyst")
st.caption("Your personal AI assistant for analyzing crypto whitepapers.")

with st.sidebar:
    st.header("Upload Your Whitepaper")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Analyze Document"):
            with st.spinner('Processing document... This may take a moment.'):
                try:
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{BACKEND_URL}/upload-whitepaper/", files=files, timeout=300)
                    
                    if response.status_code == 200:
                        st.session_state.session_id = response.json().get("session_id")
                        st.session_state.messages = [{"role": "assistant", "content": f"I've finished reading '{uploaded_file.name}'. What would you like to know?"}]
                        st.success("Document analyzed successfully!")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: Could not connect to the backend. Please ensure the server is running. Details: {e}")

    st.markdown("---")
    st.info("Built for the Seedify Vibecoins Hackathon by Krishnav Mahajan.")

# --- CHAT INTERFACE ---
if st.session_state.session_id:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask a question about the document..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/ask-question/",
                    json={"session_id": st.session_state.session_id, "query": prompt},
                    timeout=120
                )
                if response.status_code == 200:
                    answer = response.json().get("answer", "Sorry, I couldn't find an answer.")
                    # Display assistant response in chat message container
                    with st.chat_message("assistant"):
                        st.markdown(answer)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"Error from API: {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: Could not get an answer from the backend. Details: {e}")
else:
    st.info("Please upload a whitepaper to begin the analysis.")