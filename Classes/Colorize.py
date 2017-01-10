# coding: utf8
import numpy as np
import matplotlib.pyplot as plt
import skimage.color as color
import scipy.ndimage.interpolation as sni
import caffe
import os

from modules.settings import Settings as sett
from functions.otherFunctions.mail import sendMail


class Colorize:
    def __init__(self, log, user, admin, photo_path, f):
        self._log = log
        self._user_bot = user
        self._admin_bot = admin
        self._send_mail = f
        self._photo_path = photo_path

    def start_colorize(self, mess, photo_name, net):
        id_mess = self._log.admin_info("Start-up of colorization [" + str(mess.from_user.id) + "].")
        try:
            plt.rcParams['figure.figsize'] = (12, 6)
            caffe.set_mode_cpu()
            (H_in, W_in) = net.blobs['data_l'].data.shape[2:]  # get input shape
            (H_out, W_out) = net.blobs['class8_ab'].data.shape[2:]  # get output shape
            pts_in_hull = np.load('functions/colorizationPhoto/colorizationPhoto/resources/pts_in_hull.npy')  # load cluster centers
            net.params['class8_ab'][0].data[:, :, 0, 0] = pts_in_hull.transpose(
                (1, 0))  # populate cluster centers as 1x1 convolution kernel

            self._log.change_admin_info("Load the original image [" + str(mess.from_user.id) + "].", id_mess)
            img_rgb = caffe.io.load_image(sett.Photo.path + photo_name)
            img_lab = color.rgb2lab(img_rgb)  # convert image to lab color space
            img_l = img_lab[:, :, 0]  # pull out L channel
            (H_orig, W_orig) = img_rgb.shape[:2]  # original image size

            self._log.change_admin_info("Resize image to network input size [" + str(mess.from_user.id) + "].", id_mess)
            img_rs = caffe.io.resize_image(img_rgb, (H_in, W_in))  # resize image to network input size
            img_lab_rs = color.rgb2lab(img_rs)
            img_l_rs = img_lab_rs[:, :, 0]

            self._log.change_admin_info("Run network [" + str(mess.from_user.id) + "].", id_mess)
            net.blobs['data_l'].data[0, 0, :, :] = img_l_rs - 50  # subtract 50 for mean-centering
            net.forward()  # run network

            ab_dec = net.blobs['class8_ab'].data[0, :, :, :].transpose((1, 2, 0))  # this is our result
            ab_dec_us = sni.zoom(ab_dec, (1. * H_orig / H_out, 1. * W_orig / W_out, 1))  # upsample to match size of original image L
            img_lab_out = np.concatenate((img_l[:, :, np.newaxis], ab_dec_us), axis=2)  # concatenate with original image L
            img_rgb_out = np.clip(color.lab2rgb(img_lab_out), 0, 1)  # convert back to rgb

            self._log.change_admin_info("Saving [" + str(mess.from_user.id) + "].", id_mess)
            plt.imsave(sett.Photo.path + photo_name[:-4] + "_res", img_rgb_out);

            self._log.change_admin_info("Sending [" + str(mess.from_user.id) + "].", id_mess)
            image = open(sett.Photo.path + photo_name[:-4] + "_res.png", 'rb')
            self._user_bot.send_chat_action(mess.from_user.id, "upload_photo")
            self._user_bot.send_photo(mess.from_user.id, image)

            self._log.change_admin_info("Sending email [" + str(mess.from_user.id) + "].", id_mess)
            self._send_mail(mess, photo_name, photo_name[:-4] + "_res.png", 'Colorize')

            self._log.change_admin_info("Completed (colorize) [" + str(mess.from_user.id) + "]. ☺", id_mess)
        except BaseException as e:
            self._log.change_admin_info("Error (colorize) [" + str(mess.from_user.id) + "]. 😢", id_mess)
            self._log.error("Colorize [" + str(mess.from_user.id) + "] ", mess.from_user.id, e.args)
