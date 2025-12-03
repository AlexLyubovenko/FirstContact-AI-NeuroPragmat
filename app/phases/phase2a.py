# app/phases/phase2a.py
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o", temperature=0)


async def handle_phase2a(message: str, context: str, vars: Dict) -> Dict[str, Any]:
    prompt_text = """
Клиент заинтересован в ИИ-автоматизации.
Сообщение клиента: "{message}"

Задача:
1. Кратко расскажи о FirstContact AI: "Наш ИИ-ассистент принимает первые обращения, анализирует запрос на основе вашей базы знаний и передаёт квалифицированного лида менеджеру в AmoCRM".
2. Уточни: хочет ли клиент ответить на 2 вопроса или сразу созвониться с экспертом?

Ответ: до 400 символов, на 'Вы', профессионально.
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    response = await chain.ainvoke({"message": message, "context": context})

    text = message.lower()
    if any(w in text for w in ["звон", "созвон", "телефон", "связь"]):
        next_phase = "phase3B"
    else:
        next_phase = "phase3A"

    return {
        "reply": response.content,
        "next_phase": next_phase,
        "vars": {}
    }