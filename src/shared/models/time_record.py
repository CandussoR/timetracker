from dataclasses import dataclass, field
from datetime import datetime, date, time
from ulid import ULID
import re

def new_ulid():
    return str(ULID())

@dataclass
class TimeRecordInput():
    task_id : int | None = None
    date : datetime | str | None = None
    time_beginning : datetime | str | None = None
    time_ending : datetime | str | None = None
    time_elapsed : int | None = None
    tag_id : int | None = None
    log : str | None = None
    guid : str | None = field(default_factory=new_ulid)

    def __post_init__(self):
        if self.date and isinstance(self.date, str):
            self.date = datetime.strptime(self.date, "%Y-%m-%d")
        if self.time_beginning and isinstance(self.time_beginning, str):
            self.time_beginning = datetime.strptime(self.time_beginning, "%H:%M:%S")
        if self.time_ending and isinstance(self.time_ending, str):
            self.time_ending = datetime.strptime(self.time_ending, "%H:%M:%S")

    def from_dict(self, a_dict) :
        '''
           Generally used to map a Flask Schema do a dataclass. 
           Need to check for camelCase, so there is no need to elsewhere in the code.
        '''
        keys = self.__dict__.keys()
        for k,v in a_dict.items():
            k_mel = self.camel_to_underscore(k)
            if k_mel in keys:
                self.__dict__[k_mel] = a_dict[k]
        return self
    
    def camel_to_underscore(self, name):
        camel_pat = re.compile(r'([A-Z])')
        return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)

@dataclass
class TimeRecordResource():
    guid : str = field(default_factory=new_ulid)
    task_name : str | None = None
    subtask : str | None = None
    date : datetime | None = None
    time_beginning : datetime | None = None
    time_ending : datetime | None = None
    tag : str | None = None
    log : str | None = None

    def __post_init__(self):
        if self.date:
            self.date = datetime.strptime(self.date, "%Y-%m-%d").date()
        if self.time_beginning:
            self.time_beginning = datetime.strptime(self.time_beginning, "%H:%M:%S").time()
        if self.time_ending:
            self.time_ending = datetime.strptime(self.time_ending, "%H:%M:%S").time()

    def from_dict(self, a_dict) :
        '''Generally used to map a Flask Schema do a dataclass.'''
        keys = self.__dict__.keys()
        for k,v in a_dict.items():
            if k in keys:
                self.__dict__[k] = a_dict[k]
        return self