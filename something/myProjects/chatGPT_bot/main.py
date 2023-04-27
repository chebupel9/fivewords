import asyncio
import logging
import json
import tiktoken
import requests
import os

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import filters
from aiogram.utils import executor
from aiogram.utils.exceptions import TelegramAPIError
from aiogram.types import ChatActions
from db import Database
from chatgpt import gpt_prompt, gen_image, audio_to_text


logging.basicConfig(level=logging.INFO)
bot = Bot(token='BOT_TOKEN')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database('database/database.db')

async def anti_flood(*args, **kwargs):
    message = args[0]
    rate = kwargs['rate']
    mes = await message.reply("⚠️Подождите!")
    for i in range(rate):
        await mes.edit_text(f'⚠️Следующий запрос можно отправить через {rate - i} сек.')
        await asyncio.sleep(1)
    await mes.delete()

# Функция для подсчета токенов в запросе
def count_tokens(messages, model="gpt-3.5-turbo-0301"):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += -1
    num_tokens += 2
    return num_tokens


# Хэндлер для обработки команды /start
@dp.message_handler(commands='start')
async def start(message: types.Message):
    text = f"👋 *Привет, я ChatGPT - телеграм-бот, созданный, чтобы помочь вам в любых" \
           f" вопросах и разговорах! Я основан на мощной технологии искусственного интеллекта GPT-3.5, и я готов " \
           f"ответить на ваши вопросы, " \
           f"поделиться своими знаниями и просто поболтать.*\n\n" \
           f"📋 Доступные команды:\n" \
           f"👉 `!img` _[запрос]_ – генерирует изображение по запросу\n" \
           f"👉 `!bugfix` _[код]_ – исправляет ошибки в коде\n" \
           f"👉 `!ru` _[текст]_ – переводит текст на русский язык\n" \
           f"👉 `!en` _[текст]_ – переводит текст на английский язык\n\n" \
           f"🔥 *Дополнительно, ChatGPT может расшифровывать аудиофайлы и голосовые сообщения размером до 2 мб. " \
           f"Просто отправьте аудиофайл боту, и он с легкостью справится с задачей.*"
    if not db.user_exists(message.from_user.id):
        # Добавляем пользователя в БД,если его нет в БД
        db.add_user(message.from_user.id)
        await message.answer(text, parse_mode=types.ParseMode.MARKDOWN)
    else:
        await message.answer(text, parse_mode=types.ParseMode.MARKDOWN)


# Хэндлер для обработки команды !img [запрос]
@dp.message_handler(commands='img', commands_prefix='!')
@dp.throttled(anti_flood, rate=10)
async def generate_image(message: types.Message):
    # Отлавливаем ошибки
    try:
        # Получаем запрос пользователя
        prompt = message.text.split(' ', maxsplit=1)
        await message.answer(f'⏱ Генерация...')
        # Запускаем функцию gen_image в отдельном потоке и передаем в нее запрос от пользователя
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, gen_image, prompt[1])
        # В случае успеха gen_image возвращает ссылку на изображение, иначе возвращает False
        if res:
            # Отправляем get-запрос на страницу с изображением
            image = requests.get(res)
            # Отправляем пользователю полученное изображение с подписью
            await bot.send_photo(message.from_user.id,
                                 photo=image.content,
                                 caption=f'✅ Изображение по запросу "{prompt[1]}"')
        else:
            await message.reply('❌ Некорректный запрос')
    except:
        await message.reply('❌ Некорректный запрос')


# Хэндлер для обработки комманд !ru, !en, !bugfix
@dp.message_handler(commands=['ru', 'en', 'bugfix'], commands_prefix='!')
@dp.throttled(anti_flood, rate=10)
async def short_com(message: types.Message):
    # Отлавливаем ошибки
    try:
        # Разделяем сообщение на комманду и запрос
        command, prompt = message.text.split(' ', maxsplit=1)

        short_command = {
            '!en': 'Переведи на английский:',
            '!ru': 'Переведи на русский:',
            '!bugfix': 'Исправь ошибки в коде:\n'
        }
        # Формируем массив с запросом
        user_prompt = [{"role": "user", "content": f"{short_command[command]} {prompt}"}]
        # Отправляем пользователю событие "набор сообщения" в чате
        await bot.send_chat_action(message.from_user.id, ChatActions.TYPING)
        # Запускаем функцию gpt_prompt в потоке и передаем массив с запросом
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, gpt_prompt, user_prompt)
        # Отлавливаем ошибки связанные с разметкой текста
        try:
            await message.reply(response.choices[0].message.content, parse_mode=types.ParseMode.MARKDOWN)
        except TelegramAPIError:
            # Если возникла ошибка в обработке разметки, то отправляем сообщение без обработки разметки
            await message.reply(response.choices[0].message.content)

    except:
        await message.reply('❌ Некорректный запрос')


