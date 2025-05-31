import json
import telebot
import time
from datetime import datetime, timedelta
from logger_setup import setup_loggers
from handlers import start, help, flush_logs, kick_user, chat_stats, user_stats, handle_message, morph, lemmatize_words, delete_message_after_delay, handle_restart, load_stats, save_stats, get_stats, set_stats  # Импортируем обработчики
from telebot import types
from config import TOKEN
import threading

bot = telebot.TeleBot(TOKEN)

# Загружаем статистику при запуске
load_stats()

STATS_FILE = 'chat_statistics.json'

# Инициализация логгеров
command_logger, chat_logger = setup_loggers()

#Разрешённые пользователи для использования админ-команд бота
ALLOWED_USERS = [
    5113266064,   # Evanbrine
    5682932817,   # Мой второй акк 
    5143890821,   # Баунти
    725840467,    # Полина
    6604377282,   # Тая
    1274907358,   # Диззи
    915228588,    # Симон
    1249961804,   # Кто-то Тама
    6378555926,   # Глюк
    5111459895    # Мирчег  
]
#Проверка на админа
def is_admin(user_id):
    """Проверяет, разрешено ли пользователю взаимодействовать с ботом"""
    return user_id in ALLOWED_USERS

# Регистрация обработчиков команд
@bot.message_handler(commands=['start'])
def handle_start(message):
    start(message, bot)

@bot.message_handler(commands=['mystats'])
def handle_mystats(message):
    user_stats(message, bot, get_user_name)

@bot.message_handler(commands=['logs'])
def handle_flush_logs(message):
    flush_logs(message, bot)

@bot.message_handler(commands=['kick'])
def handle_kick(message):
    if not is_admin(message.from_user.id):
        return
    kick_user(message, bot)

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    chat_stats(message, bot)

@bot.message_handler(commands=['mystats'])
def handle_mystats(message):
    user_stats(message, bot)

@bot.message_handler(commands=['restart'])
def restart_command(message):
    if not is_admin(message.from_user.id):
        return
    handle_restart(message, bot)

# Флаг для режима ожидания
is_paused = False

# Команда /off
@bot.message_handler(commands=['off'])
def turn_off(message):
    global is_paused
    if not is_admin(message.from_user.id):  # Проверка прав администратора
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
    is_paused = True
    bot.reply_to(message, "Бот переведён в режим ожидания. Используйте /on, чтобы включить его снова.")
        
# Команда /on
@bot.message_handler(commands=['on'])
def turn_on(message):
    global is_paused
    if not is_admin(message.from_user.id):  # Проверка прав администратора
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
    is_paused = False
    bot.reply_to(message, "Бот снова активен!")

new_user_data = {}
# Добавляем глобальные переменные для отслеживания удалений
deleted_messages_log = {}  # {message_id: {"text": str, "user_id": int, "timestamp": datetime, "words": list}}
user_complaints = {}  # {user_id: [list of complaint timestamps]}

# Функция для генерации уникального callback_data, нужно для нажатия кнопок
def generate_callback_data(user_id):
    return f"verify_{user_id}"

def get_user_name(user_id, chat_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)

        # Проверяем username
        if member.user.username:
            return f"@{member.user.username}"

        # Если нет username, используем first_name и last_name
        if member.user.first_name and member.user.last_name:
            return f"{member.user.first_name} {member.user.last_name}".replace(" ", "_")  # Заменяем пробелы на подчеркивание для корректного форматирования

        elif member.user.first_name:
            return member.user.first_name.replace(" ", "_")

        # Если нет имени, возвращаем цифровой идентификатор
        return f"ID_{user_id}"

    except Exception as e:
        print(f"Ошибка при получении имени пользователя {user_id}: {e}")
        return f"ID_{user_id}"

