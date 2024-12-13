import unittest
from unittest.mock import MagicMock, patch
from services.user.user_service import UserService
from codegen import user_service_pb2 as pb2
import grpc
import bcrypt
import jwt

class TestUserService(unittest.TestCase):

    def setUp(self):
        # Mock the database and context
        self.mock_db = MagicMock()
        self.service = UserService(db=self.mock_db)
        self.context = MagicMock()

    # def test_register_user_success(self):
    #     # Mock database execute method
    #     self.mock_db.execute.return_value = None

    #     request = pb2.RegisterUserRequest(
    #         email="test@example.com",
    #         password="password123",
    #         name="Test User",
    #         preferences="{\"category\": [\"Cafe\"]}"
    #     )
        
    #     response = self.service.RegisterUser(request, self.context)

    #     # Assertions
    #     self.assertTrue(response.success)
    #     self.assertEqual(response.message, "User registered successfully")
    #     self.assertIn("Recommendations based on preferences", response.recommendations)
        
    #     self.mock_db.execute.assert_called_once_with(
    #         """
    #         INSERT INTO Users (email, password_hash, name, preferences, preferences_collected)
    #         VALUES (%s, %s, %s, %s, TRUE)
    #         """,
    #         (request.email, unittest.mock.ANY, request.name, request.preferences)
    #     )

    def test_register_user_success(self):
        # Mock database methods
        self.mock_db.fetch_one.return_value = None  # No existing user
        self.mock_db.execute.return_value = None  # Mock successful execution

        request = pb2.RegisterUserRequest(
            email="test@example.com",
            password="password123",
            name="Test User",
            preferences="{\"category\": [\"Cafe\"]}"
        )
        
        response = self.service.RegisterUser(request, self.context)

        # Assertions
        self.assertTrue(response.success)
        self.assertEqual(response.message, "User registered successfully")
        self.assertIn("Recommendations based on preferences", response.recommendations)
        
        self.mock_db.fetch_one.assert_called_once_with(
            "SELECT id FROM Users WHERE email = %s", (request.email,)
        )
        self.mock_db.execute.assert_called_once_with(
            """
            INSERT INTO Users (email, password_hash, name, preferences, preferences_collected)
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            (request.email, unittest.mock.ANY, request.name, request.preferences)
        )


    def test_register_user_duplicate(self):
        # Mock database to throw an exception
        self.mock_db.execute.side_effect = Exception("Email already exists")

        request = pb2.RegisterUserRequest(
            email="test@example.com",
            password="password123",
            name="Test User",
            preferences="{\"category\": [\"Cafe\"]}"
        )

        response = self.service.RegisterUser(request, self.context)

        # Assertions
        self.assertFalse(response.success)
        self.assertEqual(response.message, "User registration failed")
        self.context.set_code.assert_called_once_with(grpc.StatusCode.ALREADY_EXISTS)

    def test_login_user_success(self):
        # Mock database response
        hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.mock_db.fetch_one.return_value = {
            "id": 1,
            "password_hash": hashed_password,
            "preferences": "{\"category\": [\"Cafe\"]}",
            "preferences_collected": True
        }

        request = pb2.LoginUserRequest(
            email="test@example.com",
            password="password123"
        )

        with patch("jwt.encode", return_value="mock_token"):
            response = self.service.LoginUser(request, self.context)

        # Assertions
        self.assertTrue(response.success)
        self.assertEqual(response.message, "Login successful")
        self.assertEqual(response.token, "mock_token")
        self.assertEqual(response.user_id, 1)

    def test_login_user_invalid_password(self):
        # Mock database response
        hashed_password = bcrypt.hashpw("wrong_password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.mock_db.fetch_one.return_value = {
            "id": 1,
            "password_hash": hashed_password,
            "preferences": "{\"category\": [\"Cafe\"]}",
            "preferences_collected": True
        }

        request = pb2.LoginUserRequest(
            email="test@example.com",
            password="password123"
        )

        response = self.service.LoginUser(request, self.context)

        # Assertions
        self.assertFalse(response.success)
        self.assertEqual(response.message, "Invalid email or password")
        self.context.set_code.assert_called_once_with(grpc.StatusCode.UNAUTHENTICATED)

    def test_get_user_profile_success(self):
        # Mock database response
        self.mock_db.fetch_one.return_value = {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "preferences": {"category": ["Cafe"]}
        }

        request = pb2.GetUserProfileRequest(user_id=1)

        response = self.service.GetUserProfile(request, self.context)

        # Assertions
        self.assertEqual(response.id, 1)
        self.assertEqual(response.email, "test@example.com")
        self.assertEqual(response.name, "Test User")
        self.assertEqual(response.preferences, '{"category": ["Cafe"]}')

    def test_update_user_profile_success(self):
        # Mock database execute method
        self.mock_db.execute.return_value = None

        request = pb2.UpdateUserProfileRequest(
            user_id=1,
            name="Updated Name",
            preferences="{\"category\": [\"Updated Category\"]}"
        )

        response = self.service.UpdateUserProfile(request, self.context)

        # Assertions
        self.assertTrue(response.success)
        self.assertEqual(response.message, "User profile updated")
        self.mock_db.execute.assert_called_once_with(
            """
            UPDATE Users SET name = %s, preferences = %s WHERE id = %s
            """,
            (request.name, request.preferences, request.user_id)
        )

    def test_delete_user_success(self):
        # Mock database execute method
        self.mock_db.execute.return_value = None

        request = pb2.DeleteUserRequest(user_id=1)

        response = self.service.DeleteUser(request, self.context)

        # Assertions
        self.assertTrue(response.success)
        self.assertEqual(response.message, "User deleted successfully")
        self.mock_db.execute.assert_called_once_with("DELETE FROM Users WHERE id = %s", (request.user_id,))

if __name__ == "__main__":
    unittest.main()
