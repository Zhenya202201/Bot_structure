import logging
import os
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import FSInputFile

# --- НАСТРОЙКИ ---
API_TOKEN = '8249100655:AAFgvtY4AotMoJXyja75n4iS-g-M7hwMg18'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

TRANSLIT_MAP = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ы':'y','э':'e','ю':'yu','я':'ya'}

def to_latin(text):
    return "".join(TRANSLIT_MAP.get(c, c) for c in text.lower())

def clean_phone_format(line):
    line = re.sub(r'\(\d{4}-\d{2}-\d{2}.*?\)', '', line)
    line = re.sub(r'\s*-\s*', '-', line)
    return line.replace('\n', '').replace('\r', '').strip()

def process_data(input_text):
    blocks = re.split(r'-{10,}', input_text)
    final_result = []
    logs = []
    
    total_in = 0
    clean_out = 0
    deleted_no_match = 0
    
    idx = 1
    for block in blocks:
        block = block.strip()
        if not block or "ИМЯ:" not in block: continue
        
        total_in += 1
        name_match = re.search(r'ИМЯ:\s*(.*)', block)
        full_name = name_match.group(1).strip() if name_match else "Unknown"
        
        # Данные для поиска
        name_parts = [p.lower() for p in re.findall(r'\w+', full_name) if len(p) > 2]
        latin_variants = [to_latin(p) for p in name_parts]
        all_variants = set(name_parts + latin_variants)
        
        raw_phones = re.findall(r'(\+7\d{10}.+)', block)
        best_candidate = None
        max_score = -1

        for p_line in raw_phones:
            p_clean = clean_phone_format(p_line)
            p_lower = p_clean.lower()
            
            # Проверка на совпадение
            has_match = any(v in p_lower for v in all_variants)
            strangers = ['viktor','ivan','sergey','dmitry','alexey','vladimir','nikolay']
            is_stranger = any(s in p_lower for s in strangers if s not in all_variants)

            if has_match and not is_stranger:
                score = 10 if ('@' in p_lower and '@none' not in p_lower) else 5
                if score > max_score:
                    max_score = score
                    best_candidate = p_clean

        if best_candidate:
            # Парсим остальные поля
            dob = re.search(r'Дата Рождения:\s*(.*)', block)
            income = re.search(r'Сумма годового дохода:\s*(.*)', block)
            
            res_block = (
                f"{idx}. ИМЯ: {full_name}\n"
                f"Дата Рождения: {dob.group(1).strip() if dob else ''}\n"
                f"Номер телефона: {best_candidate}\n"
                f"Сумма годового дохода: {income.group(1).strip() if income else '0'}\n"
                "------------------------------------------"
            )
            final_result.append(res_block)
            idx += 1
            clean_out += 1
        else:
            deleted_no_match += 1
            logs.append(f"УДАЛЕНО: {full_name} (Не найдено подходящего номера)")

    # Считаем процент
    percent = (clean_out / total_in * 100) if total_in > 0 else 0
    stats = (
        f"📊 **СТАТИСТИКА ОБРАБОТКИ**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📥 Всего блоков: {total_in}\n"
        f"✅ Чистых контактов: {clean_out}\n"
        f"❌ Удалено (не совпали): {deleted_no_match}\n"
        f"📈 Эффективность: {percent:.1f}%\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    return '\n'.join(final_result), '\n'.join(logs), stats

@dp.message(F.document)
async def handle_docs(message: types.Message):
    if not message.document.file_name.endswith('.txt'):
        return await message.answer("Пришли .txt файл")

    msg = await message.answer("⌛ Обрабатываю базу...")
    
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    
    if not os.path.exists('temp'): os.makedirs('temp')
    input_path = f"temp/in_{message.document.file_name}"
    await bot.download_file(file.file_path, input_path)

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result_txt, log_txt, stats_msg = process_data(content)
    
    # Сохраняем результат и лог
    res_path = f"temp/cleaned_{message.document.file_name}"
    log_path = f"temp/log_{message.document.file_name}"
    
    with open(res_path, 'w', encoding='utf-8') as f: f.write(result_txt)
    with open(log_path, 'w', encoding='utf-8') as f: f.write(log_txt)

    # Отправляем файлы
    await message.answer_document(FSInputFile(res_path), caption="📁 Очищенная база")
    await message.answer_document(FSInputFile(log_path), caption="📝 Лог удаления")
    await message.answer(stats_msg, parse_mode="Markdown")

    # Чистим временные файлы
    for p in [input_path, res_path, log_path]: 
        if os.path.exists(p): os.remove(p)
    await msg.delete()

@dp.message()
async def welcome(message: types.Message):
    await message.answer("Пришли файл .txt для глубокой чистки.")

if __name__ == '__main__':
    import asyncio
    asyncio.run(dp.start_polling(bot))
