import xbmc
import xbmcgui
import resources.lib.addon.cache as cache
from resources.lib.addon.plugin import ADDONPATH, ADDON, PLUGINPATH, convert_type
from resources.lib.addon.parser import try_decode, urlencode_params
from resources.lib.addon.setutils import merge_two_dicts


class SearchLists():
    def list_searchdir_router(self, tmdb_type, **kwargs):
        if kwargs.get('clear_cache') != 'True':
            return self.list_searchdir(tmdb_type, **kwargs)
        cache.set_search_history(tmdb_type, clear_cache=True)
        self.container_refresh = True

    def list_searchdir(self, tmdb_type, **kwargs):
        base_item = {
            'label': u'{} {}'.format(xbmc.getLocalizedString(137), convert_type(tmdb_type, 'plural')),
            'art': {'thumb': '{}/resources/icons/tmdb/search.png'.format(ADDONPATH)},
            'infoproperties': {'specialsort': 'top'},
            'params': merge_two_dicts(kwargs, {'info': 'search', 'tmdb_type': tmdb_type})}
        items = []
        items.append(base_item)

        history = cache.get_search_history(tmdb_type)
        history.reverse()
        for i in history:
            item = {
                'label': i,
                'art': base_item.get('art'),
                'params': merge_two_dicts(base_item.get('params', {}), {'query': i})}
            items.append(item)
        if history:
            item = {
                'label': ADDON.getLocalizedString(32121),
                'art': base_item.get('art'),
                'params': merge_two_dicts(base_item.get('params', {}), {'info': 'dir_search', 'clear_cache': 'True'})}
            items.append(item)
        return items

    def list_search(self, tmdb_type, query=None, update_listing=False, page=None, **kwargs):
        original_query = query
        query = query or cache.set_search_history(
            query=try_decode(xbmcgui.Dialog().input(ADDON.getLocalizedString(32044), type=xbmcgui.INPUT_ALPHANUM)),
            tmdb_type=tmdb_type)

        if not query:
            return

        items = self.tmdb_api.get_search_list(
            tmdb_type=tmdb_type, query=query, page=page,
            year=kwargs.get('year'),
            first_air_date_year=kwargs.get('first_air_date_year'),
            primary_release_year=kwargs.get('primary_release_year'))

        if not original_query:
            params = merge_two_dicts(kwargs, {
                'info': 'search', 'tmdb_type': tmdb_type, 'page': page, 'query': query,
                'update_listing': 'True'})
            self.container_update = '{}?{}'.format(PLUGINPATH, urlencode_params(**params))
            # Trigger container update using new path with query after adding items
            # Prevents onback from re-prompting for user input by re-writing path

        self.update_listing = True if update_listing else False
        self.container_content = convert_type(tmdb_type, 'container')
        self.kodi_db = self.get_kodi_database(tmdb_type)

        return items