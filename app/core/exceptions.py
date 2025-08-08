# app/core/exceptions.py
"""Custom exceptions"""

class RBACException(Exception):
    """Base exception for RBAC system"""
    pass

class LLMException(RBACException):
    """Exception for LLM-related errors"""
    pass

class DataProcessingException(RBACException):
    """Exception for data processing errors"""
    pass

class FileHandlingException(RBACException):
    """Exception for file handling errors"""
    pass