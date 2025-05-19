# Language native package
import abc


class BaseService(metaclass=abc.ABCMeta):
    """
    This module provides the necessary functionalities for service classes.
    """
    @abc.abstractmethod
    def raise_exception(self, status_code: int, detail: str):
        """
        An abstract method for handling exceptions that may occur within a service class.

        Args:
            status_code (int): An integer representing the HTTP status code.
            detail (str, optional): A string providing additional details about the exception.
        """
