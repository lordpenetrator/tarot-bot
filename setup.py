import os
from pathlib import Path
import json
from limiter import TarotLimiter
import telebot
from telebot import TeleBot  # Добавьте эту строку в начало файла
from typing import Optional

class Config:
    """Конфигурация бота и проверки работоспособности"""
    
    def __init__(self):
        # Основные настройки
        self.BOT_TOKEN = os.getenv('BOT_TOKEN', '8175502782:AAGTNsCzaoZ_fWinvUDiCcGyBGdWTv08PeA')
        self.ADMIN_IDS = [123456789]  # Ваш ID в Telegram
        self.REQUEST_LIMITS = {
            'max_requests': 10,
            'time_window': 60,
            'cooldown': 5
        }
        
        # Пути к файлам
        self.PATHS = {
            'tarot_cards': Path('tarot_cards.json'),
            'tarot_images': Path('tarot_images'),
            'limiter_db': 'tarot_limits.db'
        }
        
        # Тексты для проверок
        self.CHECK_MESSAGES = {
            'success': "✓ {item} ({details})",
            'fail': "✗ {item} | Ошибка: {error}",
            'missing': "⚠ {item} отсутствует"
        }

    def run_health_checks(self):
        """Запуск всех проверок работоспособности"""
        print("\n" + "="*40)
        print("ПРОВЕРКА КОНФИГУРАЦИИ БОТА".center(40))
        print("="*40)
        
        checks = [
            ("Токен бота", self._check_bot_token),
            ("Файл карт Таро", self._check_tarot_cards),
            ("Изображения карт", self._check_tarot_images),
            ("База ограничений", self._check_limiter_db)
        ]
        
        results = []
        for name, check in checks:
            result, message = check()
            results.append(result)
            print(f"{'✓' if result else '✗'} {name}: {message}")
        
        print("="*40)
        if all(results):
            print("ВСЕ ПРОВЕРКИ УСПЕШНЫ".center(40))
        else:
            print("НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ".center(40))
        
        return all(results)

    def _check_bot_token(self):
        """Проверка валидности токена бота"""
        if not self.BOT_TOKEN or len(self.BOT_TOKEN) < 30:
            return False, "Неверный формат токена"
        
        bot = telebot.TeleBot(self.BOT_TOKEN)
        try:
            me = bot.get_me()
            return True, f"Бот @{me.username}"
        except Exception as e:
            return False, f"Ошибка подключения: {str(e)}"

    def _check_tarot_cards(self):
        """Проверка файла с картами Таро"""
        if not self.PATHS['tarot_cards'].exists():
            return False, "Файл не найден"
        
        try:
            with open(self.PATHS['tarot_cards'], 'r', encoding='utf-8') as f:
                cards = json.load(f)
                return True, f"Загружено {len(cards)} карт"
        except Exception as e:
            return False, f"Ошибка загрузки: {str(e)}"

    def _check_tarot_images(self):
        """Проверка директории с изображениями"""
        if not self.PATHS['tarot_images'].exists():
            return False, "Директория не найдена"
        
        try:
            images = list(self.PATHS['tarot_images'].glob('*.jpg'))
            return True, f"Найдено {len(images)} изображений"
        except Exception as e:
            return False, f"Ошибка проверки: {str(e)}"

    def _check_limiter_db(self):
        """Проверка работы базы ограничений"""
        try:
            limiter = TarotLimiter(self.PATHS['limiter_db'])
            test_id = 999999999  # Тестовый ID
            limiter.record_reading(test_id)
            status, _ = limiter.check_limit(test_id)
            limiter.clear()  # Очищаем тестовую запись
            return True, "База работает корректно"
        except Exception as e:
            return False, f"Ошибка базы: {str(e)}"
    def init_anti_ddos(self, bot_instance: TeleBot):
        """Инициализация защиты после создания бота"""
       # Импорт здесь чтобы избежать циклических зависимостей
        self.bot = bot_instance
        self.anti_ddos = SimpleAntiDDoS(bot_instance)
        return self.anti_ddos

    def handle_admin_command(self, cmd: str) -> Optional[str]:
        """Обработка команд администратора"""
        if not self.anti_ddos:
            return "Система защиты не инициализирована"
        
        cmd = cmd.strip().lower()
        
        if cmd == "unban all":
            if self.anti_ddos.clear_all_bans():
                return "✓ Все пользователи разблокированы"
            return "× Ошибка разблокировки"
        
        elif cmd.startswith("unban "):
            try:
                user_id = int(cmd.split()[1])
                if self.anti_ddos.unban_user(user_id):
                    return f"✓ Пользователь {user_id} разблокирован"
                return f"× Пользователь {user_id} не заблокирован"
            except (IndexError, ValueError):
                return "Использование: unban <user_id>"
        
        elif cmd == "list banned":
            banned = self.anti_ddos.get_banned_users()
            if banned:
                return "Заблокированные:\n" + "\n".join(f"- {uid}" for uid in banned)
            return "Нет заблокированных пользователей"
        
        return None
# Создаем экземпляр конфигурации для импорта в другие модули
config = Config()