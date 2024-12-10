# import psycopg2
# from psycopg2.extras import RealDictCursor

# class Database:
#     def __init__(self, db_name, user, password, host='localhost', port=5432):
#         self.connection = psycopg2.connect(
#             dbname=db_name, user=user, password=password, host=host, port=port
#         )
#         self.connection.autocommit = True
#         self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)

#     def fetch_one(self, query, params=None):
#         self.cursor.execute(query, params)
#         return self.cursor.fetchone()

#     def fetch_all(self, query, params=None):
#         self.cursor.execute(query, params)
#         return self.cursor.fetchall()

#     def execute(self, query, params=None):
#         self.cursor.execute(query, params)

import psycopg2
from psycopg2.extras import RealDictCursor

class Database:
    def __init__(self, db_name, user, password, host='localhost', port=5432):
        """
        Initialize the database connection.
        """
        self.connection = psycopg2.connect(
            dbname=db_name, user=user, password=password, host=host, port=port
        )
        self.connection.autocommit = True
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)

    def fetch_one(self, query, params=None):
        """
        Execute a query and fetch a single result.
        """
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetch_all(self, query, params=None):
        """
        Execute a query and fetch all results.
        """
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def execute(self, query, params=None):
        """
        Execute a query that modifies the database (e.g., INSERT, UPDATE, DELETE).
        """
        self.cursor.execute(query, params)

    def close(self):
        """
        Close the database connection.
        """
        self.cursor.close()
        self.connection.close()
