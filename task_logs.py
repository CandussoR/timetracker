import os 
import platform 
import datetime 
from subprocess import Popen

def write_log(file_path : str, task : str, subtask : str = "") :

    if not os.path.isdir(file_path):
        raise Exception("Path must point to a directory.")

    log_file_path = os.path.join(file_path, str(datetime.datetime.now().year), f"{task.replace(' ', '')}.md")

    # Prepared strings
    title = f"# {task}  \n\n"
    date_line = f"- {datetime.datetime.now().strftime('%Y-%m-%d')} :  \n  "
    subtask_string = f"- {subtask} :  \n  "

    log_file_path_exists = os.path.isfile(log_file_path)

    # Lecture de l'intégralité du fichier
    file_content = ""
    if (log_file_path_exists):
        with open(log_file_path, 'r', encoding="UTF-8", newline="") as fr:
            file_content = fr.read()

    with open(log_file_path, 'a+', encoding="ISO-8859-1", newline="") as fw:
        # Le fichier n'existait pas !? On crée la ligne d'en-tête
        if (not log_file_path_exists):
            fw.write(f"{title}{date_line}{subtask_string}")

        if file_content != "" and not file_content.endswith("  \n"):
            fw.write("  \n")

        # La date_line n'existe pas !? On l'écrit !
        if (date_line not in file_content):
            fw.write(date_line)

        position_date_line = date_line.find(date_line)
        file_content_date_line = date_line[position_date_line:]
        
        if subtask and not (subtask_string in file_content_date_line):
            fw.write(subtask_string)

    cmd = "start" if platform.system() == "Windows" else "open"
    Popen([cmd, log_file_path], shell=True)

if __name__ == "__main__":
    import json
    with open("conf.json", 'r') as fr:
        conf = json.loads(fr.read())
    # print(write_log(conf['log_path'], "Ecriture"))
    write_log(conf['log_path'], "Code")