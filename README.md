# Overview

This app is a timer/clockwatch which keeps track of activity in a SQLite database and displays some stats.

## Status
Under development.

## Future
This repo is probably going to be divided between a standalone TUI repo and a back repo meant to be used with the [timetracker front](https://github.com/CandussoR/timetracker_front).


## Install
- Clone the repo with :
  ```git@github.com:CandussoR/timer_sans_classe.git```
  - An error might occur if you haven't yet added any ssh key to Github.  
  If so, either clone with HTTPS with the command :  
  ```git clone https://github.com/CandussoR/timer_sans_classe.git```  
  or use [this Github tuto](https://docs.github.com/fr/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account) to add an ssh key.  
- The packages needed to run the script are in the file `requirements.txt`.  
  You can either install them globally on your machine using `pip install -r requirements.txt`,  
  or create a virtual environment and install the packages needed in there.  
  - To create your [virtual environment](https://docs.python.org/3/library/venv.html), customize and run the command  
  ```python -m venv path/to/env```  
  For example, `python -m venv .python-venv/timetracker` will create a timetracker folder inside the hidden python-env folder.  
  - After that, you can activate your virtual environment on Linux and Mac with  
  ```source .python-venv/timetracker/bin/activate```
  or
  ```.python-env\timetracker\Scripts\activate.bat``` on Windows.  
  - Once activated, `(timetracker)` should show in the command line prompt. Now you can run ``pip install -r requirements.txt`, which will only install the packages needed for this script to run in your environment.  
  - When you're done, you can deactivate the virtual environment with `deactivate`.  

## Making it a bit handier
- To make it easier, you can just create an alias and make the program run with one word.  
  - On mac and linux, you can add  
  ```shell
  alias timetracker='cd ; source .python-venv/timetracker/bin/activate; cd <path/to/timetracker/folder>; python script.py'
  ```  
  to your .bash_profile, and relaunch your terminal with `source .bash_profile`. Sometimes "python" won't work and you'll have to use "python3" instead, or "python3.11", or something else. It depends on your setup.  
  - On Windows, you can set a `doskey` in the command prompt :
  ```cmd
  doskey timetracker=.python-venv\timetracker\Scripts\activate.bat $T cd code\timer_sans_classe $T python script.py
  ```
- Note that there might be something better to do, but this will be good enough to play with it.

## Launching the API
* You can launch the API with the command `python3 run.py --api`.
* If you have a test database named `test.db` you'd like to branch the api too, you can use the `--test` arg :
  `python3 run.py --api --test`.
