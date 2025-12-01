# app/agents.py
import logging
from typing import Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Модель для структурированного вывода ---
class LeadInfo(BaseModel):
    intent: str = Field(description="Намерение клиента: 'узнать_цену', 'заказать_услугу', 'задать_вопрос', 'связаться_с_менеджером'")
    name: Optional[str] = Field(description="Имя клиента, если указано")
    contact: Optional[str] = Field(description="Телефон или email")
    summary: str = Field(description="Краткое резюме запроса (1 предложение)")
    is_hot: bool = Field(description="True, если клиент явно просит связаться или упоминает срочность")

parser = PydanticOutputParser(pydantic_object=LeadInfo)

# --- Промпт для агента ---
prompt = ChatPromptTemplate.from_template(
    """Вы — эксперт по первичной квалификации лидов в компании.
Контекст компании:
{context}

История диалога (последние сообщения):
{history}

Новое сообщение клиента:
"{input}"

Проанализируйте сообщение и извлеките структурированную информацию.
{format_instructions}
"""
)

llm = ChatOpenAI(model="gpt-4o", temperature=0)

def classify_and_qualify(user_message: str, history: str = "", context: str = "") -> LeadInfo:
    """Классифицирует намерение и извлекает контактные данные"""
    try:
        chain = prompt | llm | parser
        result = chain.invoke({
            "input": user_message,
            "history": history,
            "context": context,
            "format_instructions": parser.get_format_instructions()
        })
        logger.info(f"Агент вернул: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка агента: {e}")
        # Fallback
        return LeadInfo(
            intent="задать_вопрос",
            summary=user_message[:100],
            is_hot=False
        )