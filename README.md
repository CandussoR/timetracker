# Overview

This app is a timer/clockwatch which keeps track of activity in a SQLite database and displays some stats.

## Status
Under development.

## Features
* Timer / Chrono :
  * Each can have a tag in addition to a pairing of task and subtask ;
* Flows (TUI only);
* Add a past timer / edit old ones ;
* Daily, weekly, monthly and yearly generic statistics page ;
* Time record retrieval by date, period or range, + tag, + task (and subtask).

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
- If you want to use the Terminal User Interface, install the TUI requirements :
  ```pip install -r tui_requirements.txt```
- If you prefer to use the API:
  ```pip install -r requirements.txt```
- Modify the `conf_example.jsonc` (don't forget to delete the comments or it won't be loaded) and rename it to `conf.json`
- Launch the program with `python run.py <config/file/path>` for the TUI or `python run.py <config/file/path> --api` for the API.
- If you want to launch it with a test config, you can use `python run.py <testconfig/file/path> --test [--api]
> [!IMPORTANT]
> Your test config filename must begin by 'test_'.

- If you use the API, you can test things with POSTMAN (I didn't do the API doc yet though) or clone the front-end repo and follow the instructions given in the [timetracker front](https://github.com/CandussoR/timetracker_front).

## Command line : making it handier
- To make it easier to launch from the command line, you can create an alias and make the program run with one word.  
  - On mac and linux, you can add  
  ```shell
  alias timetracker='cd ; source <path_to_my_venv>/bin/activate; cd <path/to/timetracker/folder>; python run.py <path/to/conf.json>'
  ```  
  to your .bash_profile. Relaunch your terminal with `source .bash_profile`. Sometimes "python" won't work and you'll have to use "python3" instead, or "python3.11", or something else. It depends on your setup.  
  - On Windows, you can set a `doskey` in the command prompt :
  ```cmd
  doskey timetracker=<path_to_my_venv>\Scripts\activate.bat $T cd <path/to/timetracker/folder> $T python run.py <path/to/conf.json>
  ```

## Roadmap :
* Custom stat search for personalized stat elements and custom parameters ;
* Possibility to create automated custom queries to generate reports ;
* Possibility to generate reports in both html and markdown (targetting a display in Obsidian, in particular) ;
* Possibility to create a pdf for a special report.
