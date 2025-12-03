# app/main.py
import os
import re
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from .rag import init_retriever, retriever
from .dialog_state import get_dialog_state, save_dialog_state
from .phases import get_phase_handler
from .crm import send_lead_to_crm

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FirstContact AI - NeuroPragmat")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required")

application = Application.builder().token(BOT_TOKEN).build()

# Парсинг триггера из сообщения
TRIGGER_PATTERN = r'【systemTextByAi:\s*({.*?})】'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip() if update.message and update.message.text else ""
    user_id = str(user.id)
    if not text:
        return

    logger.info(f"Сообщение от {user.full_name} ({user_id}): {text}")

    # Проверка на триггер отправки в CRM
    trigger_match = re.search(TRIGGER_PATTERN, text)
    if trigger_match:
        try:
            import json
            payload_str = trigger_match.group(1)
            payload = json.loads(payload_str.replace('%%', '"'))
            if payload.get("trigger") == "NEWLEAD":
                await send_lead_to_crm(
                    lead=None,
                    user_id=user_id,
                    full_name=user.full_name or "",
                    channel="telegram",
                    original_message=text,
                    override_data=payload
                )
                # Сброс состояния после отправки
                await save_dialog_state(user_id, {"phase": "completed"})
        except Exception as e:
            logger.error(f"Ошибка парсинга триггера: {e}")
        return

    # Загрузка состояния диалога
    state = await get_dialog_state(user_id)
    if not state:
        state = {"phase": "phase1", "vars": {}}

    current_phase = state["phase"]
    if current_phase == "completed":
        # Если диалог завершён — начинаем заново
        state = {"phase": "phase1", "vars": {}}
        current_phase = "phase1"

    # Получение контекста из базы знаний
    context_str = ""
    if retriever:
        try:
            docs = retriever.invoke(text)
            context_str = "\n".join([d.page_content for d in docs])
        except Exception as e:
            logger.error(f"Ошибка RAG: {e}")

    # Обработка текущей фазы
    try:
        phase_handler = get_phase_handler(current_phase)
        if not phase_handler:
            phase_handler = get_phase_handler("phase1")
            state["phase"] = "phase1"

        result = await phase_handler(text, context_str, state["vars"])
        reply = result["reply"]
        next_phase = result["next_phase"]
        updated_vars = result["vars"]

        # Обновление состояния
        state["phase"] = next_phase
        state["vars"].update(updated_vars)
        await save_dialog_state(user_id, state)

        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Ошибка обработки фазы: {e}")
        await update.message.reply_text("Спасибо за обращение! Менеджер свяжется с вами.")

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.on_event("startup")
async def startup_event():
    logger.info("Запуск FirstContact AI (NeuroPragmat)...")
    init_retriever()
    await application.initialize()
    await application.start()

    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        try:
            await application.bot.set_webhook(webhook_url)
            logger.info(f"Telegram webhook установлен: {webhook_url}")
        except Exception as e:
            logger.error(f"Ошибка установки webhook: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
    await application.shutdown()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        update = Update.de_json(await request.json(), application.bot)
        await application.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return Response(status_code=500)

@app.get("/")
async def health():
    return {
        "status": "ok",
        "agent": "FirstContact AI",
        "agency": "NeuroPragmat",
        "retriever_loaded": retriever is not None
    }