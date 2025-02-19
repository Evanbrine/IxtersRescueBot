import logging
import os
from datetime import datetime

def setup_loggers():
    # Создаем папку для логов, если её нет
    log_dir = "bot_logs"
    os.makedirs(log_dir, exist_ok=True)

    # Создаем подпапки для логов команд и чата
    command_logs_dir = os.path.join(log_dir, "command_logs")
    chat_logs_dir = os.path.join(log_dir, "chat_logs")
    os.makedirs(command_logs_dir, exist_ok=True)
    os.makedirs(chat_logs_dir, exist_ok=True)

    # Генерируем уникальное имя файла на основе текущего времени
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    command_log_file = os.path.join(command_logs_dir, f"command_log_{current_time}.txt")
    chat_log_file = os.path.join(chat_logs_dir, f"chat_log_{current_time}.txt")

    # Настройка логирования для команд
    command_logger = logging.getLogger("command_logger")
    command_logger.setLevel(logging.INFO)
    command_handler = logging.FileHandler(command_log_file, encoding='utf-8')  # Указываем кодировку ANSI
    command_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    command_logger.addHandler(command_handler)

    # Настройка логирования для чата
    chat_logger = logging.getLogger("chat_logger")
    chat_logger.setLevel(logging.INFO)
    chat_handler = logging.FileHandler(chat_log_file, encoding='utf-8')  # Указываем кодировку ANSI
    chat_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    chat_logger.addHandler(chat_handler)

    print(f"Кодировка command_handler: {command_handler.stream.encoding}")
    print(f"Кодировка chat_handler: {chat_handler.stream.encoding}")

    command_handler = logging.FileHandler(command_log_file, encoding='utf-8')
    print(f"Кодировка command_handler: {command_handler.stream.encoding}")

    chat_handler = logging.FileHandler(chat_log_file, encoding='utf-8')
    print(f"Кодировка chat_handler: {chat_handler.stream.encoding}")

    return command_logger, chat_logger