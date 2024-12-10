from concurrent import futures
import grpc
import redis
import threading
from codegen import business_service_pb2_grpc, recommendation_service_pb2_grpc
from services.business.business_service import BusinessService
from services.recommendation.recommendation_service import RecommendationService
from consumers.business_consumer import consume_business_messages
from services.user.user_service import UserService

def initialize_redis():
    """
    Initializes the Redis client and tests the connection.
    """
    try:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=False)
        # Test the Redis connection
        redis_client.ping()
        print("Connected to Redis successfully.")
        return redis_client
    except redis.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
        return None


def serve():
    """
    Starts the gRPC server with multiple services running on the same port.
    """
    # Initialize Redis
    redis_client = initialize_redis()
    if not redis_client:
        print("Failed to initialize Redis. Exiting...")
        return

    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=consume_business_messages, daemon=True)
    consumer_thread.start()
    print("Kafka consumer thread started...")

    # Create the gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add BusinessService to the server
    business_service = BusinessService()
    business_service_pb2_grpc.add_BusinessServiceServicer_to_server(business_service, server)

    # Add RecommendationService to the server
    recommendation_service = RecommendationService(redis_client=redis_client)  # Pass Redis to the service
    recommendation_service_pb2_grpc.add_RecommendationServiceServicer_to_server(recommendation_service, server)
    
    # Add UserService to the server
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)

    # Bind server to port 50051
    server.add_insecure_port('[::]:50051')
    print("gRPC server is running on port 50051 with multiple services...")

    # Start the server
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()