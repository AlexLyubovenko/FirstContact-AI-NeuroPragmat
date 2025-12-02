# app/crm.py
import os
import logging
import httpx
from .agents import LeadInfo

logger = logging.getLogger(__name__)
ALBATO_WEBHOOK_URL = os.getenv("ALBATO_WEBHOOK_URL")

async def send_lead_to_crm(lead: LeadInfo, user_id: str, full_name: str, channel: str, original_message: str):
    if not ALBATO_WEBHOOK_URL:
        logger.warning("ALBATO_WEBHOOK_URL не задан")
        return

    payload = {
        "name": f"Запрос от {lead.name or full_name or 'Клиента'}",
        "query": original_message,
        "tags": [
            "firstcontact_ai",
            lead.intent.replace("_", " "),
            "hot_lead" if lead.is_hot else "regular"
        ],
        "contact": {
            "name": lead.name or full_name or "",
        },
        "custom_fields": {
            "ai_summary": lead.summary,
            "intent": lead.intent,
            "source": f"{channel} ({user_id})"
        }
    }

    # Явно передаём телефон/email, если есть
    if lead.contact:
        payload["query"] += f"\nКонтакт: {lead.contact}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(ALBATO_WEBHOOK_URL, json=payload)
            if resp.status_code in (200, 201, 202):
                logger.info("✅ Лид отправлен в CRM")
            else:
                logger.error(f"❌ Albato error: {resp.status_code} – {resp.text}")
    except Exception as e:
        logger.error(f"Исключение при отправке в CRM: {e}")