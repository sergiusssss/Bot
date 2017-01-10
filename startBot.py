import os
os.environ['GLOG_minloglevel'] = '5'

import warnings
warnings.filterwarnings('ignore')

from Classes import TelegramBot

temp = TelegramBot()

