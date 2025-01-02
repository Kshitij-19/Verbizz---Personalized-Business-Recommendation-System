import grpc
import json  # Import JSON to handle proper formatting
from codegen import user_service_pb2 as user_pb2
from codegen import user_service_pb2_grpc as user_pb2_grpc
from codegen import recommendation_service_pb2 as rec_pb2
from codegen import recommendation_service_pb2_grpc as rec_pb2_grpc
import logging

BACKEND_HOST = "localhost:50051"

class BackendClient:
    def __init__(self):
        self.channel = grpc.insecure_channel(BACKEND_HOST)
        self.user_stub = user_pb2_grpc.UserServiceStub(self.channel)
        self.recommendation_stub = rec_pb2_grpc.RecommendationServiceStub(self.channel)

    def register_user(self, email, password, name, preferences):
        try:
            response = self.user_stub.RegisterUser(user_pb2.RegisterUserRequest(
                email=email,
                password=password,
                name=name,
                preferences=preferences  # Expecting JSON string
            ))
            return {"success": True, "response": response}
        except grpc.RpcError as e:
            return {"success": False, "error": e.details(), "code": e.code()}

    def login_user(self, email, password):
        """
        Calls the backend login endpoint.
        """
        try:
            response = self.user_stub.LoginUser(user_pb2.LoginUserRequest(
                email=email,
                password=password
            ))
            return {
                "success": True,
                "response": {
                    "token": response.token,
                    "user_id": response.user_id,
                    "recommendations": response.recommendations,
                    "preferences": response.preferences,
                    "name": response.name,
                },
            }
        except grpc.RpcError as e:
            return {
                "success": False,
                "error": e.details(),
                "code": e.code(),
            }

    def get_recommendations(self, category, city):
        try:
            print("Inside get_recommendations")
            response = self.recommendation_stub.GetRecommendations(rec_pb2.RecommendationRequest(
                category=category,
                city=city
            ))
            return {"success": True, "response": response}
        except grpc.RpcError as e:
            return {"success": False, "error": e.details(), "code": e.code()}

    def update_preferences(self, user_id, category, city):
        try:
            logging.info("Inside update_preferences")
            response = self.user_stub.UpdatePreferences(user_pb2.UpdatePreferencesRequest(
                user_id=user_id,
                category=category,
                city=city
            ))
            return {"success": True, "response": response}
        except grpc.RpcError as e:
            return {"success": False, "error": e.details(), "code": e.code()}