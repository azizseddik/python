import pymysql

pymysql.install_as_MySQLdb()

# Django 4.x requires mysqlclient >= 2.2.1.
# PyMySQL reports itself as 1.4.6, so we spoof the version string.
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__  = "2.2.1"
