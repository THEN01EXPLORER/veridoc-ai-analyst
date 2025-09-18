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
    initial_sidebar_state="expanded"
)

# --- STYLES (INJECT CUSTOM CSS) ---
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background-color: #f0f2f6;
    }
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #ffffff;
        border-right: 1px solid #e6e6e6;
    }
    /* Main content styling */
    .main .block-container {
        padding-top: 2rem;
    }
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #1E90FF;
        background-color: #1E90FF;
        color: white;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #0073e6;
        background-color: #0073e6;
        color: white;
    }
    /* Spinner color */
    .stSpinner > div > div {
        border-top-color: #1E90FF;
    }
</style>
""", unsafe_allow_html=True)


# --- SESSION STATE INITIALIZATION ---
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'file_name' not in st.session_state:
    st.session_state.file_name = None

# --- SIDEBAR UI ---
with st.sidebar:
    st.title("VeriDoc.ai")
    st.markdown("### Your AI Whitepaper Analyst")
    
    st.markdown("---")

    uploaded_file = st.file_uploader("Upload a PDF Whitepaper", type="pdf")
    
    if st.button("Analyze Document"):
        if uploaded_file is not None:
            with st.spinner('Processing document... This may take a moment.'):
                try:
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{BACKEND_URL}/upload-whitepaper/", files=files, timeout=300)
                    
                    if response.status_code == 200:
                        st.session_state.session_id = response.json().get("session_id")
                        st.session_state.file_name = uploaded_file.name
                        st.session_state.messages = [{"role": "assistant", "content": f"I've finished analyzing **'{st.session_state.file_name}'**. What are your key questions?"}]
                        st.success("Analysis complete!")
                        st.rerun() # Rerun the script to update the main chat view
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection Error: Is the backend server running? Details: {e}")
        else:
            st.warning("Please upload a PDF file first.")

    st.markdown("---")
    st.header("Go Pro!")
    st.markdown("Unlock powerful features:")
    st.markdown("- Unlimited document uploads")
    st.markdown("- Deeper risk analysis")
    st.markdown("- Compare multiple whitepapers")
    if st.button("Upgrade to Pro (Coming Soon)"):
        st.toast("Pro features are under development. Stay tuned!")


# --- MAIN CHAT INTERFACE ---
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
                    response = requests.post(
                        f"{BACKEND_URL}/ask-question/",
                        json={"session_id": st.session_state.session_id, "query": prompt},
                        timeout=120
                    )
                    if response.status_code == 200:
                        answer = response.json().get("answer", "Sorry, I couldn't find an answer.")
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error(f"API Error: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection Error: Could not reach the backend. Details: {e}")

else:
    st.info("Upload a whitepaper using the sidebar to begin your analysis.")

