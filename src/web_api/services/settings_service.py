import pathlib
import posixpath
import os
import shutil
from flask import current_app, g
from src.shared.config.conf import Config

def update_settings(args : dict, conf : Config):
    for k,v in args.items():
        if k == "database":
            old_path = conf.database
            if os.path.isdir(v) and os.path.exists(v):
                v_posix = pathlib.PureWindowsPath(v).as_posix()
                new_path = posixpath.join(v_posix,os.path.basename(current_app.config["database"]))
                g._database.close()
                shutil.copy2(current_app.config["database"], v)
            elif os.path.isfile(v) and v.endswith(".db"):
                new_path = v
            else:
                raise ValueError("This path is neither a directory nor a database.")
            current_app.config["database"] = new_path
            conf.database = new_path    
            conf.modify()
            if "delete_database" in args and args["delete_database"]:
                os.remove(old_path)
        elif k == "timer_ring":
            if not v:
                current_app.config.update({"timer_sound_path": ""})
                conf.timer_sound_path = ""
                conf.modify()
            elif os.path.isfile(v) and v.endswith(".mp3"):
                current_app.config.update({"timer_sound_path": v})
                conf.timer_sound_path = v
                conf.modify()
            else:
                raise ValueError("Path must refer to a mp3 file.")