import grpc
import numpy as np
import redis
import pickle
from joblib import load, dump
from codegen import recommendation_service_pb2 as pb2
from codegen import recommendation_service_pb2_grpc as pb2_grpc

from db.business_db import BusinessDatabase

# Initialize database connection
db = BusinessDatabase(db_name="mydb", user="kirandevihosur", password="newpassword")
print("db info", db)

# Initialize Redis connection
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=False)

# File paths
DATA_FILE = "data/data.pkl"
SIMILARITY_MATRIX_FILE = "data/similarity_matrix.pkl"

# Load preprocessed data and similarity matrix with Redis fallback
try:
    # Check Redis cache for data and similarity matrix
    data = None
    similarity_matrix = None

    cached_data = redis_client.get("data.pkl")
    cached_similarity_matrix = redis_client.get("similarity_matrix.pkl")

    if cached_data and cached_similarity_matrix:
        print("Loading data and similarity matrix from Redis cache...")
        data = pickle.loads(cached_data)
        similarity_matrix = pickle.loads(cached_similarity_matrix)
    else:
        print("Loading data and similarity matrix from files...")
        data = load(DATA_FILE)
        similarity_matrix = load(SIMILARITY_MATRIX_FILE)

        # Cache the loaded data and similarity matrix in Redis
        redis_client.set("data.pkl", pickle.dumps(data))
        redis_client.set("similarity_matrix.pkl", pickle.dumps(similarity_matrix))

    print("Data and similarity matrix loaded successfully.")
    print(f"Initial number of businesses: {len(data)}")
    print(f"Initial similarity matrix size: {similarity_matrix.shape}")

except Exception as e:
    print(f"Error loading data: {e}")
    data = None
    similarity_matrix = None


class RecommendationService(pb2_grpc.RecommendationServiceServicer):

    def __init__(self, redis_client):
        self.redis_client = redis_client

    def GetRecommendations(self, request, context):
        """
        Provides recommendations based on user input: category, city, price, minimum rating, and review count.
        """
        global data, similarity_matrix

        if data is None or similarity_matrix is None:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Data or similarity matrix not loaded.")
            return pb2.RecommendationResponse()

        # Validate input
        if request.min_rating < 0 or request.min_rating > 5:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("min_rating must be between 0 and 5.")
            return pb2.RecommendationResponse()

        # Build a cache key based on the user input
        cache_key = f"{request.category}_{request.city}_{request.price}_{request.min_rating}_{request.min_review_count}"

        # Check if recommendations are cached
        cache_key = f"{request.category}_{request.city}_{request.price}_{request.min_rating}_{request.min_review_count}"
        cached_recommendations = self.redis_client.get(cache_key)
        if cached_recommendations:
            print(f"Cache hit for key: {cache_key}")
            return pb2.RecommendationResponse.FromString(cached_recommendations)

        print(f"Cache miss for key: {cache_key}")

        # Get the maximum review count dynamically from the database
        try:
            max_review_query = "SELECT MAX(review_count) AS max_review_count FROM Business"
            max_review_result = db.fetch_one(max_review_query)
            max_review_count = max_review_result['max_review_count'] if max_review_result else 1
            print(f"Max review count dynamically fetched: {max_review_count}")
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error fetching max review count: {str(e)}")
            return pb2.RecommendationResponse()

        # Scale inputs
        scaled_min_review_count = request.min_review_count / max_review_count
        normalized_min_rating = request.min_rating / 5.0

        # Filter the data
        filtered_data = data[
            (data['category'].str.contains(request.category, case=False, na=False)) &
            (data['city'].str.contains(request.city, case=False, na=False)) &
            (data['rating'] >= normalized_min_rating) &
            (data['review_count'] >= scaled_min_review_count) &
            (data['price'] == request.price)
        ]
        if filtered_data.empty:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No businesses match the given preferences.")
            return pb2.RecommendationResponse()

        # Use the first matching business for recommendation
        business_index = filtered_data.index[0]

        if business_index >= similarity_matrix.shape[0]:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Index out of bounds for similarity matrix.")
            return pb2.RecommendationResponse()

        # Get top 5 similar businesses
        similar_indices = similarity_matrix[business_index].argsort()[::-1][1:6]

        # Prepare the recommendations
        recommendations = []
        for idx in similar_indices:
            if idx < len(data):
                business = data.iloc[idx]
                recommendations.append(pb2.BusinessRecommendation(
                    name=business['name'],
                    category=business['category'],
                    rating=business['rating'],
                    review_count=business['review_count'],
                    city=business['city'],
                    address=business['address'],
                    phone=business['phone'],
                    price=business['price'],
                    image_url=business['image_url'],
                    url=business['url']
                ))

        # Convert the recommendations to protobuf response
        response = pb2.RecommendationResponse(recommendations=recommendations)

        # Cache the response in Redis
        redis_client.set(cache_key, response.SerializeToString(), ex=3600)  # Cache for 1 hour

        return response