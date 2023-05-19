import json

def load_conf(conf_file : str) -> dict:
    with open(conf_file, 'r') as fr:
        return json.load(fr)

def switch_logs(conf : dict, conf_file : str) -> dict:
    conf['log'] = not conf['logs']
    write_conf(conf, conf_file)
    return conf['logs']

def write_conf(conf: dict, conf_file : str):
    with open(conf_file, 'w') as fw:
        json.dump(conf, fw)

# Lire le fichier pour voir les logs
# Créer une fonction pour parser le fichier et export une variable logs
# Utiliser la variable logs dans le script,
# Créer une entrée dans le prompt permettant de modifier ou non les logs.

if __name__ == '__main__':
    conf = load_conf("conf.json")
    switch_logs(conf, "conf.json")