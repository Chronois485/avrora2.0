import os
import sys
import tempfile

import flet as ft

# Base Colors (used for themes)
DEEP_PURPLE_400 = ft.Colors.DEEP_PURPLE_400
PURPLE_400 = ft.Colors.PURPLE_400
DEEP_PURPLE_500 = ft.Colors.DEEP_PURPLE_500
INITIATION_COLOR = ft.Colors.SURFACE_CONTAINER_HIGHEST

# Theme Colors
THEME_DARK = "dark"
THEME_LIGHT = "light"

COLORS_DARK = {"BGCOLOR": "#2f0c3d", "MAINBGCOLOR": "#151218", "MAINCOLOR": ft.Colors.PURPLE_300,
               "ICON_COLOR": ft.Colors.PURPLE_300, }

COLORS_LIGHT = {"BGCOLOR": "#f3e5f5", "MAINBGCOLOR": "#fafafa", "MAINCOLOR": ft.Colors.DEEP_PURPLE_400,
                "ICON_COLOR": ft.Colors.PURPLE_600, }

ACCENT_COLORS = {"Deep Purple": ft.Colors.DEEP_PURPLE_400, "Indigo": ft.Colors.INDIGO_400, "Blue": ft.Colors.BLUE_400,
                 "Teal": ft.Colors.TEAL_400, "Green": ft.Colors.GREEN_400, "Orange": ft.Colors.ORANGE_400,
                 "Pink": ft.Colors.PINK_400, }

CHAT_FALLBACK_COLORS = {"user_bubble": ft.Colors.PRIMARY_CONTAINER, "user_text": ft.Colors.ON_PRIMARY_CONTAINER,
                        "bot_bubble": ft.Colors.SECONDARY_CONTAINER, "bot_text": ft.Colors.ON_SECONDARY_CONTAINER,
                        "system_bubble": ft.Colors.TERTIARY_CONTAINER, "system_text": ft.Colors.ON_TERTIARY_CONTAINER}

# Logging
LOG_FILENAME = "avrora.log"

# UI Icons
INFO_ICON = ft.Icons.INFO
SETTINGS_ICON = ft.Icons.SETTINGS
MIC_ICON = ft.Icons.MIC_NONE
LOADING_ICON = ft.Icons.AUTORENEW_ROUNDED
SPEAKING_ICON = ft.Icons.VOLUME_UP_OUTLINED
SUNNY_ICON = ft.Icons.SUNNY
CLOUDY_ICON = ft.Icons.WB_CLOUDY
WATER_DROP_ICON = ft.Icons.WATER_DROP
THUNDER_STORM_ICON = ft.Icons.THUNDERSTORM
CLOUDY_SNOWING_ICON = ft.Icons.CLOUDY_SNOWING
FOGGY_ICON = ft.Icons.FOGGY
THERMOSTAT_ICON = ft.Icons.DEVICE_THERMOSTAT
SEND_ICON = ft.Icons.SEND

# Core constants
WAKE_WORD = "аврора"
EXIT_COMMAND = "exit"
RESTART_COMMAND = "restart"

# Roles
USER_ROLE = "user"
PROGRAM_ROLE = "program"
SYSTEM_ROLE = "center"

# Statuses
STATUS_THINKING = "thinking"
STATUS_LISTENING = "listening"
STATUS_SPEAKING = "speaking"
STATUS_NONE = "none"

# Audio Settings
PAUSE_THRESHOLD = 0.8  # секунди тиші, після яких фраза вважається завершеною
LANGUAGE = "uk-UA"
TTS_LANGUAGE = "uk"

# Icons of weather
WEATHER_ICONS = {"ясно": SUNNY_ICON, "сонячно": SUNNY_ICON, "мінлива хмарність": CLOUDY_ICON, "хмарно": CLOUDY_ICON,
                 "похмуро": CLOUDY_ICON, "туман": FOGGY_ICON, "мгла": FOGGY_ICON, "дощ": WATER_DROP_ICON,
                 "легкий дощ": WATER_DROP_ICON, "злива": THUNDER_STORM_ICON, "гроза": THUNDER_STORM_ICON,
                 "сніг": CLOUDY_SNOWING_ICON, "легкий сніг": CLOUDY_SNOWING_ICON, "мокрий сніг": CLOUDY_SNOWING_ICON,
                 "хуртовина": CLOUDY_SNOWING_ICON, "град": CLOUDY_SNOWING_ICON,
                 "невеликий дощ з грозою": THUNDER_STORM_ICON, "дощ зі снігом": CLOUDY_SNOWING_ICON,
                 "змінна хмарність": CLOUDY_ICON}

