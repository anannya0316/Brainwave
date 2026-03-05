import streamlit as st
from streamlit_chat import message
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
import tempfile
import os
import uuid

st.title("🤖💬 Chat with Data")

tab1, tab2 = st.tabs(["Chat with PDF", "Chat with Website"])

groq_api_key = st.secrets["GROQ_API_KEY"]
llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.1-8b-instant")


# Initialize session state
def init_session_state(prefix):
    if f"{prefix}_responses" not in st.session_state:
        st.session_state[f"{prefix}_responses"] = ["How can I assist you?"]
    if f"{prefix}_requests" not in st.session_state:
        st.session_state[f"{prefix}_requests"] = []


# Load and process documents
def load_and_process_data(loader):

    if isinstance(loader, PyPDFLoader):
        documents = loader.load_and_split()
    else:
        documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150
    )

    splits = splitter.split_documents(documents)

    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    vectordb = FAISS.from_documents(splits, embeddings)

    return vectordb


# Chat interface
def chat_interface(vectordb, input_key, prefix):

    init_session_state(prefix)

    response_container = st.container()
    textcontainer = st.container()

    with textcontainer:
        query = st.chat_input("Ask something...", key=input_key)

        if query:

            with st.spinner("Thinking..."):

                docs = vectordb.similarity_search(query, k=4)

                context = "\n".join([doc.page_content for doc in docs])

                prompt = f"""
                Use the following context to answer the question.

                Context:
                {context}

                Question: {query}

                Answer in maximum 3 sentences.
                """

                response = llm.invoke(prompt).content

            st.session_state[f"{prefix}_requests"].append(query)
            st.session_state[f"{prefix}_responses"].append(response)

    with response_container:

        if st.session_state[f"{prefix}_responses"]:

            for i in range(len(st.session_state[f"{prefix}_responses"])):

                key_id = str(uuid.uuid4())

                message(
                    st.session_state[f"{prefix}_responses"][i],
                    key=f"response_{prefix}_{key_id}"
                )

                if i < len(st.session_state[f"{prefix}_requests"]):
                    message(
                        st.session_state[f"{prefix}_requests"][i],
                        is_user=True,
                        key=f"request_{prefix}_{key_id}"
                    )


# PDF TAB
with tab1:

    file = st.file_uploader("Upload PDF File", type=["pdf"])
    submit_pdf = st.checkbox("Submit and chat (PDF)")

    if submit_pdf and file is not None:

        try:

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file.read())
                file_path = temp_file.name

            loader = PyPDFLoader(file_path)

            vectordb = load_and_process_data(loader)

            chat_interface(vectordb, "input_pdf", "pdf")

        except Exception as e:
            st.error(f"Error: {e}")

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    elif submit_pdf:
        st.warning("Please upload a PDF file.")


# WEBSITE TAB
with tab2:

    url = st.text_input("Enter website URL:")
    submit_url = st.checkbox("Submit and chat (URL)")

    if submit_url and url:

        try:

            loader = WebBaseLoader(url)

            vectordb = load_and_process_data(loader)

            chat_interface(vectordb, "input_url", "url")

        except Exception as e:
            st.error(f"Error: {e}")

    elif submit_url:
        st.warning("Please enter a website URL.")