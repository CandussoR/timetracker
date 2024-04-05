from datetime import datetime


def convert_to_custom_dict(params):
    '''
        Converts the dicts returned from the front to insure data quality.
        Throws `TypeError` with wrong date formats, and `KeyError` if there are multiple time spans.
    '''
    time_format = {
        "year" : "%Y",
        "month" : "%Y-%m",
        "week" : "%Y-%m-%d",
        "day" : "%Y-%m-%d"
    }
    
    conditions = {}

    check_time_clause(params.keys())
    
    for k in params :
        if k in ["day", "month", "week", "year"]:
            conditions[k] = datetime.strptime(params[k], time_format[k])
        elif k == "week[]" and not "weekStart" in conditions.keys():
            [conditions["weekStart"], conditions["weekEnd"]] = map(lambda x : datetime.strptime(x, time_format["day"]), params.getlist("week[]"))
        elif k in ["rangeBeginning", "rangeEnding"]:
            conditions[k] = datetime.strptime(k, time_format["day"]) 
        else:
            conditions[k] = params[k]
    
    return conditions


def check_time_clause(keys : list[str]):
    time_clause = None
    for k in keys:
        if k in ["day", "month", "week[]", "year", "range[]"] :
            if time_clause:
                raise KeyError("You cannot have two time spans in one request.")
            else:
                time_clause = k
        
        