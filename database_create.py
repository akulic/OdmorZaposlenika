from PyQt5 import QtSql

dbase_name = 'odmorzap.db'


def create_connection():
    dbase = QtSql.QSqlDatabase.addDatabase('QSQLITE')
    dbase.setDatabaseName(dbase_name)
    if not dbase.open():
        raise Exception(dbase.lastError().text())
    if not dbase.tables():
        query = QtSql.QSqlQuery()
        zap, odmor = query_create_table()
        if not query.exec_(zap) or not query.exec_(odmor):
            raise Exception(dbase.lastError().text())
    query = QtSql.QSqlQuery()
    if not query.exec_('PRAGMA foreign_keys = ON'):
        raise Exception(dbase.lastError().text())
    return True


def query_create_table():
    return (
        """
        CREATE TABLE IF NOT EXISTS zaposlenici(
            rb      INTEGER PRIMARY KEY,
            ime     TEXT NOT NULL,
            prezime TEXT NOT NULL,
        );""", """
        CREATE TABLE IF NOT EXISTS odmor(
            rb            INTEGER PRIMARY KEY,
            zaposlenik_rb INTEGER NOT NULL,
            datum         TEXT    NOT NULL,
            godina        INTEGER NOT NULL,
            napomena      TEXT,
            FOREIGN KEY (zaposlenik_rb) REFERENCES zaposlenici (rb)
            ON DELETE CASCADE ON UPDATE CASCADE,
            UNIQUE(zaposlenik_rb, datum)
        );""", """
        CREATE TABLE IF NOT EXISTS ukupno_dana(
            rb              INTEGER PRIMARY KEY,
            zaposlenik_rb   INTEGER NOT NULL,
            godina          INTEGER NOT NULL,
            br_dana         INTEGER NOT NULL,
            FOREIGN KEY (zaposlenik_rb) REFERENCES zaposlenici (rb)
            ON DELETE CASCADE ON UPDATE CASCADE,
            UNIQUE (zaposlenik_rb, godina)
        );"""
    )
