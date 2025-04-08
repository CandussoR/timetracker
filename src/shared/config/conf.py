import json
import os

from src.shared.utils.posix_path import get_abspath

class Config:

    def __init__(self, filepath : str, is_tui : bool = False):
        self.conf_path = get_abspath(filepath)
        conf = self._load(filepath)
        self.database = get_abspath(conf["database"])
        self.timer_sound_path = get_abspath(conf["timer_sound_path"]) if conf["timer_sound_path"] else ""
        self.log_file = get_abspath(conf["log_file"])
        if is_tui:
            self.flows = conf["flows"]


    def _load(self, filepath : str) -> dict:

        with open(filepath, 'r') as fr:
            return json.load(fr)


    def modify(self):

        conf = {k : self.__dict__[k] for k in self.__dict__ if k != "conf_path"}

        with open(self.conf_path, 'w') as fw:
            json.dump(conf, fw, indent=4, separators=(',', ': '))

