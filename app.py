import os
import streamlit as st
import fitz  # PyMuPDF
from groq import Groq
from dotenv import load_dotenv

# Load env
load_dotenv()

# Init Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="Chatbot Documenti", page_icon="📄")
st.title("📄 Chatbot su Documenti")

# -----------------------
# Sidebar
# -----------------------
st.sidebar.header("📎 Carica documento")
uploaded_file = st.sidebar.file_uploader(
    "PDF o TXT", type=["pdf", "txt"]
)

if st.sidebar.button("🗑️ Reset chat"):
    st.session_state.messages = []

# -----------------------
# Utils
# -----------------------
def extract_text(file):
    if file.type == "application/pdf":
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    else:
        return file.read().decode("utf-8")

# -----------------------
# Session state
# -----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "document_text" not in st.session_state:
    st.session_state.document_text = None

# -----------------------
# Documento
# -----------------------
if uploaded_file:
    st.session_state.document_text = extract_text(uploaded_file)

    st.sidebar.success("Documento caricato!")
    st.sidebar.text_area(
        "Anteprima documento",
        st.session_state.document_text[:2000],
        height=200
    )

# -----------------------
# Chat UI
# -----------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Fai una domanda sul documento o chiedi un riassunto")

if prompt:
    # User message
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # Costruzione prompt con documento
    messages = []

    if st.session_state.document_text:
        messages.append({
            "role": "system",
            "content": (
                "Sei un assistente AI specializzato nell'analisi di documenti.\n"
                "Rispondi alle domande dell’utente utilizzando ESCLUSIVAMENTE "
                "le informazioni presenti nel documento fornito.\n\n"
                "Se l’informazione richiesta non è presente nel documento, "
                "rispondi chiaramente: \"L'informazione non è presente nel documento\".\n\n"
                f"DOCUMENTO:\n{st.session_state.document_text[:12000]}"
            )
        })

    messages.extend(st.session_state.messages)

    # LLM response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            stream=True
        )

        for chunk in completion:
            token = chunk.choices[0].delta.content
            if token:
                full_response += token
                placeholder.markdown(full_response)

    # Salva risposta completa
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )

