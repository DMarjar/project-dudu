# SonarQube/SonarCloud ignore start
class HttpStatusCodeError(Exception):
    """ Custom exception to handle HTTP status code errors

    Args:
        status_code (int): HTTP status code
        message (str): Error message

    Attributes:
        status_code (int): HTTP status code
        message (str): Error message
    """

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

# SonarQube/SonarCloud ignore end