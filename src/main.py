import asyncio
import logging
import os
import sys

import flet as ft

import avroraCore
import constants as const
from ui import UI

logging.basicConfig(filename=const.LOG_FILENAME, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s')


async def listen(page, ui_instance):
    """Починає основний цикл прослуховування"""
    logging.info("Starting main listening loop.")
    action_after_loop = const.EXIT_COMMAND
    while True:
        text = await avroraCore.listen(on_status_change=ui_instance.animateStatus)
        if text:
            logging.info(f"Recognized text: '{text}'")
            if text.startswith(const.WAKE_WORD):
                await ui_instance.addToChat(text, const.USER_ROLE)
                try:
                    ans, result_message = await avroraCore.doSomething(text, ui_instance, page,
                                                                       on_status_change=ui_instance.animateStatus,
                                                                       on_remind=ui_instance.addToChat)
                    if result_message:
                        await ui_instance.addToChat(result_message, const.PROGRAM_ROLE)
                    if ans == const.EXIT_COMMAND:
                        logging.info("Exit command received. Shutting down.")
                        break
                    if ans == const.RESTART_COMMAND:
                        logging.info("Restart command received. Preparing to restart.")
                        action_after_loop = const.RESTART_COMMAND
                        break
                except Exception as e:
                    error_message = f"An error occurred in doSomething: {e}"
                    logging.error(error_message, exc_info=True)
                    await ui_instance.showFatalError(f"Сталася помилка: {e}")
                    await ui_instance.addToChat(f"Сталася помилка: {e}", const.SYSTEM_ROLE)
        await asyncio.sleep(0)

    page.window.destroy()
    await asyncio.sleep(0.5)

    if action_after_loop == const.RESTART_COMMAND:
        logging.info("Executing restart.")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        logging.info("Exiting application.")


async def start_app_flow(page, ui_instance):
    """Запускає основний потік програми"""
    logging.info("Sending initial greeting.")
    _, result_message = await avroraCore.doSomething(f"{const.WAKE_WORD} {const.CMD_GREETING_VARIANTS[0]}", ui_instance,
                                                     page, on_status_change=ui_instance.animateStatus)
    await ui_instance.addToChat(result_message, const.PROGRAM_ROLE)
    await listen(page, ui_instance)


async def build_and_run_main_app(page, ui_instance):
    """Створює і запускає основну програму"""
    await ui_instance.build_ui()
    logging.info("UI has been built.")
    await ui_instance.apply_and_update_theme()

    await start_app_flow(page, ui_instance)


async def main(page: ft.Page):
    """Запускає програму"""
    logging.info("Application starting.")

    async def _start_app():
        logging.info("Name provided, building main application UI.")
        await build_and_run_main_app(page, ui_instance)

    ui_instance = UI(page, on_first_launch_complete=_start_app)
    logging.info("UI instance created.")

    settings = await avroraCore.load_settings()
    if not settings.get("name"):
        logging.info("First launch: No name found in settings, showing first launch view.")
        await ui_instance.build_first_launch_view()
    else:
        logging.info("Existing user, building main application UI.")
        await _start_app()


ft.app(target=main, name=const.APP_NAME)
