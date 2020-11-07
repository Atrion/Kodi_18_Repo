import re
import os
import sys
import xbmc
import json
import xbmcgui
import xbmcvfs
import datetime
import unicodedata
from resources.lib.addon.parser import try_int, try_encode
from resources.lib.addon.plugin import ADDON, ADDONDATA, kodi_log
from resources.lib.addon.constants import VALID_FILECHARS
from resources.lib.addon.timedate import is_future_timestamp
try:
    import cPickle as _pickle
except ImportError:
    import pickle as _pickle  # Newer versions of Py3 just use pickle
if sys.version_info[0] >= 3:
    unicode = str  # In Py3 str is now unicode


def validify_filename(filename):
    try:
        filename = unicode(filename, 'utf-8')
    except NameError:  # unicode is a default on python 3
        pass
    except TypeError:  # already unicode
        pass
    filename = str(unicodedata.normalize('NFD', filename).encode('ascii', 'ignore').decode("utf-8"))
    filename = ''.join(c for c in filename if c in VALID_FILECHARS)
    filename = filename[:-1] if filename.endswith('.') else filename
    return filename


def normalise_filesize(filesize):
    filesize = try_int(filesize)
    i_flt = 1024.0
    i_str = ['B', 'KB', 'MB', 'GB', 'TB']
    for i in i_str:
        if filesize < i_flt:
            return '{:.2f} {}'.format(filesize, i)
        filesize = filesize / i_flt
    return '{:.2f} {}'.format(filesize, 'PB')


def get_files_in_folder(folder, regex):
    return [x for x in xbmcvfs.listdir(folder)[1] if re.match(regex, x)]


def read_file(filepath):
    vfs_file = xbmcvfs.File(filepath)
    content = ''
    try:
        content = vfs_file.read()
    finally:
        vfs_file.close()
    return content


def write_to_file(filepath, content):
    f = xbmcvfs.File(filepath, 'w')
    f.write(try_encode(content))
    f.close()


def get_tmdb_id_nfo(basedir, foldername, tmdb_type='tv'):
    try:
        folder = basedir + foldername + '/'

        # Get files ending with .nfo in folder
        nfo_list = get_files_in_folder(folder, regex=r".*\.nfo$")

        # Check our nfo files for TMDb ID
        for nfo in nfo_list:
            content = read_file(folder + nfo)  # Get contents of .nfo file
            tmdb_id = content.replace('https://www.themoviedb.org/{}/'.format(tmdb_type), '')  # Clean content to retrieve tmdb_id
            tmdb_id = tmdb_id.replace('&islocal=True', '')
            if tmdb_id:
                return tmdb_id

    except Exception as exc:
        kodi_log(u'ERROR GETTING TMDBID FROM NFO:\n{}'.format(exc))


def delete_file(folder, filename, join_addon_data=True):
    fullpath = os.path.join(_get_write_path(folder, join_addon_data), filename)
    xbmcvfs.delete(fullpath)


def dumps_to_file(data, folder, filename, indent=2, join_addon_data=True):
    with open(os.path.join(_get_write_path(folder, join_addon_data), filename), 'w') as file:
        json.dump(data, file, indent=indent)


def _get_write_path(folder, join_addon_data=True):
    main_dir = os.path.join(xbmc.translatePath(ADDONDATA), folder) if join_addon_data else xbmc.translatePath(folder)
    if not os.path.exists(main_dir):
        os.makedirs(main_dir)
    return main_dir


def make_path(path, warn_dialog=False):
    if xbmcvfs.exists(path):
        return xbmc.translatePath(path)
    if xbmcvfs.mkdirs(path):
        return xbmc.translatePath(path)
    if ADDON.getSettingBool('ignore_folderchecking'):
        kodi_log(u'Ignored xbmcvfs folder check error\n{}'.format(path), 2)
        return xbmc.translatePath(path)
    kodi_log(u'XBMCVFS unable to create path:\n{}'.format(path), 2)
    if not warn_dialog:
        return
    xbmcgui.Dialog().ok(
        'XBMCVFS', '{} [B]{}[/B]\n{}'.format(
            ADDON.getLocalizedString(32122), path, ADDON.getLocalizedString(32123)))


def get_pickle_name(cache_name):
    cache_name = cache_name or ''
    cache_name = cache_name.replace('\\', '_').replace('/', '_').replace('.', '_').replace('?', '_').replace('&', '_').replace('=', '_').replace('__', '_')
    return validify_filename(cache_name).rstrip('_')


def set_pickle(my_object, cache_name, cache_days=14):
    if not my_object:
        return
    cache_name = get_pickle_name(cache_name)
    if not cache_name:
        return
    timestamp = datetime.datetime.now() + datetime.timedelta(days=cache_days)
    cache_obj = {'my_object': my_object, 'expires': timestamp.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(os.path.join(_get_write_path('pickle'), cache_name), 'wb') as file:
        _pickle.dump(cache_obj, file)
    return my_object


def get_pickle(cache_name):
    cache_name = get_pickle_name(cache_name)
    if not cache_name:
        return
    try:
        with open(os.path.join(_get_write_path('pickle'), cache_name), 'rb') as file:
            cache_obj = _pickle.load(file)
    except IOError:
        cache_obj = None
    if cache_obj and is_future_timestamp(cache_obj.get('expires', '')):
        return cache_obj.get('my_object')


def use_pickle(func, *args, **kwargs):
    """
    Simplecache takes func with args and kwargs
    Returns the cached item if it exists otherwise does the function
    """
    cache_name = kwargs.pop('cache_name', '')
    cache_only = kwargs.pop('cache_only', False)
    cache_refresh = kwargs.pop('cache_refresh', False)
    my_object = get_pickle(cache_name) if not cache_refresh else None
    if my_object:
        return my_object
    elif not cache_only:
        my_object = func(*args, **kwargs)
        return set_pickle(my_object, cache_name)
