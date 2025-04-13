import os
import stat
import subprocess

CURR_FILE = os.path.abspath(__file__)
CURR_DIR = os.path.dirname(__file__)
ORIGINAL_ROOT = os.path.abspath('../../')
DEST_PATH = os.path.abspath(os.path.join(CURR_DIR, '../../..'))
PATH_PREFIX = '../'

with open('log', 'a') as fw:
    fw.write(f'CURR FILE : {CURR_FILE}, ORIGINAL_ROOT : {ORIGINAL_ROOT}, DEST_PATH : {DEST_PATH}, PATH_JOIN_TT_FRONT : {os.path.join(DEST_PATH, "timetracker_front")}')

def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def main() -> None:
    arg = os.getenv("arg")
    test = os.getenv("test")

    print("Going outside where we'll create the front")
    os.chdir(DEST_PATH)
    
    print("cloning front")
    subprocess.call(f'git clone https://github.com/CandussoR/timetracker_front.git', shell=True)
    os.chdir(os.path.join(DEST_PATH, 'timetracker_front'))
    
    print("creating env")
    with open('.env', 'w') as fw:
        content = """VITE_APP_IP_DEV = "http://127.0.0.1:5000/"
VITE_APP_IP_PROD = "http://127.0.0.1:63267/"
VITE_APP_RING = /timer_end.mp3
VITE_APP_VERSION = 0.9.0"""
        fw.writelines(content)

#     print("installing npm packages and tauri plugins")
#     subprocess.call('npm install', shell=True)
#     subprocess.call("npm run tauri add shell", shell=True)
#     subprocess.call("npm run tauri add dialog", shell=True)

#     assert os.path.exists('src-tauri'), "No tauri path"


    print(f"Creating gitattributes in copy project")

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
        
    #     print("\tGetting platform target triple")
    #     command = 'powershell -Command "rustc -Vv | Select-String \'host:\' | ForEach-Object {($_.Line -split \' \')[1]}"'
    #     target_triple = subprocess.run(command, shell=True, text=True, capture_output=True)
    #     if target_triple.returncode == 0:
    #         target_triple = target_triple.stdout.strip()

    #     print("Replacing run.py")
    #     os.remove(os.path.join(CP_PROJECT, "backend", "run.py"))
    #     subprocess.call(f"cp {os.path.join(os.path.dirname(CURR_FILE), 'python', 'run_api.py')} {os.path.join(CP_PROJECT, 'backend', '')}")
    #     os.rename(os.path.join(CP_PROJECT, 'backend', 'run_api.py'), os.path.join(CP_PROJECT, 'backend', 'run.py'))
        
    #     conf =  {"database": "./timer_data.db", 
    #              "timer_sound_path": "",
    #              "log_file": "./logs/logs.log",
    #             }
    #     with open(os.path.join(CP_PROJECT, "backend", "conf.json"), 'w') as fw:
    #         json.dump(conf, fw)
    #     os.remove('backend/conf_example.jsonc')

    #     subprocess.call(f'C:/Users/romain/.python-venv/timetracker/Scripts/pyinstaller.exe --name timetracker-backend-{target_triple} --onefile --noconsole --hidden-import=flask --add-data "backend/conf.json;." backend/run.py')
    except Exception as e:
        print(f"Exception occured during the creation of the Python executable : {e}")

    # print("cleaning Python build files")
    # if os.path.exists('./backend'):
    #     rmtree('./backend')
    # if os.path.exists('./build'):
    #     rmtree('./build')
    # if os.path.exists('backend.spec'):
    #     os.remove('backend.spec')
    # if os.path.exists('backend.tar.gz'):
    #     os.remove('backend.tar.gz')

    # print("moving executable")
    # tauri_path = os.path.join(DEST_PATH, 'src-tauri')
    # tauri_bin_path = os.path.join(tauri_path, 'bin')
    # if not (os.path.exists(tauri_bin_path)):
    #     os.mkdir(tauri_bin_path)
    # if os.path.isfile(f'{DEST_PATH}\\src-tauri\\bin\\timetracker-backend-{target_triple}.exe'):
    #     os.remove(f'{DEST_PATH}\\src-tauri\\bin\\timetracker-backend-{target_triple}.exe')
    # shutil.copy2(f'./dist/timetracker-backend-{target_triple}.exe', f'{DEST_PATH}\\src-tauri\\bin\\')
    # rmtree('dist')
    
    # print('building exe')
    # os.chdir(DEST_PATH)
    # # subprocess.call('npm run tauri build -- --features launch_binary --debug', shell=True)
    # subprocess.call('npm run tauri build -- --features launch_binary', shell=True)

    # print("cleaning")
    # rmtree(FOLDER_CP_PROJECT, onerror=remove_readonly)

    if __name__ == '__main__':
        main()