# Keys translation
KEYS_EN = {"й": "q", "ц": "w", "у": "e", "к": "r", "е": "t", "н": "y", "г": "u", "ш": "i", "щ": "o", "з": "p", "х": "[",
           "ї": "]", "ф": "a", "і": "s", "в": "d", "а": "f", "п": "g", "р": "h", "о": "j", "л": "k", "д": "l", "ж": ";",
           "є": "'", "я": "z", "ч": "x", "с": "c", "м": "v", "и": "b", "т": "n", "ь": "m", "б": ",", "ю": "."}


# File Names
def get_resource_path(relative_path):
    """ Get absolute path to read-only resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_user_data_path(filename):
    """ Get absolute path for user-specific writable data files """
    if sys.platform.startswith('win'):
        app_data_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), "Avrora")
    elif sys.platform.startswith('darwin'):
        # macOS: ~/Library/Application Support/Avrora
        app_data_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Avrora')
    else:
        # Linux/Unix: ~/.config/avrora
        app_data_dir = os.path.join(os.path.expanduser('~'), '.config', 'avrora')

    os.makedirs(app_data_dir, exist_ok=True)  # Ensure directory exists
    return os.path.join(app_data_dir, filename)


SETTINGS_FILENAME = get_user_data_path("settings.json")
CUSTOM_COMMANDS_FILENAME = get_user_data_path("customCommands.json")
CHAT_HISTORY_FILENAME = get_user_data_path("chat_history.json")
INFO_TABLE_FILENAME = get_user_data_path("commandsTable.json")
DEFAULT_INFO_TABLE_FILENAME = get_resource_path("assets/commandsTable.json")
TODO_LIST_FILENAME = get_user_data_path("todoList.txt")

# TTS output should go to a temporary directory
TTS_OUTPUT = os.path.join(tempfile.gettempdir(), "avrora_output.mp3")

# Web Addresses
YOUTUBE_URL = "https://www.youtube.com"
TELEGRAM_WEB_URL = "https://web.telegram.org/k/"
GOOGLE_SEARCH_URL = "https://www.google.com.ua/search?q="
YOUTUBE_SEARCH_URL = "https://music.youtube.com/search?q="
GEMINI_URL = "https://gemini.google.com/?hl=uk"
CHATGPT_URL = "https://chatgpt.com"

# Other
MAX_WORKERS = 4
DEFAULT_NAME = ""
DEFAULT_TG_PATH = ""
DEFAULT_MUSIC_LINK = "https://music.youtube.com/"
DEFAULT_CITY = ""
DEFAULT_THEME = "dark"

# News Settings
NEWS_URL = "https://www.pravda.com.ua/news/"
NEWS_ARTICLE_HEADER_CLASS = "article_header"

# Window Settings
WINDOW_WIDTH = 450
WINDOW_HEIGHT = 650
WINDOW_MIN_WIDTH = 450
WINDOW_MAX_WIDTH = 450
WINDOW_MAX_HEIGHT = 650
WINDOW_MIN_HEIGHT = 650

# Font Paths
TEKTUR_FONT_PATH = get_resource_path("assets/fonts/Tektur-Regular.ttf")
TEKTUR_BOLD_FONT_PATH = get_resource_path("assets/fonts/Tektur-Bold.ttf")

# UI settings
FONT_FAMILY = "Tektur"
MARKDOWN_CODE_THEME = "atom-one-dark"
MARKDOWN_EXTENSION_SET = "git-hub-web"
SCROLL_MODE_AUTO = "auto"
ALLOWED_EXTENSIONS_EXE = ["exe"]

# UI Text
APP_NAME = "A.V.R.O.R.A."
APP_FULL_NAME = "Advanced Voice-Activated Robot for Optimized Reliable Assistance"
SETTINGS_LABEL = "Налаштування"
CUSTOM_COMMANDS_LABEL = "Користувацькі команди"
YOUR_NAME_LABEL = "Ваше ім'я"
CITY_LABEL = "Ваше місто (для погоди)"
MUSIC_LINK_LABEL = "Посилання на музичний сервіс"
TG_PATH_LABEL_PREFIX = "Файл Телеграму: "
USE_TG_ONLINE_LABEL = "Використовувати Телеграм у браузері"
PERMISSIONS_TO_CONTROL_PC_POWER_LABEL = "Дозволити контролювати живлення пк"
SELECT_TG_FILE_LABEL = "Вибрати файл Телеграму"
RESET_SETTINGS_BUTTON_LABEL = "Скинути налаштування"
DELETE_CC_LABEL = "Видалити дію"
CONFIRM_CC_LABEL = "Підтвердити"
CANCEL_CC_LABEL = "Скасувати"
NEW_COMMAND_LABEL = "Нова команда"
COMMAND_NAME_LABEL = "Ім'я команди"
COMMAND_ACTION_LABEL = "Дія"
FIRST_LAUNCH_LABEL = "Вас вітає A.V.R.O.R.A. Для того щоб продовжити представтесь."
FIRST_LAUNCH_CONFIRM_BUTTON = "Продовжити"
FIRST_LAUNCH_INPUT_LABEL = "Введіть ваше ім'я"
SETTINGS_GROUP_TG_LABEL = "Телеграм:"
SETTINGS_GROUP_PERSONAL_INFO_LABEL = "Персональна інформація:"
SETTINGS_GROUP_PERMISSIONS_LABEL = "Дозволи:"
SETTINGS_GROUP_CHAT_LABEL = "Чат:"
CUSTOM_COMMANDS_BUTTON_LABEL = "Користувацькі команди"
CLEAR_CHAT_BUTTON_LABEL = "Очистити чат"
SETTINGS_GROUP_CC_LABEL = "Користувацькі команди"
SAVE_CHAT_CHECKBOX_LABEL = "Зберігати чат"
INFO_HEADER_LABEL = "Для того щоб A.V.R.O.R.A. почала вас чути скажіть аврора [команда]"
INFO_TABLE_HEADER_COMMAND = "Команда"
INFO_TABLE_HEADER_ACTION = "Дія"
STATUS_TOOLTIP = "Статус"
DROPDOWN_CHOOSE_COMMAND_LABEL = "Оберіть команду"
FIRST_LAUNCH_EMPTY_NAME_ERROR = "Ім'я не може бути порожнім"
NEWS_HEADERS_COUNT_LABEL = "Кількість заголовків:"
SETTINGS_GROUP_PERSONALISATION_LABEL = "Персоналізація:"
THEME_SWITCH_LABEL = "Темна тема"
ACCENT_COLOR_LABEL = "Акцентний колір"
DEVELOPED_BY_LABEL = "#### Розроблено CHRONOiS"
CONTACT_US_LABEL = "#### Якщо виникнуть якісь питання звяжіться з нами за допомогою телеграму: @Chronos4"
WEATHER_HEADER_LABEL = "Прогноз погоди в місті {}"
SEND_MSG_FIELD_LABEL = "Введіть команду..."
SEND_BUTTON_LABEL = "Відправити"

CUSTOM_COMMANDS_HELP_LABEL = """
### Як додати власні команди:

