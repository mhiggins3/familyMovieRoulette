"""
Fun little skill that allows you to create a small moive DB for picking random 
movies when your kids can't decide what to watch.

"""

from __future__ import print_function
from array import *
import random
import uuid
import boto3
import json
import urllib2
import urllib
import decimal
import logging
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title':  title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


def get_random_movie(session):
        user_movies_table = boto3.resource('dynamodb').Table('UserMovies')
        movies_table = boto3.resource('dynamodb').Table('Movies')
        imdb_ids = user_movies_table.scan(FilterExpression=Attr('userId').eq(session['user']['userId']))
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

def add_movie_to_user_movies(session, movie):
    movies_table = boto3.resource('dynamodb').Table('Movies')
    year = int(movie['Year'])
    title = movie['Title']
    genre = movie['Genre']
    plot = movie['Plot']
    rated = movie['Rated']
    imdbID = movie['imdbID']
    image = movie['Poster']
    movies_table.put_item(
       Item={
           'imdbId': imdbID,
           'year': year,
           'title': title,
           'genre': genre,
           'plot': plot,
           'rated': rated,
           'image': image,
        }
    )
    user_movies_table = boto3.resource('dynamodb').Table('UserMovies') 
    user_movies_table.put_item(
        Item={
           'uuid': str(uuid.uuid4()),
           'imdbId': imdbID,
           'userId': session['user']['userId'], 
        } 
    )
    
