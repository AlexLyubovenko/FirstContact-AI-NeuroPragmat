# app/phases/phase4a.py
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o", temperature=0)


async def handle_phase4a(message: str, context: str, vars: Dict) -> Dict[str, Any]:
    prompt_text = """
Уже известна цель автоматизации: {goal}.
Теперь спроси тип бизнеса: B2B, B2C, фриланс или ИП.

Сообщение клиента: "{message}"

Ответ: до 300 символов.
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    response = await chain.ainvoke({"message": message, "context": context, "goal": vars.get("goal", "")})

    business_type = ""
    msg = message.lower()
    if "b2b" in msg or "юр" in msg or "компани" in msg:
        business_type = "B2B"
    elif "b2c" in msg or "физ" in msg or "частн" in msg:
        business_type = "B2C"
    elif "фриланс" in msg or "самозанят" in msg:
        business_type = "фриланс"
    elif "ип" in msg:
        business_type = "ИП"
    else:
        business_type = "уточнить позже"

    return {
        "reply": response.content,
        "next_phase": "phase5A" if business_type else "phase4A",
        "vars": {"business_type": business_type} if business_type else {}
    }