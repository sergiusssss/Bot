import multiprocessing as mp


class Processing:
    def __init__(self, log):
        self._log = log
        self._processes = []

    def new_process(self, function, args, name, user_id):
        try:
            p = mp.Process(target=function, args=args)
            self._processes.append(p)
            self._log.info("Create new process (" + name + " / " + str(user_id) + ") - " + str(len(self._processes) - 1))
            self._log.admin_info("Create new process (" + name + " / " + str(user_id) + ") - " + str(len(self._processes) - 1))
            self._processes[-1].start()
        except BaseException as e:
            self._log.error("Can`t create new process", user_id, e.args)

    def stop_all(self):
        try:
            if len(self._processes) > 0:
                for process in self._processes:
                    process.terminate()
                self._log.info("All processes are stopped")
                self._log.admin_info("All processes are stop")
        except BaseException:
            self._log.info("All processes do not stop")
            self._log.admin_info("All processes do not stop")

    def stop_process(self, i):
        try:
            self._processes[i].terminate()
            self._log.info("Process [" + str(i) + "] is stopped")
            self._log.admin_info("Process [" + str(i) + "] is stopped")
        except BaseException:
            self._log.info("Process [" + str(i) + "] don`t stop")
            self._log.admin_info("Process [" + str(i) + "] don`t stop")
