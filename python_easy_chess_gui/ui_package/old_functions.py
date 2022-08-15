import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path, PurePath

import chess

from python_easy_chess_gui.config import ENGINE_PATH, sys_os


def get_engines():
    """
    Get engine filenames [a.exe, b.exe, ...]

    :return: list of engine filenames
    """
    engine_list = []
    files = os.listdir(ENGINE_PATH)
    for file in files:
        if not file.endswith('.gz') and not file.endswith('.dll') \
                and not file.endswith('.DS_Store') \
                and not file.endswith('.bin') \
                and not file.endswith('.dat'):
            engine_list.append(file)

    return engine_list


def get_row(s):
    """
    This row is based on PySimpleGUI square mapping that is 0 at the
    top and 7 at the bottom.
    In contrast Python-chess square mapping is 0 at the bottom and 7
    at the top. chess.square_rank() is a method from Python-chess that
    returns row given square s.

    :param s: square
    :return: row
    """
    return 7 - chess.square_rank(s)


def get_col(s):
    """ Returns col given square s """
    return chess.square_file(s)


def relative_row(s, stm):
    """
    The board can be viewed, as white at the bottom and black at the
    top. If stm is white the row 0 is at the bottom. If stm is black
    row 0 is at the top.
    :param s: square
    :param stm: side to move
    :return: relative row
    """
    return 7 - get_row(s) if stm else get_row(s)


def clear_elements(window):
    """ Clear movelist, score, pv, time, depth and nps boxes """
    window.find_element('search_info_all_k').Update('')
    window.find_element('_movelist_').Update(disabled=False)
    window.find_element('_movelist_').Update('', disabled=True)
    window.find_element('polyglot_book1_k').Update('')
    window.find_element('polyglot_book2_k').Update('')
    window.find_element('advise_info_k').Update('')
    window.find_element('comment_k').Update('')
    window.Element('w_base_time_k').Update('')
    window.Element('b_base_time_k').Update('')
    window.Element('w_elapse_k').Update('')
    window.Element('b_elapse_k').Update('')


def get_time_mm_ss_ms(time_ms):
    """ Returns time in min:sec:millisec given time in millisec """
    s, ms = divmod(int(time_ms), 1000)
    m, s = divmod(s, 60)

    # return '{:02d}m:{:02d}s:{:03d}ms'.format(m, s, ms)
    return '{:02d}m:{:02d}s'.format(m, s)


def get_time_h_mm_ss(time_ms, symbol=True):
    """
    Returns time in h:mm:ss format.

    :param time_ms:
    :param symbol:
    :return:
    """
    s, ms = divmod(int(time_ms), 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)

    if not symbol:
        return '{:01d}:{:02d}:{:02d}'.format(h, m, s)
    return '{:01d}h:{:02d}m:{:02d}s'.format(h, m, s)


def get_players(pgn, q):
    logging.info(f'Enters get_players()')
    players = []
    games = 0
    with open(pgn) as h:
        while True:
            headers = chess.pgn.read_headers(h)
            if headers is None:
                break

            wp = headers['White']
            bp = headers['Black']

            players.append(wp)
            players.append(bp)
            games += 1

    p = list(set(players))
    ret = [p, games]

    q.put(ret)


