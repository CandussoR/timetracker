import json

class Config:

    def __init__(self, filepath : str):
        self.filepath = filepath
        conf = self._load(filepath)
        self.database = conf["database"]
        self.timer_sound_path = conf["timer_sound_path"]
        self.log_file = conf["log_file"]
        self.flows = conf["flows"]


    def _load(self, filepath : str) -> dict:

        with open(filepath, 'r') as fr:
            return json.load(fr)


    def modify(self):

        conf = {k : self.__dict__[k] for k in self.__dict__ if k != "filepath"}

        with open(self.filepath, 'w') as fw:
            json.dump(conf, fw, indent=4, separators=(',', ': '))