def get_movie_title(intent, session):
    random_movie = get_random_movie(session)
    should_end_session = True
    if random_movie: 
        speech_output = "How about you check out " + random_movie['title'] + \
                        ". It's rated " + random_movie['rated'] + \
                        ". here is a quick description. " + random_movie['plot'] + \
                        ". "
    else:
        should_end_session = False
        speech_output = "I could not find any movies in your data base " + \
                        ". Try adding a new movie by saying add the movie Goonies" + \
                        ". "

    session_attributes = {}
    reprompt_text = None

    return build_response(session_attributes, build_speechlet_response(
        "Find a movie", speech_output, reprompt_text, should_end_session))

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to family movie roulette. " \
                    "I can tell you a ramdom movie to watch by saying, " \
                    "what movie should I watch?, " \
                    "or say add the movie Goonies"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Say what movie should I watch, " \
                    "or say add the movie Goonies"
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_help_response():

    session_attributes = {}
    card_title = "Help"
    speech_output = "Welcome to family movie roulette. " \
                    "I can tell you a ramdom movie to watch by saying, " \
                    "what movie should I watch?, " \
                    "You can add a movie by saying " \
                    "add the movie Goonies. " \
                    "You can also delete an existing movie by saying, " \
                    "Delete the movive Goonies."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Say what movie should I watch, " \
                    "or say add the movie Goonies"
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thanks for looking up a move. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def add_movie(intent, session):
    """ Adds a move to the DB 
    """

    card_title = "Add a movie"
    session_attributes = {}
    should_end_session = False

    if 'Movie' in intent['slots']:
        if 'value' in intent['slots']['Movie']:
            movie_title = intent['slots']['Movie']['value']
        else:
            speech_output = "I didn't hear what movie you wanted to add." \
                            "Please try again."
            reprompt_text = "I'm not sure what movie you wanted me to add. " \
                            "You can add a movie by saying, " \
                            "add the movie Goonies."
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))
    
        encoded_movie_title = urllib.urlencode({"apikey" : "3efbd445", "t" : movie_title, "plot" : "short", "r" : "json"})
        url = "http://www.omdbapi.com/?" + encoded_movie_title
        logger.info(url)
        response = urllib2.urlopen(url);
        movie = json.load(response, parse_float = decimal.Decimal)
        if(movie['Response'] == 'False'):
            speech_output = "I could not find a movie with the title " + \
                        movie_title + \
                        ". Please try again. " 
                    
            reprompt_text = None
            return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        else:
            add_movie_to_user_movies(session, movie) 

            session_attributes = {}
            speech_output = "Ok I will add the movie " + \
                            movie_title + \
                            ". You can hear a random movie title by saying, " \
                            "what movie should I watch?"
            reprompt_text = "You can hear a random movie title by saying, " \
                            "what movie should I watch?"
    else:
        speech_output = "I didn't hear what movie you wanted to add." \
                        "Please try again."
        reprompt_text = "I'm not sure what movie you wanted me to add. " \
                        "You can add a movie by saying, " \
                        "add the movie Goonies."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def remove_movie(intent, session):
    
    card_title = "Removing Movie"
    session_attributes = {}
    should_end_session = False
    
    if 'Movie' in intent['slots']:
        if 'value' in intent['slots']['Movie']:
            movie_title = intent['slots']['Movie']['value']
        else:
            speech_output = "I didn't hear what movie you wanted to remove. " \
                            "Please try again."
            reprompt_text = "I'm not sure what movie you wanted me to remove. " \
                            "You can delete a movie by saying, " \
                            "remove the movie Goonies."
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))
        movies_table = boto3.resource('dynamodb').Table('Movies')
        user_movies_table = boto3.resource('dynamodb').Table('UserMovies') 

        user_movies_result = user_movies_table.scan(FilterExpression=Attr('userId').eq(session['user']['userId']))
        for user_movie in user_movies_result['Items']:
            imdb_id = user_movie['imdbId']
            movie = movies_table.query(KeyConditionExpression=Key('imdbId').eq(imdb_id))

            logger.info(movie)
            if movie_title.lower() in movie['Items'][0]['title'].lower():
                user_movies_table.delete_item(Key={'uuid':user_movie['uuid']})
                speech_output = "Ok I deleted the movie " + movie_title + \
                                " from your list. You can hear a random movie title by saying, " \
                            "what movie should I watch? "
                reprompt_text = "Ok I deleted the movie " + movie_title + \
                                " from your list. You can hear a random movie title by saying, " \
                            "what movie should I watch? "
                return build_response(session_attributes, build_speechlet_response(
                    card_title, speech_output, reprompt_text, should_end_session))
        
        speech_output = "I could not find the movie " + movie_title + \
                                " in your list. Please try again."
        reprompt_text = "I could not find the movie " + movie_title + \
                                " in your list.  Please try again."
                                
        return build_response(session_attributes, build_speechlet_response(
                    card_title, speech_output, reprompt_text, should_end_session))
    else:
        speech_output = "I didn't hear what movie you wanted to remove." \
                        "Please try again."
        reprompt_text = "I'm not sure what movie you wanted me to remove. " \
                        "You can remove a movie by saying, " \
                        "remove the movie Goonies."
        
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def list_movies(intent, session):
    card_title = "List Movies"
    session_attributes = {}
    should_end_session = True
    reprompt_text = None
    speech_output = ""
    movies_table = boto3.resource('dynamodb').Table('Movies')
    user_movies_table = boto3.resource('dynamodb').Table('UserMovies') 
    user_movies_result = user_movies_table.scan(FilterExpression=Attr('userId').eq(session['user']['userId']))
    if user_movies_result['Count'] == 0:
        should_end_session = False
        speech_output = "You do not have any movies saved yet. To add a movie you can say " \
                        "add the movie Goonies. "
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
        
    speech_output = "You have the following movies in your list. \n" 
    for user_movie in user_movies_result['Items']:
        imdb_id = user_movie['imdbId']
        movie = movies_table.query(KeyConditionExpression=Key('imdbId').eq(imdb_id))
        speech_output += movie['Items'][0]['title'] + ". \n"  
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    logger.info(json.dumps(session))
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'] + ", intent_name=" + intent_name)
    # Dispatch to your skill's intent handlers
    if intent_name == "AddMovieIntent":
        return add_movie(intent, session)
    elif intent_name == "FindMovieIntent":
        return get_movie_title(intent, session)
    elif intent_name == "RemoveMovieIntent":
        return remove_movie(intent, session)
    elif intent_name == "ListMoviesIntent":
        return list_movies(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent " + intent_name)


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    should_end_session = True
    session_attributes = {}
    reprompt_text = None
    speech_output = "Thank you for playing family movie roulette"
    return build_response(session_attributes, build_speechlet_response(
        "AMAZON.CancelIntent", speech_output, reprompt_text, should_end_session))


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
    else:
        raise ValueError("Invalid intent ")

