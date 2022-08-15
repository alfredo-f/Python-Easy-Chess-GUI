#!/usr/bin/env python3
""" 
python_easy_chess_gui.py

Requirements:
    Python 3.7.3 and up

PySimpleGUI Square Mapping
board = [
    56, 57, ... 63
    ...
    8, 9, ...
    0, 1, 2, ...
]

row = [
    0, 0, ...
    1, 1, ...
    ...
    7, 7 ...
]

col = [
    0, 1, 2, ... 7
    0, 1, 2, ...
    ...
    0, 1, 2, ... 7
]


Python-Chess Square Mapping
board is the same as in PySimpleGUI
row is reversed
col is the same as in PySimpleGUI

"""

import logging

from python_easy_chess_gui import ROOT_PATH
from python_easy_chess_gui.config import (
    log_format,
    BOOK_PATH,
)
from python_easy_chess_gui.ui_package.ui_module import EasyChessGui


logging.basicConfig(filename='pecg_log.txt', filemode='w', level=logging.DEBUG,
                    format=log_format)


def main():
    engine_config_file = ROOT_PATH / 'pecg_engines.json'
    user_config_file = ROOT_PATH / 'pecg_user.json'

    gui_book_file = BOOK_PATH / 'pecg_book.bin'
    computer_book_file = BOOK_PATH / 'computer.bin'
    human_book_file = BOOK_PATH / 'human.bin'

    is_use_gui_book = True
    is_random_book = True  # If false then use best book move
    max_book_ply = 8
    theme = 'Reddit'

    pecg = EasyChessGui(
        theme=theme,
        engine_config_file=engine_config_file,
        user_config_file=user_config_file,
        gui_book_file=gui_book_file,
        computer_book_file=computer_book_file,
        human_book_file=human_book_file,
        is_use_gui_book=is_use_gui_book,
        is_random_book=is_random_book,
        max_book_ply=max_book_ply,
    )

    pecg.main_loop()


if __name__ == "__main__":
    main()
