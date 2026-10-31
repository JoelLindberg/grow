import sys

# Register PyMySQL as MySQLdb if the compiled C-extension (mysqlclient) is not installed.
# This allows connecting to MariaDB 11.4 without requiring C build tools on macOS or restricted hosts.
try:
    import MySQLdb  # noqa: F401
except ImportError:
    try:
        import pymysql

        pymysql.version_info = (2, 2, 4, "final", 0)
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass

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
