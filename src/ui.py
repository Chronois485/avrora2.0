import asyncio
import json
import logging
import os
import random
import re
import time

import flet as ft

import avroraCore
import constants as const


class UI:
    def __init__(self, page, on_first_launch_complete=None):
        logging.info("Initializing UI class.")
        self.page = page
        self.on_first_launch_complete = on_first_launch_complete
        self.settings = {}
        self.settings_is_open = False
        self.info_is_open = False
        self.statusIcon = ft.IconButton(icon=const.SPEAKING_ICON, icon_size=20, tooltip=const.STATUS_TOOLTIP,
                                        animate_opacity=ft.Animation(300), animate_rotation=ft.Animation(1000),
                                        offset=ft.Offset(1.48, 0), disabled=True,
                                        rotate=ft.Rotate(angle=0, alignment=ft.alignment.center), opacity=0)
        self.chat_history_filename = const.CHAT_HISTORY_FILENAME
        self.load_chat_history()

    @staticmethod
    def generate_message_id():
        return str(time.time_ns())

    @staticmethod
    def build_info_table():
        logging.info("Building info table.")
        table = ft.DataTable(columns=[ft.DataColumn(ft.Text(const.INFO_TABLE_HEADER_COMMAND)),
                                      ft.DataColumn(ft.Text(const.INFO_TABLE_HEADER_ACTION))], data_row_min_height=10,
                             data_row_max_height=45)

        user_data_dir = os.path.dirname(const.INFO_TABLE_FILENAME)
        os.makedirs(user_data_dir, exist_ok=True)

        default_data = {}
        try:
            with open(const.DEFAULT_INFO_TABLE_FILENAME, "r", encoding="utf-8") as f:
                default_data = json.load(f)
                if not isinstance(default_data, dict):
                    logging.error(f"Default commands table {const.DEFAULT_INFO_TABLE_FILENAME} has invalid format.")
                    default_data = {}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Could not load or parse default commands table: {e}", exc_info=True)

        try:
            with open(const.INFO_TABLE_FILENAME, "r", encoding="utf-8") as f:
                user_data = json.load(f)
            if not isinstance(user_data, dict):
                logging.warning(
                    f"User commands table {const.INFO_TABLE_FILENAME} has invalid format. It will be overwritten.")
                user_data = {}
        except (FileNotFoundError, json.JSONDecodeError):
            logging.info(f"User commands table not found or corrupted. Will be created/overwritten from default.")
            user_data = {}

        if user_data != default_data and default_data:
            logging.info("User commands table is outdated or missing. Updating from default.")
            user_data = default_data
            try:
                with open(const.INFO_TABLE_FILENAME, "w", encoding="utf-8") as f:
                    json.dump(user_data, f, ensure_ascii=False, indent=4)
                logging.info("User commands table updated successfully.")
            except IOError as e:
                logging.error(f"Could not write updated commands table to {const.INFO_TABLE_FILENAME}: {e}",
                              exc_info=True)

        table_data = user_data
        if not isinstance(table_data, dict): table_data = {}

        for key, value in table_data.items():
            if key[-1] == "*":
                command_tooltip = const.TABLE_VARIANTS.get(key)
                if command_tooltip:
                    table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(key, size=10, tooltip=command_tooltip)),
                                                        ft.DataCell(ft.Text(value, size=10))]))
                else:
                    logging.info(f"Adding command {key}, with tooltip {command_tooltip} to info table.")
                    table.rows.append(
                        ft.DataRow(cells=[ft.DataCell(ft.Text(key, size=10)), ft.DataCell(ft.Text(value, size=10))]))
                    logging.warning("Error while building info table. No tooltip for command")
            else:
                table.rows.append(
                    ft.DataRow(cells=[ft.DataCell(ft.Text(key, size=10)), ft.DataCell(ft.Text(value, size=10))]))
                logging.info(f"Adding command {key} to info table.")
        logging.info(f"Info table built with {len(table.rows)} rows.")
        return table

    async def build_first_launch_view(self):
        """Будує та відображає початковий екран для першого запуску, щоб отримати ім'я користувача."""
        logging.info("Building first launch view.")
        self.page.clean()
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.bgcolor = const.COLORS_DARK["MAINBGCOLOR"]
        self.page.title = const.APP_NAME

        self.firstLaunchL = ft.Text(value=const.FIRST_LAUNCH_LABEL, size=20, text_align=const.ALIGN_CENTER, width=350)
        self.firstLaunchI = ft.TextField(label=const.FIRST_LAUNCH_INPUT_LABEL, value="", width=300)

        confirm_button = ft.ElevatedButton(text=const.FIRST_LAUNCH_CONFIRM_BUTTON,
                                           on_click=self._handle_first_launch_submit, width=200, height=40, )

        first_launch_layout = ft.Column(
            [self.firstLaunchL, ft.Container(height=10), self.firstLaunchI, ft.Container(height=20), confirm_button, ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, )

        self.page.add(first_launch_layout)
        self.page.update()

    async def _handle_first_launch_submit(self, e):
        """Обробник для кнопки 'Продовжити' на екрані першого запуску."""
        user_name = self.firstLaunchI.value.strip()
        if not user_name:
            logging.warning("Attempted to submit first launch with an empty name.")
            self.firstLaunchI.error_text = const.FIRST_LAUNCH_EMPTY_NAME_ERROR
            self.page.update()
            return

        logging.info(f"First launch submitted. User name set to: '{user_name}'")
        await avroraCore.save_settings(
            {"name": user_name, "tgo": False, "tgpath": const.DEFAULT_TG_PATH, "music": const.DEFAULT_MUSIC_LINK,
             "pcpower": False, "city": const.DEFAULT_CITY, "num_headlines": 5, "theme": "dark"})

        self.page.clean()
        self.page.update()

        if self.on_first_launch_complete:
            await self.on_first_launch_complete()

    async def build_ui(self):
        logging.info("Building main UI components.")
        self.settings = await avroraCore.load_settings()
        self.page.fonts = {"Tektur": const.TEKTUR_FONT_PATH, "TekturBold": const.TEKTUR_BOLD_FONT_PATH}
        self.page.title = const.APP_NAME
        self.page.window.width = const.WINDOW_WIDTH
        self.page.window.height = const.WINDOW_HEIGHT
        self.page.window.min_width = const.WINDOW_MIN_WIDTH
        self.page.window.max_width = const.WINDOW_MAX_WIDTH
        self.page.window.max_height = const.WINDOW_MAX_HEIGHT
        self.page.window.min_height = const.WINDOW_MIN_HEIGHT
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        accent_color = self.settings.get("accent_color", const.DEEP_PURPLE_400)
        self.page.theme = ft.Theme(color_scheme_seed=accent_color, font_family=const.FONT_FAMILY)
        self.page.dark_theme = ft.Theme(color_scheme_seed=accent_color, font_family=const.FONT_FAMILY)

        self.page.theme_mode = ft.ThemeMode.DARK if self.settings.get("theme") == "dark" else ft.ThemeMode.LIGHT

        self.settingsMenu = ft.Container(width=420, height=510, border_radius=10, offset=ft.Offset(0, -0.20),
                                         bgcolor=const.INITIATION_COLOR, border=ft.border.all(2, ft.Colors.PRIMARY),
                                         animate_offset=ft.Animation(250), padding=10)

        self.infoHeader = ft.Text(const.INFO_HEADER_LABEL, size=10)

        self.infoTable = self.build_info_table()

        self.multipleCommandsHelp = ft.Markdown(const.MULTIPLE_COMMAND_VARIANTS_HELP_LABEL, selectable=True,
                                                extension_set=const.MARKDOWN_EXTENSION_SET,
                                                code_theme=const.MARKDOWN_CODE_THEME)
        self.multipleCommandsHelp.code_block_style = ft.TextStyle(font_family=const.FONT_FAMILY)

        self.customCommandsHelp = ft.Markdown(const.CUSTOM_COMMANDS_HELP_LABEL, selectable=True,
                                              extension_set=const.MARKDOWN_EXTENSION_SET,
                                              code_theme=const.MARKDOWN_CODE_THEME)
        self.customCommandsHelp.code_block_style = ft.TextStyle(font_family=const.FONT_FAMILY)

        self.conntactUsHelp = ft.Markdown(const.CONTACT_US_LABEL, selectable=True,
                                          extension_set=const.MARKDOWN_EXTENSION_SET,
                                          code_theme=const.MARKDOWN_CODE_THEME)
        self.conntactUsHelp.code_block_style = ft.TextStyle(font_family=const.FONT_FAMILY)

        self.madeByHelp = ft.Markdown(const.DEVELOPED_BY_LABEL, selectable=True,
                                      extension_set=const.MARKDOWN_EXTENSION_SET, code_theme=const.MARKDOWN_CODE_THEME)
        self.madeByHelp.code_block_style = ft.TextStyle(font_family=const.FONT_FAMILY)

        self.infoMenuDivider = ft.Divider(height=1, thickness=2)

        self.infoMenu = ft.Container(width=420, height=510, border_radius=10, offset=ft.Offset(-2.08, -0.20),
                                     bgcolor=const.INITIATION_COLOR, border=ft.border.all(2, ft.Colors.PRIMARY),
                                     animate_offset=ft.Animation(250), padding=10)
        self.nameTlow = ft.Text(value=const.APP_FULL_NAME, text_align=const.ALIGN_CENTER, width=160, size=10)
        self.nameT = ft.Text(value=const.APP_NAME, text_align=const.ALIGN_CENTER, width=160, size=29)
        self.nameCol = ft.Column(spacing=10, controls=[self.nameT, self.nameTlow, self.statusIcon])
        self.infoMenu.content = ft.Column(
            controls=[self.infoHeader, self.infoTable, self.infoMenuDivider, self.multipleCommandsHelp,
                      self.infoMenuDivider, self.customCommandsHelp, self.infoMenuDivider, self.conntactUsHelp,
                      self.infoMenuDivider, self.madeByHelp], scroll=const.SCROLL_MODE_AUTO)
        self.msgs = list()
        self.msgsCol = ft.Column(controls=self.msgs, scroll=const.SCROLL_MODE_AUTO, expand=True)
        self.msgsBox = ft.Container(content=self.msgsCol, width=420, expand=True)

        self.chat_input = ft.TextField(hint_text=const.SEND_MSG_FIELD_LABEL, expand=True,
            on_submit=self.handle_text_command, border_radius=20, )

        self.send_button = ft.IconButton(icon=const.SEND_ICON, icon_size=20, tooltip=const.SEND_BUTTON_LABEL,
            on_click=self.handle_text_command, )

        self.input_row = ft.Row(controls=[self.chat_input, self.send_button],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER)

        self.chatCol = ft.Column(controls=[self.msgsBox, self.input_row], expand=True)
        self.chat = ft.Container(width=420, height=455, content=self.chatCol, offset=ft.Offset(-0.005, -0.049))

        self.TGPath = ft.Text(value=f"{const.TG_PATH_LABEL_PREFIX}{self.settings.get('tgpath')}", width=350)

        self.YourNameI = ft.TextField(label=const.YOUR_NAME_LABEL, value=self.settings.get("name") or "",
                                      on_change=self.update_settings, expand=False, disabled=False, visible=True)

        self.NewsHeadersCountT = ft.Text(value=const.NEWS_HEADERS_COUNT_LABEL, size=15)

        self.NewsHeadersCountS = ft.Slider(min=1, max=10, value=self.settings.get("num_headlines", 5), divisions=9,
                                           label="{value}", on_change=self.update_settings)

        self.themeS = ft.Switch(label=const.THEME_SWITCH_LABEL, value=(self.settings.get("theme") == "dark"),
                                on_change=self.switch_theme)

        self.accent_color_dropdown = ft.Dropdown(label=const.ACCENT_COLOR_LABEL,
                                                 options=[ft.dropdown.Option(color_name) for color_name in
                                                          const.ACCENT_COLORS.keys()],
                                                 value=self.settings.get("accent_color_name", "Deep Purple"),
                                                 on_change=self.switch_accent_color)

        self.CityI = ft.TextField(label=const.CITY_LABEL, value=self.settings.get("city") or "",
                                  on_change=self.update_settings, expand=False, disabled=False, visible=True)

        self.musicLinkI = ft.TextField(label=const.MUSIC_LINK_LABEL, value=self.settings.get("music") or "",
                                       on_change=self.update_settings)

        self.useTGOnlineCB = ft.Checkbox(label=const.USE_TG_ONLINE_LABEL, value=self.settings.get("tgo"),
                                         label_position=ft.LabelPosition.LEFT, on_change=self.update_settings)
        self.clearChatButton = ft.ElevatedButton(text=const.CLEAR_CHAT_BUTTON_LABEL, width=200, height=30,
                                                 on_click=self.clearChat)

        self.silentModeCB = ft.Checkbox(label=const.SILENT_MODE_CHECKBOX_LABEL,
                                        value=self.settings.get("silentmode"),
                                        label_position=ft.LabelPosition.RIGHT,
                                        on_change=self.update_settings)

        self.resetSettingsButton = ft.ElevatedButton(text=const.RESET_SETTINGS_BUTTON_LABEL, width=200, height=30,
                                                     on_click=self.resetSettings)

        self.permisionsToControlPCPowerCB = ft.Checkbox(label=const.PERMISSIONS_TO_CONTROL_PC_POWER_LABEL,
                                                        value=self.settings.get("pcpower"),
                                                        label_position=ft.LabelPosition.RIGHT,
                                                        on_change=self.update_settings)

        self.file_picker = ft.FilePicker(on_result=self.on_file_selected)
        self.page.overlay.append(self.file_picker)
        self.selectTGFile = ft.ElevatedButton(const.SELECT_TG_FILE_LABEL,
                                              on_click=lambda _: self.file_picker.pick_files(allow_multiple=False,
                                                                                             allowed_extensions=const.ALLOWED_EXTENSIONS_EXE))

        self.passiveL = ft.TextField(value=const.SETTINGS_LABEL, text_align=const.ALIGN_CENTER, border_width=0,
                                     border_radius=10)

        self.infoB = ft.IconButton(icon=const.INFO_ICON, icon_size=20, tooltip="Команди", on_click=self.openInfo,
                                   offset=ft.Offset(0, -1))

        self.settingsB = ft.IconButton(icon=const.SETTINGS_ICON, icon_size=20, tooltip="Налаштування",
                                       on_click=self.openSettings, offset=ft.Offset(0, -1))

        self.CCmLabel = ft.TextField(value=const.CUSTOM_COMMANDS_LABEL, text_align=const.ALIGN_CENTER, border_width=0,
                                     border_radius=10, disabled=True)

        self.CCmDropdownOptions = [ft.dropdown.Option("", text=const.NEW_COMMAND_LABEL)]

        self.CCmDropdown = ft.Dropdown(label=const.DROPDOWN_CHOOSE_COMMAND_LABEL, options=self.CCmDropdownOptions,
                                       on_change=self.on_CC_chosen)

        self.CCmNameI = ft.TextField(label=const.COMMAND_NAME_LABEL, value="", expand=False, disabled=False,
                                     visible=True, )

        self.CCmActionI = ft.TextField(label=const.COMMAND_ACTION_LABEL, value="", expand=False, disabled=False,
                                       visible=True)

        self.CCmDeleteB = ft.ElevatedButton(text=const.DELETE_CC_LABEL, width=150, height=30, on_click=self.delete_CC)

        self.CCmSubmitB = ft.ElevatedButton(text=const.CONFIRM_CC_LABEL, width=180, height=30, on_click=self.accept_CCm)

        self.CCmCancelB = ft.ElevatedButton(text=const.CANCEL_CC_LABEL, width=180, height=30, on_click=self.close_CCm)

        self.CCmButtonsRow = ft.Row(spacing=20, controls=[self.CCmSubmitB, self.CCmCancelB],
                                    alignment=const.ALIGN_CENTER)

        self.CCmCol = ft.Column(spacing=10, controls=[self.CCmLabel, self.CCmDropdown, self.CCmNameI, self.CCmActionI,
                                                      self.CCmDeleteB, self.CCmButtonsRow])

        self.CCm = ft.Container(width=425, height=510, border_radius=10, padding=10, alignment=ft.alignment.center,
                                content=self.CCmCol, animate_offset=ft.Animation(250), bgcolor=const.INITIATION_COLOR,
                                border=ft.border.all(2, ft.Colors.PRIMARY), offset=ft.Offset(-1.03, -1.25))

        self.CCmOpen = ft.ElevatedButton(text=const.CUSTOM_COMMANDS_BUTTON_LABEL, width=200, height=30,
                                         on_click=self.open_CCm)

        self.settingsDivider = ft.Divider(height=1, thickness=2)
        self.settingsGroupTG = ft.Text(value=const.SETTINGS_GROUP_TG_LABEL, size=20, text_align=const.ALIGN_CENTER)
        self.settingsGroupPersonalInfo = ft.Text(value=const.SETTINGS_GROUP_PERSONAL_INFO_LABEL, size=20,
                                                 text_align=const.ALIGN_CENTER)
        self.settingsGroupPermissions = ft.Text(value=const.SETTINGS_GROUP_PERMISSIONS_LABEL, size=20,
                                                text_align=const.ALIGN_CENTER)
        self.settingsGroupChat = ft.Text(value=const.SETTINGS_GROUP_CHAT_LABEL, size=20, text_align=const.ALIGN_CENTER)
        self.settingsGroupCC = ft.Text(value=const.SETTINGS_GROUP_CC_LABEL, size=20, text_align=const.ALIGN_CENTER)
        self.settingsGroupPersonalisation = ft.Text(value=const.SETTINGS_GROUP_PERSONALISATION_LABEL, size=20,
                                                    text_align=const.ALIGN_CENTER)

        self.settingsCol = ft.Column(spacing=10,
                                     controls=[self.passiveL, self.settingsGroupPersonalInfo, self.YourNameI,
                                               self.CityI, self.musicLinkI, self.NewsHeadersCountT,
                                               self.NewsHeadersCountS, self.settingsDivider,
                                               self.settingsGroupPersonalisation, self.themeS,
                                               self.accent_color_dropdown, self.settingsDivider, self.settingsGroupTG,
                                               self.TGPath, self.selectTGFile, self.useTGOnlineCB, self.settingsDivider,
                                               self.settingsGroupPermissions, self.permisionsToControlPCPowerCB,
                                               self.resetSettingsButton, self.settingsDivider, self.settingsGroupChat,
                                               self.clearChatButton, self.silentModeCB, self.settingsDivider, self.settingsGroupCC,
                                               self.CCmOpen, self.settingsDivider], scroll="auto")
        self.settingsMenu.content = self.settingsCol

        async def _apply_theme_on_mount(e):
            """
            Applies the theme colors as soon as the page is mounted.
            This ensures that components have the correct colors on the first launch.
            """
            await self.apply_and_update_theme()
            self.page.on_mount = None

        self.page.on_mount = _apply_theme_on_mount

        self.topRow = ft.Row(spacing=88, controls=[self.infoB, self.nameCol, self.settingsB])
        self.secondRow = ft.Row(controls=[self.chat, self.infoMenu, self.settingsMenu])

        await asyncio.sleep(0.1)
        self.page.add(self.topRow, self.secondRow, self.CCm)
        logging.info("Main UI components built and added to page.")

        await self.apply_and_update_theme()

    def _apply_theme_colors(self):
        """Applies colors to all relevant UI elements based on the current theme."""
        logging.info("Applying theme colors.")
        if not hasattr(self.page, 'theme') or not hasattr(self.page, 'dark_theme'):
            return

        active_theme = self.page.dark_theme if self.page.theme_mode == ft.ThemeMode.DARK else self.page.theme
        if not active_theme or not active_theme.color_scheme:
            logging.warning("Color scheme not available yet. Deferring color application.")
            return

        color_scheme = active_theme.color_scheme
        if not color_scheme:
            logging.error("Aborting color update because color scheme could not be determined.")
            return

        self.page.bgcolor = color_scheme.background

        for menu in [self.settingsMenu, self.infoMenu, self.CCm]:
            menu.bgcolor = color_scheme.surface
            menu.border = ft.border.all(2, color_scheme.primary)

        for icon_button in [self.infoB, self.settingsB, self.statusIcon]:
            icon_button.icon_color = color_scheme.primary

        for divider in [self.settingsDivider, self.infoMenuDivider]:
            divider.color = color_scheme.primary

        for text_field in [self.passiveL, self.CCmLabel]:
            text_field.border = ft.border.all(2, color=color_scheme.primary)

    async def apply_and_update_theme(self):
        """Застосовує тему та оновлює чат"""

        await self.wait_for_theme_initialization()

        self._apply_theme_colors()
        self.update_chat_from_history()
        self.page.update()

    async def update_settings(self, e):
        logging.info("Updating settings.")
        self.settings["name"] = self.YourNameI.value
        self.settings["tgo"] = self.useTGOnlineCB.value
        self.settings["music"] = self.musicLinkI.value
        self.settings["pcpower"] = self.permisionsToControlPCPowerCB.value
        self.settings["city"] = self.CityI.value
        self.settings["num_headlines"] = int(self.NewsHeadersCountS.value)
        self.settings["theme"] = "dark" if self.themeS.value else "light"
        self.settings["silentmode"] = self.silentModeCB.value

        await avroraCore.save_settings(self.settings)

        self.selectTGFile.disabled = self.settings.get("tgo", False)
        self.selectTGFile.update()

        self.CCmDropdownOptions = [ft.dropdown.Option("", text=const.NEW_COMMAND_LABEL)]
        for key in (await avroraCore.load_cc()).keys():
            self.CCmDropdownOptions.append(ft.dropdown.Option(key, text=key))

        self.CCmDropdown.options = self.CCmDropdownOptions
        self.CCmDropdown.update()

    def openSettings(self, e):
        if not self.settings_is_open and not self.info_is_open:
            logging.info("Opening settings menu.")
            self.infoB.disabled = True
            self.settingsMenu.offset = ft.Offset(-2.054, -0.20)
            self.settings_is_open = True
        else:
            logging.info("Closing settings menu.")
            self.settingsMenu.offset = ft.Offset(-1.03, -0.20)
            self.settings_is_open = False
            self.infoB.disabled = False
        self.page.update()

    def openInfo(self, e):
        if not self.info_is_open and not self.settings_is_open:
            logging.info("Opening info menu.")
            self.infoMenu.offset = ft.Offset(-1.029, -0.20)
            self.info_is_open = True
            self.settingsB.disabled = True
        else:
            logging.info("Closing info menu.")
            self.infoMenu.offset = ft.Offset(-2.08, -0.20)
            self.info_is_open = False
            self.settingsB.disabled = False
        self.page.update()

    async def resetSettings(self, e):
        logging.warning("Resetting all settings.")
        if os.path.exists(const.SETTINGS_FILENAME):
            logging.info(f"Removed settings file: {const.SETTINGS_FILENAME}")
            os.remove(const.SETTINGS_FILENAME)
        self.YourNameI.value = ""
        self.useTGOnlineCB.value = False
        self.TGPath.value = ""
        self.musicLinkI.value = ""
        self.permisionsToControlPCPowerCB.value = False
        self.CityI.value = ""
        self.silentModeCB.value = False
        self.NewsHeadersCountS.value = 5
        await self.update_settings(None)
        logging.info("Settings have been reset to default.")
        self.page.update()

    async def wait_for_theme_initialization(self, max_attempts=10, delay=0.1):
        """Чекає, доки тема буде повністю ініціалізована."""
        for _ in range(max_attempts):
            if hasattr(self.page, 'theme') and hasattr(self.page.theme, 'color_scheme'):
                return True
            await asyncio.sleep(delay)
        return False

    async def switch_theme(self, e):
        """Handles the theme switch, updates the page, and saves the setting."""
        new_theme_str = "dark" if self.themeS.value else "light"
        self.page.theme_mode = ft.ThemeMode.DARK if self.themeS.value else ft.ThemeMode.LIGHT
        logging.info(f"Theme switched to {new_theme_str}.")

        self.settings['theme'] = new_theme_str
        await avroraCore.save_settings(self.settings)

        await self.wait_for_theme_initialization()

        self.update_chat_from_history()
        await self.apply_and_update_theme()

    async def switch_accent_color(self, e):
        """Handles the accent color switch, updates the theme, and saves the setting."""
        color_name = self.accent_color_dropdown.value
        color_value = const.ACCENT_COLORS[color_name]
        logging.info(f"Accent color switched to {color_name}.")

        self.page.theme.color_scheme_seed = color_value
        self.page.dark_theme.color_scheme_seed = color_value

        self.settings['accent_color_name'] = color_name
        self.settings['accent_color'] = color_value
        await avroraCore.save_settings(self.settings)

        await self.wait_for_theme_initialization()

        self.update_chat_from_history()
        self.page.update()
        await self.apply_and_update_theme()

    async def open_CCm(self, e):
        logging.info("Opening Custom Commands menu.")
        await self.update_settings(None)
        self.openSettings(None)
        self.settingsB.disabled = True
        self.infoB.disabled = True
        self.CCm.offset = ft.Offset(0, -1.25)
        self.page.update()

    def close_CCm(self, e):
        logging.info("Closing Custom Commands menu.")
        self.CCm.offset = ft.Offset(-1.03, -1.25)
        self.settingsB.disabled = False
        self.infoB.disabled = False
        self.openSettings(None)

    async def accept_CCm(self, e):
        if self.CCmNameI.value == "" or self.CCmNameI.value == " ":
            logging.warning("Attempted to save a custom command with an empty name.")
            return
        logging.info(f"Accepting new/updated custom command: '{self.CCmNameI.value}' -> '{self.CCmActionI.value}'")
        await self.saveCC([[self.CCmNameI.value, self.CCmActionI.value]])
        self.close_CCm(None)
        self.CCmNameI.value, self.CCmActionI.value = "", ""
        self.page.update()

    async def delete_CC(self, e):
        command_to_delete = self.CCmDropdown.value
        logging.warning(f"Attempting to delete custom command: '{command_to_delete}'")
        temp = await avroraCore.load_cc()
        json_file = {}
        for key in temp.keys():
            if key == self.CCmDropdown.value:
                continue
            json_file[key] = temp.get(key)
        self.CCmNameI.value = ""
        self.CCmActionI.value = ""
        self.CCmDropdown.value = self.CCmDropdownOptions[0]
        await avroraCore.save_cc(json_file)
        logging.info(f"Successfully deleted custom command: '{command_to_delete}'")
        self.CCmActionI.update()
        self.CCmNameI.update()
        self.CCmDropdown.update()
        self.page.update()

    async def showFatalError(self, error):
        logging.critical(f"Displaying fatal error to user: {error}")
        self.nameTlow.value = f"A.V.R.O.R.A. зіткнулася з критичною помилкою, а саме {error}"
        self.nameTlow.update()
        self.page.update()

    async def on_file_selected(self, e: ft.FilePickerResultEvent):
        if self.file_picker.result and self.file_picker.result.files:
            selected_file = self.file_picker.result.files[0].path
            self.settings["tgpath"] = selected_file
            await self.update_settings(None)

    async def on_CC_chosen(self, e):
        chosen_command = self.CCmDropdown.value
        logging.info(f"Custom command chosen from dropdown: '{chosen_command}'")
        self.CCmNameI.value = self.CCmDropdown.value
        self.CCmActionI.value = (await avroraCore.load_cc()).get(self.CCmDropdown.value)
        self.page.update()

    async def animateStatus(self, status):
        logging.debug(f"Animating status to: '{status}'")
        if status == const.STATUS_THINKING:
            self.statusIcon.icon = const.LOADING_ICON
            self.statusIcon.animate_rotation = ft.Animation(1000)
            self.statusIcon.rotate = ft.Rotate(angle=360, alignment=ft.alignment.center)
            self.statusIcon.opacity = 1
        elif status == const.STATUS_LISTENING:
            self.statusIcon.icon = const.MIC_ICON
            self.statusIcon.opacity = 0
            await asyncio.sleep(0.1)
            self.statusIcon.animate_rotation = None
            self.statusIcon.rotate = ft.Rotate(angle=0, alignment=ft.alignment.center)
            self.statusIcon.opacity = 1
        elif status == const.STATUS_SPEAKING:
            self.statusIcon.icon = const.SPEAKING_ICON
            self.statusIcon.opacity = 0
            await asyncio.sleep(0.1)
            self.statusIcon.animate_rotation = None
            self.statusIcon.rotate = ft.Rotate(angle=0, alignment=ft.alignment.center)
            self.statusIcon.opacity = 1
        else:
            self.statusIcon.rotate = ft.Rotate(angle=0, alignment=ft.alignment.center)
            self.statusIcon.opacity = 0
        self.statusIcon.update()
        await asyncio.sleep(0.1)
        self.page.update()

    def _create_chat_message(self, text, user, message_id=None):
        active_theme = self.page.dark_theme if self.page.theme_mode == ft.ThemeMode.DARK else self.page.theme

        try:
            color_scheme = active_theme.color_scheme
            if color_scheme is None:
                raise AttributeError("Color scheme is None")

            if user == const.USER_ROLE:
                bubble_color = color_scheme.primary_container
                text_color = color_scheme.on_primary_container
            elif user == const.PROGRAM_ROLE:
                bubble_color = color_scheme.secondary_container
                text_color = color_scheme.on_secondary_container
            else:
                bubble_color = color_scheme.tertiary_container
                text_color = color_scheme.on_tertiary_container

        except Exception as e:
            logging.warning(f"Failed to get colors from theme: {e}, using fallback colors")
            fallback_colors = const.CHAT_FALLBACK_COLORS
            if user == const.USER_ROLE:
                bubble_color = fallback_colors["user_bubble"]
                text_color = fallback_colors["user_text"]
            elif user == const.PROGRAM_ROLE:
                bubble_color = fallback_colors["bot_bubble"]
                text_color = fallback_colors["bot_text"]
            else:
                bubble_color = fallback_colors["system_bubble"]
                text_color = fallback_colors["system_text"]

        url_pattern = re.compile(r"https?://\S+")
        spans = []

        if url_pattern.search(text):
            last_end = 0
            for match in url_pattern.finditer(text):
                start, end = match.span()
                url = match.group(0)
                if start > last_end:
                    spans.append(ft.TextSpan(text[last_end:start], ft.TextStyle(color=text_color)))
                spans.append(
                    ft.TextSpan(url, ft.TextStyle(color=ft.Colors.BLUE_400, decoration=ft.TextDecoration.UNDERLINE),
                                url=url))
                last_end = end
            if last_end < len(text):
                spans.append(ft.TextSpan(text[last_end:], ft.TextStyle(color=text_color)))
            if user == const.USER_ROLE:
                text_widget = ft.Text(spans=spans, selectable=True, text_align=const.ALIGN_RIGHT,
                                      overflow=ft.TextOverflow.CLIP)
            elif user == const.PROGRAM_ROLE:
                text_widget = ft.Text(spans=spans, selectable=True, text_align=const.ALIGN_LEFT,
                                      overflow=ft.TextOverflow.CLIP)
            else:
                text_widget = ft.Text(spans=spans, selectable=True, text_align=const.ALIGN_CENTER,
                                      overflow=ft.TextOverflow.CLIP)
        else:
            if user == const.USER_ROLE:
                text_widget = ft.Text(value=text, selectable=True, text_align=const.ALIGN_RIGHT,
                                      overflow=ft.TextOverflow.CLIP)
            elif user == const.PROGRAM_ROLE:
                text_widget = ft.Text(value=text, selectable=True, text_align=const.ALIGN_LEFT,
                                      overflow=ft.TextOverflow.CLIP)
            else:
                text_widget = ft.Text(value=text, selectable=True, text_align=const.ALIGN_CENTER,
                                      overflow=ft.TextOverflow.CLIP)
        author = ft.Text(text_align=const.ALIGN_LEFT, selectable=True, weight=ft.FontWeight.BOLD)
        if user == const.USER_ROLE:
            author.value = self.settings.get('name', '')
        elif user == const.PROGRAM_ROLE:
            author.value = const.APP_NAME

        alignment = (
            ft.MainAxisAlignment.END if user == const.USER_ROLE else ft.MainAxisAlignment.START if user == const.PROGRAM_ROLE else ft.MainAxisAlignment.CENTER)

        if text.startswith("Прогноз погоди") and user == const.PROGRAM_ROLE:
            text_split = text.split(".")
            weather_type = text_split[1].replace(" На небі ", "").lower()
            temperature = text_split[0].split(":")[1].split(" ")[2]
            weather_icon = const.WEATHER_ICONS.get(weather_type, const.INFO_ICON)
            forecast_sample = ft.Container(ft.Column(controls=[
                ft.Text(const.WEATHER_HEADER_LABEL.format(self.settings.get("city", "")), text_align=const.ALIGN_CENTER,
                        size=15), ft.Row(controls=[ft.Icon(weather_icon, size=35, tooltip=weather_type)], spacing=20),
                ft.Row(controls=[ft.Icon(const.THERMOSTAT_ICON, size=35, tooltip="Температура"),
                                 ft.Text(f": {temperature}℃", size=35, text_align=const.ALIGN_LEFT)]),
                ft.Text(f"{weather_type}, температура {temperature}℃", size=15, text_align=const.ALIGN_LEFT)],
                spacing=10), expand=True, expand_loose=True)

            new_message = ft.Row(alignment=alignment, controls=[
                ft.Container(content=ft.Column(controls=[author, forecast_sample], spacing=5), bgcolor=bubble_color,
                             border_radius=10, padding=10, margin=5, expand=True, expand_loose=True)])

        elif text.startswith("Ось останні ") and user == const.PROGRAM_ROLE:
            text_split = text.split("\n")
            text_widget = [author]
            for i in range(0, len(text_split)):
                if len(text_split[i]) > 1:
                    spans = []
                    if text_split[i][1] == ".":
                        text_widget.append(ft.Text(value=text_split[i], selectable=True, text_align=const.ALIGN_LEFT))
                        text_widget.append(ft.Divider(height=1, thickness=3, color=ft.Colors.PRIMARY))
                    elif url_pattern.search(text_split[i]):
                        last_end = 0
                        for match in url_pattern.finditer(text_split[i]):
                            start, end = match.span()
                            url = match.group(0)
                            if start > last_end:
                                spans.append(ft.TextSpan(text_split[i][last_end:start], ft.TextStyle(color=text_color)))
                            spans.append(ft.TextSpan(url, ft.TextStyle(color=ft.Colors.BLUE_400,
                                                                       decoration=ft.TextDecoration.UNDERLINE),
                                                     url=url))
                            last_end = end
                        if last_end < len(text_split[i]):
                            spans.append(ft.TextSpan(text_split[i][last_end:], ft.TextStyle(color=text_color)))
                        text_widget.append(ft.Text(spans=spans, selectable=True, text_align=const.ALIGN_LEFT))
                    else:
                        text_widget.append(ft.Text(value=text_split[i], selectable=True, text_align=const.ALIGN_LEFT))
            new_message = ft.Row(alignment=alignment, controls=[
                ft.Container(content=ft.Column(controls=text_widget, spacing=5), bgcolor=bubble_color, border_radius=10,
                             padding=10, margin=5, expand=True, expand_loose=True)])

        else:
            new_message = ft.Row(alignment=alignment, controls=[
                ft.Container(content=ft.Column(controls=[author, text_widget], spacing=5), bgcolor=bubble_color,
                             border_radius=10, padding=10, margin=5, expand=True, expand_loose=True)])

        if message_id:
            new_message.data = message_id

        return new_message

    async def addToChat(self, text, user):
        logging.debug(f"Adding to chat: user='{user}', text='{text}'")
        new_message = self._create_chat_message(text, user)
        self.msgsCol.controls.append(new_message)
        self.save_chat_history(text, user)
        self.msgsCol.update()
        self.page.update()
        await asyncio.sleep(0.1)
        self.msgsCol.scroll_to(offset=-1, duration=300)
        self.page.update()

    def on_startup(self):
        self.load_chat_history()
        self.update_chat_from_history()

    def clearChat(self, e):
        logging.info("Clearing chat history.")
        self.msgsCol.controls.clear()
        self.chat_history.clear()
        self._save_history_to_file()
        self.msgsCol.update()
        self.page.update()

    def save_chat_history(self, text, user):
        logging.debug("Saving new message to chat history.")
        new_message = {"text": text, "user": user, "id": self.generate_message_id()}
        self.chat_history.append(new_message)
        self._save_history_to_file()

    def _save_history_to_file(self):
        logging.debug(f"Writing chat history to file: {self.chat_history_filename}")
        with open(self.chat_history_filename, "w", encoding="utf-8") as f:
            json.dump(self.chat_history, f, ensure_ascii=False, indent=4)

    def load_chat_history(self):
        logging.info(f"Loading chat history from {self.chat_history_filename}")
        if os.path.exists(self.chat_history_filename):
            with open(self.chat_history_filename, "r", encoding="utf-8") as f:
                try:
                    self.chat_history = json.load(f)
                    if isinstance(self.chat_history, list) and all(isinstance(item, str) for item in self.chat_history):
                        new_chat_history = []
                        for message in self.chat_history:
                            new_chat_history.append(
                                {"text": message, "user": const.PROGRAM_ROLE, "id": self.generate_message_id()})
                        self.chat_history = new_chat_history
                    elif isinstance(self.chat_history, list) and all(
                            isinstance(item, dict) for item in self.chat_history):
                        for message in self.chat_history:
                            if "id" not in message:
                                message["id"] = self.generate_message_id()
                except json.JSONDecodeError:
                    logging.error(f"Failed to decode chat history file: {self.chat_history_filename}", exc_info=True)
                    self.chat_history = []
        else:
            logging.info("Chat history file not found, starting with empty history.")
            self.chat_history = []

    def update_chat_from_history(self):
        self.msgsCol.controls.clear()
        for message in self.chat_history:
            text = message["text"]
            user = message["user"]
            message_id = message["id"]
            new_message = self._create_chat_message(text, user, message_id)
            self.msgsCol.controls.append(new_message)
        self.page.update()

    async def saveCC(self, command):
        logging.info(f"Saving custom command(s): {command}")
        temp = await avroraCore.load_cc()
        for i in command:
            temp[i[0]] = i[1]
        await avroraCore.save_cc(temp)

    async def handle_text_command(self, e):
        """Обробляє команди, введені в текстове поле."""
        command_text = self.chat_input.value.strip()
        if not command_text:
            return
        self.chat_input.value = ""
        await self.addToChat(command_text, const.USER_ROLE)
        logging.info(f"Text command received: {command_text}.")
        ans, result_message = await avroraCore.what_command(command_text.lower(), self, self.page, self.settings)

        logging.info(f"what_command returned: ans='{ans}', message='{result_message}'")
        if ans == 1:
            await avroraCore.tts(const.RESPONSE_CLARIFY, on_status_change=None)
            result_message = const.RESPONSE_CLARIFY
        elif ans == "standard":
            ans_random = random.randint(0, 2)
            generic_responses = [resp.format(self.settings.get('name', '')) for resp in
                                 const.GENERIC_AFFIRMATIVE_RESPONSES]
            logging.info("Standard response sent.")
            result_message = generic_responses[ans_random]
            await avroraCore.tts(result_message, on_status_change=None)
        await  self.addToChat(result_message, const.PROGRAM_ROLE)

        self.page.update()