def get_engine_id_name(path_and_file, q):
    """ Returns id name of uci engine """
    id_name = None
    folder = Path(path_and_file)
    folder = folder.parents[0]

    try:
        if sys_os == 'Windows':
            engine = chess.engine.SimpleEngine.popen_uci(
                path_and_file, cwd=folder,
                creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            engine = chess.engine.SimpleEngine.popen_uci(
                path_and_file, cwd=folder)
        id_name = engine.id['name']
        engine.quit()
    except Exception:
        logging.exception('Failed to get id name.')

    q.put(['Done', id_name])


def delete_player(name, pgn, que):
    """
    Delete games of player name in pgn.

    :param name:
    :param pgn:
    :param que:
    :return:
    """
    logging.info(f'Enters delete_player()')

    pgn_path = Path(pgn)
    folder_path = pgn_path.parents[0]

    file = PurePath(pgn)
    pgn_file = file.name

    # Create backup of orig
    backup = pgn_file + '.backup'
    backup_path = Path(folder_path, backup)
    backup_path.touch()
    origfile_text = Path(pgn).read_text()
    backup_path.write_text(origfile_text)
    logging.info(f'backup copy {backup_path} is successfully created.')

    # Define output file
    output = 'out_' + pgn_file
    output_path = Path(folder_path, output)
    logging.info(f'output {output_path} is successfully created.')

    logging.info(f'Deleting player {name}.')
    gcnt = 0

    # read pgn and save each game if player name to be deleted is not in
    # the game, either white or black.
    with open(output_path, 'a') as f:
        with open(pgn_path) as h:
            game = chess.pgn.read_game(h)
            while game:
                gcnt += 1
                que.put('Delete, {}, processing game {}'.format(
                    name, gcnt))
                wp = game.headers['White']
                bp = game.headers['Black']

                # If this game has no player with name to be deleted
                if wp != name and bp != name:
                    f.write('{}\n\n'.format(game))
                game = chess.pgn.read_game(h)

    if output_path.exists():
        logging.info('Deleting player {} is successful.'.format(name))

        # Delete the orig file and rename the current output to orig file
        pgn_path.unlink()
        logging.info('Delete orig pgn file')
        output_path.rename(pgn_path)
        logging.info('Rename output to orig pgn file')

    que.put('Done')


def get_tag_date():
    """ Return date in pgn tag date format """
    return datetime.today().strftime('%Y.%m.%d')


def get_engine_hash(
    eng_id_name,
    engine_config_file,
):
    """ Returns hash value from engine config file """
    eng_hash = None
    with open(engine_config_file, 'r') as json_file:
        data = json.load(json_file)
        for p in data:
            if p['name'] == eng_id_name:
                # There engines without options
                try:
                    for n in p['options']:
                        if n['name'].lower() == 'hash':
                            return n['value']
                except KeyError:
                    logging.info('This engine {} has no options.'.format(
                        eng_id_name))
                    break
                except Exception:
                    logging.exception('Failed to get engine hash.')

    return eng_hash


def get_engine_threads(
    eng_id_name,
    engine_config_file,
):
    """
    Returns number of threads of eng_id_name from pecg_engines.json.

    :param eng_id_name: the engine id name
    :return: number of threads
    """
    eng_threads = None
    with open(engine_config_file, 'r') as json_file:
        data = json.load(json_file)
        for p in data:
            if p['name'] == eng_id_name:
                try:
                    for n in p['options']:
                        if n['name'].lower() == 'threads':
                            return n['value']
                except KeyError:
                    logging.info('This engine {} has no options.'.format(
                        eng_id_name))
                    break
                except Exception:
                    logging.exception('Failed to get engine threads.')

    return eng_threads


def get_engine_file(
    eng_id_name,
    engine_config_file,
):
    """
    Returns eng_id_name's filename and path from pecg_engines.json file.

    :param eng_id_name: engine id name
    :return: engine file and its path
    """
    eng_file, eng_path_and_file = None, None
    with open(engine_config_file, 'r') as json_file:
        data = json.load(json_file)
        for p in data:
            if p['name'] == eng_id_name:
                eng_file = p['command']
                eng_path_and_file = Path(p['workingDirectory'],
                                         eng_file).as_posix()
                break

    return eng_file, eng_path_and_file


def get_engine_id_name_list(
    engine_config_file,
):
    """
    Read engine config file.

    :return: list of engine id names
    """
    eng_id_name_list = []
    with open(engine_config_file, 'r') as json_file:
        data = json.load(json_file)
        for p in data:
            if p['protocol'] == 'uci':
                eng_id_name_list.append(p['name'])

    eng_id_name_list = sorted(eng_id_name_list)

    return eng_id_name_list


def update_engine_to_config_file(
    eng_path_file,
    new_name,
    old_name,
    user_opt,
    engine_config_file,
):
    """
    Update engine config file based on params.

    :param eng_path_file: full path of engine
    :param new_name: new engine id name
    :param new_name: old engine id name
    :param user_opt: a list of dict, i.e d = ['a':a, 'b':b, ...]
    :return:
    """
    folder = Path(eng_path_file)
    folder = folder.parents[0]
    folder = Path(folder)
    folder = folder.as_posix()

    file = PurePath(eng_path_file)
    file = file.name

    with open(engine_config_file, 'r') as json_file:
        data = json.load(json_file)

    for p in data:
        command = p['command']
        work_dir = p['workingDirectory']

        if file == command and folder == work_dir and old_name == p['name']:
            p['name'] = new_name
            for k, v in p.items():
                if k == 'options':
                    for d in v:
                        # d = {'name': 'Ponder', 'default': False,
                        # 'value': False, 'type': 'check'}
                        
                        default_type = type(d['default'])
                        opt_name = d['name']
                        opt_value = d['value']
                        for u in user_opt:
                            # u = {'name': 'CDrill 1400'}
                            for k1, v1 in u.items():
                                if k1 == opt_name:
                                    v1 = int(v1) if default_type == int else v1
                                    if v1 != opt_value:
                                        d['value'] = v1
            break

    # Save data to pecg_engines.json
    with open(engine_config_file, 'w') as h:
        json.dump(data, h, indent=4)


def is_name_exists(
    name,
    engine_config_file,
):
    """

    :param name: The name to check in pecg.engines.json file.
    :return:
    """
    with open(engine_config_file, 'r') as json_file:
        data = json.load(json_file)

    for p in data:
        jname = p['name']
        if jname == name:
            return True

    return False


def update_user_config_file(
    username,
    user_config_file,
):
    """
    Update user config file. If username does not exist, save it.
    :param username:
    :return:
    """
    with open(user_config_file, 'r') as json_file:
        data = json.load(json_file)

    # Add the new entry if it does not exist
    is_name = False
    for i in range(len(data)):
        if data[i]['username'] == username:
            is_name = True
            break

    if not is_name:
        data.append({'username': username})

        # Save
        with open(user_config_file, 'w') as h:
            json.dump(data, h, indent=4)
