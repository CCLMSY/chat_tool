class AIChatClientException(Exception):
    """Base exception for AI Chat Client"""
    pass

class APIException(AIChatClientException):
    """Raised when there's an API-related error"""
    pass

class AuthException(AIChatClientException):
    """Raised when there's an authentication error"""
    pass