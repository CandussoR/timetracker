import parse_conf as pc
import os
import datetime
from subprocess import Popen, call

def write_log(file_path : str, task : str, subtask : str = "") :
    if os.path.isdir(file_path):

        log_file_path = os.path.join(file_path, str(datetime.datetime.now().year), f"{task.replace(' ', '')}.md")

        # Prepared strings
        title = f"# {task}  \n\n"
        date_line = f"- {datetime.datetime.now().strftime('%Y-%m-%d')} :  \n"
        subtask_string = f"  - {subtask} :  \n  "

        # I prefer this to the one below
        if not os.path.isfile(log_file_path):
            Popen(['touch', log_file_path])
            # Launch a shell command
            call(f'''echo "{title + date_line + subtask_string}" >> {log_file_path}''', shell=True)

        # Checks if file exists, and if not
        # os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        else :
            with open(log_file_path, 'r', encoding="UTF-8", newline="") as fr:
                file = fr.readlines()          
                    
                if (date_line in file[::-1]) :
                    
                    if subtask and not (subtask_string in file[::-1]):
                        with open(log_file_path, 'a+', encoding="ISO-8859-1", newline="") as fw:
                            fw.write(subtask_string)
                                    
                else :
                    with open(log_file_path, 'a+', encoding="ISO-8859-1", newline="") as fw:
                        fw.write(date_line + subtask_string) if subtask else fw.write(date_line)

        Popen(['open', log_file_path])

if __name__ == "__main__":
    import json
    with open("conf.json", 'r') as fr:
        conf = json.loads(fr.read())
    print(write_log(conf['log_path'], "Feuille de route", "Avion"))