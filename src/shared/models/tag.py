from dataclasses import dataclass, field
from ulid import ULID


def new_ulid():
    return str(ULID())

@dataclass
class Tag():
    tag : str = None
    guid : str = field(default_factory=new_ulid)

    def from_dict(self, a_dict) :
        '''Generally used to map a Flask Schema do a dataclass.'''
        keys = self.__dict__.keys()
        for k,v in a_dict.items():
            if k in keys:
                self.__dict__[k] = a_dict[k]
        return self