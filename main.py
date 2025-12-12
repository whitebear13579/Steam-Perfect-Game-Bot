import flet as ft
import multiprocessing
from modules.gui import main as gui_main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    ft.app(target=gui_main)
