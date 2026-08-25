import os
import streamlit as st
import PyPDF2  
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
 
load_dotenv()
 
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
 
 
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdfreader = PdfReader(pdf)
        for page in pdfreader.pages:
            text += page.extract_text()
    return text
 
def get_text_splitter(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=10000,
        chunk_overlap=1000,
        length_function=len
    )
    return text_splitter.split_text(text)
 
def get_vector_store(texts):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(texts, embedding = embeddings)
    vector_store.save_local("faiss_index")
 
 
def get_chat_chain():
    template = """
    You are a helpful assistant.
    You are given the following extracted parts of a long document and a question.
    You should answer the question based on the context provided.
    If you can't find the answer in the context, just say "Hmm, I'm not sure."
    Context: \n{context}\n
    Question: \n{question}\n
    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain
 
def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
 
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question, k=1)
   
    chain = get_chat_chain()
 
    response = chain({"input_documents":docs, "question": user_question},
                     return_only_outputs=True)
   
    print(response)
    st.write("Reply: ", response["output_text"])
 
 
def main():
    st.set_page_config(page_title="Multiple PDFs Solution Generator", page_icon=":robot:")
    st.header("Multiple PDFs Solution Generator")
 
    user_question = st.text_input("Questions should be from uploaded PDF Files")
 
    if user_question:
        user_input(user_question)
 
    with st.sidebar:
        st.title("Material Section ")
        pdf_docs = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)
        if st.button("Click me!"):
            with st.spinner("Let me Processing for your understanding..."):
                rawtext = get_pdf_text(pdf_docs)
                #chunks of text
                texts = get_text_splitter(rawtext)
                get_vector_store(texts)
                st.success("Done!")
 
 
if __name__ == "__main__":
    main()
