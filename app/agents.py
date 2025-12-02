# app/agents.py
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LeadInfo(BaseModel):
    intent: str = Field(description="намерение: 'узнать_цену', 'заказать_услугу', 'задать_вопрос', 'связаться_с_менеджером'")
    name: str = Field(default="", description="имя клиента")
    contact: str = Field(default="", description="телефон/email")
    summary: str = Field(description="резюме запроса")
    is_hot: bool = Field(description="срочно связаться")

parser = PydanticOutputParser(pydantic_object=LeadInfo)

prompt = ChatPromptTemplate.from_template(
    """Вы — эксперт по лидам в NeuroPragmat.
Контекст компании:
{context}

Сообщение клиента:
"{input}"

Извлеките структурированную информацию.
{format_instructions}
"""
)

llm = ChatOpenAI(model="gpt-4o", temperature=0)

def classify_and_qualify(user_message: str, context: str = "") -> LeadInfo:
    try:
        chain = prompt | llm | parser
        result = chain.invoke({
            "input": user_message,
            "context": context,
            "format_instructions": parser.get_format_instructions()
        })
        return result
    except Exception as e:
        logger.error(f"Агент fallback: {e}")
        return LeadInfo(
            intent="задать_вопрос",
            summary=user_message[:100],
            is_hot=False
        )