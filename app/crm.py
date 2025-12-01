# app/crm.py
import os
import logging
import httpx
from .agents import LeadInfo

logger = logging.getLogger(__name__)

ALBATO_WEBHOOK_URL = os.getenv("ALBATO_WEBHOOK_URL")

async def send_lead_to_crm(
    lead: LeadInfo,
    user_id: str,
    full_name: str,
    channel: str = "telegram",
    original_message: str = ""
):
    """
    Отправляет структурированный лид в Albato → AmoCRM
    """
    if not ALBATO_WEBHOOK_URL:
        logger.warning("ALBATO_WEBHOOK_URL не задан — пропускаем отправку в CRM")
        return None

    # Формируем payload для AmoCRM через Albato
    payload = {
        "pipeline_id": 12345678,  # ← замените на ваш pipeline в AmoCRM (или удалите, если не нужен)
        "name": f"Запрос от {full_name or 'Клиент'}",
        "contact": {
            "name": full_name or "",
            # Albato может извлечь телефон/email из поля 'query', если не указано явно
        },
        "query": original_message.strip(),
        "tags": [
            "firstcontact_ai",
            lead.intent.replace("_", " "),
            "hot_lead" if lead.is_hot else "regular"
        ],
        "custom_fields": {
            "source": f"Telegram ({user_id})" if channel == "telegram" else channel,
            "ai_summary": lead.summary,
            "intent": lead.intent
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(ALBATO_WEBHOOK_URL, json=payload)
            if response.status_code in (200, 201, 202):
                logger.info(f"Лид успешно отправлен в CRM. Статус: {response.status_code}")
                return response.json()
            else:
                logger.error(f"Ошибка Albato: {response.status_code} – {response.text}")
                return None
    except Exception as e:
        logger.error(f"Исключение при отправке в CRM: {e}")
        return None