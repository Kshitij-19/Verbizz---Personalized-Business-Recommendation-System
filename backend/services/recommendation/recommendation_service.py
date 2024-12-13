import grpc
from codegen import recommendation_service_pb2 as pb2
from codegen import recommendation_service_pb2_grpc as pb2_grpc
import logging
import json
from sklearn.metrics.pairwise import cosine_similarity

class RecommendationService(pb2_grpc.RecommendationServiceServicer):

    def __init__(self, redis_client, db, data, vectorizer):
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
        self.vectorizer = vectorizer


    def GetRecommendations(self, request, context):
        """
        Provide recommendations based on category and city preferences, with caching.
        """
        # Combine user-selected categories into a single string for caching key
        user_categories = ' '.join(request.category).lower()
        user_city = request.city.lower()
        cache_key = f"recommendations:{user_categories}:{user_city}"

        # Check the cache
        cached_recommendations = self.redis_client.get(cache_key)
        if cached_recommendations:
            print(f"Cache hit for key: {cache_key}")
            logging.info(f"Cache hit for key: {cache_key}")
            recommendations_data = json.loads(cached_recommendations)
            return pb2.RecommendationResponse(
                recommendations=[
                    pb2.BusinessRecommendation(
                        name=rec["name"],
                        category=rec["category"],
                        rating=rec["rating"],
                        review_count=rec["review_count"],
                        city=rec["city"],
                        address=rec["address"],
                        phone=rec["phone"],
                        price=rec["price"],
                        image_url=rec["image_url"],
                        url=rec["url"]
                    )
                    for rec in recommendations_data
                ]
            )

        print(f"Cache miss for key: {cache_key}")
        logging.info(f"Cache miss for key: {cache_key}")

        print("Data check", self.data.head())

        # Filter data by city
        city_filtered_data = self.data[self.data['city'].str.lower() == user_city]
        if city_filtered_data.empty:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"No businesses found in {request.city}")
            return pb2.RecommendationResponse()

        # Prepare the user query
        user_query = ' '.join(request.category)
        user_vector = self.vectorizer.transform([user_query])

        # Vectorize the category features of the filtered data
        category_vectors = self.vectorizer.transform(city_filtered_data['category_features'])

        # Compute cosine similarity
        category_similarity = cosine_similarity(user_vector, category_vectors).flatten()

        # Add similarity scores to the filtered data
        city_filtered_data = city_filtered_data.copy()
        city_filtered_data['category_similarity'] = category_similarity

        # Filter and sort by similarity
        recommended_businesses = (
            city_filtered_data[city_filtered_data['category_similarity'] > 0]
            .sort_values(by='category_similarity', ascending=False)
        )

        # If no businesses match the category
        if recommended_businesses.empty:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"No businesses match the preferences in {request.city}")
            return pb2.RecommendationResponse()

        # Prepare the recommendations
        recommendations = []
        for _, business in recommended_businesses.head(10).iterrows():
            recommendations.append({
                "name": business['name'],
                "category": business['category'],
                "rating": business['rating'],
                "review_count": business['review_count'],
                "city": business['city'],
                "address": business['address'],
                "phone": business['phone'],
                "price": business['price'],
                "image_url": business['image_url'],
                "url": business['url']
            })
        logging.info(f"Generated recommendations: {recommendations}")
        # Cache the recommendations
        self.redis_client.set(cache_key, json.dumps(recommendations), ex=3600)  # Cache for 1 hour
        # Return recommendations in the response
        return pb2.RecommendationResponse(
            recommendations=[
                pb2.BusinessRecommendation(
                    name=rec["name"],
                    category=rec["category"],
                    rating=rec["rating"],
                    review_count=rec["review_count"],
                    city=rec["city"],
                    address=rec["address"],
                    phone=rec["phone"],
                    price=rec["price"],
                    image_url=rec["image_url"],
                    url=rec["url"]
                )
                for rec in recommendations
            ]
        )