1.  **Відкрийте налаштування** (іконка шестерні).
2.  Натисніть кнопку **"Користувацькі команди"**.
3.  У новому вікні оберіть **"Нова команда"** у випадаючому списку.
4.  **Ім'я команди:** Введіть фразу, яку будете говорити (наприклад, `відкрий мій проект`).
5.  **Дія:** Вкажіть, що потрібно зробити:
    *   Запустити програму: `C:\\\\path\\\\to\\\\program.exe`
    *   Відкрити сайт: `https://my-site.com`
    *   Виконати команду: `notepad.exe`

#### Команди зі змінними:

Ви можете створювати гнучкі команди, використовуючи `[змінна]` або `[число]`.

*   **Приклад 1 (Текст):**
    *   **Ім'я:** `знайди в ютубі [змінна]`
    *   **Дія:** `https://www.youtube.com/results?search_query=[змінна]`
    *   **Результат:** Сказавши "знайди в ютубі котиків", Аврора відкриє пошук з котиками на YouTube.

*   **Приклад 2 (Число):**
    *   **Ім'я:** `постав таймер на [число] секунд`
    *   **Дія:** `timer.exe [число]` (якщо у вас є така програма)
    *   **Результат:** Сказавши "постав таймер на 30 секунд", Аврора виконає `timer.exe 30`.
