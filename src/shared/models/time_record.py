from dataclasses import dataclass, field
from datetime import datetime
from ulid import ULID

def new_ulid():
    return str(ULID())

@dataclass
class TimeRecordInput():
    task_id : str = None
    date : datetime = None
    time_beginning : datetime = None
    time_ending : datetime = None
    time_elapsed : int = None
    tag_id : str = None
    log : str = None
    guid : str = field(default_factory=new_ulid)

    def __post_init__(self):
        if self.date and isinstance(self.date, str):
            self.date = datetime.strptime(self.date, "%Y-%m-%d")
        if self.time_beginning and isinstance(self.time_beginning, str):
            self.time_beginning = datetime.strptime(self.time_beginning, "%H:%M:%S")
        if self.time_ending and isinstance(self.time_ending, str):
            self.time_ending = datetime.strptime(self.time_ending, "%H:%M:%S")

    def from_dict(self, a_dict) :
        '''Generally used to map a Flask Schema do a dataclass.'''
        keys = self.__dict__.keys()
        for k,v in a_dict.items():
            if k in keys:
                self.__dict__[k] = a_dict[k]
        return self

@dataclass
class TimeRecordResource():
    guid : str = field(default_factory=new_ulid)
    task_guid : str = None
    date : datetime = None
    time_beginning : datetime = None
    time_ending : datetime = None
    time_elapsed : int = None
    tag_guid : str = None
    log : str = None

    def __post_init__(self):
        if self.date:
            self.date = datetime.strptime(self.date, "%Y-%m-%d").date()
        if self.time_beginning:
            print("modifying time beginning", self.time_beginning)
            self.time_beginning = datetime.strptime(self.time_beginning, "%H:%M:%S").time()
            print("modified time beginning", self.time_beginning)
        if self.time_ending:
            self.time_ending = datetime.strptime(self.time_ending, "%H:%M:%S").time()

    def from_dict(self, a_dict) :
        '''Generally used to map a Flask Schema do a dataclass.'''
        keys = self.__dict__.keys()
        for k,v in a_dict.items():
            if k in keys:
                self.__dict__[k] = a_dict[k]
        return self