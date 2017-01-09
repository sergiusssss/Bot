# coding: utf8
import numpy as np
import matplotlib.pyplot as plt
import skimage.color as color
import scipy.ndimage.interpolation as sni
import caffe
import os

from modules.settings import Settings as sett
from functions.otherFunctions.mail import sendMail


class Colorization:
    def __init__(self, log, user, admin):
        self._log = log
        self._user_bot = user
        self._admin_bot = admin

    def startColorize(self, mess, photoName, net):
        user_id = mess.from_user.id
        id_mess = self._admin_bot.send_message(sett.AndminBot.id, "Start-up of colorization [" + str(user_id) + "].").message_id
        try:
            plt.rcParams['figure.figsize'] = (12, 6)
            caffe.set_mode_cpu()
            (H_in, W_in) = net.blobs['data_l'].data.shape[2:]  # get input shape
            (H_out, W_out) = net.blobs['class8_ab'].data.shape[2:]  # get output shape
            pts_in_hull = np.load('functions/colorizationPhoto/colorizationPhoto/resources/pts_in_hull.npy')  # load cluster centers
            net.params['class8_ab'][0].data[:, :, 0, 0] = pts_in_hull.transpose(
                (1, 0))  # populate cluster centers as 1x1 convolution kernel

            self._admin_bot.edit_message_text("Load the original image [" + str(user_id) + "].", sett.AndminBot.id, id_mess)
            img_rgb = caffe.io.load_image(sett.Photo.path + photoName)
            img_lab = color.rgb2lab(img_rgb)  # convert image to lab color space
            img_l = img_lab[:, :, 0]  # pull out L channel
            (H_orig, W_orig) = img_rgb.shape[:2]  # original image size

            self._admin_bot.edit_message_text("Resize image to network input size [" + str(user_id) + "].", sett.AndminBot.id, id_mess)
            img_rs = caffe.io.resize_image(img_rgb, (H_in, W_in))  # resize image to network input size
            img_lab_rs = color.rgb2lab(img_rs)
            img_l_rs = img_lab_rs[:, :, 0]

            self._admin_bot.edit_message_text("Run network [" + str(user_id) + "].", sett.AndminBot.id, id_mess)
            net.blobs['data_l'].data[0, 0, :, :] = img_l_rs - 50  # subtract 50 for mean-centering
            net.forward()  # run network

            ab_dec = net.blobs['class8_ab'].data[0, :, :, :].transpose((1, 2, 0))  # this is our result
            ab_dec_us = sni.zoom(ab_dec, (1. * H_orig / H_out, 1. * W_orig / W_out, 1))  # upsample to match size of original image L
            img_lab_out = np.concatenate((img_l[:, :, np.newaxis], ab_dec_us), axis=2)  # concatenate with original image L
            img_rgb_out = np.clip(color.lab2rgb(img_lab_out), 0, 1)  # convert back to rgb

            self._admin_bot.edit_message_text("Saving [" + str(user_id) + "].", sett.AndminBot.id, id_mess)
            plt.imsave(sett.Photo.path + photoName[:-4] + "_res", img_rgb_out);

            self._admin_bot.edit_message_text("Sending [" + str(user_id) + "].", sett.AndminBot.id, id_mess)
            image = open(sett.Photo.path + photoName[:-4] + "_res.png", 'rb')
            self._user_bot.send_chat_action(user_id, "upload_photo")
            self._user_bot.send_photo(user_id, image)

            self._admin_bot.edit_message_text("Sending email [" + str(user_id) + "].", sett.AndminBot.id, id_mess)
            sendMail(mess, photoName, photoName[:-4] + "_res.png", 'Colorize')

            os.remove(sett.Photo.path + photoName[:-4] + "_res.png")
            os.remove(sett.Photo.path + photoName)

            self._admin_bot.edit_message_text("Completed (colorize) [" + str(user_id) + "]. ☺", sett.AndminBot.id, id_mess)
        except BaseException as e:
            self._admin_bot.edit_message_text("Error (colorize) [" + str(user_id) + "]. 😢", id_mess)
            self._log.warning("Error (colorize) [" + str(user_id) + "] (" + str(e.args) + ")")
