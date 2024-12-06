import psycopg2
from psycopg2.extras import RealDictCursor

class BusinessDatabase:
    def __init__(self, db_name, user, password, host='localhost', port=5432):
        self.connection = psycopg2.connect(
            dbname=db_name, user=user, password=password, host=host, port=port
        )
        self.connection.autocommit = True
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)

    def fetch_one(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetch_all(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def execute(self, query, params=None):
        self.cursor.execute(query, params)