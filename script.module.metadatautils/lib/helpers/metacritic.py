#!/usr/bin/python
# -*- coding: utf-8 -*-

'''get metadata from metacritic'''

from utils import get_json, formatted_number, int_with_commas, try_parse_int, KODI_LANGUAGE, ADDON_ID
from simplecache import use_cache
import arrow
import xbmc
import xbmcaddon



class Marcalencc(object):
    '''get metadata from marcalencc'''
    
    def __init__(self, *args):
        pass
    
    def get_details_by_title(self, title, media_type=""):
        ''' get marcalencc details by title
            title --> The title of the media to look for (required)
            media_type --> The type of the media: movie/tvshow (required)
        '''
        if "movie" in media_type:
            media_type = "movie"
        if "show" in media_type:
            media_type = "tvshow"
        params = {media_type, title}
        data = self.get_datacc(params)
        return self.map_detailscc(data)
        
    @staticmethod
    def get_datacc(params):
        '''helper method to get data from marcalencc json API'''
        data = get_json('http://api.marcalencc.com/metacritic/',params)
        if data:
            return data
        else:
            return {}

    @staticmethod
    def map_detailscc(data):
        '''helper method to map the details received from marcalencc to kodi compatible format'''
        result = {}
        for key, value in data.iteritems():
            #filter the N/A values
            if value == "N/A" or not value:
                continue
            if key == "Title":
                result["cc.title"] = value
            if key == "Director":
                result["cc.director"] = value
            if key == "ReleaseDate":
                result["cc.release"] = value
            if key == "CriticRating":
                result["criticrating"] = value
            if key == "CriticReviewCount":
                result["criticreviewcount"] = value
            if key == "UserRating":
                result["cc.userrating"] = value
            if key == "UserReviewCount":
                result["cc.userreviewcount"] = value
            elif key == "Studio": 
                result["cc.studio"] = value
        return result	