import json

class Config:

    filepath = "./conf.json"

    def __init__(self):
        conf = self._load_conf()
        self.bdd = conf["database"]
        self.logs = conf["logs"]
        self.sound = conf["timer_sound_path"]
        self.flows = conf["flows"]

    def _load_conf(self) -> dict:
        with open(self.filepath, 'r') as fr:
            return json.load(fr)

    def modify_conf(self):
        conf = {k : self.__dict__[k] for k in self.__dict__ if k is not "filepath"}
        with open(self.filepath, 'w') as fw:
            json.dump(conf, fw)

if __name__ == '__main__':
    conf = Config()
    print(1)