# Функция для отправки сообщения с кнопкой для капчи
def send_verification_message(chat_id, user_id):
    # Создаем кнопку с уникальным callback_data
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Я не бот!", callback_data=generate_callback_data(user_id))
    markup.add(button)

    # Получаем имя пользователя для формирования сообщения
    user_name = get_user_name(user_id, chat_id)

    # Отправляем сообщение в чат
    msg = bot.send_message(
        chat_id,
        f"👋 <a href='tg://user?id={user_id}'>{user_name}</a>, подтвердите, что вы не бот! У вас 30 секунд",
        parse_mode="HTML",
        reply_markup=markup, # для кнопок
        disable_notification=True # отключение уведомления для остальных участников
    )

    # Сохраняем данные о пользователе
    new_user_data[user_id] = {
        "chat_id": chat_id,
        "message_id": msg.message_id,
        "timer": None,
        "msg_object": msg  # Добавляем объект сообщения для удаления
    }

    # Запускаем таймер на 30 секунд
    timer = threading.Timer(30.0, kick_user_if_no_response, args=[chat_id, user_id])
    new_user_data[user_id]["timer"] = timer
    timer.start()

# Функция для кика пользователя, если он не ответил на капчу
def kick_user_if_no_response(chat_id, user_id):
    if user_id in new_user_data:
        # Кикаем пользователя
        bot.kick_chat_member(chat_id, user_id)
        msg1 = bot.send_message(chat_id, f"Пользователь {get_user_name(user_id, chat_id)} был кикнут за неактивность.", parse_mode="HTML")
        
        # Удаляем сообщение с кнопкой "Я не бот!"
        msg2 = new_user_data[user_id]["msg_object"]
        bot.delete_message(msg1.chat.id, msg1.message_id)
        # Удаляем сообщение "был кикнут за неактивность"
        bot.delete_message(msg2.chat.id, msg2.message_id)

        # Удаляем данные пользователя
        del new_user_data[user_id]

# Обработчик новых участников чата (отправка капчи)
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    for new_user in message.new_chat_members:
        # Отправляем сообщение с кнопкой
        send_verification_message(message.chat.id, new_user.id)

# Обработчик нажатия на кнопку
@bot.callback_query_handler(func=lambda call: True)
def unified_callback_handler(call):
    """Обрабатывает все callback'и: капчу и кнопки обратной связи"""
    
    # Обработка капчи (callback_data содержит verify_user_id)
    if call.data.startswith('verify_'):
        user_id = int(call.data.split('_')[1])
        if user_id == call.from_user.id:
            # Получаем корректное имя пользователя
            user_name = get_user_name(user_id, call.message.chat.id)

            # Отправляем подтверждение и удаляем кнопку
            confirmation_msg = bot.send_message(call.message.chat.id, f"Привет, {user_name}! Вы успешно подтвердили, что вы не бот.", disable_notification=True)
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

            # Удаляем подтверждающее сообщение через 5 секунд
            delete_message_after_delay(call.message.chat.id, confirmation_msg.message_id, bot, delay=5)

            # Останавливаем таймер
            if user_id in new_user_data:
                new_user_data[user_id]['timer'].cancel()
                del new_user_data[user_id]

        # Отвечаем на callback
        bot.answer_callback_query(call.id)
        return
    
    # Обработка кнопок обратной связи (complaint_ и correct_)
    if call.data.startswith('complaint_') or call.data.startswith('correct_'):
        print(f"Получен callback обратной связи: {call.data}")
        print(f"От пользователя: {call.from_user.id}")
        
        try:
            action, message_id = call.data.split('_', 1)
            message_id = int(message_id)
            user_id = call.from_user.id
            
            print(f"Action: {action}, Message ID: {message_id}")
            
            # Проверяем, является ли пользователь разрешенным
            if not is_admin(call.from_user.id):
                print("Пользователь не в списке разрешенных")
                bot.answer_callback_query(
                    call.id, 
                    "Только администраторы могут оценивать работу бота.", 
                    show_alert=True
                )
                return
            
            print("Пользователь разрешен, продолжаем")
            
            # Проверяем, есть ли информация об удаленном сообщении
            if message_id in deleted_messages_log:
                deleted_info = deleted_messages_log[message_id]
                
                if action == "complaint":
                    # Обрабатываем жалобу
                    handle_user_complaint(
                        deleted_info["user_id"], 
                        deleted_info["text"], 
                        deleted_info["words"]
                    )
                    
                    bot.answer_callback_query(
                        call.id, 
                        "Коэффициенты были уменьшены по решению администратора.", 
                        show_alert=True
                    )
                    
                elif action == "correct":
                    # Обрабатываем подтверждение правильности
                    handle_correct_deletion(
                        deleted_info["text"], 
                        deleted_info["words"]
                    )
                    
                    bot.answer_callback_query(
                        call.id, 
                        "Коэффициенты были усилены по решению администратора.", 
                        show_alert=True
                    )
                
                # Удаляем кнопки
                bot.edit_message_reply_markup(
                    call.message.chat.id, 
                    call.message.message_id, 
                    reply_markup=None
                )
                
                # Удаляем запись из лога
                del deleted_messages_log[message_id]
                
            else:
                bot.answer_callback_query(
                    call.id, 
                    "Информация об этом сообщении не найдена.", 
                    show_alert=True
                )
                
        except Exception as e:
            print(f"Ошибка при обработке обратной связи: {e}")
            bot.answer_callback_query(call.id, "Произошла ошибка.")
        
        return
    
    # Если callback не распознан
    print(f"Неизвестный callback: {call.data}")
    bot.answer_callback_query(call.id)

# Функция для логирования действий пользователя
def log_user_action(message, action):
    user_info = f"Пользователь {message.from_user.username} (ID: {message.from_user.id})"
    command_logger.info(f"{user_info} {action}")

# Функция для логирования сообщений чата
def log_chat_message(message):
    user_info = f"Пользователь {message.from_user.username} (ID: {message.from_user.id})"
    chat_logger.info(f"{user_info} отправил сообщение: {message.text}")

# Чтение файла с запрещёнными словами
try:
    with open('forbidden_message.json', 'r', encoding='utf-8') as file:
        forbidden_dict = json.load(file)
        print("Содержимое файла с запрещёнными словами:", forbidden_dict)
except Exception as e:
    print(f"Ошибка при чтении файла с запрещёнными словами: {e}")
    forbidden_dict = {}

# Чтение файла с фразами
try:
    with open('forbidden_phrases.json', 'r', encoding='utf-8') as file:
        forbidden_phrases = json.load(file)
        print("Содержимое файла с фразами:", forbidden_phrases)
except Exception as e:
    print(f"Ошибка при чтении файла с фразами: {e}")
    forbidden_phrases = []

def save_forbidden_phrases():
    try:
        with open('forbidden_phrases.json', 'w', encoding='utf-8') as file:
            json.dump(forbidden_phrases, file, ensure_ascii=False, indent=4)
        print("Фразы успешно сохранены в файл.")
    except Exception as e:
        print(f"Ошибка при сохранении файла с фразами: {e}")

def save_forbidden_dict():
    try:
        with open('forbidden_message.json', 'w', encoding='utf-8') as file:
            json.dump(forbidden_dict, file, ensure_ascii=False, indent=4)
        print("Словарь успешно сохранён в файл.")
    except Exception as e:
        print(f"Ошибка при сохранении словаря: {e}")

last_matched_words = []
last_matched_phrases = []
last_message_chat_id = None
last_message_id = None
last_message_deleted = False
last_message_text = ""
last_all_words = []
message_repeat_count = 0

def calculate_risk_with_tracking(message):
    global last_matched_words, last_matched_phrases, last_message_chat_id, last_message_id, last_message_deleted, last_message_text, message_repeat_count, last_all_words

    print("Начинаем расчёт риска для сообщения:", message.text)
    words = message.text.lower().split()
    lemmatized_words = lemmatize_words(words)
    print(f"Сообщение в начальной форме: {lemmatized_words}")

    # Проверяем, повторяется ли сообщение
    if (last_message_chat_id == message.chat.id and 
        last_message_text.lower() == message.text.lower() and 
        not last_message_deleted):
        message_repeat_count += 1
        print(f"Обнаружено повторение #{message_repeat_count} сообщения: '{message.text}'")
        
        if message_repeat_count >= 2:
            print("Запускаем агрессивное автообучение из-за повторений!")
            auto_learn_aggressive(lemmatized_words, message_repeat_count)
    else:
        message_repeat_count = 1

    total_risk = 0
    matched_phrases = []
    matched_words = []

    # Проверяем фразы
    for phrase in forbidden_phrases:
        phrase_words = phrase["words"]
        if all(word in lemmatized_words for word in phrase_words):
            total_risk += phrase["multiplier"]
            matched_phrases.append(phrase)
            print(f"Найдена фраза: {phrase_words}, риск увеличен на {phrase['multiplier']}")
    
    # Проверяем отдельные слова
    for word in lemmatized_words:
        if word in forbidden_dict:
            total_risk += forbidden_dict[word]
            matched_words.append(word)
            print(f"Найдено запрещённое слово: {word}, риск увеличен на {forbidden_dict[word]}")
    
    average_risk = total_risk / len(lemmatized_words) if len(lemmatized_words) > 0 else 0
    print(f"Средний риск сообщения: {average_risk}")

    # Сохраняем для последующего обучения
    last_matched_words = matched_words
    last_matched_phrases = matched_phrases
    last_all_words = lemmatized_words
    last_message_chat_id = message.chat.id
    last_message_id = message.message_id
    last_message_deleted = False
    last_message_text = message.text

    return average_risk

LEARNING_RATE = 0.1

def auto_learn_aggressive(lemmatized_words, repeat_count):
    """Агрессивное обучение для повторяющихся сообщений"""
    global forbidden_dict
    
    base_increase = 1.0 * repeat_count
    
    for word in lemmatized_words:
        if len(word) > 2:
            old_value = forbidden_dict.get(word, 0)
            new_value = old_value + base_increase
            forbidden_dict[word] = new_value
            print(f"Агрессивное обучение: '{word}' {old_value} -> {new_value}")
    
    save_forbidden_dict()

def manual_learn(positive_feedback, multiplier=1):
    """Ручное обучение - работает со всеми словами сообщения"""
    global forbidden_dict, forbidden_phrases
    
    if positive_feedback:
        base_adjustment = -LEARNING_RATE * multiplier
        
        for word in last_matched_words:
            old_value = forbidden_dict.get(word, 0)
            new_value = max(0, old_value + base_adjustment)
            forbidden_dict[word] = new_value
            print(f"Похвала: уменьшен коэффициент слова '{word}': {old_value} -> {new_value}")

        for phrase in last_matched_phrases:
            old_value = phrase["multiplier"]
            new_value = max(0, old_value + base_adjustment)
            phrase["multiplier"] = new_value
            print(f"Похвала: уменьшен множитель фразы {phrase['words']}: {old_value} -> {new_value}")
    
    else:
        base_adjustment = LEARNING_RATE * multiplier
        
        for word in last_all_words:
            if len(word) > 2:
                old_value = forbidden_dict.get(word, 0)
                new_value = old_value + base_adjustment
                forbidden_dict[word] = new_value
                print(f"Ругань: увеличен коэффициент слова '{word}': {old_value} -> {new_value}")
        
        for phrase in last_matched_phrases:
            old_value = phrase["multiplier"]
            new_value = old_value + base_adjustment
            phrase["multiplier"] = new_value
            print(f"Ругань: увеличен множитель фразы {phrase['words']}: {old_value} -> {new_value}")

    save_forbidden_dict()
    save_forbidden_phrases()

def handle_user_complaint(user_id, message_text, lemmatized_words):
    """Обрабатывает жалобу пользователя на неправильное удаление"""
    global forbidden_dict, forbidden_phrases, user_complaints
    
    # Записываем жалобу
    if user_id not in user_complaints:
        user_complaints[user_id] = []
    user_complaints[user_id].append(datetime.now())
    
    # Уменьшаем коэффициенты слов из удаленного сообщения
    reduction = 0.3  # Коэффициент уменьшения
    
    for word in lemmatized_words:
        if word in forbidden_dict and forbidden_dict[word] > 0:
            old_value = forbidden_dict[word]
            new_value = max(0, old_value - reduction)
            forbidden_dict[word] = new_value
            print(f"Жалоба: уменьшен коэффициент слова '{word}': {old_value} -> {new_value}")
    
    # Проверяем фразы и уменьшаем их множители
    for phrase in forbidden_phrases:
        phrase_words = phrase["words"]
        if all(word in lemmatized_words for word in phrase_words):
            old_value = phrase["multiplier"]
            new_value = max(0, old_value - reduction)
            phrase["multiplier"] = new_value
            print(f"Жалоба: уменьшен множитель фразы {phrase['words']}: {old_value} -> {new_value}")
    
    save_forbidden_dict()
    save_forbidden_phrases()

def create_complaint_keyboard(message_id):
    """Создает inline клавиатуру для жалобы"""
    from telebot import types
    
    keyboard = types.InlineKeyboardMarkup()
    complaint_btn = types.InlineKeyboardButton(
        "❌ Это ошибка!", 
        callback_data=f"complaint_{message_id}"
    )
    correct_btn = types.InlineKeyboardButton(
        "✅ Ты молодец", 
        callback_data=f"correct_{message_id}"
    )
    keyboard.add(complaint_btn, correct_btn)
    return keyboard

def handle_correct_deletion(message_text, lemmatized_words):
    """Обрабатывает подтверждение правильности удаления"""
    global forbidden_dict, forbidden_phrases
    
    # Увеличиваем коэффициенты слов из правильно удаленного сообщения
    increase = 0.2  # Коэффициент увеличения
    
    for word in lemmatized_words:
        if len(word) > 2:  # Игнорируем короткие слова
            old_value = forbidden_dict.get(word, 0)
            new_value = old_value + increase
            forbidden_dict[word] = new_value
            print(f"Подтверждение: увеличен коэффициент слова '{word}': {old_value} -> {new_value}")
    
    # Проверяем фразы и увеличиваем их множители
    for phrase in forbidden_phrases:
        phrase_words = phrase["words"]
        if all(word in lemmatized_words for word in phrase_words):
            old_value = phrase["multiplier"]
            new_value = old_value + increase
            phrase["multiplier"] = new_value
            print(f"Подтверждение: увеличен множитель фразы {phrase['words']}: {old_value} -> {new_value}")
    
    save_forbidden_dict()
    save_forbidden_phrases()

@bot.message_handler(commands=['goodgirl', 'badgirl', 'badgirl_hard'])
def feedback_handler(message):
    global last_message_chat_id, last_message_id, last_all_words
    
    if last_message_chat_id != message.chat.id or last_message_id is None:
        bot.reply_to(message, "Нет проанализированного сообщения для оценки.")
        return
    
    if not last_all_words:
        bot.reply_to(message, "Нет данных о последнем сообщении для обучения.")
        return

    if message.text.startswith('/goodgirl'):
        positive = True
        multiplier = 1
        action = "похвалы"
    elif message.text.startswith('/badgirl'):
        positive = False
        multiplier = 1
        action = "ругани"
    elif message.text.startswith('/badgirl_hard'):
        positive = False
        multiplier = 3
        action = "сильной ругани"
    else:
        bot.reply_to(message, "Неизвестная команда.")
        return

    print(f"Ручное обучение: {action} для сообщения с {len(last_all_words)} словами")
    manual_learn(positive_feedback=positive, multiplier=multiplier)

    if positive:
        response = f"Спасибо за похвалу! Уменьшил коэффициенты найденных слов/фраз."
    else:
        response = f"Понял! Увеличил коэффициенты всех слов сообщения (множитель {multiplier}x)."
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['last'])
def show_last_message(message):
    if last_message_chat_id != message.chat.id or not last_all_words:
        bot.reply_to(message, "Нет данных о последнем сообщении.")
        return
    
    response = f"Последнее сообщение: '{last_message_text}'\n"
    response += f"Слова: {', '.join(last_all_words)}\n"
    response += f"Найденные запрещенные слова: {', '.join(last_matched_words) if last_matched_words else 'нет'}\n"
    response += f"Найденные фразы: {len(last_matched_phrases)} шт."
    
    bot.reply_to(message, response)

# Ручное удаление сообщений
@bot.message_handler(commands=['delete'])
def delete_message_command(message):
    # Проверяем, является ли пользователь администратором
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "У вас нет прав для удаления сообщений.")
        return
    
    # Проверяем, является ли сообщение ответом на другое сообщение
    if message.reply_to_message:
        try:
            # Удаляем сообщение, на которое ответили
            bot.delete_message(message.chat.id, message.reply_to_message.message_id)
            
            # Удаляем саму команду /delete
            bot.delete_message(message.chat.id, message.message_id)
            
            print(f"Сообщение {message.reply_to_message.message_id} удалено администратором {message.from_user.id}")
            
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")
            bot.reply_to(message, "Не удалось удалить сообщение. Возможно, оно уже удалено или у бота нет прав.")
    else:
        bot.reply_to(message, "Чтобы удалить сообщение, ответьте на него командой /delete")

@bot.message_handler(commands=['ban'])
def ban_user_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав для бана пользователей.")
        return
    
    if not message.reply_to_message:
        bot.reply_to(message, "ℹ Чтобы забанить пользователя, ответьте на его сообщение командой /ban")
        return
    
    try:
        user_to_ban = message.reply_to_message.from_user
        chat_id = message.chat.id
        
        # Получаем корректное имя пользователя
        user_name = get_user_name(user_to_ban.id, chat_id)
        
        # 1. Баним пользователя
        bot.ban_chat_member(chat_id=chat_id, user_id=user_to_ban.id)
        
        # 2. Удаляем команду /ban и сообщение, на которое ответили
        bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        bot.delete_message(chat_id=chat_id, message_id=message.reply_to_message.message_id)
        
        # 3. Отправляем уведомление
        ban_msg = bot.send_message(
            chat_id=chat_id,
            text=f"⛔ Пользователь {user_name} забанен.",
            parse_mode="HTML",
            disable_notification=True
        )
        
        # 4. Удаляем уведомление через 20 секунд
        delete_message_after_delay(chat_id, ban_msg.message_id, bot, delay=20)
        
        # Логируем действие
        log_user_action(message, f"забанил пользователя {user_name}")
        
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}"
        if "administrator" in str(e).lower():
            error_msg = "⚠ Нельзя забанить администратора"
        elif "rights" in str(e).lower():
            error_msg = "🔒 У бота недостаточно прав"
        bot.reply_to(message, error_msg)
        print(f"Ошибка при бане пользователя: {e}")

# ID стикера для ответа (замените на нужный)
DEATH_STICKER_ID = "CAACAgIAAxkBAAEOurJoUxggzyeaCqvdxffnUvoqhbXyjwAChycAAkyc2EgHFZIB1hcAAeY2BA"  # Вставьте реальный file_id стикера
#Функция для отправки стикера на слова сдохнуть
def check_death_word_and_respond(message):
    """Проверяет наличие слова 'сдохнуть' и отвечает стикером"""
    
    # Получаем слова из сообщения и лемматизируем их
    words = message.text.lower().split()
    lemmatized_words = lemmatize_words(words)
    
    # Лемматизируем искомое слово для сравнения
    target_word = lemmatize_words(["сдохнуть", "умереть", "добить", "убить"])[0]
    
    print(f"Ищем слово: {target_word}")
    print(f"В словах: {lemmatized_words}")
    
    # Проверяем, есть ли искомое слово в сообщении
    if target_word in lemmatized_words:
        print(f"Найдено слово '{target_word}' в сообщении!")
        
        try:
            # Отправляем стикер в ответ
            bot.send_sticker(
                chat_id=message.chat.id,
                sticker=DEATH_STICKER_ID,
                reply_to_message_id=message.message_id
            )
            print("Стикер отправлен!")
            
        except Exception as e:
            print(f"Ошибка при отправке стикера: {e}")
            # Если стикер не отправился, можно отправить текст
            bot.reply_to(message, "💀")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    global is_paused, last_message_deleted, deleted_messages_log, stats
    if is_paused:
        return
    else:
        print("Новое сообщение получено!")
        print("Текст сообщения:", message.text)
    
        # Обновляем статистику через handle_message
        handle_message(message, bot)
    
        # Проверяем длину сообщения
        words = message.text.split()
        if len(words) < 5:
            print(f"Сообщение от {message.from_user.username} содержит меньше 5 слов. Пропускаем.")
            check_death_word_and_respond(message)
            return
    
        # Рассчитываем средний риск
        average_risk = calculate_risk_with_tracking(message)
    
        # Проверяем, превышает ли риск порог
        if average_risk >= 2.5:
            print(f"Сообщение от {message.from_user.username} превысило порог риска.")
            try:
                # Обновляем счетчик удаленных сообщений
                chat_id = message.chat.id
                if chat_id in stats:
                    stats[chat_id]["deleted_messages_count"] += 1
                    save_stats()  # Сохраняем статистику после обновления счетчика

                # Получаем имя пользователя
                user_name = get_user_name(message.from_user.id, message.chat.id)
                
                # Сохраняем информацию об удаляемом сообщении
                deleted_messages_log[message.message_id] = {
                    "text": message.text,
                    "user_id": message.from_user.id,
                    "timestamp": datetime.now(),
                    "words": last_all_words.copy()
                }
                
                # Создаём текст уведомления с цитатой
                notification_text = (
                    f"❌ Удалено сообщение от {user_name}:\n\n"
                    f"> {message.text}\n\n"
                    f"Причина: подозрение на рекламу"
                )
                
                # Удаляем исходное сообщение
                bot.delete_message(message.chat.id, message.message_id)
                
                # Отправляем уведомление с кнопками
                keyboard = create_complaint_keyboard(message.message_id)
                msg = bot.send_message(
                    chat_id=message.chat.id, 
                    text=notification_text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                    disable_notification=True
                )

                # Удаляем сообщение с уведомлением через 30 секунд
                delete_message_after_delay(message.chat.id, msg.message_id, bot, delay=30)

                print(f"Сообщение {message.message_id} удалено.")
                last_message_deleted = True
                message_repeat_count = 0
                
                # Положительное обучение
                if last_matched_words or last_matched_phrases:
                    print("Автообучение: подтверждаем правильность удаления")
                    manual_learn(positive_feedback=True, multiplier=0.5)
                    
            except Exception as e:
                print(f"Ошибка при удалении: {e}")
                last_message_deleted = False
        else:
            print("Сообщение безопасно.")
            last_message_deleted = False
            check_death_word_and_respond(message)

# Функция для очистки старых записей из лога (вызывать периодически)
def cleanup_old_logs():
    """Удаляет записи старше 1 часа из лога удаленных сообщений"""
    global deleted_messages_log
    current_time = datetime.now()
    to_delete = []
    
    for msg_id, info in deleted_messages_log.items():
        if current_time - info["timestamp"] > timedelta(hours=1):
            to_delete.append(msg_id)
    
    for msg_id in to_delete:
        del deleted_messages_log[msg_id]
    
    print(f"Очищено {len(to_delete)} старых записей из лога")

bot.polling(none_stop=True, interval=0)