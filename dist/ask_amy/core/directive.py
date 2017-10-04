import logging
from ask_amy.core.object_dictionary import ObjectDictionary

logger = logging.getLogger()


class AudioPlayer(ObjectDictionary):
    def __init__(self, audio_dict=None):
        super().__init__(audio_dict)

    @classmethod
    def play(cls, url, offset_in_milliseconds=0,  token="0", expected_previous_token=None):
        behaviors = ["REPLACE_ALL", "ENQUEUE", "REPLACE_ENQUEUED"]
        logger.debug("**************** entering AudioPlayer.play")

        directive = {
            "type": "AudioPlayer.Play",
            "playBehavior": "REPLACE_ALL",
            "audioItem": {
                "stream": {
                    "url": url,
                    "token": token,
                    "offsetInMilliseconds": offset_in_milliseconds
                }
            }
        }
        #if play_behavior == 'ENQUEUE':
        #    directive["audioItem"]["stream"]["expectedPreviousToken"] = expected_previous_token
        logger.debug("XXXXXX {}".format(directive))
        return cls(directive)

    @classmethod
    def stop(cls):
        logger.debug("**************** entering AudioPlayer.stop")
        directive = {"type": "AudioPlayer.Stop"}
        return cls(directive)

    @classmethod
    def clear_queue(cls, clear_behavior):
        behaviors = ['CLEAR_ENQUEUED', 'CLEAR_ALL']
        logger.debug("**************** entering AudioPlayer.clear_queue")
        directive = {"type": "AudioPlayer.ClearQueue", "clearBehavior": clear_behavior}
        return cls(directive)
