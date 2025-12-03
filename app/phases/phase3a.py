# app/phases/phase3a.py
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o", temperature=0)


async def handle_phase3a(message: str, context: str, vars: Dict) -> Dict[str, Any]:
    prompt_text = """
Клиент согласился ответить на вопросы.
Сообщение: "{message}"

Задача: спросить цель автоматизации: лидогенерация, поддержка клиентов или обработка заказов.
Не задавай другие вопросы.

Ответ: до 300 символов.
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    response = await chain.ainvoke({"message": message, "context": context})

    # Извлечение цели (упрощённо)
    goal = ""
    msg = message.lower()
    if "лид" in msg or "лидогенер" in msg:
        goal = "лидогенерация"
    elif "поддерж" in msg or "вопрос" in msg:
        goal = "поддержка клиентов"
    elif "заказ" in msg or "обработ" in msg:
        goal = "обработка заказов"
    else:
        goal = "уточнить позже"

    return {
        "reply": response.content,
        "next_phase": "phase4A" if goal else "phase3A",
        "vars": {"goal": goal} if goal else {}
    }