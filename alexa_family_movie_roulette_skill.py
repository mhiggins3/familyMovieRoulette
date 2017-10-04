from __future__ import print_function
from ask_amy.core.reply import Reply
from ask_amy.state_mgr.stack_dialog_mgr import required_fields
from ask_amy.state_mgr.stack_dialog_mgr import StackDialogManager
from array import *
from boto3.dynamodb.conditions import Key, Attr
import boto3
import decimal
import json
import logging 
import random
import urllib
import urllib.request
from urllib.error import URLError
from urllib.parse import urlencode
import uuid

logger = logging.getLogger()
  
class AlexaFamilyMovieRouletteSkill(StackDialogManager):

    def launch_request(self):
        logger.debug("**************** entering {}.launch_request".format(self.__class__.__name__))
        self._intent_name = 'launch_request'
        return self.handle_default_intent()

    def new_session_started(self):
        logger.debug("**************** entering {}.new_session_started".format(self.__class__.__name__))

    @required_fields(['AddMovie'])
    def add_movie_intent(self):
        logger.debug("**************** entering {}.add_movie_intent".format(self.__class__.__name__))
        movie = MovieService.add_movie(self.request.attributes['AddMovie'], self.session.user_id)

        condition = 'add_movie_succeded'
        if movie['Response'] == 'False':
            condition = 'add_movie_failed'

        reply_dialog = self.reply_dialog[self.intent_name]['conditions'][condition]
        return Reply.build(reply_dialog, self.event)

    def find_movie_intent(self):
        logger.debug("**************** entering {}.find_movie_intent".format(self.__class__.__name__))
        session = self.session

        random_movie = MovieService.find_movie_for_user(self.session.user_id)
        condition = 'find_movie_failed'
        if random_movie:
            self.session.attributes['movie_title'] = random_movie['title']
            self.session.attributes['rating'] = random_movie['rated']
            self.session.attributes['description'] = random_movie['plot']
            condition = 'find_movie_succeded'

        logger.debug("**************** entering {}.find_movie_intent condition: {} ".format(self.intent_name, condition))
        logger.debug(self.reply_dialog['find_movie_intent'])
        reply_dialog = self.reply_dialog[self.intent_name]['conditions'][condition]
        return Reply.build(reply_dialog, self.event)

    def list_movies_intent(self):
        logger.debug("**************** entering {}.list_movie_intent".format(self.__class__.__name__))
        movies = MovieService.find_movies_for_user(self.session.user_id)
        condition = 'list_movies_failed'
        if(len(movies) > 0):
            condition = 'list_movies_succeded'
            movies_text = ""
            for movie in movies:
                movies_text += movie['Items'][0]['title'] + ". \n"
            self.session.attributes['movies'] = movies_text

        reply_dialog = self.reply_dialog[self.intent_name]['conditions'][condition]
        return Reply.build(reply_dialog, self.event)

    @required_fields(['RemoveMovie'])
    def remove_movie_intent(self):
        logger.debug("**************** entering {}.remove_movie_intent".format(self.__class__.__name__))
        logger.debug(self.session.user_id)

        status = MovieService.delete_movie_for_user(self.request.attributes['RemoveMovie'], self.session.user_id)
        condition = "remove_movie_failed"
        if(status == 'true'):
            condition = "remove_movie_failed"

        reply_dialog = self.reply_dialog[self.intent_name]['conditions'][condition]
        return Reply.build(reply_dialog, self.event)

    def play_movie_intent(self):
        logger.debug("**************** entering {}.play_movie_intent".format(self.__class__.__name__))

