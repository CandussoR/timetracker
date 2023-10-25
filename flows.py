from conf import Config

class Flow:
    def __init__(self, name: str , timers: list[int], pauses: list[int]):     
        self.name = name
        self.timers = timers
        self.pauses = pauses
    
    def __repr__(self) -> str:
        return f"{self.name} : {self.get_sets()}"
    
    def get_sets(self) -> list[tuple[int, int]]:
        return list(zip(self.timers, self.pauses))
    
    def to_dict(self) -> dict:
        return { self.name : {"timers": self.timers, "pauses" : self.pauses} }
    
class FlowBuilder:
    def __init__(self):
        self.name = None
        self.timers = None
        self.pauses = None

    def with_name(self, name : str):
        self.name = name
        return self
    
    def with_timers(self, timers : list[int]):
        self.timers = timers
        return self
    
    def with_pauses(self, pauses : list[int]):
        self.pauses = pauses
        return self
    
    def build(self) -> Flow:
        return Flow(self.name, self.timers, self.pauses)

class CommandLineFlowBuilder:
    ''' A interactive builder of Flow for the command line. '''

    def __init__(self):
        self.name = self._input_flo_name()
        self.timers, self.pauses = self._timers_and_pauses(self._input_flow_times())
        
    def _input_flow_times(self) -> list[list[str]]:
        ''' Asking user input for time and pauses. Function abstracted for separation purpose.
            Returns a list of a timer and a pause for each couple specified. '''
        timers_and_pauses = []
        while True:
            timer_pause = input("Enter a timer and a pause in the form timer/pause.\n> ")
            if not timer_pause :
                return timers_and_pauses
            timers_and_pauses.append(timer_pause.split('/'))

    def _input_flow_name(self) -> str :
        return input("Enter a name for the flow :\n> ")

    def _timers_and_pauses(self, timers_and_pauses : list[list[str]] ) -> tuple[list[int], list[int]] :
        ''' Returns a tuple containing one list for the timers, and another one for the pauses.'''
        timers = [int(item[0]) for item in timers_and_pauses]
        pauses = [int(item[1]) for item in timers_and_pauses]
        return timers, pauses
    
    def build(self) -> Flow:
        return Flow(self.name, self.timers, self.pauses)

class FlowCollection :
    '''List of flows used to both present the flows to a user and allow a user to manipulate them.'''
    def __init__(self, conf : Config):
        self.conf = conf
        self.flows = self.__load(conf.flows)

    def __load(self, flows : list[dict[str, dict]]):
        loaded = []

        for flow in flows:
            for key, value in flow.items():
                builder = FlowBuilder()
                obj = builder.with_name(key).with_timers(value["timers"]).with_pauses(value["pauses"]).build()
                loaded.append(obj)

        return loaded

    def add(self) :
        flow = CommandLineFlowBuilder()
        self.flows.append( flow.to_dict() )

    def delete(self, index : int):
        try:
            self.flows.pop(index)
            self.write()
        except KeyError as e:
            raise e
        except Exception as e:
            raise Exception(e)

    def write(self) :
        self.conf.modify()

if __name__ == '__main__':
    conf = Config()
    collection = FlowCollection(conf)
    for i, flow in enumerate(collection.flows):
        print(i,flow)
        
    # collection.add()
    # collection.write()
    try:
        collection.delete(3)
    except KeyError as e:
        collection.delete("Ascendant")
        collection.write()
    except Exception as e:
        print(Exception(e))