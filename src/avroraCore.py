import asyncio
import json
import logging
import os
import random
import re
import sys
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from ctypes import cast, POINTER
from datetime import datetime
from datetime import timedelta
from urllib.parse import quote_plus

import geocoder
import psutil
import pyautogui
import python_weather
import requests
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from bs4 import BeautifulSoup
from comtypes import CLSCTX_ALL
from gtts import gTTS
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

import constants as const
from constants import CMD_CHANGE_ACCENT_COLOR

executor = ThreadPoolExecutor(max_workers=const.MAX_WORKERS)

_PROGRAMS_CACHE = None
_PROGRAMS_CACHE_LOCK = asyncio.Lock()


async def run_command(command):
    """Виконує команду для терміналу"""
    logging.info(f"Executing system command: '{command}'")
    loop = asyncio.get_running_loop()
    process = await loop.run_in_executor(executor, os.system, command)
    logging.info(f"Command '{command}' finished with exit code {process}.")
    return process


async def timer(duration, thing):
    """Запускає таймер"""
    logging.info(f"Starting timer for {duration} seconds for: {thing}")
    await asyncio.sleep(duration)
    logging.info(f"Timer finished for: {thing}")
    return thing


def uk_to_en(text):
    """Перетворює символи кирилиці в латинницю"""
    logging.info(f"Converting Ukrainian text to English: '{text}'")
    result = ""
    for symbol in text:
        en_symbol = const.KEYS_EN.get(symbol)
        if en_symbol:
            result += en_symbol
        else:
            result += symbol
    logging.info(f"Converted to English: '{result}'")
    return result


async def save_settings(settings, filename=const.SETTINGS_FILENAME):
    logging.info(f"Saving settings to {filename}.")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, _save_settings, settings, filename)


def _save_settings(settings, filename):
    """Зберігає налаштування"""
    logging.debug(f"Writing settings to {filename}: {settings}")
    with open(filename, "w") as file:
        json.dump(settings, file)


async def load_settings(filename=const.SETTINGS_FILENAME):
    logging.info("Loading settings.")
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _load_settings, filename)


def _load_settings(filename):
    """Завантажує налаштування"""
    defaults = {"name": const.DEFAULT_NAME, "tgo": False, "tgpath": const.DEFAULT_TG_PATH,
                "music": const.DEFAULT_MUSIC_LINK, "pcpower": False, "city": const.DEFAULT_CITY, "num_headlines": 5,
                "theme": const.DEFAULT_THEME, "silentmode": False}
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                settings = json.load(file)
                if not isinstance(settings, dict):
                    settings = {}
        except (json.JSONDecodeError, OSError) as e:
            logging.error(f"Failed to load or parse settings from {filename}: {e}", exc_info=True)
            settings = {}
    else:
        logging.info(f"Settings file {filename} not found, using defaults.")
        settings = {}

    final_settings = defaults.copy()
    final_settings.update(settings)

    logging.info(f"Settings loaded: {final_settings}")
    if final_settings != settings:
        _save_settings(final_settings, filename)

    return final_settings


async def save_cc(command, filename=const.CUSTOM_COMMANDS_FILENAME):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, _save_cc, command, filename)


def _save_cc(command, filename):
    """Зберігає користувацькі команди"""
    with open(filename, "w") as file:
        json.dump(command, file)


async def load_cc(filename=const.CUSTOM_COMMANDS_FILENAME):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _load_cc, filename)


def _load_cc(filename):
    """Завантажує користувацькі команди"""
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return {}


def _get_start_menu_dirs():
    """Отримує шляхи до користувача і стандартних каталогів з програмами"""
    if sys.platform != "win32":
        return []

    # Common Start Menu
    common_start_menu = os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft', 'Windows', 'Start Menu',
                                     'Programs')

    # User's Start Menu
    user_start_menu = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs')

    return [d for d in [common_start_menu, user_start_menu] if d and os.path.isdir(d)]


def _scan_programs():
    """Сканує типові місцеперебування програм і повертає словник"""
    programs = {}
    start_menu_dirs = _get_start_menu_dirs()

    for directory in start_menu_dirs:
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(('.lnk', '.exe')):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(root, filename)
                    programs[name.lower()] = path
    return programs


async def find_installed_programs():
    """Знаходить завантаженні програми"""
    global _PROGRAMS_CACHE
    async with _PROGRAMS_CACHE_LOCK:
        if _PROGRAMS_CACHE is None:
            logging.info("Scanning for installed programs...")
            loop = asyncio.get_running_loop()
            _PROGRAMS_CACHE = await loop.run_in_executor(executor, _scan_programs)
            logging.info(f"Found {len(_PROGRAMS_CACHE)} programs.")
        return _PROGRAMS_CACHE


async def get_location():
    """Отримує інформацію про місцеперебування"""
    logging.info("Attempting to get location via geocoder.")
    location = geocoder.ip(const.GEOCODER_IP_ME)
    if not location.city:
        logging.warning("Failed to determine city from IP.")
        return const.RESPONSE_LOCATION_FAILED
    logging.info(f"Location determined: {location.city}, {location.country}")
    return location


async def get_weather_info():
    """Отримує інформацію про погоду для поточного місцеперебування"""
    settings = await load_settings()  # This is already logged in load_settings
    city = settings.get("city")
    try:
        if not city:
            location = await get_location()
            if not location.city:
                return const.RESPONSE_WEATHER_FAILED_NO_CITY
            city = location.city
        async with python_weather.Client(unit=python_weather.METRIC, locale=python_weather.Locale.UKRAINIAN) as client:
            logging.info(f"Fetching weather for city: {city}")
            weather = await client.get(city)

            response = const.RESPONSE_WEATHER_FORECAST.format(city, weather.temperature, weather.description)
            logging.info(f"Successfully fetched weather: {response}")
            return response
    except Exception as e:
        logging.error(f"Error getting weather for city '{city}': {e}", exc_info=True)
        return const.RESPONSE_WEATHER_ERROR


