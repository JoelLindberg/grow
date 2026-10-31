-- Allow the application database user to create and drop test databases
-- when running `python manage.py test` against local MariaDB.
GRANT ALL PRIVILEGES ON `test_%`.* TO 'grow'@'%';
FLUSH PRIVILEGES;

