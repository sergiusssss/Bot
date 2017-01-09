import os
import caffe
from google.protobuf import text_format
import numpy as np
from math import ceil


class Net:
    def __init__(self, log, path, name):
        self._log = log
        self._name = name
        self._path = path
        self._status = False
        self._model = None
        self._load_model()
        if not self.check_status():
            self._log.warning("Model don't load - " + self._name)
        else:
            self._log.info("Model is load - " + self._name)

    def _load_model(self):
        try:
            if "param.txt" in os.listdir(self._path):
                try:
                    model = caffe.io.caffe_pb2.NetParameter()
                    text_format.Merge(open(self._path + '/deploy.prototxt').read(), model)
                    model.force_backward = True
                    open('tmp.prototxt', 'w').write(str(model))
                    self._model = caffe.Classifier('tmp.prototxt',
                                                   self._path + '/' + self._name + ".caffemodel",
                                                   mean=np.float32([104.0, 116.0, 122.0]),
                                                   channel_swap=(2, 1, 0))
                    os.remove('tmp.prototxt')
                except BaseException as e:
                    self._log.error("Model with parameters loading error", e=e.args)
            else:
                try:
                    self._model = caffe.Net(self._path + '/deploy.prototxt',
                                            self._path + '/' + self._name + ".caffemodel", caffe.TEST)
                except BaseException as e:
                    self._log.error("Model standart loading error", e=e.args)
            self._status = True
        except BaseException as e:
            self._log.error("Model loading error", e=e.args)

    def check_status(self):
        if self._model is None:
            return False
        else:
            return True

    def get_model(self):
        return self._model

    def get_name(self):
        return self._name

    def get_layers(self):
        try:
            keys = []
            with open(self._path + '/deploy.prototxt') as f:
                text = f.read()
                for key in self._model.blobs.keys():
                    key_index = text.find(key)
                    type_index = text.find("type", key_index)
                    type_s_front = text.find("\"", type_index) + 1
                    type_s_back = text.find("\"", type_s_front)
                    type_s = text[type_s_front: type_s_back]
                    if (type_s == "Convolution") or (type_s == "ReLU") or (type_s == "LRN") or (type_s == "Pooling"):
                        keys.append(key)

                if ceil(len(keys) / 50) > 1:
                    cof = ceil(len(keys) / 50)
                    new_keys = []
                    for i in range(len(keys)):
                        if i % cof != 0:
                            keys.remove(i)
            return keys
        except BaseException as e:
            self._log.error("Can`t open keys of net [" + self._name + "]", e=e.args)

class Networks:
    def __init__(self, log, path_to_models):
        self._log = log
        self._path_to_models = path_to_models
        self._standart_nets = {}
        self._parameterized_nets = {}
        self.load_base_models()

    def load_base_models(self):
        try:
            if len(os.listdir(self._path_to_models)) >= 1:
                for net_name in os.listdir(self._path_to_models):
                    try:
                        path_to_model = self._path_to_models + "/" + net_name

                        net = Net(self._log, path_to_model, net_name)
                        if net.check_status():
                            if "param.txt" in os.listdir(path_to_model):
                                self._parameterized_nets[net_name] = net
                            else:
                                self._standart_nets[net_name] = net
                    except BaseException as e:
                        self._log.fatal("Error loading model (" + net_name + ")", e.args)
                        return False
                return True
            else:
                self._log.fatal("Nope models for download!")
        except BaseException as e:
            self._log.fatal("Error loading models!!!", e=e.args)

    def get_parameterized_net(self, item):
        return self._parameterized_nets[item]

    def get_parameterized_keys(self):
        return self._parameterized_nets.keys()

    def get_standart_net(self, item):
        return self._standart_nets[item]

    def get_standart_keys(self):
        return self._standart_nets.keys()
