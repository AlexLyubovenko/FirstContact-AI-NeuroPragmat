# app/rag.py
import os
import logging
from typing import List
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from .config import KNOWLEDGE_DIR

logger = logging.getLogger(__name__)
embeddings = OpenAIEmbeddings()

def load_documents() -> List:
    """Загружает документы из папки knowledge/ (поддерживает .txt, .md, .pdf)"""
    docs = []
    if not os.path.exists(KNOWLEDGE_DIR):
        logger.warning(f"Папка {KNOWLEDGE_DIR} не найдена. Создаём пустую.")
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        return []

    for filename in os.listdir(KNOWLEDGE_DIR):
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        try:
            if filename.endswith((".txt", ".md")):
                # Используем TextLoader для .txt и .md
                loader = TextLoader(filepath, encoding="utf-8")
                docs.extend(loader.load())
                logger.info(f"Загружен текстовый файл: {filename}")
            elif filename.endswith(".pdf"):
                loader = PyPDFLoader(filepath)
                docs.extend(loader.load())
                logger.info(f"Загружен PDF: {filename}")
            else:
                logger.info(f"Пропущен неподдерживаемый файл: {filename}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке {filename}: {e}")

    return docs

def create_or_load_vectorstore():
    """Создаёт или загружает FAISS-индекс. Индекс сохраняется в /tmp/faiss_index (Render-friendly)"""
    # В Render /tmp — writable filesystem
    faiss_path = "/tmp/faiss_index"

    if os.path.exists(faiss_path):
        logger.info("Загружаем существующий FAISS-индекс из /tmp")
        try:
            return FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            logger.warning(f"Не удалось загрузить индекс: {e}. Создаём новый.")

    logger.info("Создаём новый FAISS-индекс...")
    docs = load_documents()
    if not docs:
        logger.warning("Нет документов для индексации!")
        return None

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(docs)

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(faiss_path)
    logger.info(f"Индекс сохранён в {faiss_path}")
    return vectorstore

# Глобальный retriever
retriever = None

def init_retriever():
    global retriever
    vectorstore = create_or_load_vectorstore()
    if vectorstore:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        logger.info("Retriever успешно инициализирован.")
    else:
        retriever = None
        logger.warning("Retriever не создан (нет документов).")