# Хендлер для обработки комманды /clear
@dp.message_handler(commands='clear')
@dp.throttled(anti_flood, rate=5)
async def clear(message: types.Message):
    mes = await message.answer('🧹Очищаю чат...')
    # Обновляем чат пользователя в БД
    db.update_user_chat('[]', message.from_user.id)
    await asyncio.sleep(1)
    await mes.edit_text('✅ Чат очищен!')


# Хендлер для обработки текстовых сообщений
@dp.message_handler(filters.Text)
@dp.throttled(anti_flood, rate=10)
async def echo(message: types.Message):
    # Проверяем является ли полученное сообщение ответом на другое сообщение
    if message.reply_to_message is not None:
        # Разделяем сообщения
        replied_message = message.reply_to_message
        text = str(replied_message.text).replace('"', "``").replace("'", "`")
        # Создаем массив с запросом
        prompt = [{"role": "system", "content": f"{text}"}, {"role": "user", "content": f"{message.text}"}]
    else:
        question = str(message.text).replace('"', "``").replace("'", "`")
        user_chat = json.loads(db.get_user_chat(message.from_user.id))
        # Проверяем запрос на количество токенов (у API ограничение в 4097 токенов)
        if count_tokens(user_chat) >= 3800:
            # Удаляем ранние запросы пока количество токенов не станет меньше 3000
            while count_tokens(user_chat) > 3000:
                user_chat.pop(0)
        else:
            pass
        user_chat.append({"role": "user", "content": f"{question}"})
        prompt = user_chat

    await bot.send_chat_action(message.from_user.id, ChatActions.TYPING)
    # Запускаем функцию gpt_prompt в потоке и передаем запрос
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, gpt_prompt, prompt)

    if message.reply_to_message is not None:
        pass
    else:
        answer = str(response.choices[0].message.content).replace("'", "`").replace('"', '``')
        prompt.append({"role": "system", "content": f"{answer}"})
        db.update_user_chat(str(prompt), message.from_user.id)

    # Отлавливаем ошибки связанные с разметкой текста
    try:
        await message.reply(response.choices[0].message.content, parse_mode=types.ParseMode.MARKDOWN)
    except TelegramAPIError:
        # Если возникла ошибка в обработке разметки, то отправляем сообщение без обработки разметки
        await message.reply(response.choices[0].message.content)


# Хэндлер для обработки голосовых сообщений и аудиофайлов
@dp.message_handler(content_types=[types.ContentType.VOICE, types.ContentType.AUDIO])
@dp.throttled(anti_flood, rate=10)
async def handle_audio_voice(message: types.Message):
    audio_file = None
    # Обработка голосовых сообщений
    if message.voice:
        if int(message.voice.file_size) < 2000000:
            if os.path.isfile(f'user_audio/{message.from_user.id}.ogg'):
                await message.reply('⏱ Подождите, идет расшифровка другого файла...')
            else:
                await message.voice.download(destination_file=f'user_audio/{message.from_user.id}.ogg')
                audio_file = f'user_audio/{message.from_user.id}.ogg'
        else:
            await message.answer('❌ Большой размер файла')
    # Обработка аудиофайлов
    elif message.audio:
        formats = ['audio/m4a', 'audio/mp3', 'audio/webm', 'audio/mp4', 'audio/mpga', 'audio/wav', 'audio/mpeg']
        if message.audio.mime_type in formats:
            if int(message.audio.file_size) < 2000000:
                if os.path.isfile(f'user_audio/{message.from_user.id}.mp3'):
                    await message.reply('⏱ Подождите, идет расшифровка другого файла...')
                else:
                    await message.audio.download(destination_file=f'user_audio/{message.from_user.id}.mp3')
                    audio_file = f'user_audio/{message.from_user.id}.mp3'
            else:
                await message.answer('❌ Большой размер файла')
        else:
            await message.answer('❌ Неподдерживаемый формат файла')
    # Запускаем функцию audio_to_text в потоке
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, audio_to_text, audio_file)
    if not response:
        # Если слова не были распознаны
        await message.reply(f'_Звуки тишины..._', parse_mode=types.ParseMode.MARKDOWN)
    else:
        await message.reply(f'_{response}_', parse_mode=types.ParseMode.MARKDOWN)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)