def _get_news_headlines(url="", class_name=""):
    """Отримує заголовки новин з інтернету"""
    logging.info(f"Fetching news headlines from URL: {url} with class: {class_name}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, const.HTML_PARSER)
        titles = []
        for div in soup.find_all("div", {"class": class_name}):
            for a in div.find_all("a"):
                titles.append(a.text)
        logging.info(f"Found {len(titles)} headlines.")
        return titles
    except requests.RequestException as e:
        logging.error(f"Network error while fetching news from {url}: {e}", exc_info=True)
        return []
    except Exception as e:
        logging.error(f"Error parsing news from {url}: {e}", exc_info=True)
        return []


async def get_news_headlines(url="", class_name=""):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _get_news_headlines, url, class_name)


async def _get_first_youtube_video_url(query):
    """Шукає в YouTube і повертає URL першого відео, форматує для YouTube Music."""
    try:
        search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        logging.info(f"Searching YouTube with URL: {search_url}")

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(executor, lambda: requests.get(search_url,
                                                                             headers={'User-Agent': 'Mozilla/5.0',
                                                                                      'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7'}))
        response.raise_for_status()

        html_content = response.text

        match = re.search(r"var ytInitialData = ({.*?});", html_content)
        if not match:
            logging.error("Could not find ytInitialData in YouTube search page. The page structure may have changed.")
            return None

        try:
            data_str = match.group(1)
            data = json.loads(data_str)

            video_results = \
                data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']

            video_id = None
            for section in video_results:
                if 'itemSectionRenderer' in section:
                    for item in section['itemSectionRenderer']['contents']:
                        if 'videoRenderer' in item and 'videoId' in item['videoRenderer']:
                            video_id = item['videoRenderer']['videoId']
                            logging.info(f"Found videoId: {video_id}")
                            break
                if video_id:
                    break

            if video_id:
                video_url = f"https://music.youtube.com/watch?v={video_id}"
                logging.info(f"Created YouTube Music URL: {video_url}")
                return video_url
            else:
                logging.warning(f"No videoRenderer with a videoId found in ytInitialData for query '{query}'.")
                return None

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logging.error(f"Error parsing ytInitialData JSON for query '{query}': {e}", exc_info=True)
            logging.debug(f"ytInitialData structure might have changed. Data snippet: {data_str[:1000]}")
            return None

    except requests.RequestException as e:
        logging.error(f"Network error while searching YouTube for '{query}': {e}", exc_info=True)
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred in _get_first_youtube_video_url for '{query}': {e}", exc_info=True)
        return None


async def listen(on_status_change=None):
    loop = asyncio.get_running_loop()
    if on_status_change:
        await on_status_change(const.STATUS_LISTENING)
    result = await loop.run_in_executor(executor, _listen)
    if on_status_change:
        await on_status_change(const.STATUS_NONE)
    return result


