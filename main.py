import telebot # библиотека для обращения к боту
import json
import random
import time
import os
import threading # чтобы распараллеливать процесссы
from telebot import apihelper
from pathlib import Path
from telebot import types
from limiter import TarotLimiter
from anti_ddos import SimpleAntiDDoS
from setup import config
limiter = TarotLimiter()



# Инициализация бота. 
bot = telebot.TeleBot(config.BOT_TOKEN)
anti_ddos = SimpleAntiDDoS(bot)
'''#def console_listener(limiter):
    #Ожидает команды администратора в консоли
    while True:
        cmd = input().strip().lower()
        
        if cmd == "stats":
            print(f"Всего раскладов сделано: {limiter.get_readings_count()}")
        elif cmd == "clear base":
            if limiter.clear():
                print("✓ База ограничений очищена")
            else:
                print("× Ошибка очистки базы")
        elif cmd == "help":
            print("Доступные команды:\n"
                  "stats - показать статистику\n"
                  "clear base - очистить базу ограничений\n"
                  "unban all - разблокировать всех\n"
                  "unban <user_id> - разблокировать пользователя\n"
                  "list banned - показать заблокированных")
        else:
            response = config.handle_admin_command(cmd)
            if response:
                print(response)
                '''

# Загрузка карт Таро
try:
    with open('tarot_cards.json', 'r', encoding='utf-8') as file:
        tarot_cards = list(json.load(file).values())  # Преобразуем значения словаря в список
except FileNotFoundError:
    tarot_cards = []
    print("Ошибка: Файл tarot_cards.json не найден")

# Путь к изображениям
tarot_images = Path(__file__).parent / "tarot_images"

# Хранилище данных пользователей
user_data = {}

# Главное меню
def show_main_menu(chat_id, full_greeting=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "Мой знак зодиака", 
        "Расклад Таро на неделю",
        "Задать вопрос",
        "Наш телеграм канал"
    ]
    markup.add(*[types.KeyboardButton(btn) for btn in buttons])
    
    if full_greeting:
        user = user_data.get(chat_id, {})
        name = user.get('name', 'друг')
        text = (
            f"Привет, {name}! 👋\n"
            "Я - бот-предсказатель. Я могу сделать расклад таро на неделю по вашему знаку зодиака.\n"
            "Важное замечание: цель моего существования сугубо развлекательная.\n"
            "Если всё будет хорошо, мой создатель будет развивать меня и добавлять интересные функции, "
            "и я смогу радовать вас больше :)\n"
            "Выберите действие из меню ниже:"
        )
    else:
        text = "Выберите действие:"
    
    bot.send_message(chat_id, text, reply_markup=markup)

# Обработчики команд
@bot.message_handler(commands=['start'])
@anti_ddos
def handle_start(message):
    user_data[message.chat.id] = {'name': message.from_user.first_name}
    show_main_menu(message.chat.id, full_greeting=True)

