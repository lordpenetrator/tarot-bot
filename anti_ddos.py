# anti_ddos.py
import time
from collections import defaultdict, deque
from functools import wraps
import threading
from datetime import datetime
import telebot

class SimpleAntiDDoS:
    def __init__(self, bot_instance):
        self.request_limits = defaultdict(deque)
        self.max_requests = 7  # Максимальное количество запросов
        self.time_window = 30  # Окно времени в секундах
        self.ban_time = 300    # Время бана в секундах (5 минут)
        self.ban_list = {}     # {user_id: (unban_time, notification_sent)}
        self.lock = threading.RLock()
        self.bot = bot_instance
        self.cleaner_thread = threading.Thread(target=self._clean_old_records, daemon=True)
        self.cleaner_thread.start()

    def _log_attack(self, user_id, username, attack_type):
        """Логирование атаки в консоль"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = (
            f"[{timestamp}] DDoS Alert! User ID: {user_id} | "
            f"Username: @{username if username else 'unknown'} | "
            f"Attack Type: {attack_type}"
        )
        print("\033[91m" + log_message + "\033[0m")  # Красный цвет в консоли

    def _clean_old_records(self):
        """Очистка старых записей"""
        while True:
            time.sleep(30)
            current_time = time.time()
            with self.lock:
                # Очистка старых запросов
                for user_id in list(self.request_limits.keys()):
                    while (self.request_limits[user_id] and 
                           current_time - self.request_limits[user_id][0] > self.time_window):
                        self.request_limits[user_id].popleft()
                    
                    if not self.request_limits[user_id]:
                        del self.request_limits[user_id]
                
                # Очистка истекших банов
                for user_id in list(self.ban_list.keys()):
                    if current_time > self.ban_list[user_id][0]:
                        del self.ban_list[user_id]

    def _send_block_notification(self, message, ban_duration):
        """Отправка уведомления о блокировке"""
        try:
            if ban_duration >= 60:
                duration = f"{ban_duration//60} минут"
            else:
                duration = f"{ban_duration} секунд"
            
            self.bot.send_message(
                message.chat.id,
                f"⛔ Вы заблокированы на {duration} за чрезмерную активность"
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")

    def __call__(self, func):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            user_id = message.from_user.id
            username = message.from_user.username
            current_time = time.time()

            with self.lock:
                # Проверка бана
                if user_id in self.ban_list:
                    unban_time, notification_sent = self.ban_list[user_id]
                    
                    if current_time < unban_time:
                        if not notification_sent:
                            self._log_attack(user_id, username, "BAN applied")
                            self.ban_list[user_id] = (unban_time, True)  # Помечаем как отправленное
                            self._send_block_notification(message, self.ban_time)
                        return  # Блокируем выполнение команды
                    else:
                        del self.ban_list[user_id]

                # Очистка старых запросов
                while (self.request_limits[user_id] and 
                       current_time - self.request_limits[user_id][0] > self.time_window):
                    self.request_limits[user_id].popleft()

                # Проверка лимита запросов
                if len(self.request_limits[user_id]) >= self.max_requests:
                    self._log_attack(user_id, username, "Rate limit exceeded")
                    self.ban_list[user_id] = (current_time + self.ban_time, False)
                    return  # Блокируем выполнение команды

                # Фиксация запроса
                self.request_limits[user_id].append(current_time)

            return func(message, *args, **kwargs)
        
        return wrapper