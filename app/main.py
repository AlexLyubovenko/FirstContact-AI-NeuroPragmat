# app/main.py
import os
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from .rag import init_retriever, retriever
from .agents import classify_and_qualify, is_greeting
from .crm import send_lead_to_crm

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FirstContact AI - NeuroPragmat")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required")

application = Application.builder().token(BOT_TOKEN).build()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip() if update.message and update.message.text else ""
    if not text:
        return

    logger.info(f"Сообщение от {user.full_name} ({user.id}): {text}")

    # Если приветствие — отвечаем, но НЕ отправляем в CRM
    if is_greeting(text):
        await update.message.reply_text(
            "Здравствуйте! 👋\nЯ — ИИ-ассистент агентства NeuroPragmat.\n\nЧем могу помочь?\n\n✅ Автоматизация лидогенерации\n✅ Интеграция с AmoCRM\n✅ ИИ-консультанты 24/7"
        )
        return

    # Обработка содержательного запроса
    context_str = ""
    if retriever:
        try:
            docs = retriever.invoke(text)
            context_str = "\n".join([d.page_content for d in docs])
        except Exception as e:
            logger.error(f"Ошибка RAG: {e}")

    try:
        lead_info = classify_and_qualify(user_message=text, context=context_str)
    except Exception as e:
        logger.error(f"Ошибка агента: {e}")
        await update.message.reply_text("Спасибо за обращение! Менеджер свяжется с вами в ближайшее время.")
        return

    # Формируем ответ
    if lead_info.name and lead_info.contact:
        reply = f"Спасибо за ваш запрос! {lead_info.summary} Наш менеджер свяжется с вами в ближайшее время."
    elif lead_info.intent == "связаться_с_менеджером" or lead_info.is_hot:
        reply = "Благодарю за обращение! Менеджер свяжется с вами в ближайшее время. Уточните, пожалуйста, ваше имя и телефон для ускорения."
    else:
        reply = f"Спасибо за ваш запрос! {lead_info.summary} Наш ассистент уже подбирает решение."

    await update.message.reply_text(reply)

    # Отправляем ТОЛЬКО содержательные запросы в CRM
    await send_lead_to_crm(
        lead=lead_info,
        user_id=str(user.id),
        full_name=user.full_name or "",
        channel="telegram",
        original_message=text
    )

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
    else:
        logger.warning("WEBHOOK_URL не задан")

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