@bot.message_handler(func=lambda m: m.text == "Назад")
def handle_back(message):
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "Мой знак зодиака")
@anti_ddos
def ask_zodiac(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    zodiacs = [
        "♈ Овен", "♉ Телец", "♊ Близнецы",
        "♋ Рак", "♌ Лев", "♍ Дева",
        "♎ Весы", "♏ Скорпион", "♐ Стрелец",
        "♑ Козерог", "♒ Водолей", "♓ Рыбы"
    ]
    
    for i in range(0, len(zodiacs), 3):
        markup.add(*[types.KeyboardButton(z) for z in zodiacs[i:i+3]])
    
    markup.add(types.KeyboardButton("Назад"))
    bot.send_message(message.chat.id, "Выберите ваш знак зодиака:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text.startswith(s) for s in ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]))
def save_zodiac(message):
    # Инициализируем запись, если её нет
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {'name': message.from_user.first_name}
    
    try:
        zodiac = message.text.split(maxsplit=1)[1]
        user_data[message.chat.id]['zodiac'] = zodiac
        bot.send_message(message.chat.id, f"Ваш знак зодиака: {zodiac}")
        show_main_menu(message.chat.id)
    except Exception as e:
        print(f"Ошибка сохранения знака зодиака: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка, попробуйте ещё раз")

@bot.message_handler(func=lambda m: m.text == "Расклад Таро на неделю")
@anti_ddos
def make_tarot_reading(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Устанавливаю связь с космосом...")
    time.sleep(3)
    bot.send_message(chat_id, "Открываю канал космической энергии...")
    time.sleep(3)
    bot.send_message(chat_id, "Принимаю послания звёзд и планет...")
    time.sleep(3)
     # Проверка ограничения
    allowed, _ = limiter.check_limit(chat_id)
    if not allowed:
        limiter.send_warning(bot, chat_id)
        return
    
    if 'zodiac' not in user_data.get(chat_id, {}):
        bot.send_message(chat_id, "Пожалуйста, сначала выберите ваш знак зодиака!")
        return ask_zodiac(message)
    
    if not tarot_cards:
        bot.send_message(chat_id, "Извините, карты Таро временно недоступны.")
        return
    '''
    Самая главная функция этого бота. Из папки с картинками до этого мы взяли названия всех файлов,
    преобразовали их в список, взяли 3 рандомных, далее в цикле к каждой случайно отобранной карте случайно выбираем её положение, далее подтягивается трактование и картинка.
     Это всё происходит в цикле из трех итераций для начала, середины и конца недели.
    '''
    try:
        selected_cards = random.sample(tarot_cards, 3)  # Теперь tarot_cards - список
    except ValueError:
        bot.send_message(chat_id, "Недостаточно карт для расклада")
        return
    
    periods = ["Начало недели", "Середина недели", "Конец недели"]
    
    for i, card in enumerate(selected_cards):
        position = random.choice(['upright', 'reversed'])
        card_text = f"✨ {periods[i]}: {card[position]}"
        
        image_path = tarot_images / f"{card['id']}.jpg"
        if image_path.exists():
            with open(image_path, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption=card_text)
        else:
            bot.send_message(chat_id, card_text)
        
        if i < 2:
            time.sleep(3)

    limiter.record_reading(chat_id)
    
    time.sleep(3)
    show_main_menu(chat_id)

@bot.message_handler(func=lambda m: m.text == "Задать вопрос")
@anti_ddos
def handle_question(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Написать в телеграм", url="https://t.me/DarthPenetrator"))
    bot.send_message(message.chat.id, "Вы можете задать вопрос, написав мне в телеграм:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Просмотреть отзывы")
@anti_ddos
def handle_reviews(message): # почему то эта кнопка не высвечивается
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("тык", url="https://t.me/client_reviews_chat"))
    bot.send_message(message.chat.id, "Здесь вы сможете отзывы людей, которым я уже успел сделать расклад за 3 года :):", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Наш телеграм канал")
@anti_ddos
def handle_channel(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Подписаться на канал", url="https://t.me/best_in_the_world_gadalka_group"))
    bot.send_message(message.chat.id, "Можете подписаться на канал, здесь будет публиковаться время от времени авторский контент по тематике:", reply_markup=markup)


def polling_with_retry():
    """Функция с автоматическим перезапуском polling при ошибках"""
    retry_delay = 5  # Начальная задержка между попытками
    while True:
        try:
            print("Запуск polling...")
            bot.polling(
                none_stop=True,
                timeout=30,
                long_polling_timeout=25,
                allowed_updates=["message", "callback_query"]
            )
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 429:  # Too Many Requests
                retry_after = int(e.result.headers.get('Retry-After', 10))
                print(f"Превышен лимит запросов. Повтор через {retry_after} сек.")
                time.sleep(retry_after)
                retry_delay = min(retry_delay * 1.5, 60)  # Экспоненциальная задержка
            else:
                print(f"Ошибка Telegram API: {e}")
                time.sleep(retry_delay)
        except Exception as e:
            print(f"Критическая ошибка polling: {e}")
            time.sleep(retry_delay)
        finally:
            bot.stop_polling()  # Гарантированная очистка

if __name__ == '__main__':
    try:
        config.run_health_checks()
        print("Бот запущен. Команды:\nstats - статистика\nclear base - очистить ограничения\nhelp - помощь\nexit - выход")
        
        # Запуск polling с автоматическим восстановлением
        polling_thread = threading.Thread(target=polling_with_retry, daemon=True)
        polling_thread.start()
        
        # Обработка консольных команд
        while True:
            try:
                cmd = input().strip().lower()
                
                if cmd == "stats":
                    print(f"Всего раскладов: {limiter.get_readings_count()}")
                elif cmd == "clear base":
                    limiter.clear()
                    print("✓ База очищена")
                elif cmd == "help":
                    print("Доступные команды:\n"
                          "stats - статистика\n"
                          "clear base - очистка базы\n"
                          "exit - выход")
                elif cmd == "exit":
                    break
                    
            except Exception as e:
                print(f"Ошибка обработки команды: {e}")
                
    except KeyboardInterrupt:
        print("\nПолучен сигнал завершения...")
    finally:
        print("Остановка бота...")
        bot.stop_polling()
        print("Бот успешно остановлен")
