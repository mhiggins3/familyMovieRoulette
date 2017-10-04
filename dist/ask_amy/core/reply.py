import logging

from ask_amy.core.object_dictionary import ObjectDictionary
from ask_amy.core.directive import AudioPlayer

logger = logging.getLogger()


class Reply(ObjectDictionary):
    def __init__(self, card_dict=None):
        super().__init__(card_dict)

    @classmethod
    def constr(cls, response, session_attributes=None):
        logger.debug("**************** entering Reply.constr")
        reply = {'version': '1.0'}
        if session_attributes is not None:
            reply['sessionAttributes'] = session_attributes
        reply['response'] = response.json()
        return cls(reply)

    @staticmethod
    def build(dialog_dict, event=None):
        logger.debug("**************** entering Reply.build")
        prompt = None
        reprompt = None
        card = None

        if 'speech_out_ssml' in dialog_dict:
            prompt = Prompt.ssml(dialog_dict['speech_out_ssml'], event)
        if 're_prompt_ssml' in dialog_dict:
            reprompt = Prompt.ssml(dialog_dict['re_prompt_ssml'], event)
        # Note speech_out_text will take precedence over speech_out_ssml
        if 'speech_out_text' in dialog_dict:
            prompt = Prompt.text(dialog_dict['speech_out_text'], event)
        if 're_prompt_text' in dialog_dict:
            reprompt = Prompt.text(dialog_dict['re_prompt_text'], event)
        if 'should_end_session' in dialog_dict:
            should_end_session = dialog_dict['should_end_session']
        else:
            should_end_session = True
        if 'card_title' in dialog_dict:
            card = Card.simple(dialog_dict['card_title'], dialog_dict['speech_out_text'], event)

        if 'card' in dialog_dict:
            card_dict = dialog_dict['card']
            if 'small_image' in card_dict:
                card = Card.standard(card_dict['title'], card_dict['content'], card_dict['small_image'],
                                     card_dict['large_image'], event)
            elif 'type' in card_dict:

                card = Card.link_account(None, None)
            else:
                card = Card.simple(card_dict['title'], card_dict['content'], event)

        response = Response.constr(prompt, reprompt, card, should_end_session)

        attributes = {}
        if event is not None:
            if event.session is not None:
                attributes = event.session.attributes

        reply = Reply.constr(response, attributes)
        return reply.json()

    @staticmethod
    def build_audio(dialog_dict, event=None):
        logger.debug("**************** entering Reply.build")
        prompt = None
        card = None
        command = event.request.attributes['command']
        if command == 'play':
            url = event.session.attributes['active_url']
            offset = event.session.attributes['offset']
            audio_player = AudioPlayer.play(url, offset)
        else:  # command must be stop
            audio_player = AudioPlayer.stop()

        response = Response.audio_play(audio_player, prompt, card)

        attributes = {}
        if event is not None:
            if event.session is not None:
                attributes = event.session.attributes

        reply = Reply.constr(response, attributes)
        return reply.json()


class Response(ObjectDictionary):
    def __init__(self, card_dict=None):
        super().__init__(card_dict)

    @classmethod
    def constr(cls, out_speech, reprompt=None, card=None, should_end_session=True):
        logger.debug("**************** entering Response.constr")
        response = {}
        if out_speech is not None:
            response['outputSpeech'] = out_speech.json()
        if reprompt is not None:
            output_speech = {'outputSpeech': reprompt.json()}
            response['reprompt'] = output_speech
        if card is not None:
            response['card'] = card.json()
        if should_end_session is not None:
            response['shouldEndSession'] = should_end_session
        return cls(response)

    @classmethod
    def audio_play(cls, audio_player, out_speech=None, card=None):
        logger.debug("**************** entering Response.audio_play")
        response = {}
        if out_speech is not None:
            response['outputSpeech'] = out_speech.json()

        if card is not None:
            response['card'] = card.json()

        response['directives'] = []
        response['directives'].append(audio_player.json())
        response['shouldEndSession'] = True
        return cls(response)

    @classmethod
    def audio_stop(cls, audio_stop, out_speech=None, card=None):
        logger.debug("**************** entering Response.audio_play")
        response = {}
        if out_speech is not None:
            response['outputSpeech'] = out_speech.json()

        if card is not None:
            response['card'] = card.json()

        response['directives'] = []
        response['directives'].append(audio_stop.json())
        response['shouldEndSession'] = True
        return cls(response)


