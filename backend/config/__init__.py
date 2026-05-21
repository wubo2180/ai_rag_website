# Prefer mysqlclient when available; fall back to PyMySQL on hosts without MySQL dev libraries.
try:
    import MySQLdb  # noqa: F401
except ImportError:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass
