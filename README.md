# Overview

This app is a timer/clockwatch which keeps track of activity in a SQLite database and displays some stats.

## Status
Under development.

## Features
* Timer / Chrono :
  * Each can have a tag in addition to a pairing of task and subtask ;
* Flows ;
* Add a past timer / edit old ones ;
* Daily, weekly, monthly and yearly generic statistics page ;
* Timer retrieval by date, period or range, + tag, + task (and subtask).

## Good to know
* Because the sql requests use the RETURNING keyword, **SQlite must be at least version 3.35**.

## Future
This repo is probably going to be divided between a standalone TUI repo and a back repo meant to be used with the [timetracker front](https://github.com/CandussoR/timetracker_front).

## Install
- Clone the repo with :
  ```git clone https://github.com/CandussoR/timetracker.git```
- Head to your repo :
  ```cd timetracker```
- Optional : create a virtual environment :
  ```python -m venv venv``` (or path/to/venv_name)
  - After that, you can activate your virtual environment on Linux and Mac with  
  ```source venv/bin/activate```
  or
  ```venv\Scripts\activate.bat``` on Windows ;
- If you want to use the TUI, install the TUI requirements :
  ```pip install -r tui_requirements.txt```
- If you prefer to use the API:
  ```pip install -r requirements.txt```
- Modify the `conf_example.json` and rename it to `conf.json`
- Launch the program with `python run.py <config/file/path>` for the TUI or `python run.py <config/file/path> --api` for the API.
- If you want to launch it with a test environment, you can use `python run.py <testconfig/file/path> --test [--api]`
- If you use the API, you can test things with POSTMAN (I didn't do the API doc yet though) or clone and follow the instructions given in the [timetracker front](https://github.com/CandussoR/timetracker_front).

## Making it a bit handier
- To make it easier to launch from the command line, you can create an alias and make the program run with one word.  
  - On mac and linux, you can add  
  ```shell
  alias timetracker='cd ; source <path_to_my_venv>/bin/activate; cd <path/to/timetracker/folder>; python run.py'
  ```  
  to your .bash_profile, and relaunch your terminal with `source .bash_profile`. Sometimes "python" won't work and you'll have to use "python3" instead, or "python3.11", or something else. It depends on your setup.  
  - On Windows, you can set a `doskey` in the command prompt :
  ```cmd
  doskey timetracker=<path_to_my_venv>\Scripts\activate.bat $T cd <path/to/timetracker/folder> $T python run.py
  ```

## Roadmap :
* Statistics UI elements for custom search ;
* Creation of a custom dashboard thanks to a selection of graph & display elements wanted ;
* Possibility to create automated custom queries to generate reports ;
* Possibility to generate reports in both html and markdown (targetting a display in Obsidian, in particular) ;
* Possibility to create a pdf for a special report.
