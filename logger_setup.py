# -*- coding: cp1251 -*-
import logging
import os
from datetime import datetime

def setup_loggers():
    # ������� ����� ��� �����, ���� � ���
    log_dir = "bot_logs"
    os.makedirs(log_dir, exist_ok=True)

    # ������� �������� ��� ����� ������ � ����
    command_logs_dir = os.path.join(log_dir, "command_logs")
    chat_logs_dir = os.path.join(log_dir, "chat_logs")
    os.makedirs(command_logs_dir, exist_ok=True)
    os.makedirs(chat_logs_dir, exist_ok=True)

    # ���������� ���������� ��� ����� �� ������ �������� �������
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    command_log_file = os.path.join(command_logs_dir, f"command_log_{current_time}.txt")
    chat_log_file = os.path.join(chat_logs_dir, f"chat_log_{current_time}.txt")

    # ��������� ����������� ��� ������
    command_logger = logging.getLogger("command_logger")
    command_logger.setLevel(logging.INFO)
    command_handler = logging.FileHandler(command_log_file, encoding='cp1251')  # ��������� ��������� ANSI
    command_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    command_logger.addHandler(command_handler)

    # ��������� ����������� ��� ����
    chat_logger = logging.getLogger("chat_logger")
    chat_logger.setLevel(logging.INFO)
    chat_handler = logging.FileHandler(chat_log_file, encoding='cp1251')  # ��������� ��������� ANSI
    chat_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    chat_logger.addHandler(chat_handler)

    print(f"��������� command_handler: {command_handler.stream.encoding}")
    print(f"��������� chat_handler: {chat_handler.stream.encoding}")

    command_handler = logging.FileHandler(command_log_file, encoding='cp1251')
    print(f"��������� command_handler: {command_handler.stream.encoding}")

    chat_handler = logging.FileHandler(chat_log_file, encoding='cp1251')
    print(f"��������� chat_handler: {chat_handler.stream.encoding}")

    return command_logger, chat_logger