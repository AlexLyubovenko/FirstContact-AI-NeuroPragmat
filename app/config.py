# app/config.py
import os

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")
FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_index")