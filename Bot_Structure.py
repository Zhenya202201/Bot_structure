import telebot
from telebot import types
import g4f
import time
import concurrent.futures
import random
import os
from flask import Flask
from threading import Thread

# --- НАСТРОЙКИ ---
TOKEN = '8249100655:AAFgvtY4AotMoJXyja75n4iS-g-M7hwMg18'
PASSWORD = "jeka3131"
VERSION = "v3.8 Armor Edition"
AUTHOR = "𝕵𝖊𝖐𝖆"

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=4)
app = Flask('')

@app.route('/')
def home(): return "Бот работает 24/7"

def run_flask():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

user_data = {}

# Пункт 7: Уникализация текста
def unique_text(text):
    if not text: return text
    chars = {'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x'}
    letters = list(text)
    for i in range(len(letters)):
        if letters[i].lower() in chars and random.random() < 0.15:
            new_char = chars[letters[i].lower()]
            letters[i] = new_char.upper() if letters[i].isupper() else new_char
    return "".join(letters)

def main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🚀 Новый запрос"), types.KeyboardButton("🔄 Ещё варианты"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_message(message.chat.id, f"⚙️ **SYSTEM ONLINE**\nВерсия: `{VERSION}`\nАвтор: `{AUTHOR}`\n\nВведите пароль:")
        bot.register_next_step_handler(message, check_password)
    except: pass

def check_password(message):
    if message.text == PASSWORD:
        bot.send_message(message.chat.id, f"✅ **ДОСТУП ОТКРЫТ**\nДобро пожаловать, {AUTHOR}", reply_markup=main_markup())
    else:
        bot.send_message(message.chat.id, "❌ Отказ. Еще раз:")
        bot.register_next_step_handler(message, check_password)

@bot.message_handler(func=lambda m: m.text == "🚀 Новый запрос")
def start_form(message):
    bot.send_message(message.chat.id, "👤 Введите ФИО:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_fio)

def process_fio(message):
    user_data[message.chat.id] = {'fio': message.text}
    bot.send_message(message.chat.id, "💼 Должность:")
    bot.register_next_step_handler(message, process_post)

def process_post(message):
    user_data[message.chat.id]['post'] = message.text
    bot.send_message(message.chat.id, "🏫 Организация:")
    bot.register_next_step_handler(message, process_org)

def process_org(message):
    user_data[message.chat.id]['org'] = message.text
    generate_ai(message)

@bot.message_handler(func=lambda m: m.text == "🔄 Ещё варианты")
def generate_ai(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "Сначала введите данные!")
        return

    bot.send_message(chat_id, "🛡️ **Генерация Anti-Ban...**")
    data = user_data[chat_id]
    headers = ["Представляюсь", "Разрешите представиться", "Меня зовут", "Я", "С вами", "Позвольте представиться", "Моё имя", "Представляю себя", "К вам обращается", "Хотел бы представиться", "Позвольте назвать себя", "Обращаюсь к вам", "Я являюсь", "Приветствую вас", "С вами на связи", "Давайте познакомимся", "Кратко о себе", "Могу представиться", "Считаю нужным представиться", "Для начала представлюсь"]
    
    prompt = f"Напиши ровно 20 строк. Каждая с нового слова: {', '.join(headers)}. Данные: {data['fio']}, {data['post']}, {data['org']}. Всё в РОДИТЕЛЬНОМ ПАДЕЖЕ. Только список."

    # Функция вызова нейросети обернута в try
    def ask_ai():
        try:
            return g4f.ChatCompletion.create(model=g4f.models.default, messages=[{"role": "user", "content": prompt}])
        except Exception as e:
            return f"Error: {e}"

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(ask_ai)
        try:
            res = future.result(timeout=30)
            if res and "Error" not in res:
                bot.send_message(chat_id, unique_text(res), reply_markup=main_markup())
            else:
                bot.send_message(chat_id, "⚠️ Сбой нейросети. Жми 'Ещё варианты'.", reply_markup=main_markup())
        except Exception:
            bot.send_message(chat_id, "⚠️ Время вышло. Попробуй снова.", reply_markup=main_markup())

# ГЛАВНЫЙ ЦИКЛ С ПЕРЕЗАГРУЗКОЙ ПОСЛЕ ВЫЛЕТА
if __name__ == '__main__':
    keep_alive()
    print(f"Бот {VERSION} запущен...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            print(f"Критический сбой: {e}")
            time.sleep(5) # Пауза перед авто-рестартом