class MovieService(object):
    
    @staticmethod
    def add_movie(movie_title, user_id):
        movie = ImdbService.search_movie_title(movie_title)
        logger.debug("******************** userid:" + user_id)
        if(movie['Response'] == 'False'):
            return movie
        else:
            user_movies_table = boto3.resource('dynamodb').Table('UserMovies')
            result = user_movies_result = user_movies_table.scan(FilterExpression=Attr('userId').eq(user_id) & Attr('imdbId').eq(movie['imdbID']))
            if result['Count'] > 0:
                return movie
            
            return MovieService.add_movie_to_user_movies(movie, user_id)

    @staticmethod 
    def delete_movie_for_user(movie_title, user_id):
        movies_table = boto3.resource('dynamodb').Table('Movies')
        user_movies_table = boto3.resource('dynamodb').Table('UserMovies')
        user_movies_result = user_movies_table.scan(FilterExpression=Attr('userId').eq(user_id))
        for user_movie in user_movies_result['Items']:
            imdb_id = user_movie['imdbId']
            movie = movies_table.query(KeyConditionExpression=Key('imdbId').eq(imdb_id))
            if movie_title.lower() in movie['Items'][0]['title'].lower():
                user_movies_table.delete_item(Key={'uuid':user_movie['uuid']})
                return 'true'
        return 'false'

    @staticmethod 
    def find_movies_for_user(user_id):
        movies_table = boto3.resource('dynamodb').Table('Movies') 
        user_movies_table = boto3.resource('dynamodb').Table('UserMovies')
        logger.debug("**************** user_id: " + user_id)
        user_movies_result = user_movies_table.scan(FilterExpression=Attr('userId').eq(user_id))
        movies = []
        if user_movies_result['Count'] > 0:
            for user_movie in user_movies_result['Items']:
                imdb_id = user_movie['imdbId']
                movie = movies_table.query(KeyConditionExpression=Key('imdbId').eq(imdb_id))
                movies.append(movie)
        return movies

    @staticmethod 
    def find_movie_for_user(user_id):
        user_movies_table = boto3.resource('dynamodb').Table('UserMovies')
        movies_table = boto3.resource('dynamodb').Table('Movies')
        imdb_ids = user_movies_table.scan(FilterExpression=Attr('userId').eq(user_id))
        count = imdb_ids['Count']
        movie_list = imdb_ids['Items']

        if count == 0:
            return {}
        else:    
            logger.info(imdb_ids)
            logger.info(movie_list)
            user_movie = random.choice(movie_list)            
            imdb_id = user_movie['imdbId']
            movie = movies_table.query(KeyConditionExpression=Key('imdbId').eq(imdb_id))
            logger.info(movie['Items'][0])
            return movie['Items'][0]
   
    
    @staticmethod
    def add_movie_to_user_movies(movie, user_id):
        movies_table = boto3.resource('dynamodb').Table('Movies')
        movie_item = {
        'year': int(movie['Year']),
        'title': movie['Title'],
        'genre': movie['Genre'], 
        'plot': movie['Plot'], 
        'rated': movie['Rated'],  
        'imdbId': movie['imdbID'],
        'image': movie['Poster'],
        }
        movies_table.put_item(Item=movie_item)
        user_movies_table = boto3.resource('dynamodb').Table('UserMovies')
        user_movies_table.put_item(
            Item={
               'uuid': str(uuid.uuid4()),
               'imdbId': movie['imdbID'],
               'userId': user_id,
            }
        )
        movie_item['Response'] = 'True'
        return movie_item 

class ImdbService(object):
    BASE_URL = "http://www.omdbapi.com/" 
    API_KEY = "3efbd445"

    @staticmethod
    def search_movie_title(movie_title):
        query_params = {"apikey" : ImdbService.API_KEY, "t" : movie_title, "plot" : "short", "r" : "json"}
        movie = ImdbService._http_call(ImdbService.BASE_URL, query_params)
        if movie is None:
            movie['Response'] = "False"
        return movie;
   
    @staticmethod
    def _http_call(uri_path, query_params=None, ret_json=True):
        url = uri_path
        if query_params is not None:
            url += "?" + urlencode(query_params)

        try:
            request_url = urllib.request.Request(url)
            with urllib.request.urlopen(request_url) as response:
                data = response.read()
                encoding = response.info().get_content_charset('utf-8')
                ret_val = data.decode(encoding)
                if ret_json:
                    ret_val = json.loads(ret_val)
        except URLError as e:
            ret_val = None
            if hasattr(e, 'reason'):
                logger.critical('We failed to reach a server.')
                logger.critical('Reason: ', e.reason)
            elif hasattr(e, 'code'):
                logger.critical('The server couldn\'t fulfill the request.')
                logger.critical('Error code: ', e.code)
        return ret_val 
