# -*- coding: cp1251 -*-

import json
import telebot
import time
from logger_setup import setup_loggers

bot = telebot.TeleBot('7700621878:AAF2bmL1zNP6CWtAlCuquVO9_pr1ww21Y7Q')

# ������������� ��������
command_logger, chat_logger = setup_loggers()

# ������� ��� ����������� �������� ������������
def log_user_action(message, action):
    user_info = f"������������ {message.from_user.username} (ID: {message.from_user.id})"
    command_logger.info(f"{user_info} {action}")

# ������� ��� ����������� ��������� ����
def log_chat_message(message):
    user_info = f"������������ {message.from_user.username} (ID: {message.from_user.id})"
    chat_logger.info(f"{user_info} �������� ���������: {message.text}")

# ��������� ������� /logs
@bot.message_handler(commands=['logs'])
def flush_logs(message):
    # ������������� ���������� ���� � ����
    for handler in command_logger.handlers:
        handler.flush()
    for handler in chat_logger.handlers:
        handler.flush()
    bot.reply_to(message, "���� �������� � ����.")

# ��������� ������� /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "������! � ������ ������ �������� �� ������. ������ /help, ����� ������, ��� � ����.")
    log_user_action(message, "�������� ������� /start")

# ��������� ������� /help
@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "/kick - ������� ������������")
    log_user_action(message, "�������� ������� /help")

# �������0
@bot.message_handler(commands=['xyu'])
def xyu(message):
    bot.reply_to(message, "������ ��� ��� ���� �����������")
    log_user_action(message, "�������� ������� /xyu")

#��������� ����
@bot.message_handler(commands=['kick'])
def kick_user(message):
    if message.reply_to_message:
        chat_id = message.chat.id
        user_id = message.reply_to_message.from_user.id
        user_status = bot.get_chat_member(chat_id, user_id).status
        if user_status == 'administrator' or user_status == 'creator':
            bot.reply_to(message, "���������� ������� ��������������.")
        else:
            bot.kick_chat_member(chat_id, user_id)
            bot.reply_to(message, f"������������ {message.reply_to_message.from_user.username} ��� ������.")
    else:
        bot.reply_to(message, "��� ������� ������ ���� ������������ � ����� �� ��������� ������������, �������� �� ������ �������.")

#�������������� ��������� ��� ����� � ��� ������ ������������
@bot.message_handler(content_types=['new_chat_members'])
def greet_new_members(message):
    for new_member in message.new_chat_members:
        # ���������� ��������� � ������
        bot.send_message(
            message.chat.id,
            f"������, {new_member.first_name}! ���� �� �� ������, �� ������ ��� ������� https://telegra.ph/ixtersrules-09-04."
        )

'''
@bot.message_handler(commands=['info'])
def send_chat_info(message):
    try:
        # �������� ���������� � ����
        chat_info = bot.get_chat(message.chat.id)
        
        # ���������� ���������� ������������
        bot.reply_to(message, f"���������� � ����:\n"
                              f"ID: {chat_info.id}\n"
                              f"���: {chat_info.type}\n"
                              f"��������: {chat_info.title}\n"
                              f"��� ������������: {chat_info.username}\n"
                              f"��������: {chat_info.description}\n"
                              f"������-�����������: {chat_info.invite_link}")
    except Exception as e:
        bot.reply_to(message, f"������: {e}")
'''


'''
#����������
@bot.message_handler(func=lambda message: True) 
def echo_all(message): 
    bot.reply_to(message, message.text)
'''   
'''
    # ��������� ���� ��� ������
    with open("message%20ratios.txt", "r") as file:
        for line in file:  # ������ ���� ���������
            if len(line) > 2: 
                stripped_line = line[:-3]  # �������� ��������� ��� �������
                if stripped_line in line: # ��������� ������ �� ������ ������ � ������
                    line_number = line.replace(stripped_line, '') # �������� ������ ������ �� �������
                    bot.reply_to(message, line_number)
                bot.reply_to(message, stripped_line)
                time.sleep(4)
'''

# ������ ����� � ������������ �������
try:
    with open('forbidden_message.txt', 'r', encoding='cp1251') as file:  # ��������� ��������� cp1251
        forbidden_dict = json.load(file)
        print("���������� �����:", forbidden_dict)  # �������
except Exception as e:
    print(f"������ ��� ������ �����: {e}")
    forbidden_dict = {}  # ���� ���� �� ������� ���������, ���������� ������ �������

