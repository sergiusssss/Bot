# coding=utf-8
import sys
import logging
import string
import random
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
import smtplib
from telebot import TeleBot
from telebot import types
from Classes.Settings import Settings
from Classes.Logger import Logger
from Classes.Status import Status
from Classes.Networks import Networks
from Classes.DeepDream import DeepDream
from Classes.Processing import Processing


class TelegramBot:
    def __init__(self):
        try:
            self._user_bot = TeleBot(Settings.UserBot.token)
            self._admin_bot = TeleBot(Settings.AdminBot.token)
            self._log = Logger(self._admin_bot, self._user_bot, Settings.logger_name, Settings.AdminBot.id, Settings.path_to_logs)
            self._statuses = Status(self._log)
            self._processing = Processing(self._log)
            self._networks = Networks(self._log, Settings.Networks.path_to_models)
            self._deepdream = DeepDream(self._log, self._user_bot, self._admin_bot, Settings.AdminBot.id, Settings.Photo.path, self._send_mail)
            self._init_handlers()
            self._log.admin_info("Bot is running!!")
            self._log.info("Bot is running!!")
            self.start()
        except SystemExit:
            pass
        except BaseException as e:
            self._processing.stop_all()
            self._log.fatal("Bot is not running!!", e=e.args)

    def start(self):
        self._user_bot.polling(none_stop=True, interval=1)

    # local functions
    def _random_string(self, n):
        a = string.ascii_letters + string.digits
        return ''.join([random.choice(a) for i in range(n)])

    # web functions
    def _send_mail(self, mess, first_photo, second_photo, msg):
        try:
            file_path_one = Settings.Photo.path + first_photo
            file_path_two = Settings.Photo.path + second_photo
            msg_root = MIMEMultipart('related')
            msg_root['Subject'] = mess.from_user.first_name + " " + mess.from_user.last_name
            msg_root['From'] = Settings.Mail.username
            msg_root['To'] = Settings.Mail.username
            msg_root.preamble = 'This is a multi-part message in MIME format.'

            msg_alternative = MIMEMultipart('alternative')
            msg_root.attach(msg_alternative)

            msg_text = MIMEText('<i>' + msg + '</i><br><img src="cid:image1"><img src="cid:image2"><br>', 'html')
            msg_alternative.attach(msg_text)

            fp = open(file_path_one, 'rb')
            msg_image_one = MIMEImage(fp.read())
            fp.close()
            msg_image_one.add_header('Content-ID', '<image1>')
            msg_root.attach(msg_image_one)

            fp = open(file_path_two, 'rb')
            msg_image_two = MIMEImage(fp.read())
            fp.close()
            msg_image_two.add_header('Content-ID', '<image2>')
            msg_root.attach(msg_image_two)

            smtp = smtplib.SMTP('smtp.mail.ru:587')
            smtp.ehlo()
            smtp.starttls()
            smtp.login(Settings.Mail.username, Settings.Mail.password)
            smtp.sendmail(Settings.Mail.username, Settings.Mail.username, msg_root.as_string())
            smtp.quit()
        except BaseException as e:
            self._log.warning("Mail sending error [" + mess.from_user.id + "]")

    def _download_photo(self, message):
        try:
            photo_name = self._random_string(8)
            photo_id = message.photo[-1].file_id
            photo_image = self._user_bot.download_file(self._user_bot.get_file(photo_id).file_path)
            with open(Settings.Photo.path + photo_name + ".jpg", 'wb') as imgfile:
                imgfile.write(photo_image)
            return photo_name
        except BaseException as e:
            self._log.error("Can`t download photo [" + message.from_user.id + "]", message.from_user.id, e.args)

    # handlers
    def _text_mess(self, message):
        self._user_bot.send_message(message.from_user.id, message.text)

    def _photo_mess(self, message):
        try:
            if self._statuses[message.from_user.id].get_status() == 0:
                self._user_bot.send_message(message.from_user.id, "I don't know what to do 😕")
            else:
                photo_name = self._download_photo(message)
                if self._statuses[message.from_user.id].get_status() == 1:
                   self._colorize_function(message, photo_name)
                elif self._statuses[message.from_user.id].get_status() == 23:
                    self._deepdream_function(message, photo_name)
        except BaseException as e:
            self._log.error("Something went wrong with photo", message.from_user.id, e.args)

    # handlers commands
    def _deepdream_command(self, message):
        try:
            keyboard = types.InlineKeyboardMarkup()
            for net in self._networks.get_parameterized_keys():
                callback_button = types.InlineKeyboardButton(text=net, callback_data="deepdream_net_" + net)
                keyboard.add(callback_button)
            self._user_bot.send_message(message.chat.id, "Please, choose a neural network", reply_markup=keyboard)
            self._statuses[message.chat.id].set_status(21)
        except BaseException as e:
            self._log.error("DeepDream command error ", message.from_user.id, e.args)

    def _colorize_command(self, message):
        pass

    def _stop_command(self):
        self._processing.stop_all()
        self._log.warning("Bot is stopped!")
        self._log.admin_info("Bot is stopped!")
        sys.exit()

    def _stop_process_command(self, i):
        self._processing.stop_process(i)

    def _stop_all_command(self):
        self._processing.stop_all()

    # callbacks
    def _deepdream_callback(self, call):
        try:
            if call.data[:14] == "deepdream_net_":
                if self._statuses[call.message.chat.id].get_status() == 21:
                    self._statuses[call.message.chat.id].set_net(call.data[14:])
                    self._user_bot.edit_message_text(chat_id=call.message.chat.id,
                                                     message_id=call.message.message_id, text=call.data[14:])
                    layers = self._networks.get_parameterized_net(
                        self._statuses[call.message.chat.id].get_net()).get_layers()

                    keyboard = types.InlineKeyboardMarkup()
                    for layer in layers:
                        self._log.debug(layer)
                        callback_button = types.InlineKeyboardButton(text=layer,
                                                                     callback_data="deepdream_layer_" + layer)
                        keyboard.add(callback_button)
                    self._user_bot.send_message(call.message.chat.id, "Please, choose layer level",
                                                reply_markup=keyboard)
                    self._statuses[call.message.chat.id].set_status(22)
            elif call.data[:16] == "deepdream_layer_":
                if self._statuses[call.message.chat.id].get_status() == 22:
                    self._statuses[call.message.chat.id].set_layer(str(call.data[16:]).replace(".", "/"))
                    self._user_bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                     text=call.data[16:])
                    self._user_bot.send_message(call.message.chat.id, "Send your photo, please")
                    self._statuses[call.message.chat.id].set_status(23)
        except BaseException as e:
            self._log.error("Something went wrong with callback", call.message.from_user.id, e.args)

    # functional
    def _deepdream_function(self, message, photo_name):
        try:
            args = (message,
                                 photo_name + ".jpg",
                                 self._networks.get_parameterized_net(
                                 self._statuses[message.from_user.id].get_net()).get_model(),
                                 self._statuses[message.from_user.id].get_layer())
            self._processing.new_process(self._deepdream.start_deep_dream, args, "DeepDream", message.from_user.id)
            self._user_bot.send_message(message.from_user.id, "I'm working on it")
            self._statuses[message.from_user.id].set_status(0)
        except BaseException as e:
            self._log.error("Something went wrong with deepdream starting", message.from_user.id, e.args)

    def _colorize_function(self, message, photo_name):
        pass
        # try:
        #     p = mp.Process(target=self._colorize.startColorize, args=(message, photo_name + ".jpg",
        #                                                               self._networks[
        #                                                                   'colorization_v2'].get_standart()))
        #     p.start()
        # except BaseException as e:
        #     self._user_bot.send_message(message.from_user.id, "Something went wrong 😢" + str(e.args))
        # self._user_bot.send_message(message.from_user.id, "I'm working on it")
        # self._log.info("Colorize [" + str(message.from_user.id) + "]")
        # self._states_users[message.from_user.id] = 0

    def _weather_function(self, message):
        pass

    # init handlers
    def _init_handlers(self):
        # admin
        @self._user_bot.message_handler(commands=['stopbot'])
        def handle_command(message):
            if message.from_user.id == Settings.AdminBot.id:
                self._stop_command()

        @self._user_bot.message_handler(commands=['allprocessesstop'])
        def handle_command(message):
            if message.from_user.id == Settings.AdminBot.id:
                self._stop_all_command()

        @self._user_bot.message_handler(commands=['processstop'])
        def handle_command(message):
            if message.from_user.id == Settings.AdminBot.id:
                self._stop_process_command(int(message.text.split()[1]))

        # user
        @self._user_bot.message_handler(commands=['weather'])
        def handle_command(message):
            self._weather_function(message)

        @self._user_bot.message_handler(commands=['colorize'])
        def handle_command(message):
            self._colorize_command(message)

        @self._user_bot.message_handler(commands=['deepdream'])
        def handle_command(message):
            self._deepdream_command(message)

        @self._user_bot.message_handler(content_types=['text'])
        def handle_text(message):
            self._text_mess(message)

        @self._user_bot.message_handler(content_types=['photo'])
        def handle_photo(message):
            self._photo_mess(message)

        @self._user_bot.callback_query_handler(func=lambda call: True)
        def callback_inline(call):
            self._deepdream_callback(call)
