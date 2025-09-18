🤖 VeriDoc.ai - Your AI Crypto Whitepaper Analyst

VeriDoc.ai is a powerful, "Vibe Coded" application built for the Seedify Vibecoins Hackathon. It transforms dense, complex crypto whitepapers into conversational AI analysts, making deep due diligence 10x faster and accessible to everyone.

 <!-- We will add this link in a later step -->

🔥 The Problem

The crypto space is full of innovation, but every project comes with a 50-page whitepaper full of technical jargon. For investors, researchers, and even developers, analyzing these documents is a slow, painful, and manual process. This creates a high barrier to entry and makes it easy to miss critical details, leading to poor investment decisions.

✨ The Solution

VeriDoc.ai solves this problem with a simple, elegant solution: Chat with the document.

Upload: Securely upload any crypto whitepaper in PDF format.

Analyze: Our powerful backend, built with FastAPI and LangChain, processes the document, creating an intelligent knowledge base using Pinecone's vector database.

Query: Ask complex questions in plain English—"What is the tokenomics model?", "Explain the consensus mechanism simply," "What are the primary risks mentioned?"—and get instant, accurate answers sourced directly from the document.

🛠️ Tech Stack & "Vibe Coding"

This project was built rapidly using a modern, AI-first stack, fully embracing the "Vibe Coding" philosophy. Our goal is to demonstrate how a solo developer can build a robust, market-ready application in record time.

Backend: FastAPI

AI Orchestration: LangChain

Vector Database: Pinecone

LLMs: OpenAI (GPT-3.5-Turbo, text-embedding-3-small)

Frontend: Streamlit

AI-Assisted Development: All major components, from API endpoints to unit tests, were scaffolded and refactored using LLMs. See our prompts.md file for a full log of our "Vibe Coding" process!

🚀 Getting Started

To run this project locally, follow these steps:

1. Clone the repository:

git clone [https://github.com/THEN01EXPLORER/veridoc-ai-analyst.git](https://github.com/THEN01EXPLORER/veridoc-ai-analyst.git)
cd veridoc-ai-analyst


2. Create and activate the virtual environment:

python -m venv venv
source venv/Scripts/activate


3. Install dependencies:

pip install -r requirements.txt


4. Set up your .env file:
Create a .env file in the root directory and add your secret API keys:

OPENAI_API_KEY="sk-..."
PINECONE_API_KEY="..."
PINECONE_INDEX_NAME="veridoc-index-solo"


5. Run the application:
You need two terminals running simultaneously.

Terminal 1 (Backend): uvicorn main:app --reload

Terminal 2 (Frontend): streamlit run app.py

🎯 Project Vision & Monetization

VeriDoc.ai is designed from the ground up to be a monetizable Micro-SaaS, directly aligning with my goal of launching valuable AI tools. Our vision includes a Pro Tier with features designed for professional investors and analysts:

Unlimited document uploads and history

Advanced risk-detection summaries using fine-tuned models

The ability to compare multiple whitepapers side-by-side

This project is the first step in a mission to build a portfolio of successful, revenue-generating tools for the Web3 and AI ecosystems.