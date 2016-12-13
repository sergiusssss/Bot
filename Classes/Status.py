class User:
    def __init__(self, user_id, status=0, net="bvlc_googlenet", layer="conv2/3x3_reduce"):
        self._id = user_id
        self._status = status
        self._net = net
        self._layer = layer
        self._del_message = []

    def set_del_message(self, new_del_message):
        self._del_message = new_del_message

    def get_del_message(self):
        return self._del_message

    def set_status(self, new_status):
        self._status = new_status

    def get_status(self):
        return self._status

    def set_net(self, new_net):
        self._net = new_net

    def get_net(self):
        return self._net

    def set_layer(self, new_layer):
        self._layer = new_layer

    def get_layer(self):
        return self._layer


class Status:
    def __init__(self, log):
        self._users = {}
        self._log = log

    def __getitem__(self, item):
        try:
            return self._users[item]
        except:
            try:
                self._users[item] = User(item)
                return self._users[item]
            except:
                self._log.error("Can't get value this user - " + str(item))
