import unittest
from unittest.mock import MagicMock, patch
from db.db import Database
from psycopg2 import OperationalError

class TestDatabase(unittest.TestCase):

    @patch("psycopg2.connect")
    def setUp(self, mock_connect):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor
        mock_connect.return_value = self.mock_connection

        self.db = Database(
            db_name="test_db",
            user="test_user",
            password="test_pass",
            host="localhost",
            port=5432
        )

    def test_fetch_one_success(self):
        # Mock the cursor's behavior
        self.mock_cursor.fetchone.return_value = {"id": 1, "name": "Test"}

        query = "SELECT * FROM test_table WHERE id = %s"
        params = (1,)
        result = self.db.fetch_one(query, params)

        # Assertions
        self.mock_cursor.execute.assert_called_once_with(query, params)
        self.assertEqual(result, {"id": 1, "name": "Test"})

    def test_fetch_one_failure(self):
        # Mock the cursor's behavior to throw an error
        self.mock_cursor.execute.side_effect = OperationalError("Query failed")

        query = "SELECT * FROM test_table WHERE id = %s"
        params = (1,)
        result = self.db.fetch_one(query, params)

        # Assertions
        self.mock_cursor.execute.assert_called_once_with(query, params)
        self.assertIsNone(result)

    def test_fetch_all_success(self):
        # Mock the cursor's behavior
        self.mock_cursor.fetchall.return_value = [
            {"id": 1, "name": "Test1"},
            {"id": 2, "name": "Test2"}
        ]

        query = "SELECT * FROM test_table"
        result = self.db.fetch_all(query)

        # Assertions
        self.mock_cursor.execute.assert_called_once_with(query, None)
        self.assertEqual(result, [
            {"id": 1, "name": "Test1"},
            {"id": 2, "name": "Test2"}
        ])

    def test_fetch_all_failure(self):
        # Mock the cursor's behavior to throw an error
        self.mock_cursor.execute.side_effect = OperationalError("Query failed")

        query = "SELECT * FROM test_table"
        result = self.db.fetch_all(query)

        # Assertions
        self.mock_cursor.execute.assert_called_once_with(query, None)
        self.assertIsNone(result)

    def test_execute_success(self):
        # Mock the cursor's behavior
        query = "INSERT INTO test_table (name) VALUES (%s)"
        params = ("Test",)

        self.db.execute(query, params)

        # Assertions
        self.mock_cursor.execute.assert_called_once_with(query, params)

    def test_execute_failure(self):
        # Mock the cursor's behavior to throw an error
        self.mock_cursor.execute.side_effect = OperationalError("Query failed")

        query = "INSERT INTO test_table (name) VALUES (%s)"
        params = ("Test",)
        result = self.db.execute(query, params)

        # Assertions
        self.mock_cursor.execute.assert_called_once_with(query, params)
        self.assertIsNone(result)

    def test_close_success(self):
        self.db.close()

        # Assertions
        self.mock_cursor.close.assert_called_once()
        self.mock_connection.close.assert_called_once()

    # def test_close_failure(self):
    #     # Mock the cursor's behavior to throw an error
    #     self.mock_cursor.close.side_effect = OperationalError("Close failed")
    #     self.mock_connection.close.side_effect = OperationalError("Close failed")

    #     self.db.close()

    #     # Assertions
    #     self.mock_cursor.close.assert_called_once()
    #     self.mock_connection.close.assert_called_once()

    def test_close_failure(self):
        # Mock the cursor's and connection's close methods to throw an error
        self.mock_cursor.close.side_effect = OperationalError("Close failed")
        self.mock_connection.close.side_effect = OperationalError("Close failed")

        self.db.close()

        # Assertions
        self.mock_cursor.close.assert_called_once()
        self.mock_connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
