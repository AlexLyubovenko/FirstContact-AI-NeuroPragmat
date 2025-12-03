# app/phases/phase1.py
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o", temperature=0)


async def handle_phase1(message: str, context: str, vars: Dict) -> Dict[str, Any]:
    prompt_text = """
Ты — Анастасия, ИИ-ассистент агентства NeuroPragmat.
Первое сообщение клиента: "{message}"

Задача:
1. Дать краткую ценность: "Мы создаём ИИ-ассистентов, которые 24/7 квалифицируют лиды и передают их в AmoCRM".
2. Узнать, хочет ли клиент узнать больше.
3. Не задавать лишних вопросов.

Ответ должен быть дружелюбным, профессиональным, до 400 символов.
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    response = await chain.ainvoke({"message": message, "context": context})

    text = message.lower()
    if any(w in text for w in ["да", "хочу", "расскажи", "интересно", "нужно", "требуется"]):
        next_phase = "phase2A"
    elif any(w in text for w in ["нет", "не хочу", "не интересно"]):
        next_phase = "phase2A"  # даже при "нет" — даём информацию
    else:
        next_phase = "phase1"

    return {
        "reply": response.content,
        "next_phase": next_phase,
        "vars": {}
    }