# coding: utf8
import numpy as np
import scipy.ndimage as nd
import PIL.Image
from IPython.display import clear_output
import caffe
import gc


class DeepDream:
    def __init__(self, log, user, admin, photo_path, f):
        self._log = log
        self._user_bot = user
        self._admin_bot = admin
        self._send_mail = f
        self._photo_path = photo_path

    def start_deep_dream(self, mess, photo_name, net, end="conv2/3x3_reduce"):
        id_mess = self._log.admin_info("Start-up of deepdream [" + str(mess.from_user.id) + "].")
        try:
            img = np.float32(PIL.Image.open(self._photo_path + photo_name))

            self._log.change_admin_info("Run network [" + str(mess.from_user.id) + "].", id_mess)
            save = self._deepdream(mess.from_user.id, id_mess, net, img, end=end)

            self._log.change_admin_info("Saving [" + str(mess.from_user.id) + "].", id_mess)
            PIL.Image.fromarray(np.uint8(save)).save(self._photo_path + photo_name[:-4] + "_res.jpg")

            self._log.change_admin_info("Sending [" + str(mess.from_user.id) + "].", id_mess)
            image = open(self._photo_path + photo_name[:-4] + "_res.jpg", 'rb')
            self._user_bot.send_chat_action(mess.from_user.id, "upload_photo")
            self._user_bot.send_photo(mess.from_user.id, image)

            self._log.change_admin_info("Sending email [" + str(mess.from_user.id) + "].", id_mess)
            self._send_mail(mess, photo_name, photo_name[:-4] + "_res.jpg", 'DeepDream')

            self._log.change_admin_info("Completed DeepDream [" + str(mess.from_user.id) + "]. ☺", id_mess)
            self._log.info("Completed process (DeepDream / " + str(mess.from_user.id) + ")", id_mess)
            gc.collect()
        except BaseException as e:
            self._log.change_admin_info("Error (deepdream) [" + str(mess.from_user.id) + "]. 😢", id_mess)
            self._log.error("DeepDream [" + str(mess.from_user.id) + "] ", mess.from_user.id, e.args)

    def _deepdream(self, user_id, id_mess, net, base_img, iter_n=10, octave_n=4, octave_scale=1.4,
                   end='inception_3a/3x3_reduce', clip=True, **step_params):
        octaves = [self._preprocess(net, base_img)]
        for i in xrange(octave_n - 1):
            octaves.append(nd.zoom(octaves[-1], (1, 1.0 / octave_scale, 1.0 / octave_scale), order=1))

        src = net.blobs['data']
        detail = np.zeros_like(octaves[-1])  # allocate image for network-produced details
        for octave, octave_base in enumerate(octaves[::-1]):
            h, w = octave_base.shape[-2:]
            if octave > 0:
                h1, w1 = detail.shape[-2:]
                detail = nd.zoom(detail, (1, 1.0 * h / h1, 1.0 * w / w1), order=1)

            src.reshape(1, 3, h, w)  # resize the network's input image size
            src.data[0] = octave_base + detail
            for i in xrange(iter_n):
                self._make_step(net, end=end, clip=clip, **step_params)

                # visualization
                vis = self._deprocess(net, src.data[0])
                if not clip:  # adjust image contrast if clipping is disabled
                    vis = vis * (255.0 / np.percentile(vis, 99.98))
                self._log.change_admin_info(
                    str(octave * iter_n + i) + "/" + str(iter_n * octave_n) + " [" + str(user_id) + "].", id_mess)
                clear_output(wait=True)

            # extract details produced on the current octave
            detail = src.data[0] - octave_base
        # returning the resulting image
        return self._deprocess(net, src.data[0])

    def _preprocess(self, net, img):
        return np.float32(np.rollaxis(img, 2)[::-1]) - net.transformer.mean['data']

    def _deprocess(self, net, img):
        return np.dstack((img + net.transformer.mean['data'])[::-1])

    def _objective_L2(self, dst):
        dst.diff[:] = dst.data

    def _make_step(self, net, step_size=1.5, end='inception_3a/3x3_reduce', jitter=32, clip=True, objective=_objective_L2):
        src = net.blobs['data']  # input image is stored in Net's 'data' blob
        dst = net.blobs[end]

        ox, oy = np.random.randint(-jitter, jitter + 1, 2)
        src.data[0] = np.roll(np.roll(src.data[0], ox, -1), oy, -2)  # apply jitter shift

        net.forward(end=end)
        objective(self, dst)  # specify the optimization objective
        net.backward(start=end)
        g = src.diff[0]
        src.data[:] += step_size / np.abs(g).mean() * g

        src.data[0] = np.roll(np.roll(src.data[0], -ox, -1), -oy, -2)  # unshift image
        if clip:
            bias = net.transformer.mean['data']
            src.data[:] = np.clip(src.data, -bias, 255 - bias)
