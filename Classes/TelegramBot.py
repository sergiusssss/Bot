from telebot import TeleBot
from telebot import types
from Classes.Settings import Settings
from Classes.Logger import Logger
from Classes.Status import Status


class TelegramBot:
    def __init__(self):
        self._user_bot = TeleBot(Settings.UserBot.token)
        self._admin_bot = TeleBot(Settings.AdminBot.token)
        self._log = Logger(self._admin_bot, Settings.logger_name, Settings.AdminBot.id)
        self._statuses = Status(self._log)
        self._init_handlers()

    def start(self):
        self._user_bot.polling(none_stop=True, interval=1)

    def _text(self, message):
        self._user_bot.send_message(message.from_user.id, message.text)

    def _deepdream(self, message):
        self._user_bot.send_message(message.from_user.id, u"deepdream")

    def _colorize(self, message):
        self._user_bot.send_message(message.from_user.id, u"colorize")

    def _init_handlers(self):
        @self._user_bot.message_handler(content_types=['text'])
        def handle_text(message):
            self._text(message)

        @self._user_bot.message_handler(content_types=['photo'])
        def handle_text(message):
            pass

        @self._user_bot.message_handler(commands=['deepdream'])
        def handle_text(message):
            try:
                keyboard = types.InlineKeyboardMarkup()
                for net in ["q", "w", "4"]:#self._networks.keys():
                    callback_button = types.InlineKeyboardButton(text=net, callback_data="deepdream_net_" + net)
                    keyboard.add(callback_button)
                self._user_bot.send_message(message.chat.id, "Please, choose a neural network", reply_markup=keyboard)
                self._nets_users.new_net(message.from_user.id)
                self._states_users[message.from_user.id] = 21
                self._log.info("DeepDream (com) [" + str(message.from_user.id) + "]")
            except BaseException as e:
                self._log.error("DeepDream command error (" + str(e.args) + ")")
            pass

        @self._user_bot.message_handler(commands=['deepdream'])
        def handle_text(message):
            pass

        @self._user_bot.callback_query_handler(func=lambda call: True)
        def callback_inline(call):
            pass
            # if call.data[:14] == "deepdream_net_":
            #     bot.deepdream_button_net(call)
            # elif call.data[:16] == "deepdream_layer_":
            #     bot.deepdream_button_layeer(call)