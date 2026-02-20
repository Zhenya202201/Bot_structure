import telebot
from telebot import types
import g4f
import time
import concurrent.futures
import random
import os
from flask import Flask
from threading import Thread

TOKEN = '8249100655:AAFgvtY4AotMoJXyja75n4iS-g-M7hwMg18'
PASSWORD = "jeka3131"
VERSION = "v3.9 Fix Edition"
AUTHOR = "𝕵𝖊𝖐𝖆"

bot = telebot.TeleBot(TOKEN, threaded=True)
app = Flask('')

@app.route('/')
def home(): return "OK"

def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))))
    t.daemon = True
    t.start()

user_data = {}

def unique_text(text):
    chars = {'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x'}
    return "".join([chars.get(c.lower(), c) if random.random() < 0.1 else c for c in text])

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"⚙️ {VERSION}\nАвтор: {AUTHOR}\nПароль:")
    bot.register_next_step_handler(message, check_password)

def check_password(message):
    if message.text == PASSWORD:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🚀 Новый запрос", "🔄 Ещё варианты")
        bot.send_message(message.chat.id, "✅ Доступ разрешен", reply_markup=markup)
    else:
        bot.register_next_step_handler(bot.send_message(message.chat.id, "❌ Нет. Еще раз:"), check_password)

@bot.message_handler(func=lambda m: m.text == "🚀 Новый запрос")
def ask_fio(message):
    bot.send_message(message.chat.id, "👤 ФИО:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, lambda m: save_data(m, 'fio', "💼 Должность:", ask_post))

def ask_post(message):
    save_data(message, 'post', "🏫 Организация:", ask_org)

def ask_org(message):
    save_data(message, 'org', "⚡ Генерирую...", generate_ai)

def save_data(message, key, next_text, next_step):
    user_data.setdefault(message.chat.id, {})[key] = message.text
    bot.send_message(message.chat.id, next_text)
    bot.register_next_step_handler(message, next_step)

def generate_ai(message):
    chat_id = message.chat.id
    if chat_id not in user_data or 'org' not in user_data[chat_id]:
        user_data.setdefault(chat_id, {})['org'] = message.text
    
    d = user_data[chat_id]
    headers = [
        "Представляюсь", "Разрешите представиться", "Меня зовут", "Я", "С вами",
        "Позвольте представиться", "Моё имя", "Представляю себя", "К вам обращается",
        "Хотел бы представиться", "Позвольте назвать себя", "Обращаюсь к вам",
        "Я являюсь", "Приветствую вас", "С вами на связи", "Давайте познакомимся",
        "Кратко о себе", "Могу представиться", "Считаю нужным представиться", "Для начала представлюсь"
    ]
    
    # Теперь мы просим ИИ ТОЛЬКО правильно склонить ФИО и должность
    prompt = f"Склони в родительный падеж: {d['fio']} и {d['post']}. Напиши результат строго в одну строку через запятую. Например: Иванова Ивана Ивановича, директора."

    def ask():
        try:
            res = g4f.ChatCompletion.create(model=g4f.models.default, messages=[{"role":"user","content":prompt}])
            # Если ИИ ответил, склеиваем вручную для гарантии
            parts = res.replace('.', '').split(',')
            fio_sklon = parts[0].strip()
            post_sklon = parts[1].strip() if len(parts) > 1 else d['post']
            
            final_list = []
            for i, h in enumerate(headers):
                line = f"{i+1}. {h}, {fio_sklon}, {post_sklon} {d['org']}."
                final_list.append(unique_text(line))
            return "\n".join(final_list)
        except: return None

    with concurrent.futures.ThreadPoolExecutor() as ex:
        try:
            final_res = ex.submit(ask).result(timeout=30)
            bot.send_message(chat_id, final_res or "⚠️ Ошибка. Жми 'Ещё варианты'")
        except:
            bot.send_message(chat_id, "⚠️ Тайм-аут")

if __name__ == '__main__':
    keep_alive()
    bot.polling(none_stop=True)
    
