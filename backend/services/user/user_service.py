import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from codegen import user_service_pb2 as user_pb2, user_service_pb2_grpc as user_pb2_grpc
from codegen import recommendation_service_pb2 as rec_pb2
import grpc
import json
import logging
from kafka import KafkaConsumer

# Initialize Kafka consumer
consumer = KafkaConsumer(
    'preferences_update',
    bootstrap_servers='localhost:9092',  # Update with your Kafka broker address
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    group_id='recommendation-service'
)


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")

class UserService(user_pb2_grpc.UserServiceServicer):
    def __init__(self, db, redis_client, recommendation_service):
        """
        Initialize the UserService with a database connection.
        :param db: Database connection instance
        """
        self.db = db
        self.redis_client = redis_client
        self.recommendation_service = recommendation_service

    def RegisterUser(self, request, context):
        """
        Register a new user and fetch initial recommendations based on preferences.
        """
        try:
            # Hash the password
            hashed_password = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            # Log raw preferences for debugging
            logging.info(f"Raw preferences from request: {request.preferences}")

            # Parse preferences from JSON string
            preferences = json.loads(request.preferences)

            # Ensure preferences are JSON-serializable (convert any non-native types)
            normalized_preferences = {
                key: (
                    [str(item) for item in value] if isinstance(value, list) else str(value)
                )
                for key, value in preferences.items()
            }
            preferences_json = json.dumps(normalized_preferences)

            # Insert user into the database
            query = """
            INSERT INTO Users (email, password_hash, name, preferences, preferences_collected)
            VALUES (%s, %s, %s, %s, TRUE)
            """
            self.db.execute(query, (request.email, hashed_password, request.name, preferences_json))

            # Call RecommendationService
            rec_request = rec_pb2.RecommendationRequest(
                category=normalized_preferences["category"],  # List of strings
                city=normalized_preferences["city"]  # String
            )
            logging.info(f'Recommendation request: {rec_request}')
            response = self.recommendation_service.GetRecommendations(rec_request, context)
            logging.info(f'Response from recommendation service: {response}')

            # Prepare recommendations response
            recommendations = [
                {
                    "name": rec.name,
                    "category": rec.category.split(", "),  # Already a string in this structure
                    "rating": float(rec.rating),  # Ensure rating is treated as float
                    "review_count": int(rec.review_count),  # Ensure review_count is an integer
                    "city": rec.city,
                    "address": rec.address,
                    "phone": rec.phone,
                    "price": rec.price,
                    "image_url": rec.image_url,
                    "url": rec.url,
                }
                for rec in response.recommendations
            ]

            logging.info(f'Recommendations: {recommendations}')

            # Serialize recommendations to JSON
            serialized_recommendations = json.dumps(recommendations)

            # Return the response
            return user_pb2.RegisterUserResponse(
                message="User registered successfully.",
                success=True,
                recommendations=serialized_recommendations  # Return as JSON string
            )
        except grpc.RpcError as e:
            logging.error(f"Error calling Recommendation Service: {e.details()}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to fetch recommendations.")
            return user_pb2.RegisterUserResponse(
                message="User registered, but recommendations failed.",
                success=False,
            )
        except Exception as e:
            logging.error(f"Error during registration: {str(e)}")
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("Email already exists.")
            return user_pb2.RegisterUserResponse(
                message="User registration failed.",
                success=False,
            )

    def LoginUser(self, request, context):
        """
        Authenticate a user and fetch recommendations for returning users.
        """
        try:
            # Fetch user from the database
            query = "SELECT id,name, password_hash, preferences, preferences_collected FROM Users WHERE email = %s"
            user = self.db.fetch_one(query, (request.email,))
            if not user:
                logging.error("User not found.")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("User not found")
                return user_pb2.LoginUserResponse(message="Invalid email or password", success=False)

            logging.info(f"User found: ID {user['id']}")

            # Verify password
            if not bcrypt.checkpw(request.password.encode("utf-8"), user["password_hash"].encode("utf-8")):
                logging.error("Invalid password.")
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details("Invalid credentials")
                return user_pb2.LoginUserResponse(message="Invalid email or password", success=False)

            # Generate JWT token
            token = jwt.encode(
                {"user_id": user["id"], "exp": datetime.utcnow() + timedelta(hours=2)},
                SECRET_KEY,
                algorithm="HS256",
            )
            logging.info(f"JWT token generated for user {user['id']}")

            # Returning user logic
            if isinstance(user["preferences"], str):
                preferences = json.loads(user["preferences"])  # Parse preferences only if it's a JSON string
            else:
                preferences = user["preferences"]  # Use directly if it's already a dict

            # Check if preferences are collected
            if not user["preferences_collected"]:
                logging.info("User has not set preferences yet.")
                return user_pb2.LoginUserResponse(
                    message="Preferences required",
                    success=True,
                    token=token,
                    user_id=user["id"],
                    preferences=json.dumps(preferences),
                    name=user["name"],
                )



            logging.info(f"User preferences: {preferences}")

            # Check cache for recommendations
            cache_key = f"user_{user['id']}_recommendations"
            if self.redis_client:
                cached_recommendations = self.redis_client.get(cache_key)
                if cached_recommendations:
                    logging.info(f"Cache hit for user {user['id']}")
                    return user_pb2.LoginUserResponse(
                        message="Login successful.",
                        success=True,
                        token=token,
                        user_id=user["id"],
                        preferences=json.dumps(preferences),
                        recommendations=cached_recommendations,  # Cached recommendations
                        name=user["name"],
                    )

            # Fetch recommendations if not cached
            rec_request = rec_pb2.RecommendationRequest(
                category=preferences["category"], city=preferences["city"]
            )
            response = self.recommendation_service.GetRecommendations(rec_request, context)
            logging.info(f"Response from recommendation service: {response}")

            # Prepare recommendations response
            recommendations = [
                {
                    "name": rec.name,
                    "category": rec.category,
                    "rating": rec.rating,
                    "review_count": rec.review_count,
                    "city": rec.city,
                    "address": rec.address,
                    "phone": rec.phone,
                    "price": rec.price,
                    "image_url": rec.image_url,
                    "url": rec.url,
                }
                for rec in response.recommendations
            ]

            logging.info(f"Recommendations for user {user['id']}: {recommendations}")

            serialized_recommendations = json.dumps(recommendations)

            # Save recommendations to cache
            if self.redis_client:
                self.redis_client.set(cache_key, serialized_recommendations, ex=3600)  # Cache for 1 hour

            return user_pb2.LoginUserResponse(
                message="Login successful.",
                success=True,
                token=token,
                user_id=user["id"],
                preferences=json.dumps(preferences),
                recommendations=serialized_recommendations,
                name=user["name"],
            )
        except grpc.RpcError as e:
            logging.error(f"Error calling Recommendation Service: {e.details()}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to fetch recommendations.")
            return user_pb2.LoginUserResponse(
                message="Login successful, but recommendations failed.",
                success=True,
                token=token,
                user_id=user["id"],
                preferences=json.dumps(preferences),
                recommendations="[]",
                name=user["name"],
            )
        except Exception as e:
            logging.error(f"Error during login: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error.")
            return user_pb2.LoginUserResponse(message="Login failed.", success=False)

    def GetUserProfile(self, request, context):
        try:
            query = "SELECT id, email, name, preferences FROM Users WHERE id = %s"
            print("Value in user ser fun:", request.user_id)
            user = self.db.fetch_one(query, (request.user_id,))
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
            self.db.execute(query, (request.name, request.preferences, request.user_id))
            return user_pb2.UpdateUserProfileResponse(message="User profile updated", success=True)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error')
            return user_pb2.UpdateUserProfileResponse(message="Update failed", success=False)

    def DeleteUser(self, request, context):
        try:
            query = "DELETE FROM Users WHERE id = %s"
            self.db.execute(query, (request.user_id,))
            return user_pb2.DeleteUserResponse(message="User deleted successfully", success=True)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error')
            return user_pb2.DeleteUserResponse(message="Delete failed", success=False)

    def UpdatePreferences(self, request, context):
        """
        Updates user preferences, generates new recommendations if needed, and manages caching appropriately.
        """
        try:
            logging.info("Updating preferences... backend")
            logging.info(f"Request received: {request}")

            # Fetch the existing preferences for the user from the database
            query = "SELECT preferences FROM Users WHERE id = %s"
            existing_user = self.db.fetch_one(query, (request.user_id,))
            if not existing_user:
                logging.warning(f"User not found for user_id: {request.user_id}")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("User not found.")
                return user_pb2.UpdatePreferencesResponse(
                    message="User not found.",
                    success=False,
                    recommendations="[]"
                )

            # Parse the existing preferences
            existing_preferences = existing_user["preferences"]
            if isinstance(existing_preferences, str):
                existing_preferences = json.loads(existing_preferences)
            logging.info(f"Parsed existing preferences: {existing_preferences}")

            # Create a dictionary from the incoming preferences
            new_preferences = {
                "category": list(request.category),
                "city": request.city
            }
            logging.info(f"New preferences: {new_preferences}")

            # Check if preferences have changed
            if existing_preferences == new_preferences:
                logging.info("Preferences unchanged. Checking cache for recommendations.")
                cache_key = f"recommendations:{' '.join(request.category).lower()}:{request.city.lower()}"
                redis_client = self.redis_client

                if redis_client:
                    cached_recommendations = redis_client.get(cache_key)
                    if cached_recommendations:
                        logging.info("Returning cached recommendations.")
                        return user_pb2.UpdatePreferencesResponse(
                            message="Preferences unchanged. Returning cached recommendations.",
                            success=True,
                            recommendations=cached_recommendations.decode("utf-8")
                        )
                logging.info("No cached recommendations found.")

            # Update preferences in the database
            preferences_json = json.dumps(new_preferences)
            update_query = "UPDATE Users SET preferences = %s WHERE id = %s"
            self.db.execute(update_query, (preferences_json, request.user_id))
            logging.info(f"Preferences updated in the database for user_id {request.user_id}.")

            # Invalidate the cache for the old recommendations
            cache_key = f"recommendations:{' '.join(request.category).lower()}:{request.city.lower()}"
            if self.redis_client:
                logging.info(f"Invalidating cache for key: {cache_key}")
                self.redis_client.delete(cache_key)

            # Fetch new recommendations from the recommendation service
            rec_request = rec_pb2.RecommendationRequest(
                category=request.category,
                city=request.city
            )
            response = self.recommendation_service.GetRecommendations(rec_request, context)
            logging.info(f"Recommendations fetched: {response}")

            # Prepare recommendations for response
            recommendations = [
                {
                    "name": rec.name,
                    "category": rec.category,
                    "rating": rec.rating,
                    "review_count": rec.review_count,
                    "city": rec.city,
                    "address": rec.address,
                    "phone": rec.phone,
                    "price": rec.price,
                    "image_url": rec.image_url,
                    "url": rec.url,
                }
                for rec in response.recommendations
            ]
            serialized_recommendations = json.dumps(recommendations)
            logging.info(f"Serialized recommendations: {serialized_recommendations}")

            return user_pb2.UpdatePreferencesResponse(
                message="Preferences updated successfully.",
                success=True,
                recommendations=serialized_recommendations
            )

        except grpc.RpcError as e:
            logging.error(f"gRPC error while fetching recommendations: {e.details()}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to fetch new recommendations.")
            return user_pb2.UpdatePreferencesResponse(
                message="Failed to update preferences.",
                success=False,
                recommendations="[]"
            )
        except Exception as e:
            logging.error(f"Error during preference update: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error.")
            return user_pb2.UpdatePreferencesResponse(
                message="Failed to update preferences.",
                success=False,
                recommendations="[]"
            )
