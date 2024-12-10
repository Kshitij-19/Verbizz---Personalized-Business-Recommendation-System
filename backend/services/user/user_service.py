import bcrypt
import jwt
import os
from datetime import datetime, timedelta
# from proto import user_pb2, user_pb2_grpc
from codegen import user_service_pb2 as user_pb2, user_service_pb2_grpc as user_pb2_grpc
from db.db import Database
import grpc
import json


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")

db = Database(db_name="postgres", user="postgres", password="rootpass123")

class UserService(user_pb2_grpc.UserServiceServicer):

    def RegisterUser(self, request, context):
        try:
            # Hash the password
            hashed_password = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt())

            # Insert user into the database
            query = """
            INSERT INTO Users (email, password_hash, name, preferences, preferences_collected)
            VALUES (%s, %s, %s, %s, TRUE)
            """
            db.execute(query, (request.email, hashed_password.decode('utf-8'), request.name, request.preferences))

            # Fetch recommendations based on preferences
            recommendations = self.get_recommendations(request.preferences)

            return user_pb2.RegisterUserResponse(
                message="User registered successfully",
                success=True,
                recommendations=recommendations
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details('Email already exists')
            return user_pb2.RegisterUserResponse(message="User registration failed", success=False)

    def get_recommendations(self, preferences):
        # Call the Recommendation API or logic
        # For simplicity, mock recommendations here
        return f"Recommendations based on preferences: {preferences}"

    # def LoginUser(self, request, context):
    #     try:
    #         # Fetch user from the database
    #         query = "SELECT id, password_hash, preferences, preferences_collected FROM Users WHERE email = %s"
    #         user = db.fetch_one(query, (request.email,))
    #         if not user:
    #             context.set_code(grpc.StatusCode.NOT_FOUND)
    #             context.set_details('User not found')
    #             return user_pb2.LoginUserResponse(message="Invalid email or password", success=False)

    #         # Verify password
    #         if not bcrypt.checkpw(request.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
    #             context.set_code(grpc.StatusCode.UNAUTHENTICATED)
    #             context.set_details('Invalid credentials')
    #             return user_pb2.LoginUserResponse(message="Invalid email or password", success=False)

    #         # Generate JWT token
    #         token = jwt.encode(
    #             {"user_id": user['id'], "exp": datetime.utcnow() + timedelta(hours=2)},
    #             SECRET_KEY,
    #             algorithm="HS256"
    #         )

    #         # Handle first-time vs returning user logic
    #         if not user['preferences_collected']:
    #             return user_pb2.LoginUserResponse(
    #                 message="Preferences required",
    #                 success=True,
    #                 token=token
    #             )
    #         else:
    #             # Fetch recommendations for returning users
    #             recommendations = self.get_recommendations(user['preferences'])
    #             return user_pb2.LoginUserResponse(
    #                 message="Login successful",
    #                 success=True,
    #                 token=token,
    #                 recommendations=recommendations
    #             )
    #     except Exception as e:
    #         context.set_code(grpc.StatusCode.INTERNAL)
    #         context.set_details('Internal server error')
    #         return user_pb2.LoginUserResponse(message="Login failed", success=False)

    def LoginUser(self, request, context):
        try:
            # Fetch user from the database
            query = "SELECT id, password_hash, preferences, preferences_collected FROM Users WHERE email = %s"
            user = db.fetch_one(query, (request.email,))
            if not user:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('User not found')
                return user_pb2.LoginUserResponse(message="Invalid email or password", success=False)

            # Verify password
            if not bcrypt.checkpw(request.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details('Invalid credentials')
                return user_pb2.LoginUserResponse(message="Invalid email or password", success=False)

            # Generate JWT token
            token = jwt.encode(
                {"user_id": user['id'], "exp": datetime.utcnow() + timedelta(hours=2)},
                SECRET_KEY,
                algorithm="HS256"
            )

            # Handle first-time vs returning user logic
            if not user['preferences_collected']:
                return user_pb2.LoginUserResponse(
                    message="Preferences required",
                    success=True,
                    token=token,
                    user_id=user['id']  # Include user_id in the response
                )
            else:
                # Fetch recommendations for returning users
                recommendations = self.get_recommendations(user['preferences'])
                return user_pb2.LoginUserResponse(
                    message="Login successful",
                    success=True,
                    token=token,
                    user_id=user['id'],  # Include user_id in the response
                    recommendations=recommendations
                )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error')
            return user_pb2.LoginUserResponse(message="Login failed", success=False)


    # def GetUserProfile(self, request, context):
    #     try:
    #         query = "SELECT id, email, name, preferences FROM Users WHERE id = %s"
    #         print("Value in user ser fun:", request.user_id)
    #         user = db.fetch_one(query, (request.user_id,))
    #         print("User is :", user)
    #         if not user:
    #             context.set_code(grpc.StatusCode.NOT_FOUND)
    #             context.set_details('User not found')
    #             return user_pb2.GetUserProfileResponse()

    #         return user_pb2.GetUserProfileResponse(
    #             id=user['id'],
    #             email=user['email'],
    #             name=user['name'],
    #             preferences=user['preferences']
    #         )
    #     except Exception as e:
    #         print("Exception is:", e)
    #         context.set_code(grpc.StatusCode.INTERNAL)
    #         context.set_details('Internal server error')
    #         return user_pb2.GetUserProfileResponse()

    def GetUserProfile(self, request, context):
        try:
            query = "SELECT id, email, name, preferences FROM Users WHERE id = %s"
            print("Value in user ser fun:", request.user_id)
            user = db.fetch_one(query, (request.user_id,))
            print("User is :", user)
            if not user:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('User not found')
                return user_pb2.GetUserProfileResponse()

            # Serialize the preferences field to JSON string
            serialized_preferences = json.dumps(user['preferences']) if user['preferences'] else ""

            return user_pb2.GetUserProfileResponse(
                id=user['id'],
                email=user['email'],
                name=user['name'],
                preferences=serialized_preferences  # Ensure this is a string
            )
        except Exception as e:
            print("Exception is:", e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error')
            return user_pb2.GetUserProfileResponse()

    def UpdateUserProfile(self, request, context):
        try:
            query = """
            UPDATE Users SET name = %s, preferences = %s WHERE id = %s
            """
            db.execute(query, (request.name, request.preferences, request.user_id))
            return user_pb2.UpdateUserProfileResponse(message="User profile updated", success=True)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error')
            return user_pb2.UpdateUserProfileResponse(message="Update failed", success=False)

    def DeleteUser(self, request, context):
        try:
            query = "DELETE FROM Users WHERE id = %s"
            db.execute(query, (request.user_id,))
            return user_pb2.DeleteUserResponse(message="User deleted successfully", success=True)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error')
            return user_pb2.DeleteUserResponse(message="Delete failed", success=False)
