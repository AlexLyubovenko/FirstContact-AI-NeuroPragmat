# app/rag.py
import os
import logging
from typing import List
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)
embeddings = OpenAIEmbeddings()

def load_documents() -> List:
    knowledge_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge")
    docs = []
    if not os.path.exists(knowledge_dir):
        logger.warning(f"Папка knowledge не найдена: {knowledge_dir}")
        return docs

    for filename in os.listdir(knowledge_dir):
        if filename.startswith("."):
            continue
        filepath = os.path.join(knowledge_dir, filename)
        try:
            if filename.endswith((".txt", ".md")):
                loader = TextLoader(filepath, encoding="utf-8")
                docs.extend(loader.load())
                logger.info(f"Загружен: {filename}")
            elif filename.endswith(".pdf"):
                loader = PyPDFLoader(filepath)
                docs.extend(loader.load())
                logger.info(f"Загружен PDF: {filename}")
        except Exception as e:
            logger.error(f"Ошибка {filename}: {e}")
    return docs

def create_or_load_vectorstore():
    faiss_path = "/tmp/faiss_index"
    if os.path.exists(faiss_path):
        try:
            return FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            logger.warning(f"Ошибка загрузки индекса: {e}")

    logger.info("Создаём FAISS-индекс...")
    docs = load_documents()
    if not docs:
        logger.warning("Нет документов")
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(faiss_path)
    logger.info(f"Индекс сохранён в {faiss_path}")
    return vectorstore

retriever = None

def init_retriever():
    global retriever
    vectorstore = create_or_load_vectorstore()
    if vectorstore:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        logger.info("✅ Retriever инициализирован")
    else:
        retriever = None
        logger.warning("⚠️ Retriever не создан")