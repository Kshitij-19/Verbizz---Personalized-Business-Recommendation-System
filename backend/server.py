from concurrent import futures
import grpc
import redis
import threading
import os
from dotenv import load_dotenv
from codegen import business_service_pb2_grpc, recommendation_service_pb2_grpc, user_service_pb2_grpc
from services.business.business_service import BusinessService
from services.recommendation.recommendation_service import RecommendationService
from services.user.user_service import UserService
from consumers.business_consumer import consume_business_messages
from db.db import Database
from joblib import load
from kafka import KafkaProducer
import json

# Load environment variables
load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka-service:9092')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'rootpass123')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))

DATA_FILE = "data/data.pkl"
SIMILARITY_MATRIX_FILE = "data/similarity_matrix.pkl"

# Global resources
redis_client = None
db = None
data = None
similarity_matrix = None
kafka_producer = None

def initialize_resources():
    """
    Initializes global resources like Redis, database connection, and data files.
    """
    global redis_client, db, data, similarity_matrix, kafka_producer

    # Initialize Redis
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)
        redis_client.ping()
        print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except redis.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
        redis_client = None

    # Initialize Database
    try:
        db = Database(db_name=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        print(f"Connected to Database at {DB_HOST}:{DB_PORT}")
    except Exception as e:
        print(f"Error connecting to Database: {e}")
        db = None

    # Load data and similarity matrix
    try:
        print("Loading data and similarity matrix from files...")
        data = load(DATA_FILE)
        similarity_matrix = load(SIMILARITY_MATRIX_FILE)
        print("Data and similarity matrix loaded successfully.")
    except FileNotFoundError:
        print("Data files not found. Ensure that `data.pkl` and `similarity_matrix.pkl` exist.")
        data = None
        similarity_matrix = None
    except Exception as e:
        print(f"Unexpected error loading data or similarity matrix: {e}")
        data = None
        similarity_matrix = None

        # Initialize Kafka Producer
    try:
        kafka_producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
        kafka_producer = None


def serve():
    """
    Starts the gRPC server with multiple services running on the same port.
    """
    initialize_resources()

    if not db or not redis_client or data is None or similarity_matrix is None or data.empty:
        print("Failed to initialize all resources. Exiting...")
        return

    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=consume_business_messages, daemon=True)
    consumer_thread.start()
    print("Kafka consumer thread started...")

    # Create the gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add BusinessService to the server
    business_service = BusinessService(db=db, kafka_producer=kafka_producer)
    business_service_pb2_grpc.add_BusinessServiceServicer_to_server(business_service, server)

    # Add RecommendationService to the server
    recommendation_service = RecommendationService(db=db, redis_client=redis_client, data=data, similarity_matrix=similarity_matrix)
    recommendation_service_pb2_grpc.add_RecommendationServiceServicer_to_server(recommendation_service, server)

    # Add UserService to the server
    user_service = UserService(db=db)
    user_service_pb2_grpc.add_UserServiceServicer_to_server(user_service, server)

    # Bind server to port 50051
    server.add_insecure_port('[::]:50051')
    print("gRPC server is running on port 50051 with multiple services...")

    # Start the server
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()