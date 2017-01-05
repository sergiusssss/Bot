# coding=utf-8
import string
import random
import multiprocessing as mp
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

class TelegramBot:
    def __init__(self):
        try:
            self._user_bot = TeleBot(Settings.UserBot.token)
            self._admin_bot = TeleBot(Settings.AdminBot.token)
            self._log = Logger(self._admin_bot, Settings.logger_name, Settings.AdminBot.id, Settings.path_to_logs)
            self._statuses = Status(self._log)
            self._networks = Networks(self._log, Settings.Networks.path_to_models)
            self._deepdream = DeepDream(self._log, self._user_bot, self._admin_bot, Settings.AdminBot.id, Settings.Photo.path, self._send_mail)
            self._init_handlers()
            self._log.info("Bot is running!!")
            self.start()
        except BaseException as e:
            self._log.error("Bot is not running!!", e.args)

    def start(self):
        self._user_bot.polling(none_stop=True, interval=1)

    def _send_mail(self, mess, first_photo, second_photo, msg):
        filePathOne = Settings.Photo.path + first_photo
        filePathTwo = Settings.Photo.path + second_photo
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = mess.from_user.first_name + " " + mess.from_user.last_name
        msgRoot['From'] = Settings.Mail.username
        msgRoot['To'] = Settings.Mail.username
        msgRoot.preamble = 'This is a multi-part message in MIME format.'

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)

        msgText = MIMEText('<i>' + msg + '</i><br><img src="cid:image1"><img src="cid:image2"><br>Nifty!', 'html')
        msgAlternative.attach(msgText)

        fp = open(filePathOne, 'rb')
        msgImageOne = MIMEImage(fp.read())
        fp.close()
        msgImageOne.add_header('Content-ID', '<image1>')
        msgRoot.attach(msgImageOne)

        fp = open(filePathTwo, 'rb')
        msgImageTwo = MIMEImage(fp.read())
        fp.close()
        msgImageTwo.add_header('Content-ID', '<image2>')
        msgRoot.attach(msgImageTwo)

        smtp = smtplib.SMTP('smtp.mail.ru:587')
        smtp.ehlo()
        smtp.starttls()
        smtp.login(Settings.Mail.username, Settings.Mail.password)
        smtp.sendmail(Settings.Mail.username, Settings.Mail.username, msgRoot.as_string())
        smtp.quit()

    @staticmethod
    def _random_string(n):
        a = string.ascii_letters + string.digits
        return ''.join([random.choice(a) for i in range(n)])

    def _download_photo(self, message):
        photo_name = self._random_string(8)
        photo_id = message.photo[-1].file_id
        photo_image = self._user_bot.download_file(self._user_bot.get_file(photo_id).file_path)
        with open(Settings.Photo.path + photo_name + ".jpg", 'wb') as imgfile:
            imgfile.write(photo_image)
        return photo_name

    def _text_mess(self, message):
        self._user_bot.send_message(message.from_user.id, message.text)

    def _photo_mess(self, message):
        try:
            if self._statuses[message.from_user.id].get_status() == 0:
                self._user_bot.send_message(message.from_user.id, "I don't know what to do 😕")
            else:
                photo_name = self._download_photo(message)
                if self._statuses[message.from_user.id].get_status() == 1:
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
                elif self._statuses[message.from_user.id].get_status() == 23:
                    try:
                        p = mp.Process(target=self._deepdream.start_deep_dream,
                                       args=(message,
                                             photo_name + ".jpg",
                                             self._networks.get_parameterized_net(self._statuses[message.from_user.id].get_net()).get_model(),
                                             self._statuses[message.from_user.id].get_layer()))
                        p.start()
                    except BaseException as e:
                        self._user_bot.send_message(message.from_user.id, "Something went wrong 😢" + str(e.args))
                    self._user_bot.send_message(message.from_user.id, "I'm working on it")
                    self._log.info("DeepDream [" + str(message.from_user.id) + "]")
                    self._statuses[message.from_user.id].set_status(0)
        except BaseException as e:
            self._user_bot.send_message(message.from_user.id, "Something went wrong 😢")
            self._log.error("Something went wrong (deepdream) ", e.args)

    def _deepdream_command(self, message):
        self._user_bot.send_message(message.from_user.id, u"deepdream")

    def _colorize_command(self, message):
        self._user_bot.send_message(message.from_user.id, u"colorize")

    def _init_handlers(self):
        @self._user_bot.message_handler(commands=['colorize'])
        def handle_text(message):
            pass

        @self._user_bot.message_handler(commands=['deepdream'])
        def handle_text(message):
            try:
                keyboard = types.InlineKeyboardMarkup()
                for net in self._networks.get_parameterized_keys():
                    callback_button = types.InlineKeyboardButton(text=net, callback_data="deepdream_net_" + net)
                    keyboard.add(callback_button)
                self._user_bot.send_message(message.chat.id, "Please, choose a neural network", reply_markup=keyboard)
                self._statuses[message.chat.id].set_status(21)
                self._log.info("DeepDream (com) [" + str(message.from_user.id) + "]")
            except BaseException as e:
                self._log.error("DeepDream command error ", e.args)

        @self._user_bot.message_handler(content_types=['text'])
        def handle_text(message):
            self._text_mess(message)

        @self._user_bot.message_handler(content_types=['photo'])
        def handle_text(message):
            self._photo_mess(message)

        @self._user_bot.callback_query_handler(func=lambda call: True)
        def callback_inline(call):
            if call.data[:14] == "deepdream_net_":
                try:
                    if self._statuses[call.message.chat.id].get_status() == 21:
                        self._statuses[call.message.chat.id].set_net(call.data[14:])
                        self._user_bot.edit_message_text(chat_id=call.message.chat.id,
                                                         message_id=call.message.message_id, text=call.data[14:])
                        layers = self._networks.get_parameterized_net(self._statuses[call.message.chat.id].get_net()).get_layers()

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
                    self._log.error("DeepDream load net error ", e.args)
            elif call.data[:16] == "deepdream_layer_":
                if self._statuses[call.message.chat.id].get_status() == 22:
                    self._statuses[call.message.chat.id].set_layer(str(call.data[16:]).replace(".", "/"))
                    self._user_bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                     text=call.data[16:])
                    self._user_bot.send_message(call.message.chat.id, "Send your photo, please")
                    self._statuses[call.message.chat.id].set_status(23)
