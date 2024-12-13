import unittest
from unittest.mock import patch
import grpc
from concurrent import futures
from codegen import user_service_pb2, user_service_pb2_grpc
from services.user.user_service import UserService
from db.db import Database
import bcrypt

class TestUserServiceIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up a real gRPC server with the UserService
        cls.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        # Mock Database instance
        cls.mock_db = Database(
            db_name="postgres",
            user="postgres",
            password="rootpass123",
            host="localhost",
            port=5432
        )

        # Add UserService to the gRPC server
        cls.user_service = UserService(db=cls.mock_db)
        user_service_pb2_grpc.add_UserServiceServicer_to_server(cls.user_service, cls.server)

        # Start the gRPC server
        cls.server.add_insecure_port("[::]:50051")
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop(None)

    def setUp(self):
        # Create a gRPC channel to connect to the test server
        self.channel = grpc.insecure_channel("localhost:50051")
        self.stub = user_service_pb2_grpc.UserServiceStub(self.channel)

        # Mock database setup
        self.mock_db.execute("DELETE FROM Users")

    def tearDown(self):
        self.channel.close()

    def test_register_user_success(self):
        request = user_service_pb2.RegisterUserRequest(
            email="testuser@example.com",
            password="password123",
            name="Test User",
            preferences="{\"category\": [\"Cafe\"]}"
        )
        response = self.stub.RegisterUser(request)

        self.assertTrue(response.success)
        self.assertEqual(response.message, "User registered successfully")
        self.assertIn("Recommendations", response.recommendations)

    def test_register_user_already_exists(self):
        # Insert a user manually into the database
        self.mock_db.execute(
            """
            INSERT INTO Users (email, password_hash, name, preferences, preferences_collected)
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            ("testuser@example.com", "hashed_password", "Test User", "{}")
        )

        # Try to register the same user
        request = user_service_pb2.RegisterUserRequest(
            email="testuser@example.com",
            password="password123",
            name="Test User",
            preferences="{\"category\": [\"Cafe\"]}"
        )

        with self.assertRaises(grpc.RpcError) as context:
            self.stub.RegisterUser(request)

        self.assertEqual(context.exception.code(), grpc.StatusCode.ALREADY_EXISTS)
        self.assertEqual(context.exception.details(), "Email already exists")


    def test_login_user_success(self):
        # Insert a user manually into the database
        hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.mock_db.execute(
            """
            INSERT INTO Users (email, password_hash, name, preferences, preferences_collected)
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            ("testuser@example.com", hashed_password, "Test User", "{}")
        )

        # Login with the same user
        request = user_service_pb2.LoginUserRequest(
            email="testuser@example.com",
            password="password123"
        )
        response = self.stub.LoginUser(request)

        self.assertTrue(response.success)
        self.assertEqual(response.message, "Login successful")
        self.assertIsNotNone(response.token)

    def test_login_user_invalid_credentials(self):
        request = user_service_pb2.LoginUserRequest(
            email="nonexistent@example.com",
            password="wrongpassword"
        )
        with self.assertRaises(grpc.RpcError) as context:
            self.stub.LoginUser(request)

        self.assertEqual(context.exception.code(), grpc.StatusCode.NOT_FOUND)
        self.assertEqual(context.exception.details(), "User not found")

    def test_get_user_profile_success(self):
        # Insert a user manually into the database
        self.mock_db.execute(
            """
            INSERT INTO Users (id, email, password_hash, name, preferences, preferences_collected)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            """,
            (1, "testuser@example.com", "hashed_password", "Test User", "{\"category\": [\"Cafe\"]}")
        )

        request = user_service_pb2.GetUserProfileRequest(user_id=1)
        response = self.stub.GetUserProfile(request)

        self.assertEqual(response.id, 1)
        self.assertEqual(response.email, "testuser@example.com")
        self.assertEqual(response.name, "Test User")

    def test_get_user_profile_not_found(self):
        request = user_service_pb2.GetUserProfileRequest(user_id=999)
        with self.assertRaises(grpc.RpcError) as context:
            self.stub.GetUserProfile(request)

        self.assertEqual(context.exception.code(), grpc.StatusCode.NOT_FOUND)
        self.assertEqual(context.exception.details(), "User not found")

if __name__ == "__main__":
    unittest.main()
