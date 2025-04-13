import shelve
from datetime import datetime, timedelta

class TarotLimiter:
    def __init__(self, db_path='tarot_limits.db'):
        self.db_path = db_path
        self.total_readings = 0  # Сбор данных о раскладах пользователей
        self.warning_msg = (
            "Ай-ай-ай, у вас же уже есть трактование своего будущего!\n"
            "Если хотите его изменить, то полагайтесь на свои силы, "
            "а не на бездушного бота...\n\n"
            "Ну или попробуйте через {}"
        )
    
    def get_readings_count(self):
        """Возвращает общее количество сделанных раскладов"""
        return self.total_readings
    
    def check_limit(self, user_id):
        with shelve.open(self.db_path) as db:
            last_time = db.get(str(user_id))
            if last_time is None:
                return True, None
            
            time_left = last_time + timedelta(hours=24) - datetime.now()
            if time_left > timedelta(0):
                hours = time_left.seconds // 3600
                minutes = (time_left.seconds % 3600) // 60
                return False, f"{hours} часов {minutes} минут"
            return True, None
    
    def record_reading(self, user_id):
        with shelve.open(self.db_path) as db:
            db[str(user_id)] = datetime.now()
            self.total_readings += 1
    
    def send_warning(self, bot, chat_id):
        allowed, time_left = self.check_limit(chat_id)
        if not allowed and time_left:
            bot.send_message(chat_id, self.warning_msg.format(time_left))
    
    def clear(self):
        try:
            with shelve.open(self.db_path) as db:
                db.clear()
                self.total_readings = 0  # Сбрасываем счетчик при очистке
            return True
        except Exception:
            return False