import json

class Config:

    filepath = "./conf.json"

    def __init__(self):

        conf = self._load()
        self.database = conf["database"]
        self.logs = conf["logs"]
        self.log_path = conf["log_path"]
        self.timer_sound_path = conf["timer_sound_path"]
        self.flows = conf["flows"]


    def _load(self) -> dict:

        with open(self.filepath, 'r') as fr:
            return json.load(fr)


    def modify(self):

        conf = {k : self.__dict__[k] for k in self.__dict__ if k != "filepath"}

        with open(self.filepath, 'w') as fw:
            json.dump(conf, fw, indent=4, separators=(',', ': '))


if __name__ == '__main__':
    conf = Config()