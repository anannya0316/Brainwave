import streamlit as st
from PyPDF2 import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI
# Load API Key
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# Initialize Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY
)

# Function to extract text from PDF
def extract_text_from_pdfs(pdf_files):
    full_text = ""

    for pdf_file in pdf_files:
        pdf_reader = PdfReader(pdf_file)

        for page in pdf_reader.pages:
            page_text = page.extract_text()

            if page_text is not None:
                full_text += page_text + "\n"

    return full_text.strip()


# Function to summarize text using Gemini
def summarize_text(text):

    prompt = f"""
    Summarize the following document.

    Return the summary as:
    - Bullet points
    - Covering the key ideas
    - Add emojis where useful

    TEXT:
    {text}
    """

    response = llm.invoke(prompt)

    return response.content


# Streamlit UI
st.title("🚀 Document Summarizer")

pdf_files = st.file_uploader(
    "Upload PDF files",
    type="pdf",
    accept_multiple_files=True
)

if pdf_files:

    if st.button("Generate Summary"):

        with st.spinner("Reading PDFs..."):
            text = extract_text_from_pdfs(pdf_files)

        if len(text) == 0:
            st.error("⚠️ Could not extract text from this PDF.")
            st.stop()

        with st.spinner("Generating summary..."):
            summary = summarize_text(text[:20000])

        st.subheader("📄 Summary")
        st.write(summary)