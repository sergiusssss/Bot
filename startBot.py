import os
os.environ['GLOG_minloglevel'] = '4'

from Classes import TelegramBot

temp = TelegramBot()

temp.start()
