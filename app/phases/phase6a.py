# app/phases/phase6a.py
import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o", temperature=0)


def normalize_phone(phone: str) -> str:
    # Убираем всё, кроме цифр
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    if digits.startswith('7') and len(digits) == 11:
        return f"+{digits}"
    return phone  # возвращаем как есть, если не распознали


async def handle_phase6a(message: str, context: str, vars: Dict) -> Dict[str, Any]:
    prompt_text = """
Теперь запроси имя и телефон для связи.
Сообщение: "{message}"

Ответ: вежливо, до 300 символов.
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    response = await chain.ainvoke({"message": message, "context": context})

    # Извлечение имени (просто первое слово после "меня зовут")
    name = ""
    if "зовут" in message.lower():
        parts = message.split("зовут", 1)
        if len(parts) > 1:
            name = parts[1].strip().split()[0]
    elif len(message.split()) > 1:
        name = message.split()[0]

    # Извлечение телефона
    phone_match = re.search(r'(?:\+7|8|7)(?:[\s\-()]*\d){10}', message)
    phone = normalize_phone(phone_match.group(0)) if phone_match else ""

    updated_vars = {}
    if name:
        updated_vars["name"] = name
    if phone:
        updated_vars["phone"] = phone

    next_phase = "phase7" if name and phone else "phase6A"

    return {
        "reply": response.content,
        "next_phase": next_phase,
        "vars": updated_vars
    }