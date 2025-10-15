import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Настройки
BOT_TOKEN = "AAGqhaY6KgG0FWN0s2VYc6-BmONfDATGieQ"
ADMIN_ID = 8293278146

# Цены
SELL_PRICE = 150
BUY_PRICE = 50

# Хранилище активных чатов
active_chats = {}

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton("💰 Купить пак", callback_data="buy_pack")],
        [InlineKeyboardButton("💸 Продать пак", callback_data="sell_pack")],
        [InlineKeyboardButton("📊 Цены", callback_data="prices")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_name = query.from_user.username or query.from_user.first_name
    
    if query.data == "buy_pack":
        active_chats[user_id] = {"type": "buy", "admin_notified": False}
        
        await query.edit_message_text(
            f"🛒 Вы хотите купить пак за {SELL_PRICE}₽\n\n"
            "Создан анонимный чат с администратором. Ожидайте ответа...\n\n"
            "Для отмены используйте /cancel"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🛒 НОВЫЙ ЗАКАЗ НА ПОКУПКУ\n\n"
                 f"Пользователь: {user_name}\n"
                 f"ID: {user_id}\n"
                 f"Сумма: {SELL_PRICE}₽\n\n"
                 f"Ответьте на ЭТО сообщение, чтобы начать общение с покупателем."
        )
        
    elif query.data == "sell_pack":
        active_chats[user_id] = {"type": "sell", "admin_notified": False}
        
        await query.edit_message_text(
            f"💸 Вы хотите продать пак за {BUY_PRICE}₽\n\n"
            "Создан анонимный чат с администратором. Ожидайте ответа...\n\n"
            "Для отмены используйте /cancel"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💸 ПРЕДЛОЖЕНИЕ О ПРОДАЖЕ\n\n"
                 f"Пользователь: {user_name}\n"
                 f"ID: {user_id}\n"
                 f"Предлагаемая цена: {BUY_PRICE}₽\n\n"
                 f"Ответьте на ЭТО сообщение, чтобы начать общение с продавцом."
        )
        
    elif query.data == "prices":
        await query.edit_message_text(
            f"📊 ТЕКУЩИЕ ЦЕНЫ:\n\n"
            f"💰 Покупка у нас: {SELL_PRICE}₽ за пак\n"
            f"💸 Продажа нам: {BUY_PRICE}₽ за пак\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Купить пак", callback_data="buy_pack")],
                [InlineKeyboardButton("💸 Продать пак", callback_data="sell_pack")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
            ])
        )
    
    elif query.data == "back_to_main":
        keyboard = [
            [InlineKeyboardButton("💰 Купить пак", callback_data="buy_pack")],
            [InlineKeyboardButton("💸 Продать пак", callback_data="sell_pack")],
            [InlineKeyboardButton("📊 Цены", callback_data="prices")]
        ]
        await query.edit_message_text(
            "👋 Добро пожаловать!\n\nВыберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cancel для отмены чата"""
    user_id = update.message.from_user.id
    
    if user_id in active_chats:
        chat_type = active_chats[user_id]["type"]
        del active_chats[user_id]
        
        type_text = "покупки" if chat_type == "buy" else "продажи"
        await update.message.reply_text(f"❌ Чат для {type_text} отменен.")
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ Пользователь {user_id} отменил чат {type_text}."
        )
    else:
        await update.message.reply_text("У вас нет активных чатов.")

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений от администратора"""
    if update.message.from_user.id != ADMIN_ID:
        return
    
    # Проверяем, является ли сообщение ответом (reply)
    if update.message.reply_to_message:
        original_text = update.message.reply_to_message.text
        
        # Ищем ID пользователя в тексте сообщения
        if "ID:" in original_text:
            lines = original_text.split('\n')
            for line in lines:
                if line.startswith("ID:"):
                    user_id = int(line.split(":")[1].strip())
                    
                    # Отправляем сообщение пользователю
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"📨 Сообщение от администратора:\n\n{update.message.text}"
                        )
                        await update.message.reply_text("✅ Сообщение отправлено пользователю")
                    except Exception as e:
                        await update.message.reply_text(f"❌ Ошибка отправки: {e}")
                    return  # Важно: выходим после обработки
    
    # Если это не ответ на сообщение от бота, игнорируем
    return

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений от пользователя в активном чате"""
    user_id = update.message.from_user.id
    
    # Если пользователь в активном чате
    if user_id in active_chats:
        # Пересылаем сообщение администратору
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👤 Сообщение от пользователя {user_id}:\n\n{update.message.text}"
        )
        await update.message.reply_text("✅ Сообщение отправлено администратору")
    else:
        # Если не в активном чате, предлагаем начать общение
        await update.message.reply_text("Используйте кнопки для начала общения с администратором.")

def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ВАЖНО: Сначала обработчик сообщений админа, потом общий
    application.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY, handle_admin_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Обработчики кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запуск бота
    print("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
