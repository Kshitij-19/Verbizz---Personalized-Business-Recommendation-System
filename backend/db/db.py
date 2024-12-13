import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import OperationalError, Error


class Database:
    def __init__(self, db_name, user, password, host, port):
        self.connection = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.connection.autocommit = True
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)

    def fetch_one(self, query, params=None):
        """
        Execute a query and fetch a single result.
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error executing query: {e}")
            return None

    def fetch_all(self, query, params=None):
        """
        Execute a query and fetch all results.
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error executing query: {e}")
            return None

    def execute(self, query, params=None):
        """
        Execute a query that modifies the database (e.g., INSERT, UPDATE, DELETE).
        """
        try:
            self.cursor.execute(query, params)
            print("Query executed successfully.")
        except Error as e:
            print(f"Error executing query: {e}")
            return None

    # def close(self):
    #     """
    #     Close the database connection.
    #     """
    #     try:
    #         if self.cursor:
    #             self.cursor.close()
    #         if self.connection:
    #             self.connection.close()
    #         print("Database connection closed.")
    #     except Error as e:
    #         print(f"Error closing database connection: {e}")

    def close(self):
        """
        Close the database connection.
        """
        try:
            if self.cursor:
                self.cursor.close()
        except Error as e:
            print(f"Error closing cursor: {e}")

        try:
            if self.connection:
                self.connection.close()
        except Error as e:
            print(f"Error closing database connection: {e}")