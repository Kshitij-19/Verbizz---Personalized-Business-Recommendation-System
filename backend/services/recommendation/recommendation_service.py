import grpc
from codegen import recommendation_service_pb2 as pb2
from codegen import recommendation_service_pb2_grpc as pb2_grpc


class RecommendationService(pb2_grpc.RecommendationServiceServicer):

    def __init__(self, redis_client, db, data, similarity_matrix):
        """
        Initializes the RecommendationService with the required resources.
        :param redis_client: Redis client instance.
        :param db: Database instance.
        :param data: Preloaded data for recommendations.
        :param similarity_matrix: Preloaded similarity matrix.
        """
        self.redis_client = redis_client
        self.db = db
        self.data = data
        self.similarity_matrix = similarity_matrix

    def GetRecommendations(self, request, context):
        """
        Provides recommendations based on user input: category, city, price, minimum rating, and review count.
        """
        if self.data is None or self.similarity_matrix is None:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Data or similarity matrix not loaded.")
            return pb2.RecommendationResponse()

        # Validate input
        if request.min_rating < 0 or request.min_rating > 5:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("min_rating must be between 0 and 5.")
            return pb2.RecommendationResponse()

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
            max_review_result = self.db.fetch_one(max_review_query)
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
        filtered_data = self.data[
            (self.data['category'].str.contains(request.category, case=False, na=False)) &
            (self.data['city'].str.contains(request.city, case=False, na=False)) &
            (self.data['rating'] >= normalized_min_rating) &
            (self.data['review_count'] >= scaled_min_review_count) &
            (self.data['price'] == request.price)
        ]

        if filtered_data.empty:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No businesses match the given preferences.")
            return pb2.RecommendationResponse()

        # Use the first matching business for recommendation
        business_index = int(filtered_data.index[0])  # Convert index to integer

        # Validate the index against similarity matrix dimensions
        if business_index < 0 or business_index >= self.similarity_matrix.shape[0]:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Index out of bounds for similarity matrix.")
            return pb2.RecommendationResponse()

        # Get top 5 similar businesses
        similar_indices = self.similarity_matrix[business_index].argsort()[::-1][1:6]

        # Prepare the recommendations
        recommendations = []
        for idx in similar_indices:
            if idx < len(self.data):
                business = self.data.iloc[idx]
                original_rating = round(business['rating'] * 5.0, 2)  # Assuming rating was normalized to 0-1
                original_review_count = int(business['review_count'] * max_review_count)  # Assuming max_review_count is known
                recommendations.append(pb2.BusinessRecommendation(
                    name=business['name'],
                    category=business['category'],
                    rating=original_rating,
                    review_count=original_review_count,
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
        self.redis_client.set(cache_key, response.SerializeToString(), ex=3600)  # Cache for 1 hour

        return response