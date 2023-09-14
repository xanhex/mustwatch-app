# coding: utf-8
"""
Must Watch.

The app that provides you with the list of the best movies.
You can mark the movies 'watched' and filter them out
(slide to left/right gestures).
Supports data update from API. UI presented in dark theme and supports
two languages (EN/RU).
"""
import kivy

kivy.require('2.1.0')

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import get_color_from_hex

load_dotenv('./data/.env')

os.environ['KIVY_ORIENTATION'] = 'Portrait'

__version__ = '0.1'

# For Windows

# Config.set('graphics', 'width', '405')
# Config.set('graphics', 'height', '900')
# Config.set('graphics', 'resizable', '0')

# MustWatch API endpoint
# Refer to https://github.com/Jmastermind/mustwatch-django
ENDPOINT = os.getenv('ENDPOINT')


class UI(BoxLayout):
    """UI root layout."""


class InfoPopup(Popup):
    """System info popup."""


class ProcessPopup(Popup):
    """Process popup."""


class SM(ScreenManager):
    """Main UI."""

    def on_touch_move(self, touch) -> None:
        """Slide getsture handler."""
        app = App.get_running_app()
        if (touch.ox - touch.x) > 100 and not app.watchlist and app.get_data():
            app.filter(True)
        elif (touch.ox - touch.x) < -100 and app.watchlist:
            app.filter(False)
            self.current = 'all'


