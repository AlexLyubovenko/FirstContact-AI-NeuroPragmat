# app/agents.py
import logging
import re
from typing import List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LeadInfo(BaseModel):
    intent: str = Field(default="задать_вопрос", description="намерение")
    name: str = Field(default="", description="имя клиента")
    contact: str = Field(default="", description="телефон или email")
    summary: str = Field(default="Запрос от клиента", description="резюме")
    is_hot: bool = Field(default=False, description="срочность")

def is_greeting(text: str) -> bool:
    greetings = ["привет", "здравствуйте", "хай", "hi", "hello", "добрый день", "доброе утро", "добрый вечер"]
    return any(g in text.lower() for g in greetings)

def extract_contact(text: str) -> str:
    # Извлекаем телефон или email
    phone = re.search(r'(?:\+7|8|7)(?:[\s\-()]*\d){10}', text)
    if phone:
        return phone.group(0)
    email = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email:
        return email.group(0)
    return ""

parser = PydanticOutputParser(pydantic_object=LeadInfo)

prompt = ChatPromptTemplate.from_template(
    """Вы — эксперт по лидам в NeuroPragmat.
Анализируйте сообщение и определите:
1. Намерение: "заказать_услугу", "узнать_цену", "связаться_с_менеджером", "задать_вопрос"
2. Если клиент проявил интерес — установите is_hot = True
3. Сформулируйте краткое резюме (1 предложение)

Сообщение:
"{input}"
{format_instructions}
"""
)

llm = ChatOpenAI(model="gpt-4o", temperature=0)

def classify_and_qualify(user_message: str, context: str = "") -> LeadInfo:
    try:
        contact = extract_contact(user_message)
        chain = prompt | llm | parser
        result = chain.invoke({
            "input": user_message,
            "format_instructions": parser.get_format_instructions()
        })
        result.contact = contact
        if result.intent in ["заказать_услугу", "узнать_цену", "связаться_с_менеджером"]:
            result.is_hot = True
        return result
    except Exception as e:
        logger.error(f"Агент fallback: {e}")
        return LeadInfo(
            summary=user_message[:100],
            contact=extract_contact(user_message)
        )