def _listen():
    """Записує мову з мікрофона та розпізнає її"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        logging.info("Adjusting for ambient noise.")
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        recognizer.pause_threshold = const.PAUSE_THRESHOLD
        try:
            logging.info("Listening for audio...")
            audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            logging.info("Audio captured, recognizing...")
            text = recognizer.recognize_google(audio_data, language=const.LANGUAGE)
            logging.info(f"Recognized text: '{text.lower()}'")
            return text.lower()
        except sr.WaitTimeoutError:
            logging.debug("Listening timed out.")
            return ""
        except sr.UnknownValueError:
            logging.debug("Google Speech Recognition could not understand audio.")
            return ""
        except sr.RequestError as e:
            logging.error(f"Google Speech Recognition service error; {e}", exc_info=True)
            return ""


async def tts(text, output=const.TTS_OUTPUT, on_status_change=None):
    settings = await load_settings()
    if not settings.get("silentmode", ""):
        loop = asyncio.get_running_loop()
        logging.info("Avrora started talking.")
        if on_status_change:
            await on_status_change(const.STATUS_SPEAKING)
        await loop.run_in_executor(executor, _tts, text, output)
        if on_status_change:
            await on_status_change(const.STATUS_NONE)
            logging.info("Avrora stoped talking.")
    else:
        logging.info("Silent mode is open, stopping voice")


def _tts(text, output):
    """Озвучує текст"""

    def _speak():
        try:
            ans = gTTS(text=text, lang=const.TTS_LANGUAGE, slow=False)
            if os.path.exists(output):
                os.remove(output)
            ans.save(output)
        except Exception as e:
            logging.error(f"Error generating or saving TTS audio: {e}")
            raise

    try:
        _speak()
        if not os.path.exists(output) or os.path.getsize(output) == 0:
            raise RuntimeError(f"TTS output file is missing or empty: {output}")
        data, fs = sf.read(output, dtype='float32')
        sd.play(data, fs)
        logging.debug(f"TTS audio played successfully from {output}")
    except Exception as e:
        logging.error(f"Error playing TTS audio from {output}: {e}")
        raise e


class TodoListManager:
    def __init__(self, filename=const.TODO_LIST_FILENAME):
        self.filename = filename
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            logging.info(f"ToDo list file '{self.filename}' not found. Creating.")
            with open(self.filename, 'w', encoding='utf-8') as f:
                pass  # Create an empty file

    def get_tasks(self):
        self._ensure_file_exists()
        with open(self.filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip()]

    def add_task(self, task):
        tasks = self.get_tasks()
        if task in tasks:
            return False  # Task already exists
        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write(f"{task}\n")
        return True

    def remove_task(self, task_to_remove):
        tasks = self.get_tasks()
        if task_to_remove not in tasks:
            return False  # Task not found
        new_tasks = [task for task in tasks if task != task_to_remove]
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.writelines(f"{t}\n" for t in new_tasks)
        return True

    def clear_tasks(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            pass


async def show_reminder(duration, reminder_text, settings, on_remind=None):
    """Показує нагадування"""
    logging.info(f"Reminder set for '{reminder_text}' in {duration} seconds.")
    await timer(duration, reminder_text)
    response = const.RESPONSE_REMINDER_TRIGGERED.format(settings.get('name', ''), reminder_text)
    logging.info(f"Triggering reminder: '{response}'")
    await tts(response)
    if on_remind:
        await on_remind(response, const.PROGRAM_ROLE)


async def _schedule_alarm(alarm_time_str, settings, on_remind):
    """Встановлює будильник на вказаний час"""
    try:
        alarm_hour, alarm_minute = map(int, alarm_time_str.split(':'))

        now = datetime.now()
        if not (0 <= alarm_hour <= 23 and 0 <= alarm_minute <= 59):
            raise ValueError("Година або хвилина виходить за допустимі межі (0-23 для години, 0-59 для хвилини).")

        alarm_time = now.replace(hour=alarm_hour, minute=alarm_minute, second=0,
                                 microsecond=0)  # This line can raise ValueError if hour/minute are invalid

        # If the alarm time is in the past, set it for tomorrow
        if alarm_time <= now:
            alarm_time += timedelta(days=1)

        time_to_wait = (alarm_time - now).total_seconds()

        logging.info(f"Scheduling alarm for {alarm_time_str} (in {time_to_wait:.2f} seconds)")
        if time_to_wait < 0.1:
            time_to_wait = 0.1
        await asyncio.sleep(time_to_wait)
        logging.info(f"Alarm triggered for {alarm_time_str}. Preparing message.")

        alarm_message = const.RESPONSE_ALARM_TRIGGERED.format(settings.get('name', ''), alarm_time.strftime('%H:%M'))
        try:
            logging.info(f"Calling TTS for alarm message: '{alarm_message}'")
            await tts(alarm_message)
            logging.info(f"TTS completed for alarm message.")
        except Exception as tts_e:
            logging.error(f"Error during TTS playback for alarm: {tts_e}")
            if on_remind:
                await on_remind(const.RESPONSE_ALARM_TTS_ERROR.format(tts_e), const.PROGRAM_ROLE)
            return

        if on_remind:
            logging.info(f"Calling on_remind for alarm message.")
            await on_remind(alarm_message, const.PROGRAM_ROLE)
            logging.info(f"on_remind completed for alarm message.")

    except ValueError as e:
        error_msg = const.RESPONSE_ALARM_ERROR_FORMAT.format(settings.get('name', ''), e)
        logging.error(f"Alarm scheduling error: {e} for time string '{alarm_time_str}'")
        await tts(error_msg)
        if on_remind:
            await on_remind(error_msg, const.PROGRAM_ROLE)
    except Exception as e:  # Catch any other unexpected errors during alarm scheduling
        logging.error(f"Unexpected error in _schedule_alarm: {e} for time string '{alarm_time_str}'")
        await tts(const.RESPONSE_ALARM_ERROR_UNKNOWN.format(e), on_status_change=None)


async def doSomething(command, ui_instance, page, on_status_change=None, on_remind=None):
    """Основний цикл обробки тексту і команд від користувача"""
    logging.info(f"Processing command: '{command}'")
    if on_status_change:
        await on_status_change(const.STATUS_THINKING)
    settings = await load_settings(const.SETTINGS_FILENAME)
    what_to_do_parts = command.split(f"{const.WAKE_WORD} ")

    if command.lower() == const.WAKE_WORD:
        logging.info("Responded to wake word 'аврора'.")
        page.window.minimized = False
        page.window.focused = True
        result_message = const.RESPONSE_ASSISTANT_PRESENT.format(settings.get('name', ''))
        await tts(result_message, on_status_change=on_status_change)
        if on_status_change:
            await on_status_change(const.STATUS_NONE)
        return 0, result_message
    if len(what_to_do_parts) > 1:
        what_to_do = what_to_do_parts[-1]
        logging.debug(f"Extracted task: '{what_to_do}'")
    else:
        result_message = const.RESPONSE_UNKNOWN_COMMAND_AFTER_WAKE_WORD.format(settings.get('name', ''))
        logging.warning(f"Could not extract task from command: '{command}'")
        await tts(result_message, on_status_change=on_status_change)
        if on_status_change:
            await on_status_change(const.STATUS_NONE)
        return 1, result_message
    ans, result_message = await what_command(what_to_do, ui_instance, page, settings, on_status_change=on_status_change,
                                             on_remind=on_remind)
    logging.info(f"what_command returned: ans='{ans}', message='{result_message}'")
    if ans == 1:
        await tts(const.RESPONSE_CLARIFY, on_status_change=on_status_change)
        result_message = const.RESPONSE_CLARIFY
    elif ans == "standard":
        ans_random = random.randint(0, 2)
        generic_responses = [resp.format(settings.get('name', '')) for resp in const.GENERIC_AFFIRMATIVE_RESPONSES]
        logging.info("Standard response sent.")
        result_message = generic_responses[ans_random]
        await tts(result_message, on_status_change=on_status_change)
        ans = 0
    if on_status_change:
        await on_status_change(const.STATUS_NONE)
    return ans, result_message


async def what_command(what_to_do, ui_instance, page, settings, on_status_change=None, on_remind=None):
    """Визначає яку команду сказав користувач і виконує відповідні дії"""
    logging.info(f"Executing command logic for: '{what_to_do}'")
    ans = 1
    todo_manager = TodoListManager()
    does_something = False
    custom_commands = await load_cc()
    for com in custom_commands.keys():
        contains_variable = False
        variable_start = 1
        variable_ends = 1
        if "[" in com and "]" in com:
            contains_variable = True
            variable_start = com.find("[")
            variable_ends = com.find("]")

        if what_to_do[:len(com)] == com.lower() and not contains_variable:
            logging.info(f"Matched custom command: '{com}'")
            await run_command(custom_commands.get(com))
            does_something = True
            break
        elif what_to_do[:variable_start] == com.lower()[:variable_start] and what_to_do[variable_ends:] == com.lower()[
                                                                                                           variable_ends:] and contains_variable:
            varible = what_to_do[variable_start:variable_ends]
            try:
                if com.lower()[variable_start + 1:variable_ends] == const.CUSTOM_COMMAND_VAR_NUM:
                    varible = int(varible)
            except Exception as e:
                logging.error(f"Error processing variable for custom command '{com}': {e}", exc_info=True)
                await tts(const.RESPONSE_CUSTOM_COMMAND_ERROR.format(settings.get('name', '')),
                          on_status_change=on_status_change)

                break

            act = custom_commands.get(com).replace(const.CUSTOM_COMMAND_VAR_STR, varible)
            await run_command(act)
            logging.info(f"Matched custom command with variable: '{com}', executing: '{act}'")
            does_something = True
    if does_something:
        ans = 0
        await tts(const.RESPONSE_CUSTOM_COMMAND_EXECUTING.format(settings.get('name', '')),
                  on_status_change=on_status_change)
        return ans, const.RESPONSE_CUSTOM_COMMAND_EXECUTING.format(settings.get('name', ''))

    elif what_to_do.startswith(const.CMD_SEARCH):
        logging.info("Executing 'search' command.")
        prompt = what_to_do[len(const.CMD_SEARCH):]
        prompt = quote_plus(prompt)
        webbrowser.open(f"{const.GOOGLE_SEARCH_URL}{prompt}")
        ans = 0
        await tts(const.RESPONSE_SEARCHING.format(settings.get('name', '')), on_status_change=on_status_change)
        return ans, const.RESPONSE_SEARCHING.format(settings.get('name', ''))

    elif what_to_do.startswith(const.CMD_OPEN):
        logging.info(f"Executing 'open' command for: '{what_to_do[len(const.CMD_OPEN):]}'")
        program = what_to_do[len(const.CMD_OPEN):]
        if "youtube" in program:
            webbrowser.open(const.YOUTUBE_URL)
            does_something = True

        elif "telegram" in program:
            if settings.get("tgo"):
                webbrowser.open(const.TELEGRAM_WEB_URL)
            else:
                os.startfile(settings.get("tgpath"))
            does_something = True

        elif "gemini" in program:
            webbrowser.open_new_tab(const.GEMINI_URL)
            does_something = True

        elif any(term in program for term in ["chat gpt", "chatgpt", "чат гпт", "чат gpt"]):
            webbrowser.open_new_tab(const.CHATGPT_URL)
            does_something = True

        elif "музику" in program:
            webbrowser.open(settings.get("music"))
            does_something = True

        if does_something:
            await tts(const.RESPONSE_OPENING.format(settings.get('name', '')), on_status_change=on_status_change)
            ans = 0
            return ans, const.RESPONSE_OPENING.format(settings.get('name', ''))
        else:
            await tts(const.RESPONSE_SEARCHING_PROGRAM.format(settings.get('name', '')),
                      on_status_change=on_status_change)
            installed_programs = await find_installed_programs()
            program_to_open_lower = program.lower()

            best_match_path = None
            best_match_name = None

            if program_to_open_lower in installed_programs:
                best_match_path = installed_programs[program_to_open_lower]
                best_match_name = program
            else:
                for name, path in installed_programs.items():
                    if name.startswith(program_to_open_lower):
                        best_match_path = path
                        best_match_name = os.path.splitext(os.path.basename(path))[0]
                        break
                if not best_match_path:
                    for name, path in installed_programs.items():
                        if program_to_open_lower in name:
                            best_match_path = path
                            best_match_name = os.path.splitext(os.path.basename(path))[0]
                            break
            if best_match_path:
                try:
                    os.startfile(best_match_path)
                    response_message = const.RESPONSE_OPENING_PROGRAM.format(best_match_name)
                    await tts(response_message, on_status_change=on_status_change)
                    return 0, response_message
                except Exception as e:
                    logging.error(f"Failed to start program '{best_match_path}': {e}")
                    await tts(const.RESPONSE_FAILED_TO_START_PROGRAM.format(best_match_name),
                              on_status_change=on_status_change)

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_PLAY_MUSIC_SIMPLE_VARIANTS):
        webbrowser.open(settings.get("music"))
        await tts(const.RESPONSE_TURNING_ON_MUSIC.format(settings.get('name', '')), on_status_change=on_status_change)
        ans = 0
        return ans, const.RESPONSE_TURNING_ON_MUSIC.format(settings.get('name', ''))


    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_PLAY_SONG_VARIANTS):
        logging.info("Executing 'play song' command.")
        prefix_used = next((cmd for cmd in const.CMD_PLAY_SONG_VARIANTS if what_to_do.startswith(cmd)), None)
        if not prefix_used:
            return 1, ""  # Should not happen, but for safety

        query = what_to_do[len(prefix_used):].strip()

        if not query:
            response = "Яку пісню увімкнути?"
            await tts(response, on_status_change=on_status_change)
            return 0, response

        await tts(const.RESPONSE_SEARCHING.format(settings.get('name', '')), on_status_change=on_status_change)

        video_url = await _get_first_youtube_video_url(query)

        if video_url:
            webbrowser.open(video_url)
            response_message = const.RESPONSE_TURNING_ON_SONG_ON_YTM.format(query, settings.get('name', ''))
            await tts(response_message, on_status_change=on_status_change)
            ans = 0
            return ans, response_message
        else:
            response_message = const.RESPONSE_SONG_NOT_FOUND.format(query)
            logging.warning(f"Failed to find song '{query}' on YouTube.")
            await tts(response_message, on_status_change=on_status_change)
            ans = 0
            return ans, response_message
    elif what_to_do.startswith(const.CMD_RESTART_APP):
        await tts(const.RESPONSE_RESTARTING_APP.format(settings.get('name', '')), on_status_change=on_status_change)
        logging.warning("Restart command received. Restarting application.")
        ans = const.RESTART_COMMAND
        return ans, const.RESPONSE_RESTARTING_APP.format(settings.get('name', ''))

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_GREETING_VARIANTS):
        logging.info("Executing 'greeting' command.")
        response = const.RESPONSE_GREETING.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif what_to_do.startswith(const.CMD_WHO_ARE_YOU):
        logging.info("Executing 'who are you' command.")
        response = const.RESPONSE_WHO_ARE_YOU.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif what_to_do.startswith(const.CMD_GOODBYE):
        logging.info("Executing 'goodbye' command.")
        response = const.RESPONSE_GOODBYE.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = const.EXIT_COMMAND
        return ans, response

    elif what_to_do.startswith(const.CMD_CPU_LOAD):
        logging.info("Executing 'cpu load' command.")
        await tts(const.RESPONSE_MEASURING_CPU.format(settings.get('name', '')), on_status_change=on_status_change)
        cpu_load = const.RESPONSE_CPU_LOAD.format(psutil.cpu_percent(interval=1), settings.get('name', ''))
        await tts(cpu_load, on_status_change=on_status_change)
        ans = 0
        logging.info(f"CPU load reported: {cpu_load}")
        return ans, cpu_load

    elif what_to_do.startswith(const.CMD_RAM_LOAD):
        logging.info("Executing 'ram load' command.")
        mem = psutil.virtual_memory()
        response = const.RESPONSE_RAM_LOAD.format(mem.percent, mem.total / (1024 ** 3), mem.available / (1024 ** 3))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif what_to_do.startswith(const.CMD_WHAT_TIME):
        logging.info("Executing 'what time' command.")
        current_datetime = datetime.now()
        hour = current_datetime.hour
        minute = current_datetime.minute
        second = current_datetime.second
        response = const.RESPONSE_CURRENT_TIME.format(settings.get('name', ''), f"{hour:02d}", f"{minute:02d}",
                                                      f"{second:02d}")
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_GET_NEWS_VARIANTS):
        logging.info("Executing 'get news' command.")
        await tts(const.RESPONSE_SEARCHING_NEWS.format(settings.get('name', '')), on_status_change=on_status_change)
        try:
            headlines = await get_news_headlines(const.NEWS_URL, const.NEWS_ARTICLE_HEADER_CLASS)
            if headlines:
                num_headlines = min(len(headlines), settings.get("num_headlines", 5))
                text_to_say = const.RESPONSE_LATEST_NEWS.format(num_headlines)
                for i in range(num_headlines):
                    text_to_say += f"{i + 1}. {headlines[i]}. \n"
                chat_text = text_to_say
                text_to_say += const.RESPONSE_NEWS_SOURCE_TTS
                chat_text += const.RESPONSE_NEWS_SOURCE_CHAT.format(const.NEWS_URL)
                await tts(text_to_say, on_status_change=on_status_change)
                ans = 0
                return ans, chat_text
            else:
                text_to_say = const.RESPONSE_FAILED_TO_GET_NEWS.format(settings.get('name', ''))
                await tts(text_to_say, on_status_change=on_status_change)
                ans = 0
                return ans, text_to_say
        except Exception as e:
            logging.error(f"Помилка під час отримання або обробки новин: {e}")
            text_to_say = const.RESPONSE_ERROR_GETTING_NEWS.format(settings.get('name', ''))
            await tts(text_to_say, on_status_change=on_status_change)
            ans = 0
            return ans, text_to_say

    elif what_to_do.startswith(const.CMD_THANK_YOU_PREFIX):
        logging.info("Executing 'thank you' command.")
        response = const.RESPONSE_THANK_YOU.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif what_to_do.startswith(const.CMD_MOVE_CURSOR):
        direction = what_to_do[len(const.CMD_MOVE_CURSOR):]
        logging.info(f"Executing 'move cursor' command: {direction}")
        logging.info("trying to move cursor")
        cursor_pos = pyautogui.position()
        does_something = False
        if direction == const.CMD_PARAM_UP:
            pyautogui.moveTo(cursor_pos.x, cursor_pos.y + 100, 0.01)
            does_something = True
            logging.info("moved cursor up")
        elif direction == const.CMD_PARAM_DOWN:
            pyautogui.moveTo(cursor_pos.x, cursor_pos.y - 100, 0.01)
            does_something = True
            logging.info("moved cursor down")
        elif direction == const.CMD_PARAM_LEFT:
            pyautogui.moveTo(cursor_pos.x - 100, cursor_pos.y, 0.01)
            does_something = True
            logging.info("moved cursor left")
        elif direction == const.CMD_PARAM_RIGHT:
            pyautogui.moveTo(cursor_pos.x + 100, cursor_pos.y, 0.01)
            does_something = True
            logging.info("moved cursor right")
        else:
            response = const.RESPONSE_UNKNOWN_DIRECTION.format(settings.get('name', ''))
            await tts(response)
            ans = 0
            return ans, response

        if does_something:
            response = const.RESPONSE_MOVING_CURSOR.format(settings.get('name', ''))
            await tts(response, on_status_change=on_status_change)
            ans = 0
            return ans, response

    elif what_to_do.startswith(const.CMD_CLICK):
        logging.info("Executing 'click' command.")
        pyautogui.click()
        response = const.RESPONSE_CLICKING.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif what_to_do.startswith(const.CMD_DOUBLE_CLICK):
        logging.info("Executing 'double click' command.")
        pyautogui.doubleClick()
        response = const.RESPONSE_CLICKING.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif what_to_do.startswith(const.CMD_SCROLL):
        direction = what_to_do[len(const.CMD_SCROLL):]
        logging.info(f"Executing 'scroll' command: {direction}")
        if direction == const.CMD_PARAM_UP:
            pyautogui.scroll(-500)
            response = const.RESPONSE_SCROLLING.format(settings.get('name', ''))
            await tts(response, on_status_change=on_status_change)
            ans = 0
            return ans, response
        elif direction == const.CMD_PARAM_DOWN:
            pyautogui.scroll(500)
            response = const.RESPONSE_SCROLLING.format(settings.get('name', ''))
            await tts(response, on_status_change=on_status_change)
            ans = 0
            return ans, response


    elif what_to_do.startswith(const.CMD_REMIND):
        logging.info("Executing 'reminder' command.")
        parts = what_to_do.split(" ")

        try:
            index_of_che = parts.index(const.CMD_PARAM_REMINDER_SEPARATOR)
        except ValueError:
            await tts(const.RESPONSE_CLARIFY.format(settings.get('name', '')), on_status_change=on_status_change)
            return [0, ""]

        reminder_text = " ".join(parts[2:index_of_che])

        duration_str = parts[index_of_che + 1]
        unit = parts[index_of_che + 2]

        try:
            duration = int(duration_str)
        except ValueError:
            await tts(const.RESPONSE_CLARIFY.format(settings.get('name', '')), on_status_change=on_status_change)
            return [0, const.RESPONSE_CLARIFY.format(settings.get('name', ''))]

        if any(u in unit for u in const.CMD_PARAM_TIME_UNITS_SEC):
            duration = duration
        elif any(u in unit for u in const.CMD_PARAM_TIME_UNITS_MIN):
            duration = duration * 60
        elif any(u in unit for u in const.CMD_PARAM_TIME_UNITS_HOUR):
            duration = duration * 60 * 60
        else:
            await tts(const.RESPONSE_CLARIFY.format(settings.get('name', '')), on_status_change=on_status_change)
            return [0, const.RESPONSE_CLARIFY.format(settings.get('name', ''))]

        display_duration = duration_str
        response = const.RESPONSE_REMINDER_SET.format(reminder_text, display_duration, unit, settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        asyncio.create_task(show_reminder(duration, reminder_text, settings, on_remind=on_remind))
        ans = 0
        return ans, response

    elif what_to_do.startswith(const.CMD_SET_ALARM):
        time_str = what_to_do[len(const.CMD_SET_ALARM):].strip()
        logging.info(f"Executing 'set alarm' command for: {time_str}")
        response = const.RESPONSE_ALARM_SET.format(time_str, settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        asyncio.create_task(_schedule_alarm(time_str, settings, on_remind))
        ans = 0
        return ans, response

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_GET_WEATHER_VARIANTS):
        logging.info("Executing 'get weather' command.")
        weather_info = await get_weather_info()
        await tts(weather_info, on_status_change=on_status_change)
        ans = 0
        return ans, weather_info

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_GET_LOCATION_VARIANTS):
        logging.info("Executing 'get location' command.")
        location_obj = await get_location()
        if location_obj and location_obj.city:
            location = const.RESPONSE_LOCATION.format(location_obj.city, location_obj.country)
        else:
            location = const.RESPONSE_LOCATION_FAILED

        await tts(location, on_status_change=on_status_change)
        ans = 0
        return ans, location

    elif what_to_do.startswith(const.CMD_CALCULATE):
        expression_str = what_to_do[len(const.CMD_CALCULATE):].strip()
        logging.info(f"Executing 'calculate' command for expression: {expression_str}")
        for word in const.CMD_PARAM_CALC_PLUS:
            expression_str = expression_str.replace(word, "+")
        for word in const.CMD_PARAM_CALC_MINUS:
            expression_str = expression_str.replace(word, "-")
        for word in const.CMD_PARAM_CALC_MUL:
            expression_str = expression_str.replace(word, "*")
        for word in const.CMD_PARAM_CALC_DIV:
            expression_str = expression_str.replace(word, "/")
        expression_str = expression_str.replace(const.CMD_PARAM_CALC_REPLACE_NA, "")

        if not all(c in const.CMD_PARAM_CALC_ALLOWED_CHARS for c in expression_str):
            logging.warning(f"Calculator expression contains invalid characters: '{expression_str}'")
            response = const.RESPONSE_CALC_INVALID_EXPRESSION.format(settings.get('name', ''))
            await tts(response, on_status_change=on_status_change)
            return 0, response

        try:
            result = eval(expression_str)
            response = const.RESPONSE_CALC_RESULT.format(result)
            logging.info(f"Calculation result for '{expression_str}' is '{result}'")
            await tts(response, on_status_change=on_status_change)
            ans = 0
            return ans, response
        except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
            error_msg = const.RESPONSE_CALC_ERROR.format(e)
            logging.error(f"Calculator error: {e} for expression: '{expression_str}'")
            await tts(error_msg, on_status_change=on_status_change)
            return 0, error_msg
        except Exception as e:
            error_msg = const.RESPONSE_CALC_UNKNOWN_ERROR.format(e)
            logging.error(f"Unknown calculator error: {e} for expression: '{expression_str}'")
            await tts(error_msg, on_status_change=on_status_change)
            return 0, error_msg


    elif what_to_do.startswith(const.CMD_SHUTDOWN_PC):
        if settings.get("pcpower"):
            logging.warning("Executing 'shutdown PC' command.")
            response = const.RESPONSE_SHUTTING_DOWN_PC.format(settings.get('name', ''))
            await tts(response, on_status_change=on_status_change)
            os.system(const.SYS_CMD_SHUTDOWN)
            ans = 0
            return ans, response
        else:
            response = const.RESPONSE_PC_POWER_NO_PERMS.format(const.RESPONSE_PC_POWER_ACTION_SHUTDOWN,
                                                               settings.get('name', ''))
            await tts(response, on_status_change=on_status_change)
            return 0, response

    elif what_to_do.startswith(const.CMD_RESTART_PC):
        if settings.get("pcpower"):
            logging.warning("Executing 'restart PC' command.")
            response = const.RESPONSE_RESTARTING_PC.format(settings.get('name', ''))
            await tts(response, on_status_change=on_status_change)
            os.system(const.SYS_CMD_RESTART)
            ans = 0
            return ans, response
        else:
            response = const.RESPONSE_PC_POWER_NO_PERMS.format(const.RESPONSE_PC_POWER_ACTION_RESTART,
                                                               settings.get('name', ''))
            await tts(response, on_status_change=on_status_change)
            return 0, response


    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_HIDE_WINDOW_VARIANTS):
        logging.info("Executing 'minimize window' command.")
        pyautogui.hotkey(*const.HOTKEY_WIN_DOWN)
        pyautogui.hotkey(*const.HOTKEY_WIN_DOWN)
        response = const.RESPONSE_HIDING_WINDOW.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_SHOW_WINDOW_VARIANTS):
        logging.info("Executing 'maximize window' command.")
        pyautogui.hotkey(*const.HOTKEY_WIN_UP)
        response = const.RESPONSE_SHOWING_WINDOW.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_HIDE_ALL_WINDOWS_VARIANTS):
        logging.info("Executing 'show desktop' command.")
        pyautogui.hotkey(*const.HOTKEY_WIN_M)
        response = const.RESPONSE_HIDING_ALL_WINDOWS.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_SHOW_ALL_WINDOWS_VARIANTS):
        logging.info("Executing 'show all windows' command.")
        pyautogui.hotkey(*const.HOTKEY_WIN_SHIFT_M)
        response = const.RESPONSE_SHOWING_ALL_WINDOWS.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_CLOSE_PROGRAM_VARIANTS):
        logging.info("Executing 'close program' command.")
        pyautogui.hotkey(*const.HOTKEY_ALT_F4)
        response = const.RESPONSE_CLOSING_PROGRAM.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_SWITCH_WINDOW_VARIANTS):
        logging.info("Executing 'switch window' command.")
        pyautogui.hotkey(*const.HOTKEY_ALT_TAB)
        response = const.RESPONSE_SWITCHING_WINDOW.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif what_to_do.startswith(const.CMD_SWITCH_TAB):
        logging.info("Executing 'switch tab' command.")
        pyautogui.hotkey(*const.HOTKEY_CTRL_TAB)
        response = const.RESPONSE_SWITCHING_TAB.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif what_to_do.startswith(const.CMD_HIDE_SELF):
        logging.info("Executing 'hide self' command.")
        page.window.minimized = True
        page.window.focused = False
        response = const.RESPONSE_HIDING_SELF.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response

    elif what_to_do.startswith(const.CMD_GET_DATE):
        logging.info("Executing 'get date' command.")
        current_datetime = datetime.now()
        day_of_week = const.DAYS_OF_WEEK_UK[current_datetime.weekday()]
        response = const.RESPONSE_CURRENT_DATE.format(settings.get('name', ''), day_of_week, current_datetime.day,
                                                      current_datetime.month, current_datetime.year)
        await tts(response, on_status_change=on_status_change)
        ans = 0
        return ans, response
    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_SET_VOLUME_VARIANTS):
        logging.info(f"Executing 'set volume' command.")

        prefix_used = next((cmd for cmd in const.CMD_SET_VOLUME_VARIANTS if what_to_do.startswith(cmd)), None)
        if not prefix_used:
            return 1, ""

        volume_str = what_to_do[len(prefix_used):].strip()
        try:
            volume_value = int(volume_str) / 100
            if not (0.0 <= volume_value <= 1.0):
                raise ValueError("Гучність має бути в межах від 0 до 100")
        except (ValueError, TypeError):
            await tts(const.RESPONSE_CLARIFY.format(settings.get('name', '')), on_status_change=on_status_change)
            logging.warning(f"Could not parse volume value: '{volume_str}'")
            return 0, const.RESPONSE_CLARIFY.format(settings.get('name', ''))

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(volume_value, None)

        logging.info(f"Volume set to {volume_value * 100}%")
        response = const.RESPONSE_SETTING_VOLUME.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        return 0, response

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_SHOW_TODO_VARIANTS):
        logging.info("Executing 'show todo' command.")
        tasks = todo_manager.get_tasks()
        if not tasks:
            response = const.RESPONSE_SHOW_TODO_EMPTY.format(settings.get('name', ''))
        else:
            todo_list_content = "\n".join(tasks)
            response = const.RESPONSE_SHOW_TODO.format(settings.get('name', ''), todo_list_content)
        await tts(response, on_status_change=on_status_change)
        return 0, response

    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_CLEAR_TODO_VARIANTS):
        logging.info("Executing 'clear todo' command.")
        todo_manager.clear_tasks()
        response = const.RESPONSE_CLEAR_TODO.format(settings.get('name', ''))
        await tts(response, on_status_change=on_status_change)
        return 0, response

    elif what_to_do.startswith(const.CMD_ADD_TODO):
        logging.info("Executing 'add todo' command.")
        task = what_to_do[len(const.CMD_ADD_TODO):].strip()
        if task:
            if todo_manager.add_task(task):
                response = const.RESPONSE_ADD_TODO.format(task, settings.get('name', ''))
            else:
                response = const.RESPONSE_ADD_TODO_EXISTS.format(task)
            await tts(response, on_status_change=on_status_change)
            return 0, response

    elif what_to_do.startswith(const.CMD_REMOVE_TODO):
        logging.info("Executing 'remove todo' command.")
        task_to_remove = what_to_do[len(const.CMD_REMOVE_TODO):].strip()
        if task_to_remove:
            if todo_manager.remove_task(task_to_remove):
                response = const.RESPONSE_REMOVE_TODO.format(settings.get('name', ''))
            else:
                response = const.RESPONSE_REMOVE_TODO_NOT_FOUND.format(task_to_remove)
            await tts(response, on_status_change=on_status_change)
            return 0, response
    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_PAUSE_SONG_VARIANTS):
        logging.info("Executing 'pause song' command.")
        pyautogui.press('space')
        response = const.RESPONSE_PAUSE_SONG.format(settings.get('name', ''))
        ans = 0
        await tts(response, on_status_change=on_status_change)
        return ans, response
    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_RESUME_SONG_VARIANTS):
        logging.info("Executing 'resume song' command.")
        pyautogui.press('space')
        response = const.RESPONSE_RESUME_SONG.format(settings.get('name', ''))
        ans = 0
        await tts(response, on_status_change=on_status_change)
        return ans, response
    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_NEXT_SONG_VARIANTS):
        logging.info("Executing 'next song' command.")
        pyautogui.press(const.HOTKEY_NEXT_SONG)
        response = const.RESPONSE_NEXT_SONG.format(settings.get('name', ''))
        ans = 0
        await tts(response, on_status_change=on_status_change)
        return ans, response
    elif any(what_to_do.startswith(cmd) for cmd in const.CMD_PREVIOUS_SONG_VARIANTS):
        logging.info("Executing 'previous song' command.")
        pyautogui.press(const.HOTKEY_PREVIOUS_SONG)
        response = const.RESPONSE_PREVIOUS_SONG.format(settings.get('name', ''))
        ans = 0
        await tts(response, on_status_change=on_status_change)
    elif what_to_do.startswith(const.CMD_WRITE_TEXT):
        logging.info("Executing 'write text' command.")
        text = what_to_do[len(const.CMD_WRITE_TEXT):].strip()
        if text:
            pyautogui.typewrite(uk_to_en(text), interval=0.03)
            pyautogui.press('enter')
            response = const.RESPONSE_WRITE_TEXT.format(settings.get('name', ''))
            ans = 0
        else:
            response = const.RESPONSE_CLARIFY.format(settings.get('name', ''))
            ans = 0
        await tts(response, on_status_change=on_status_change)
        return ans, response
    elif what_to_do.startswith(const.CMD_CLEAR_CHAT):
        logging.info("Executing 'clear chat' command.")
        ui_instance.clearChat(None)
        await tts(const.GENERIC_AFFIRMATIVE_RESPONSES[3].format(settings.get('name', '')),
                  on_status_change=on_status_change)
        ans = 0
        return ans, ""
    elif what_to_do.startswith(const.CMD_NAME_ME):
        logging.info("Executing 'name me' command.")
        name = what_to_do[len(const.CMD_NAME_ME):].strip()
        if not name:
            response = const.RESPONSE_CLARIFY.format(settings.get('name', ''))
            ans = 0
        else:
            ui_instance.YourNameI.value = name
            await ui_instance.update_settings(None)
            page.update()
            response = const.RESPONSE_NEW_NAME.format(settings.get('name', ''))
            ans = 0
        await tts(response, on_status_change=on_status_change)
        return ans, response
    elif what_to_do.startswith(const.CMD_I_AM_IN_CITY):
        logging.info("Executing 'i am in city' command.")
        city = what_to_do[len(const.CMD_I_AM_IN_CITY):].strip()
        if not city:
            response = const.RESPONSE_CLARIFY.format(settings.get('name', ''))
            ans = 0
        else:
            ui_instance.CityI.value = city
            await ui_instance.update_settings(None)
            page.update()
            response = const.RESPONSE_REMEMBERED.format(settings.get('name', ''))
            ans = 0
        await tts(response, on_status_change=on_status_change)
        return ans, response
    elif what_to_do.startswith(const.CMD_SILENT_MODE_ON):
        logging.info("Executing 'silent mode on' command.")
        ui_instance.silentModeCB.value = True
        await ui_instance.update_settings(None)
        page.update()
        response = const.RESPONSE_CHANGE_SETTINGS.format(settings.get('name', ''))
        ans = 0
        return ans, response
    elif what_to_do.startswith(const.CMD_SILENT_MODE_OFF):
        logging.info("Executing 'silent mode off' command.")
        ui_instance.silentModeCB.value = False
        await ui_instance.update_settings(None)
        page.update()
        response = const.RESPONSE_CHANGE_SETTINGS.format(settings.get('name', ''))
        ans = 0
        await tts(response, on_status_change=on_status_change)
        return ans, response
    elif what_to_do.startswith(const.CMD_SET_NUM_OF_HEADLINES):
        logging.info("Executing 'set num of headlines' command.")
        num = what_to_do[len(const.CMD_SET_NUM_OF_HEADLINES):].strip()
        if not num:
            response = const.RESPONSE_CLARIFY.format(settings.get('name', ''))
            ans = 0
        else:
            try:
                if ui_instance.NewsHeadersCountS.min <= int(num) <= ui_instance.NewsHeadersCountS.max + 1:
                    ui_instance.NewsHeadersCountS.value = int(num)
                else:
                    raise ValueError("Кількість новин має бути між 1 і 10.")
            except:
                await tts(const.RESPONSE_CLARIFY)
                ans = 0
                return ans, const.RESPONSE_CLARIFY
            await ui_instance.update_settings(None)
            page.update()
            response = const.RESPONSE_CHANGE_SETTINGS.format(settings.get('name', ''))
            ans = 0
        await tts(response, on_status_change=on_status_change)
        return ans, response
    elif what_to_do.startswith(const.CMD_CHANGE_THEME):
        logging.info("Executing 'change theme' command.")
        ui_instance.themeS.value = not ui_instance.themeS.value
        await ui_instance.update_settings(None)
        await ui_instance.switch_theme(None)
        page.update()
        response = const.RESPONSE_CHANGE_SETTINGS.format(settings.get('name', ''))
        ans = 0
        await tts(response, on_status_change=on_status_change)
        return ans, response
    elif what_to_do.startswith(CMD_CHANGE_ACCENT_COLOR):
        logging.info("Executing 'change accent color' command.")
        next_color = const.ACCENT_COLORS_LIST[const.ACCENT_COLORS_LIST.index(
            ui_instance.accent_color_dropdown.value) + 1] if const.ACCENT_COLORS_LIST.index(
            ui_instance.accent_color_dropdown.value) + 1 != len(const.ACCENT_COLORS_LIST) else const.ACCENT_COLORS_LIST[
            0]
        ui_instance.accent_color_dropdown.value = next_color
        await ui_instance.update_settings(None)
        await ui_instance.switch_accent_color(None)
        page.update()
        response = const.RESPONSE_CHANGE_SETTINGS.format(settings.get('name', ''))
        ans = 0
        await tts(response, on_status_change=on_status_change)
        return ans, response

    logging.warning(f"Command not recognized: '{what_to_do}'")
    return ans, const.RESPONSE_UNKNOWN_COMMAND.format(what_to_do, settings.get('name', ''))
