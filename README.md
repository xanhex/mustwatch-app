# MustWatchApp

## Description

Cross-platform app that provides you with the list of the best movies.
You can mark the movies 'watched' and filter them out (slide to
left/right gestures). Supports data update from
[API](https://github.com/xanhex/mustwatch-django/).
UI presented in dark theme and supports two languages (EN/RU).

## Stack

- Python
- Kivy
- Requests

## Standards

- pep8
- flake8
- black
- pymarkdown

## How to run

1. Clone the repo and activate virtual environment.
2. Install dependencies from `requirements.txt`.
3. Execute `main.py` from the root directory of the project

    ```bash
    python main.py
    ```

## Build

The built apk file is located at `builds` folder, just copy and install it on
your Android device.

To build your own version consider to use
[buildozer](https://kivy.org/doc/stable/guide/packaging-android.html).

## Demo

![screenshot](https://github.com/xanhex/mustwatch-app/blob/master/demo.png)
