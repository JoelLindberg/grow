import sys

# Python 3.14+ compatibility patch for Django 5.1 BaseContext.__copy__.
# In Python 3.14, copy(super()) returns a super proxy object instead of
# delegating to the instance, causing an AttributeError during test client
# template context capture.
if sys.version_info >= (3, 14):
    from django.template.context import BaseContext

    def _basecontext_copy(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = _basecontext_copy
