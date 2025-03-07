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
from consumers.update_preferences_consumer import start_kafka_consumer
from db.db import Database
from joblib import load
from kafka import KafkaProducer
import json
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
import logging

# Load environment variables
load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka-service:9092')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'rootpass123')
DB_HOST = os.getenv('DB_HOST', 'localhost') #postgres-service for docker
DB_PORT = int(os.getenv('DB_PORT', 5432))

DATA_FILE = "data/full_data.pkl"
VECTORIZER_FILE = "data/tfidf_vectorizer.pkl"

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to logging.DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Global resources
redis_client = None
db = None
data = None
vectorizer = None
kafka_producer = None

def initialize_resources():
    """
    Initializes global resources like Redis, database connection, and data files.
    """
    global redis_client, db, data, vectorizer, kafka_producer

    # Initialize Redis
    logging.info("Initializing Redis...")
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)
        redis_client.ping()
        print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except redis.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
        redis_client = None

    # Initialize Database
    logging.info("Initializing Database...")
    try:
        db = Database(db_name=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        print(f"Connected to Database at {DB_HOST}:{DB_PORT}")
    except Exception as e:
        print(f"Error connecting to Database: {e}")
        db = None

    logging.info("Database... connected")
    # Load data and vectorizer
    logging.info("Loading data and vectorizer from files...")
    try:
        print("Loading data and vectorizer from files...")
        data = load(DATA_FILE)
        vectorizer = load(VECTORIZER_FILE)
        print("Data and similarity matrix loaded successfully.")
    except FileNotFoundError:
        print("Data files not found. Ensure that `data.pkl` and `vectorizer.pkl` exist.")
        data = None
        vectorizer = None
    except Exception as e:
        print(f"Unexpected error loading data or vectorizer: {e}")
        data = None
        vectorizer = None

        # Initialize Kafka Producer
    logging.info("Data and vectorizer loaded successfully.")


    try:
        kafka_producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logging.info(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
        logging.info("Error connecting to Kafka: {e}")
        kafka_producer = None


def serve():
    """
    Starts the gRPC server with multiple services running on the same port.
    """
    initialize_resources()

    logging.info(f"Kafka producer started  {kafka_producer}")

    if not db or not redis_client or data is None or vectorizer is None or data.empty:
        print("Failed to initialize all resources. Exiting...")
        logging.info("Failed to initialize all resources. Exiting...")
        return

    # Create the gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add BusinessService to the server
    business_service = BusinessService(db=db, kafka_producer=kafka_producer)
    business_service_pb2_grpc.add_BusinessServiceServicer_to_server(business_service, server)

    # Add RecommendationService to the server
    recommendation_service = RecommendationService(db=db, redis_client=redis_client, data=data, vectorizer=vectorizer)
    recommendation_service_pb2_grpc.add_RecommendationServiceServicer_to_server(recommendation_service, server)


    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(
        target=start_kafka_consumer,
        args=(redis_client, db, recommendation_service),
        daemon=True
    )
    consumer_thread.start()
    print("Kafka consumer thread started...")


    # Add UserService to the server
    user_service = UserService(db=db, redis_client=redis_client, recommendation_service=recommendation_service)
    user_service_pb2_grpc.add_UserServiceServicer_to_server(user_service, server)

    # Add Health Checking Service
    health_service = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_service, server)

    # Set the health status of the services
    health_service.set('', health_pb2.HealthCheckResponse.SERVING)

    # Bind server to port 50051
    server.add_insecure_port('[::]:50051')
    logging.info("gRPC server is running on port 50051 with health checks...")

    # Start the server
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()