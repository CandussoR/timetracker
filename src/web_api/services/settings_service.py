import pathlib
import posixpath
import os
import shutil
from flask import current_app, g
from src.shared.config.conf import Config
from src.shared.utils.posix_path import get_abspath
from src.shared.database.sqlite_db import connect

def update_settings(args : dict, conf : Config):
    for k,v in args.items():
        if k == "database":
            old_path = conf.database
            # Moving db
            if os.path.isdir(v) and os.path.exists(v):
                v_posix = pathlib.PureWindowsPath(v).as_posix()
                new_path = posixpath.join(v_posix,os.path.basename(current_app.config["database"]))
                g._database.close()
                shutil.copy2(current_app.config["database"], v)
                if ("delete_database" in args and args["delete_database"]):
                    os.remove(old_path)
            # Switching db
            elif os.path.isfile(v) and v.endswith(".db"):
                new_path = v
                # Automatic deletion of old db if empty
                rows, = g._database.execute('SELECT COUNT(id) FROM timer_data').fetchone()
                if rows == 0:
                    g._database.close()
                    os.remove(old_path)
            else:
                raise ValueError("This path is neither a directory nor a database.")

            # Updating config
            current_app.config["database"] = new_path
            conf.database = new_path    
            conf.modify()

        elif k == "timer_ring":
            if not v:
                current_app.config.update({"timer_sound_path": ""})
                conf.timer_sound_path = ""
                conf.modify()
            elif os.path.isfile(v) and v.endswith(".mp3"):
                current_app.config.update({"timer_sound_path": get_abspath(v)})
                conf.timer_sound_path = v
                conf.modify()
            else:
                raise ValueError("Path must refer to a mp3 file.")