import shutil
from typing import Literal
import os
import subprocess
from shutil import rmtree
import json
import stat

FOLDER_CP_PROJECT = "C:/Users/romain/code/timetracker-back"
CP_PROJECT = os.path.join(FOLDER_CP_PROJECT, 'timer_sans_classe')
ORIGINAL_ROOT = "C:/Users/romain/code/python/timer_sans_classe"
CURR_FILE = os.path.abspath(__file__)
CP_CURR_FILE = os.path.join(CP_PROJECT, os.path.basename(CURR_FILE))
PATH_PREFIX = '../'

def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def main(dest_path : str, arg: Literal['api', 'tui'], dev : bool) -> None:
    if not os.path.exists(dest_path):
        print("Destination doesn't exist, creating folder")
        os.mkdir(dest_path)
    
    print("cloning front")
    subprocess.call(f'git clone https://github.com/CandussoR/timetracker_front.git {dest_path}', shell=True)
    os.chdir(dest_path)

    print("creating env")
    with open('.env', 'w') as fw:
        content = """VITE_APP_IP_DEV = "http://127.0.0.1:5000/"
VITE_APP_IP_PROD = "http://127.0.0.1:63267/"
VITE_APP_RING = /timer_end.mp3
VITE_APP_VERSION = 1.0.0"""
        fw.writelines(content)

    print("installing npm packages and tauri plugins")
    subprocess.call('npm install', shell=True)
    subprocess.call("npm run tauri add shell", shell=True)
    subprocess.call("npm run tauri add dialog", shell=True)

    assert os.path.exists('src-tauri'), "No tauri path"

    print(f"Copying this project into {FOLDER_CP_PROJECT}")
    if os.path.exists(FOLDER_CP_PROJECT):
        print("path exists")
        subprocess.call(f'rm -rf {FOLDER_CP_PROJECT}')
    os.mkdir(FOLDER_CP_PROJECT)
    subprocess.call(f'cp -r {ORIGINAL_ROOT} {FOLDER_CP_PROJECT}/')

    print(f"Creating gitattributes in copy project")
    os.chdir(CP_PROJECT)

    attributes_path = os.path.abspath(os.path.join('.', '.gitattributes'))
    with open(attributes_path, 'w') as fw:
        general = ".github/ export-ignore\ntests/ export-ignore\narchived export-ignore\nscripts export-ignore\n__pycache__/ export-ignore"
        content_api = "\nsrc/tui export-ignore\ntui_requirements.txt export-ignore"
        content_tui = "tests/ export-ignore\nsrc/web_api export-ignore\nrequirements.txt export-ignore"
        fw.writelines(general)
        fw.writelines(content_api if arg=='api' else content_tui)
    
    try:
        print("creating git archive")
        ret_code = subprocess.call('git archive --format=tar.gz --worktree-attributes --output=backend.tar.gz HEAD', shell=True)
        if not ret_code:
            os.remove(attributes_path)
        subprocess.call('mkdir backend')
        subprocess.call('tar -xzf backend.tar.gz -C backend')
        assert os.path.exists(os.path.join(CP_PROJECT, 'backend')), "Backend doesn't exists"

        print("\tGetting platform target triple")
        command = 'powershell -Command "rustc -Vv | Select-String \'host:\' | ForEach-Object {($_.Line -split \' \')[1]}"'
        target_triple = subprocess.run(command, shell=True, text=True, capture_output=True)
        if target_triple.returncode == 0:
            target_triple = target_triple.stdout.strip()

        print("Replacing run.py")
        os.remove(os.path.join(CP_PROJECT, "backend", "run.py"))
        if dev :
            subprocess.call(f"cp {os.path.join(os.path.dirname(CURR_FILE), 'python', 'run_api_dev.py')} {os.path.join(CP_PROJECT, 'backend', '')}")
        else:
            subprocess.call(f"cp {os.path.join(os.path.dirname(CURR_FILE), 'python', 'run_api.py')} {os.path.join(CP_PROJECT, 'backend', '')}")
        
        os.rename(os.path.join(CP_PROJECT, 'backend', 'run_api_dev.py' if dev else 'run_api.py'), os.path.join(CP_PROJECT, 'backend', 'run.py'))
        
        conf =  {"database": "./timer_data.db", 
                 "timer_sound_path": "",
                 "log_file": "./logs/logs.log",
                }
        with open(os.path.join(CP_PROJECT, "backend", "conf.json"), 'w') as fw:
            json.dump(conf, fw)
        os.remove('backend/conf_example.jsonc')

        if dev:
            subprocess.call(f'C:/Users/romain/.python-venv/timetracker/Scripts/pyinstaller.exe --name timetracker-backend-dev-{target_triple} --onefile --noconsole --hidden-import=flask --add-data "backend/conf.json;." backend/run.py')
        else :
            subprocess.call(f'C:/Users/romain/.python-venv/timetracker/Scripts/pyinstaller.exe --name timetracker-backend-{target_triple} --onefile --noconsole --hidden-import=flask --add-data "backend/conf.json;." backend/run.py')
    except Exception as e:
        print(f"Exception occured during the creation of the Python executable : {e}")

    print("cleaning Python build files")
    if os.path.exists('./backend'):
        rmtree('./backend')
    if os.path.exists('./build'):
        rmtree('./build')
    if os.path.exists('backend.spec'):
        os.remove('backend.spec')
    if os.path.exists('backend.tar.gz'):
        os.remove('backend.tar.gz')

    print("moving executable")
    tauri_path = os.path.join(dest_path, 'src-tauri')
    tauri_bin_path = os.path.join(tauri_path, 'bin')
    if not (os.path.exists(tauri_bin_path)):
        os.mkdir(tauri_bin_path)
    # Deleting previous version of sidecar if any
    if dev :
        if os.path.isfile(f'{dest_path}\\src-tauri\\bin\\timetracker-backend-dev-{target_triple}.exe'):
            os.remove(f'{dest_path}\\src-tauri\\bin\\timetracker-backend-dev-{target_triple}.exe')
    else:
        if os.path.isfile(f'{dest_path}\\src-tauri\\bin\\timetracker-backend-{target_triple}.exe'):
            os.remove(f'{dest_path}\\src-tauri\\bin\\timetracker-backend-{target_triple}.exe')
    # Copying new sidecar version
    if dev :
        shutil.copy2(f'./dist/timetracker-backend-dev-{target_triple}.exe', f'{dest_path}\\src-tauri\\bin\\')
    else:
        shutil.copy2(f'./dist/timetracker-backend-{target_triple}.exe', f'{dest_path}\\src-tauri\\bin\\')
    rmtree('dist')
    
    print('building exe')
    os.chdir(dest_path)
    subprocess.call('npm run tauri build', shell=True)

    print("cleaning")
    rmtree(FOLDER_CP_PROJECT, onerror=remove_readonly)

if __name__ == '__main__':
    import sys
    test = False
    dest_path, *args = sys.argv[1:]
    if args[0] not in ('api', 'tui'):
        raise ValueError(f"Arg can only be either 'api' or 'tui' : got {args[0]}.")
    if len(args) > 1 and args[1] and args[1] == '--test':
        test = True
    main(dest_path, args[0], test)
    