import datetime
import logging
import sys
from colorlog import ColoredFormatter


class Logger:
    def __init__(self, admin, name, admin_id, path_to_log):
        self._admin = admin
        self._admin_id = admin_id
        self._log = logging.getLogger(name)
        self._log.setLevel(logging.DEBUG)

        self._formatter = ColoredFormatter(
                "%(log_color)s%(levelname)-4s [%(asctime)s]:  %(message)s",
                datefmt=None,
                reset=True,
                log_colors={
                        'DEBUG':    'cyan',
                        'INFO':     'green',
                        'WARNING':  'yellow',
                        'ERROR':    'red',
                        'CRITICAL': 'red,bg_white',
                },
                secondary_log_colors={},
                style='%')
        self._ch = logging.StreamHandler()
        self._ch.setLevel(logging.DEBUG)
        self._ch.setFormatter(self._formatter)
        self._log.addHandler(self._ch)

        self._log_file_name = "log_" + datetime.datetime.now().strftime("%d-%m-%Y") + ".log"
        formatter = logging.Formatter("%(levelname)-4s [%(asctime)s]: "
                                      " %(message)s \r")
        self._fl = logging.FileHandler(path_to_log + "/" + self._log_file_name)
        self._fl.setLevel(logging.ERROR)
        self._fl.setFormatter(formatter)
        self._log.addHandler(self._fl)

    def _send_to_admin(self, message, level_name):
        try:
            string_error = "<b>" + level_name + "</b>\n" \
                            "<pre>" + datetime.datetime.now().strftime("%d.%m.%Y %I:%M") + "</pre>\n"\
                            "(<code>" + message + "</code>)"
            self._admin.send_message(self._admin_id, string_error, parse_mode='HTML')
        except:
            self._log.debug("Can not send a message to admin! ")

    def debug(self, message, e="Unknown error!!!"):
        self._log.debug(message)

    def info(self, message, e="Unknown error!!!"):
        self._log.info(message)

    def warning(self, message, e="Unknown error!!!"):
        self._log.warning(message)

    def error(self, message, e="Unknown error!!!"):
        self._send_to_admin(message, "ERROR")
        self._log.error(message + "(" + str(e) + ")")

    def fatal(self, message, e="Unknown error!!!"):
        self._send_to_admin(message, "FATAL")
        self._log.fatal(message + "(" + str(e) + ")")
        sys.exit()
