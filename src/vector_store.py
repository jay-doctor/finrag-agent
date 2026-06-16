# Option 1: OpenAI embeddings (active – requires OPENAI_API_KEY)
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

def create_vectorstore(docs):
    # Active: OpenAI embeddings (better retrieval)
    embeddings = OpenAIEmbeddings()
    
    # Option 2: HuggingFace embeddings (backup – commented)
    # from langchain_community.embeddings import HuggingFaceEmbeddings
    # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Batch processing to avoid 300k token limit
    batch_size = 100
    vectorstore = None
    
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        if vectorstore is None:
            vectorstore = Chroma.from_documents(batch, embeddings, persist_directory="./chroma_db")
        else:
            vectorstore.add_documents(batch)
    
    return vectorstore

def get_retriever(vectorstore, k=20):
    return vectorstore.as_retriever(search_kwargs={"k": k})