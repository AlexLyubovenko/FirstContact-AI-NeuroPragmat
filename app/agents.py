# app/agents.py
import logging
import re
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LeadInfo(BaseModel):
    intent: str = Field(description="намерение: 'узнать_цену', 'заказать_услугу', 'задать_вопрос', 'связаться_с_менеджером'")
    name: str = Field(default="", description="имя клиента, если указано")
    contact: str = Field(default="", description="телефон или email")
    summary: str = Field(description="резюме запроса (1 предложение)")
    is_hot: bool = Field(description="True, если клиент явно просит связаться или упоминает срочность")

def extract_name(text: str) -> str:
    patterns = [
        r'(?:меня\s+зовут|я\s+—|имя\s+моё|имя\s+)\s*([А-Яа-яЁё\s]+)',
        r'^([А-Я][а-я]+(?:\s+[А-Я][а-я]+)*)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
        if match:
            return match.group(1).strip()
    return ""

def extract_phone(text: str) -> str:
    phone_pattern = r'(?:\+7|8|7)(?:[\s\-()]*\d){10}'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else ""

parser = PydanticOutputParser(pydantic_object=LeadInfo)

prompt = ChatPromptTemplate.from_template(
    """Вы — эксперт по первичной квалификации лидов в компании NeuroPragmat.
Контекст компании:
{context}

Сообщение клиента:
"{input}"

Проанализируйте сообщение и извлеките структурированную информацию.
Особое внимание уделите:
- Наличию имени (например, "меня зовут...", "я — ...", "Дмитрий")
- Наличию телефона (форматы: +7..., 8..., 7... без пробелов)
- Намерению клиента (заказать услугу, узнать цену, задать вопрос, связаться с менеджером)

Если имя или телефон явно указаны — не запрашивайте их повторно.

{format_instructions}
"""
)

llm = ChatOpenAI(model="gpt-4o", temperature=0)

def classify_and_qualify(user_message: str, context: str = "") -> LeadInfo:
    try:
        name = extract_name(user_message)
        phone = extract_phone(user_message)

        chain = prompt | llm | parser
        result = chain.invoke({
            "input": user_message,
            "context": context,
            "format_instructions": parser.get_format_instructions()
        })

        if name:
            result.name = name
        if phone:
            result.contact = phone

        return result

    except Exception as e:
        logger.error(f"Ошибка агента: {e}")
        return LeadInfo(
            intent="задать_вопрос",
            summary=user_message[:100],
            is_hot=False
        )