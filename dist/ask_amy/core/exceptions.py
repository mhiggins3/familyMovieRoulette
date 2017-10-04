"""
Global exception and warning classes.
"""


class ASKAmyError(Exception):
    """ Common base class for all ASK Amy exceptions."""


class ApplicationIdError(ASKAmyError):
    """The application id provided does not match application id for this skill"""


class IntentControlError(ASKAmyError):
    """The Intent Name does not map to an Intent in the IntentControl section for this skill"""


class DialogIntentError(ASKAmyError):
    """The Method Name does not map to an Intent in the Dialog section for this skill"""


class SkillLoadError(ASKAmyError):
    """Unable to load, bootstrap and execute the skill """


class SlotValidatorLoadError(ASKAmyError):
    """Unable to load, a custom defined type"""


class FileExistsError(ASKAmyError):
    """Code Generator is attempting to write to a file that already exists """


class SessionError(ASKAmyError):
    """Error in session """
