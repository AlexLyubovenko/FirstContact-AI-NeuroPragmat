# app/rag.py
import os
import logging
from typing import List
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredMarkdownLoader,
    PyPDFLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from .config import KNOWLEDGE_DIR, FAISS_INDEX_PATH

logger = logging.getLogger(__name__)
embeddings = OpenAIEmbeddings()

def load_documents() -> List:
    """Загружает все документы из папки knowledge/"""
    docs = []
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)
        logger.warning(f"Папка {KNOWLEDGE_DIR} создана. Добавьте туда файлы (txt, md, pdf).")
        return []

    for filename in os.listdir(KNOWLEDGE_DIR):
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        try:
            if filename.endswith(".txt"):
                loader = TextLoader(filepath, encoding="utf-8")
            elif filename.endswith(".md"):
                loader = UnstructuredMarkdownLoader(filepath)
            elif filename.endswith(".pdf"):
                loader = PyPDFLoader(filepath)
            else:
                logger.info(f"Пропущен файл: {filename} (неподдерживаемый формат)")
                continue

            docs.extend(loader.load())
            logger.info(f"Загружен файл: {filename}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке {filename}: {e}")

    return docs

def create_or_load_vectorstore() -> FAISS:
    """Создаёт FAISS-индекс или загружает существующий"""
    if os.path.exists(FAISS_INDEX_PATH):
        logger.info("Загружаем существующий FAISS-индекс...")
        return FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

    logger.info("Создаём новый FAISS-индекс...")
    docs = load_documents()
    if not docs:
        logger.warning("Нет документов для индексации!")
        return None

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(docs)

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)
    logger.info(f"Индекс сохранён в {FAISS_INDEX_PATH}")
    return vectorstore

# Глобальный retriever (инициализируется при старте)
retriever = None

def init_retriever():
    global retriever
    vectorstore = create_or_load_vectorstore()
    if vectorstore:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    else:
        retriever = None