"""

MULTIPLE_COMMAND_VARIANTS_HELP_LABEL = """
### Варіації команд

Якщо після назви команди стоїть * (зірочка), то команда має декілька варіацій.

**Приклад:**
    включи музику*
    
Побачити варіації команд можливо якщо навестися на команду. 
"""

# Alignments
ALIGN_LEFT = "left"
ALIGN_RIGHT = "right"
ALIGN_CENTER = "center"

# Commands
CMD_GREETING_VARIANTS = ["вітаю", "startup."]
CMD_WHO_ARE_YOU = "хто ти"
CMD_GOODBYE = "до побачення"
CMD_RESTART_APP = "перезавантаження"
CMD_SEARCH = "знайди "
CMD_OPEN = "відкрий "
CMD_PLAY_MUSIC_SIMPLE_VARIANTS = ["включи музику", "ввімкни музику", "увімкни музику"]
CMD_PLAY_SONG_VARIANTS = ["включи пісню ", "ввімкни пісню ", "увімкни пісню "]
CMD_CPU_LOAD = "навантаження на процесор"
CMD_RAM_LOAD = "навантаження на оперативну пам'ять"
CMD_WHAT_TIME = "котра година"
CMD_GET_NEWS_VARIANTS = ["які новини", "покажи новини"]
CMD_THANK_YOU_PREFIX = "дякую"
CMD_MOVE_CURSOR = "курсор "
CMD_CLICK = "натисни"
CMD_DOUBLE_CLICK = "натисни 2 рази"
CMD_SCROLL = "прокрути "
CMD_REMIND = "нагадай про"
CMD_SET_ALARM = "будильник на "
CMD_GET_WEATHER_VARIANTS = ["яка погода", "погода", "прогноз погоди"]
CMD_GET_LOCATION_VARIANTS = ["де я", "місто"]
CMD_CALCULATE = "порахуй "
CMD_SHUTDOWN_PC = "вимкни пк"
CMD_RESTART_PC = "перезапусти пк"
CMD_HIDE_WINDOW_VARIANTS = ["сховай вікно", "згорни вікно", "сховай програму", "згорни програму"]
CMD_SHOW_WINDOW_VARIANTS = ["покажи вікно", "розгорнеш вікно", "розгорни вікно", "покажи програму",
                            "розгорнеш програму", "розгорни програму"]
CMD_HIDE_ALL_WINDOWS_VARIANTS = ["сховай всі вікна", "покажи робочий стіл", "згорни всі вікна", "сховай всі програми",
                                 "згорни всі програми"]
CMD_SHOW_ALL_WINDOWS_VARIANTS = ["покажи всі вікна", "розгорнеш всі вікна", "розгорни всі вікна", "покажи всі програми",
                                 "розгорнеш всі програми", "розгорни всі програми"]
CMD_CLOSE_PROGRAM_VARIANTS = ["закрий програму", "закрий вікно"]
CMD_SWITCH_WINDOW_VARIANTS = ["зміни вікно", "зміни програму"]
CMD_SWITCH_TAB = "зміни вкладку"
CMD_HIDE_SELF = "сховаєшся"
CMD_GET_DATE = "дата"
CMD_SET_VOLUME_VARIANTS = ["звук на ", "гучність на "]
CMD_SHOW_TODO_VARIANTS = ["що в мене в списку справ", "що в списку справ", "список справ"]
CMD_ADD_TODO = "додай до списку справ "
CMD_REMOVE_TODO = "видали з списку справ "
CMD_CLEAR_TODO_VARIANTS = ["очисти список справ", "очистити список справ"]
CMD_NEXT_SONG_VARIANTS = ["наступна пісня", "наступний трек", "переключи трек", "переключи пісню"]
CMD_PREVIOUS_SONG_VARIANTS = ["попередня пісня", "попередній трек"]
CMD_PAUSE_SONG_VARIANTS = ["пауза", "пауза трека", "пауза пісні", "призупини трек", "призупини пісню", "призупини",
                           "постав на паузу"]
CMD_RESUME_SONG_VARIANTS = ["віднови пісню", "віднови трек", "продовжити трек", "продовжи пісню", "зніми з паузи"]
CMD_WRITE_TEXT = "напиши "

# Command parameters
CMD_PARAM_UP = "вверх"
CMD_PARAM_DOWN = "вниз"
CMD_PARAM_LEFT = "вліво"
CMD_PARAM_RIGHT = "вправо"
CMD_PARAM_REMINDER_SEPARATOR = "через"
CMD_PARAM_TIME_UNITS_SEC = ["секунд", "секунда", "секунди"]
CMD_PARAM_TIME_UNITS_MIN = ["хвилин", "хвилина", "хвилини"]
CMD_PARAM_TIME_UNITS_HOUR = ["годин", "година", "години"]
CMD_PARAM_CALC_PLUS = ["плюс", "додати"]
CMD_PARAM_CALC_MINUS = ["мінус", "відняти"]
CMD_PARAM_CALC_MUL = ["помножити на", "помножити"]
CMD_PARAM_CALC_DIV = ["ділення на", "ділення", "поділити на", "поділити"]
CMD_PARAM_CALC_REPLACE_NA = "на"
CMD_PARAM_CALC_ALLOWED_CHARS = "0123456789+-*/. "

# System commands
SYS_CMD_SHUTDOWN = "shutdown -s -t 0"
SYS_CMD_RESTART = "shutdown -r -t 0"

# PyAutoGUI hotkeys
HOTKEY_WIN_DOWN = ('win', 'down')
HOTKEY_WIN_UP = ('win', 'up')
HOTKEY_WIN_M = ('win', 'm')
HOTKEY_WIN_SHIFT_M = ('win', 'shift', 'm')
HOTKEY_ALT_F4 = ('alt', 'f4')
HOTKEY_ALT_TAB = ('alt', 'tab')
HOTKEY_CTRL_TAB = ('ctrl', 'tab')
HOTKEY_NEXT_SONG = ('shift', 'n')
HOTKEY_PREVIOUS_SONG = ('shift', 'p')

# Other strings
GEOCODER_IP_ME = "me"
HTML_PARSER = "html.parser"
CUSTOM_COMMAND_VAR_NUM = "число"
CUSTOM_COMMAND_VAR_STR = "[змінна]"
DAYS_OF_WEEK_UK = ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"]

# Response templates
RESPONSE_ASSISTANT_PRESENT = "Я тут, {}"
RESPONSE_UNKNOWN_COMMAND_AFTER_WAKE_WORD = "Не розумію команду після кодового слова, {}"
RESPONSE_CLARIFY = "Не розумію, можете уточнити?"
GENERIC_AFFIRMATIVE_RESPONSES = ["Секунду, {}", "Зараз, {}", "Звісно, {}"]
RESPONSE_WHO_ARE_YOU = "{}, я голосовий помічник AVRORA що розшифровується як " + APP_FULL_NAME + ", чим я можу вам допомогти?"
RESPONSE_RESTARTING_APP = "Перезавантажуюся, {}"
RESPONSE_GREETING = "Вітаю, {}, все готово до роботи"
RESPONSE_GOODBYE = "До побачення, {}"
RESPONSE_SEARCHING = "Шукаю, {}"
RESPONSE_OPENING = "відкриваю, {}"
RESPONSE_SEARCHING_PROGRAM = "Шукаю вашу програму, {}"
RESPONSE_OPENING_PROGRAM = "Відкриваю {}"
RESPONSE_FAILED_TO_START_PROGRAM = "Не вдалося запустити {}"
RESPONSE_TURNING_ON_MUSIC = "Вмикаю, {}"
RESPONSE_TURNING_ON_SONG = "Вмикаю {}, {}"
RESPONSE_TURNING_ON_SONG_ON_YTM = "Вмикаю {} на YouTube Music, {}"
RESPONSE_SONG_NOT_FOUND = "На жаль, не вдалося знайти пісню {}."
RESPONSE_MEASURING_CPU = "заміряю {}"
RESPONSE_CPU_LOAD = "{}% {}"
RESPONSE_RAM_LOAD = "Використано {}%. всього пам'яті {:.2f} гігабайти. доступно пам'яті {:.2f} гігабайти"
RESPONSE_CURRENT_TIME = "{}, зараз {}:{}:{}"
RESPONSE_SEARCHING_NEWS = "Шукаю новини, {}"
RESPONSE_LATEST_NEWS = "Ось останні {} новин: \n"
RESPONSE_NEWS_SOURCE_TTS = " Новини отримано з ресурсу: посилання видалено."
RESPONSE_NEWS_SOURCE_CHAT = "\nНовини отримано з ресурсу: {}"
RESPONSE_FAILED_TO_GET_NEWS = "Вибачте, {}, не вдалося отримати новини."
RESPONSE_ERROR_GETTING_NEWS = "Вибачте, {}, виникла помилка при отриманні новин."
RESPONSE_THANK_YOU = "Завжди до ваших послуг, {}"
RESPONSE_MOVING_CURSOR = "Пересуваю, {}"
RESPONSE_UNKNOWN_DIRECTION = "Не можу зрозуміти напрямок, повторіть будь ласка, {}"
RESPONSE_CLICKING = "Натискаю, {}"
RESPONSE_SCROLLING = "Прогортаю, {}"
RESPONSE_REMINDER_SET = "Добре, нагадаю про {} через {} {}, {}"
RESPONSE_REMINDER_TRIGGERED = "Нагадую, {}: {}"
RESPONSE_ALARM_SET = "Будильник встановлено на {}, {}."
RESPONSE_ALARM_TRIGGERED = "Будильник! {}, зараз {}."
RESPONSE_ALARM_ERROR_FORMAT = "Неправильний формат часу. Будь ласка, вкажіть час у форматі ГГ:ХХ, {}. Помилка: {}"
RESPONSE_ALARM_ERROR_UNKNOWN = "Виникла невідома помилка при встановленні будильника: {}"
RESPONSE_ALARM_TTS_ERROR = "Будильник спрацював, але виникла помилка відтворення звуку: {}"
RESPONSE_LOCATION = "Ви знаходитесь у місті {}, {}."
RESPONSE_LOCATION_FAILED = "Не вдалося визначити ваше місцезнаходження."
RESPONSE_WEATHER_FAILED_NO_CITY = "Не вдалося визначити ваше місто. Спробуйте вказати його в налаштуваннях."
RESPONSE_WEATHER_CURRENT = "Погода в місті {} зараз така: Температура {} градусів Цельсія, а відчувається як {}. На небі {}."
RESPONSE_WEATHER_FORECAST = "Прогноз погоди на сьогодні в місті {}: Температура {} градусів Цельсія. На небі {}."
RESPONSE_WEATHER_ERROR = "Вибачте, не вдалося отримати дані про погоду."
RESPONSE_CALC_INVALID_EXPRESSION = "Вибачте, {}, я не можу обчислити цей вираз. Будь ласка, використовуйте лише числа та основні операції."
RESPONSE_CALC_RESULT = "Результат: {}"
RESPONSE_CALC_ERROR = "Не можу порахувати. Перевірте вираз. Помилка: {}"
RESPONSE_CALC_UNKNOWN_ERROR = "Виникла невідома помилка під час обчислення: {}"
RESPONSE_SHUTTING_DOWN_PC = "Вимкнення пк, {}"
RESPONSE_RESTARTING_PC = "Перезавантаження пк, {}"
RESPONSE_PC_POWER_NO_PERMS = "Вибачте, але немає доступу для {} пк, {}"
RESPONSE_PC_POWER_ACTION_SHUTDOWN = "вимкнення"
RESPONSE_PC_POWER_ACTION_RESTART = "перезавантаження"
RESPONSE_HIDING_WINDOW = "Згортаю, {}"
RESPONSE_SHOWING_WINDOW = "Розгортаю, {}"
RESPONSE_HIDING_ALL_WINDOWS = "Згортаю всі вікна, {}"
RESPONSE_SHOWING_ALL_WINDOWS = "Розгортаю всі вікна, {}"
RESPONSE_CLOSING_PROGRAM = "Закриваю вікно, {}"
RESPONSE_SWITCHING_WINDOW = "Перемикаю, {}"
RESPONSE_SWITCHING_TAB = "Змінюю вкладку, {}"
RESPONSE_HIDING_SELF = "Звісно, {}"
RESPONSE_CURRENT_DATE = "{}, сьогодні {} {}.{}.{}"
RESPONSE_SETTING_VOLUME = "Змінюю звук, {}"
RESPONSE_SHOW_TODO = "Ось ваш список справ, {}:\n{}"
RESPONSE_SHOW_TODO_EMPTY = "У вас немає справ, {}"
RESPONSE_TODO_LIST_NOT_FOUND = "Список справ не знайдено, створюю новий, {}"
RESPONSE_ADD_TODO = "Додаю {} до списку справ, {}"
RESPONSE_ADD_TODO_EXISTS = "Не вдалося додати до списку справ, пункт {} уже існує"
RESPONSE_REMOVE_TODO = "Видаляю з списку справ, {}"
RESPONSE_REMOVE_TODO_NOT_FOUND = "Не вдалося видалити з списку справ, {}, такого пункту не існує"
RESPONSE_CLEAR_TODO = "Очищую список справ, {}"
RESPONSE_PAUSE_SONG = "Призупиняю, {}"
RESPONSE_RESUME_SONG = "Відновлюю, {}"
RESPONSE_NEXT_SONG = "Наступний трек, {}"
RESPONSE_PREVIOUS_SONG = "Попередній трек, {}"
RESPONSE_WRITE_TEXT = "Написала, {}"
RESPONSE_CUSTOM_COMMAND_EXECUTING = "Виконую, {}"
RESPONSE_CUSTOM_COMMAND_ERROR = "Помилка з користувацькою командою, {}"
RESPONSE_UNKNOWN_COMMAND = "Не розумію команду '{}', {}"

# Variants of commands for command table
TABLE_VARIANTS = {"включи музику*": "ввімкни музику\nувімкни музику",
                  "включи пісню [назва]*": "ввімкни пісню [назва]\nувімкни пісню [назва]",
                  "які новини*": "покажи новини", "яка погода*": "погода\nпрогноз погоди", "де я*": "місто",
                  "згорни вікно*": "сховай вікно\nсховай програму\nзгорни програму",
                  "розгорни вікно*": "покажи вікно\nрозгорнеш вікно\nпокажи програму\nрозгорни програму\nрозгорнеш програму",
                  "згорни всі вікна*": "сховай всі вікна\nпокажи робочий стіл\nсховай всі програми\nзгорни всі програми",
                  "розгорни всі вікна*": "покажи всі вікна\nрозгорнеш всі вікна\nпокажи всі програми\nрозгорнеш всі програми\nрозгорни всі програми",
                  "закрий програму*": "закрий вікно", "зміни вікно*": "зміни програму",
                  "гучність на [0-100]*": "звук на [0-100]",
                  "список справ*": "що в мене в списку справ\nщо в списку справ",
                  "очисти список справ*": "очистити список справ",
                  "пауза*": "пауза трека\nпауза пісні\nпризупини трек\nпризупини пісню\nпризупини\nпостав на паузу",
                  "віднови пісню*": "віднови трек\nпродовжити трек\nпродовжи пісню\nзніми з паузи",
                  "наступна пісня*": "наступний трек\nпереключи трек\nпереключи пісню",
                  "попередня пісня*": "попередня пісня\nпопередній трек"}
