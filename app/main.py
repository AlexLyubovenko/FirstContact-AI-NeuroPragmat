# app/main.py
import os
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Импорты модулей проекта
from .rag import init_retriever, retriever
from .agents import classify_and_qualify
from .crm import send_lead_to_crm

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(title="FirstContact AI - NeuroPragmat")

# Инициализация Telegram-приложения
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    logger.error("BOT_TOKEN не задан в .env!")
    raise ValueError("BOT_TOKEN is required")

application = Application.builder().token(bot_token).build()

# === Обработчик входящих сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text if update.message and update.message.text else ""
    chat_id = update.effective_chat.id

    if not text.strip():
        return

    logger.info(f"Сообщение от {user.full_name} ({user.id}): {text}")

    # 1. Получаем релевантный контекст из базы знаний
    context_str = ""
    if retriever:
        try:
            docs = retriever.invoke(text)
            context_str = "\n".join([d.page_content for d in docs])
        except Exception as e:
            logger.error(f"Ошибка при поиске в базе знаний: {e}")

    # 2. Анализируем сообщение с помощью агента
    try:
        lead_info = classify_and_qualify(
            user_message=text,
            context=context_str
        )
    except Exception as e:
        logger.error(f"Ошибка агента: {e}")
        # Fallback-ответ
        await update.message.reply_text("Спасибо за обращение! Менеджер свяжется с вами в ближайшее время.")
        return

    # 3. Формируем ответ клиенту
    if lead_info.intent == "связаться_с_менеджером" or lead_info.is_hot:
        reply = "Благодарю за обращение! Менеджер свяжется с вами в ближайшее время. Для ускорения уточните, пожалуйста, ваше имя и телефон."
    else:
        reply = f"Спасибо за ваш запрос! {lead_info.summary} Наш ассистент уже подбирает для вас решение."

    await update.message.reply_text(reply)

    # 4. Отправляем лид в CRM
    await send_lead_to_crm(
        lead=lead_info,
        user_id=str(user.id),
        full_name=user.full_name or "",
        channel="telegram",
        original_message=text
    )

# Регистрация обработчика
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === События жизненного цикла ===
@app.on_event("startup")
async def startup_event():
    """Инициализация RAG и установка Telegram webhook"""
    logger.info("Запуск FirstContact AI (NeuroPragmat)...")
    init_retriever()

    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        try:
            await application.bot.set_webhook(webhook_url)
            logger.info(f"Telegram webhook успешно установлен: {webhook_url}")
        except Exception as e:
            logger.error(f"Ошибка установки webhook: {e}")
    else:
        logger.warning("WEBHOOK_URL не задан — webhook не установлен")

# === Эндпоинты ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Принимает входящие обновления от Telegram"""
    try:
        update = Update.de_json(await request.json(), application.bot)
        await application.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return Response(status_code=500)

@app.get("/")
async def health():
    """Health-check для мониторинга"""
    return {
        "status": "ok",
        "agent": "FirstContact AI",
        "agency": "NeuroPragmat",
        "retriever_loaded": retriever is not None
    }