class MyApp(App):
    """Main app class."""

    title = 'MustWatch'
    icon = './data/img/icon.png'

    status = 'System message'

    data = []
    not_watched_data = []
    current_movie = 0
    language = ''
    common_fields = [
        'year',
        'kp',
        'imdb',
        'poster',
        'watched',
        'kp',
        'imdb',
        'poster',
        'watched',
    ]
    translated_fields = [
        'title',
        'type',
        'genre',
        'director_1',
        'director_2',
        'star_1',
        'star_2',
        'star_3',
        'description',
    ]
    watchlist = False

    def setup(self) -> None:
        """Popups setup."""
        self.progress_popup = ProcessPopup()
        self.info_popup = InfoPopup()

    def initiate(self) -> None:
        """Initiate app data."""
        self.read_settings()
        self.read_data()
        self.get_not_watched_data()
        self.get_movie()

    def reset_data(self) -> None:
        """
        Reset app data.

        Deletes movies.json and all poster images from the folder.
        """
        Path('data/movies.json').unlink(missing_ok=True)
        for poster in Path('data/posters').glob('*'):
            if not poster.match('noposter.png'):
                poster.unlink()
        self.data = []
        self.get_movie()

    def download_posters(self, data) -> None:
        """Download posters from MustWatch server."""
        posters_urls = [i['poster'] for i in data]
        try:
            for p in posters_urls:
                response = requests.get(p)
                fname = p.split('/')[-1]
                with open(f'./data/posters/{fname}', 'wb') as f:
                    f.write(response.content)
        except Exception:
            self.info_popup.ids.message.text = 'Can not download posters'
            self.info_popup.open()

    def download_data(self) -> dict:
        """Download movies.json and movies posters from MustWatch using API."""
        api_answer = False
        try:
            api_answer = requests.get(ENDPOINT)
        except requests.RequestException:
            self.info_popup.ids.message.text = 'Server is not available'
            self.info_popup.open()
        if api_answer:
            if api_answer.status_code != requests.codes.OK:
                self.info_popup.ids.message.text = 'Invalid API answer'
                self.info_popup.open()
            return api_answer.json()
        return False

    def convert_data(self, data: list) -> list:
        """Convert raw data to proper."""
        for movie in data:
            for m in self.data:
                if movie['id'] == m['id']:
                    movie['watched'] = m['watched']
            movie['poster'] = (
                './data/posters/' + movie['poster'].split('/')[-1]
            )
        return data

    def read_settings(self) -> None:
        """Read settings from data.json and set app language."""
        try:
            with open('./data/data.json', 'r') as f:
                self.settings = json.load(f)
        except IOError:
            self.info_popup.ids.message.text = 'Can not read settings data'
            self.info_popup.open()
        self.language = self.settings['language']
        self.ui.ids.lang.text = 'RU' if self.language else 'ENG'

    def save_settings(self) -> None:
        """Save settings to data.json."""
        json_string = json.dumps(self.settings, indent=4)
        try:
            with open('./data/data.json', 'w') as f:
                f.write(json_string)
        except IOError:
            self.info_popup.ids.message.text = 'Can not save settings'
            self.info_popup.open()

    def read_data(self) -> None:
        """Read movies data from movies.json."""
        try:
            with open('./data/movies.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except IOError:
            self.info_popup.ids.message.text = 'Can not read movies data'
            self.info_popup.open()

    def get_not_watched_data(self) -> None:
        """Get not watched movies list."""
        self.not_watched_data = [m for m in self.data if not m['watched']]

    def save_data(self, data, bk=False) -> None:
        """Save movies data to movies.json."""
        if bk:
            Path('data/movies.json').replace('data/data_bk.json')
        json_string = json.dumps(data, indent=4, ensure_ascii=False)
        try:
            with open('./data/movies.json', 'w', encoding='utf-8') as f:
                f.write(json_string)
        except IOError:
            self.info_popup.ids.message.text = 'Can not save data'
            self.info_popup.open()

    def schedule_download(self) -> None:
        """Schedule downloading from server."""
        self.progress_popup.ids.message.text = 'Setting up database'
        self.progress_popup.open()
        Clock.schedule_once(self.obtain_data)
        self.progress_popup.dismiss()

    def obtain_data(self, dt: float) -> None:
        """[async] Download data from server and convert it."""
        data = self.download_data()
        if isinstance(data, list):
            self.download_posters(data)
            conv_data = self.convert_data(data)
            self.save_data(conv_data)
            Clock.schedule_once(lambda dt: self.initiate(), 1)

    def get_prev_cur_next(self, data) -> dict:
        """Get previous, current and next movies."""
        return (
            (
                data[self.current_movie - 1]
                if self.current_movie - 1 >= 0
                else False
            ),
            (
                data[self.current_movie]
                if self.current_movie < len(data)
                else False
            ),
            (
                data[self.current_movie + 1]
                if self.current_movie + 1 < len(data)
                else False
            ),
        )

    def get_data(self) -> list:
        """Get movies data."""
        data = self.data if not self.watchlist else self.not_watched_data
        if not data:
            if self.watchlist:
                self.ui.ids.all_watched.ids.no_movies.text = (
                    'All movies watched'
                )
            else:
                self.ui.ids.all_watched.ids.no_movies.text = 'No movies'
                self.no_data = True
            self.ui.ids.sm.current = 'all_watched'
            return None
        self.ui.ids.sm.current = 'all'
        return data

    def get_movie(self, mode='default') -> None:
        """Get the movie."""
        data = self.get_data()
        if not isinstance(data, list):
            return
        previous, current, next = self.get_prev_cur_next(data)
        if mode == 'prev' and previous:
            self.current_movie = self.current_movie - 1
            movie = previous
        elif mode == 'next' and next:
            self.current_movie = self.current_movie + 1
            movie = next
        elif mode == 'next_available':
            if next:
                self.current_movie = self.current_movie + 1
                movie = next
            elif current:
                movie = current
            else:
                self.current_movie = self.current_movie - 1
                movie = previous
        elif mode == 'default':
            movie = data[self.current_movie]
        previous, current, next = self.get_prev_cur_next(data)
        self.update_fields(movie, (bool(previous), bool(next)))

    def update_fields(
        self,
        movie,
        previous_next,
    ) -> None:
        """Update UI."""
        try:
            for field in self.common_fields:
                if field == 'poster':
                    self.ui.ids['poster'].source = (
                        movie['poster']
                        if Path(movie['poster']).exists()
                        else './data/posters/noposter.png'
                    )
                if field == 'watched':
                    self.ui.ids['watched'].state = (
                        'down' if movie['watched'] else 'normal'
                    )
                else:
                    self.ui.ids[field].text = movie[field]
            for field in self.translated_fields:
                self.ui.ids[field].text = movie[field + self.language]
            (
                self.ui.ids['prev'].disabled,
                self.ui.ids['prev'].opacity,
            ) = not previous_next[0], int(previous_next[0])
            (
                self.ui.ids['next'].disabled,
                self.ui.ids['next'].opacity,
            ) = not previous_next[1], int(previous_next[1])
        except Exception:
            self.info_popup.ids.message.text = 'Couldn not update UI'
            self.info_popup.open()

    def filter(self, mode) -> None:
        """Switch watched/all movies screen mode."""
        self.watchlist = mode
        self.current_movie = 0
        self.ui.ids['all'].bg_color = (
            get_color_from_hex(self.ui.main_color)
            if not mode
            else get_color_from_hex(self.ui.third_color)
        )
        self.get_movie()

    def switch_movie(self) -> None:
        """Switch movie."""
        if not self.watchlist:
            self.data[self.current_movie]['watched'] = not self.data[
                self.current_movie
            ]['watched']
            self.get_not_watched_data()
        else:
            for m in self.data:
                if m['id'] == self.not_watched_data[self.current_movie]['id']:
                    m['watched'] = not m['watched']
                    break
            self.get_not_watched_data()
            self.get_movie('next_available')
        self.save_data(self.data)

    def switch_language(self) -> None:
        """Switch app language."""
        self.language = '' if self.language else '_ru'
        self.ui.ids.lang.text = 'RU' if self.language else 'ENG'
        self.settings['language'] = self.language
        self.save_settings()
        self.get_movie()

    def build(self) -> SM:
        """App startup."""
        self.setup()
        self.ui = UI()
        self.initiate()
        return self.ui

    def on_stop(self):
        """Save data on quit."""
        self.save_data(self.data)


if __name__ == '__main__':
    MyApp().run()
