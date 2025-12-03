# app/phases/phase5a.py
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o", temperature=0)


async def handle_phase5a(message: str, context: str, vars: Dict) -> Dict[str, Any]:
    prompt_text = """
Известно: цель = {goal}, бизнес = {business_type}.
Спроси: есть ли CRM? (AmoCRM, Bitrix24, другая, нет).

Сообщение: "{message}"

Ответ: до 300 символов.
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    response = await chain.ainvoke({
        "message": message,
        "context": context,
        "goal": vars.get("goal", ""),
        "business_type": vars.get("business_type", "")
    })

    crm = ""
    msg = message.lower()
    if "amo" in msg or "амо" in msg:
        crm = "AmoCRM"
    elif "bitrix" in msg or "битрикс" in msg:
        crm = "Bitrix24"
    elif "нет" in msg or "не используем" in msg:
        crm = "нет"
    elif "друг" in msg:
        crm = "другая"
    else:
        crm = "уточнить позже"

    return {
        "reply": response.content,
        "next_phase": "phase6A" if crm else "phase5A",
        "vars": {"crm": crm} if crm else {}
    }