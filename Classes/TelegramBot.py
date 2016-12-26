from telebot import TeleBot
from telebot import types
from Classes.Settings import Settings
from Classes.Logger import Logger
from Classes.Status import Status
from Classes.Networks import Networks


class TelegramBot:
    def __init__(self):
        self._user_bot = TeleBot(Settings.UserBot.token)
        self._admin_bot = TeleBot(Settings.AdminBot.token)
        self._log = Logger(self._admin_bot, Settings.logger_name, Settings.AdminBot.id)
        self._statuses = Status(self._log)
        self._networks = Networks(self._log, Settings.Networks.path_to_models)
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
                #self._nets_users.new_net(message.from_user.id)
                #self._states_users[message.from_user.id] = 21
                self._log.info("DeepDream (com) [" + str(message.from_user.id) + "]")
            except BaseException as e:
                self._log.error("DeepDream command error (" + str(e.args) + ")")

        @self._user_bot.message_handler(commands=['deepdream'])
        def handle_text(message):
            pass

        @self._user_bot.callback_query_handler(func=lambda call: True)
        def callback_inline(call):
            pass
            if call.data[:14] == "deepdream_net_":
                try:
                    if self._statuses[call.message.chat.id].get_status() == 21:
                        self._statuses[call.message.chat.id].set_net(call.data[14:])
                        self._user_bot.edit_message_text(chat_id=call.message.chat.id,
                                                         message_id=call.message.message_id, text=call.data[14:])
                        layers = self._networks[self._statuses[call.message.chat.id].get_net()].get_layers()

                        keyboard = types.InlineKeyboardMarkup()
                        for layer in layers:
                            self._log.debug(layer)
                            callback_button = types.InlineKeyboardButton(text=layer,
                                                                                     callback_data="deepdream_layer_" + layer)
                            keyboard.add(callback_button)
                        self._user_bot.send_message(call.message.chat.id, "Please, choose layer level",
                                                    reply_markup=keyboard)
                        self._statuses[call.message.chat.id].set_status(22)
                except BaseException as e:
                    self._log.error("DeepDream load net error (" + str(e.args) + ")")
            elif call.data[:16] == "deepdream_layer_":
                if self._statuses[call.message.chat.id].get_status() == 22:
                    self._statuses[call.message.chat.id].set_layer(str(call.data[16:]).replace(".", "/"))
                    self._user_bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                     text=call.data[16:])
                    self._user_bot.send_message(call.message.chat.id, "Send your photo, please")
                    self._statuses[call.message.chat.id].set_status(23)