# ������� ��� �������� ����������
stats = {}

# ������� ��� ������� �����
def calculate_risk(message):
    words = message.text.lower().split()  # ��������� ��������� �� �����
    total_risk = 0
    
    # ������� ����� ����
    for word in words:
        if word in forbidden_dict:
            total_risk += forbidden_dict[word]
    
    # ���������� ������� ���� (����� ���� / ���������� ����)
    return total_risk / len(words) if len(words) > 0 else 0

# ���������� ������� /stats
@bot.message_handler(commands=['stats'])
def chat_stats(message):
    chat_id = message.chat.id
    
    # ���� ���������� ��� ����� ���� �����������, ������ �
    if chat_id not in stats:
        stats[chat_id] = {
            "message_count": 0,
            "user_count": 0,
            "deleted_messages_count": 0,  # ������� �������� ���������
            "users": {}  # ������� ��� ���������� �������������
        }
        bot.reply_to(message, "���������� ���� ����������������.")
    else:
        # ���� ���������� ����, ������� �
        bot.reply_to(message, f"���������� ����:\n"
                              f"���������: {stats[chat_id]['message_count']}\n"
                              f"�������������: {stats[chat_id]['user_count']}\n"
                              f"�������� ���������: {stats[chat_id]['deleted_messages_count']}")
        log_user_action(message, "�������� ������� /stats")

# ���������� ������� /mystats (���������� ���������� ������������)
@bot.message_handler(commands=['mystats'])
def user_stats(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # ���������, ���� �� ���������� ��� ����� ���� � ������������
    if chat_id in stats and user_id in stats[chat_id]["users"]:
        user_stat = stats[chat_id]["users"][user_id]
        bot.reply_to(message, f"���� ����������:\n"
                              f"���������: {user_stat['message_count']}\n"
                              f"��������� ���������: {user_stat['last_message']}")
    else:
        bot.reply_to(message, "���� ���������� �����������.")
    log_user_action(message, "�������� ������� /mystats")

# ���������� ���� ���������
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    message_id = message.message_id  # ID ��������� ��� ��������
    
    # ���� ���������� ��� ����� ���� �����������, ������ �
    if chat_id not in stats:
        stats[chat_id] = {
            "message_count": 0,
            "user_count": 0,
            "deleted_messages_count": 0,  # ������� �������� ���������
            "users": {}  # ������� ��� ���������� �������������
        }
    
    # ��������� ���������� ����
    stats[chat_id]["message_count"] += 1
    
    # ��������� ���������� ������������
    if user_id not in stats[chat_id]["users"]:
        stats[chat_id]["users"][user_id] = {
            "message_count": 0,
            "last_message": None
        }
        stats[chat_id]["user_count"] += 1
    
    stats[chat_id]["users"][user_id]["message_count"] += 1
    stats[chat_id]["users"][user_id]["last_message"] = message.text

    # ��������� ����� ���������
    words = message.text.split()
    if len(words) < 10:  # ���� ��������� ������ 10 ����, ����������
        print(f"��������� �� {message.from_user.username} �������� ������ 10 ����. ����������.")  # �������
        return
    
    # ������������ ������� ����
    average_risk = calculate_risk(message)
    print(f"������� ���� ���������: {average_risk}")  # �������
    
    # ���������, ��������� �� ���� �����
    if average_risk > 10:  # ����� �����
        print(f"��������� �� {message.from_user.username} ��������� ����� �����.")  # �������
        try:
            # ����������� ������� �������� ���������
            stats[chat_id]["deleted_messages_count"] += 1
            
            # ������� ���������
            bot.delete_message(chat_id, message_id)
            print(f"��������� {message_id} �������.")  # �������
            
            # ������ ������������
            bot.kick_chat_member(chat_id, user_id)
            bot.send_message(chat_id, f"������������ {message.from_user.username} ��� ������ �� ���� �� ��������� ������.")
            
            # �������� ��� ������������
            log_user_action(message, "��� ������ �� ���� �� ��������� ������")
        except Exception as e:
            print(f"������: {e}")  # �������
    else:
        print("��������� ���������.")  # �������






#�������� �� ������������ �������� �������
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def handle_other_commands(message):
    if message.text != '/start':  # ���������, ��� ��� �� /start
        bot.reply_to(message, "������, � �� ���� ����� �������, ���� /help, ����� ������.")

#�������� ��������� ���� �� ���������
bot.polling(none_stop=True, interval=0)

