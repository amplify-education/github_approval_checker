"""
Contains defintions for all custom exceptions raised.
"""


class ConfigError(Exception):
    """
    Indicates an error with the specified configuration file.
    """
    def __init__(self, message, response=({"status": "Config File Error"}, 500)):
        super(ConfigError, self).__init__(message)
        self.response = response


class APIError(Exception):
    """
    Indicates that the API encountered an error.
    """
    def __init__(self, message, response=({"status": "API Error"}, 500)):
        super(APIError, self).__init__(message)
        self.response = response


class SignatureError(Exception):
    """
    Indicates an error in the process of validating the request signature.
    """
    def __init__(self, message):
        super(SignatureError, self).__init__(message)
        self.response = ({
            'status': 'Signature Validation Error',
            'message': message
        }, 400)