class CommunicationChannel(ObjectDictionary):
    def __init__(self, card_dict=None):
        super().__init__(card_dict)

    @staticmethod
    def concat_text_if_list(text_obj):
        logger.debug("**************** entering OutText.concat_text_if_list")
        text_str = ''
        if type(text_obj) is str:
            text_str = text_obj
        elif type(text_obj) is list:
            for text_line in text_obj:
                text_str += text_line
        return text_str

    @staticmethod
    def inject_event_data(text, event):
        logger.debug("**************** entering OutText.inject_session_data")
        if text is None:
            return text
        out_list = []
        indx = 0
        # len_text = len(text)
        done = False
        while not done:
            start_token_index = text.find("{")
            if start_token_index == -1:
                out_list.append(text)
                done = True
            else:
                end_token_index = text.find("}")
                fragment = text[indx:start_token_index]
                token = text[start_token_index + 1:end_token_index]
                text = text[end_token_index + 1:len(text)]
                if fragment != '':
                    out_list.append(fragment)
                out_list.append(CommunicationChannel.process_token(token, event))
                if text.find("{") == -1:
                    if text != '':
                        out_list.append(text)
                    done = True
        return "".join(out_list)

    @staticmethod
    def process_token(token, event):
        logger.debug("**************** entering OutText.process_token")
        if event.request.attribute_exists(token):
            value = event.request.attributes[token]
        elif event.session.attribute_exists(token):
            value = event.session.attributes[token]
        else:
            value = ''
        return str(value)


class Prompt(CommunicationChannel):
    def __init__(self, card_dict=None):
        super().__init__(card_dict)

    @classmethod
    def ssml(cls, ssml, event=None):
        logger.debug("**************** entering Prompt.ssml")
        ssml = Prompt.concat_text_if_list(ssml)
        if event is not None:
            ssml = Prompt.inject_event_data(ssml, event)
        prompt = {'type': 'SSML', 'ssml': "<speak>{}</speak>".format(ssml)}
        return cls(prompt)

    @classmethod
    def text(cls, text, event=None):
        logger.debug("**************** entering Prompt.text")
        text = Prompt.concat_text_if_list(text)
        if event is not None:
            text = Prompt.inject_event_data(text, event)
        prompt = {'type': 'PlainText', 'text': text}
        return cls(prompt)


class Card(CommunicationChannel):
    def __init__(self, card_dict=None):
        super().__init__(card_dict)

    @classmethod
    def simple(cls, title, content, event=None):
        logger.debug("**************** entering Card.simple")
        content = Card.concat_text_if_list(content)
        if event is not None:
            content = Card.inject_event_data(content, event)
            title = Card.inject_event_data(title, event)
        card = {'type': 'Simple', 'title': title, 'content': content}
        return cls(card)

    @classmethod
    def standard(cls, title, content, small_image_url, large_image_url, event=None):
        logger.debug("**************** entering Card.standard")
        content = Card.concat_text_if_list(content)
        if event is not None:
            content = Card.inject_event_data(content, event)
            title = Card.inject_event_data(title, event)
        card = {'type': 'Standard', 'title': title, 'text': content}
        image = {}
        card['image'] = image
        image['smallImageUrl'] = small_image_url  # 720w x 480h pixels
        image['largeImageUrl'] = large_image_url  # 1200w x 800h pixels
        return cls(card)

    @classmethod
    def link_account(cls, title, content, event=None):
        logger.debug("**************** entering Card.link_account")
        content = Card.concat_text_if_list(content)
        if event is not None:
            content = Card.inject_event_data(content, event)
        card = {'type': 'LinkAccount'}
        return cls(card)
