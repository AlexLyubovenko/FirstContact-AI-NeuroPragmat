# app/phases/phase7.py
from typing import Dict, Any
import re


async def handle_phase7(message: str, context: str, vars: Dict) -> Dict[str, Any]:
    name = vars.get("name", "Клиент")
    phone = vars.get("phone", "")
    goal = vars.get("goal", "")
    business_type = vars.get("business_type", "")
    crm = vars.get("crm", "")

    # Формируем summarize
    summarize = f"Клиент заинтересован в автоматизации {goal} для {business_type}. Использует CRM: {crm}."

    # Собираем вопросы (все, что задавал клиент — упрощённо: всё сообщение)
    quest = message

    # Формируем триггер
    trigger = (
        f'【systemTextByAi: {{"trigger": "NEWLEAD", '
        f'"name": %%"{name}"%%, '
        f'"phone": %%"{phone}"%%, '
        f'"summarize": %%"{summarize}"%%, '
        f'"quest": %%"{quest}"%%, '
        f'"business_type": %%"{business_type}"%%, '
        f'"goal": %%"{goal}"%%, '
        f'"crm": %%"{crm}"%%}}】'
    )

    reply = (
        f"Отлично, {name}! 🙌\n\n"
        f"Ваша заявка принята. Менеджер NeuroPragmat свяжется с вами в ближайшее время.\n\n"
        f"Хорошего дня!"
    )

    return {
        "reply": reply + "\n\n" + trigger,
        "next_phase": "completed",
        "vars": vars
    }