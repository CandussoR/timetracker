from dataclasses import dataclass, field
from ulid import ULID

def new_ulid():
    return str(ULID())

@dataclass
class Task:
    task_name : str = None
    subtask : str = None
    guid : str = field(default_factory=new_ulid)


    def __post_init__(self):
        if self.task_name is not None : self.task_name = self.task_name.title()
        if self.subtask is not None : self.subtask = self.subtask.title()


    def __lt__(self, other):
        return self.guid < other.guid
    

    def from_dict(self, a_dict) :
        '''Generally used to map a Flask Schema do a dataclass.'''
        keys = self.__dict__.keys()
        for k,v in a_dict.items():
            if k in keys:
                self.__dict__[k] = a_dict[k]
        return self