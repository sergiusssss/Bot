from telebot import TeleBot
from Classes import Settings
from Classes.Logger import Logger


class TelegramBot:
    def __init__(self):
        self._user_bot = TeleBot(Settings.UserBot.token)
        self._admin_bot = TeleBot(Settings.AdminBot.token)
        self._log = Logger(self._admin_bot, Settings.logger_name, Settings.AdminBot.id)
        self._init_handlers()

    def start(self):
        self._user_bot.polling(none_stop=True, interval=1)

    def _text(self, message):
        self._user_bot.send_message(message.from_user.id, message.text)

    def _init_handlers(self):
        @self._user_bot.message_handler(content_types=['text'])
        def handle_text(message):
            self._text(message)

        @self._user_bot.message_handler(content_types=['photo'])
        def handle_text(message):
            pass
