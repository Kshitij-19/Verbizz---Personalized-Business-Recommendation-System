import unittest
from unittest.mock import Mock, patch
import grpc
import pandas as pd
import numpy as np
from codegen import recommendation_service_pb2 as pb2
from services.recommendation.recommendation_service import RecommendationService

class TestRecommendationService(unittest.TestCase):
    def setUp(self):
        # Create mock dependencies
        self.mock_redis_client = Mock()
        self.mock_db = Mock()
        
        # Prepare sample data for testing
        self.sample_data = pd.DataFrame({
            'name': ['Business1', 'Business2', 'Business3', 'Business4'],
            'category': ['Restaurant', 'Cafe', 'Restaurant', 'Bar'],
            'city': ['New York', 'Chicago', 'New York', 'Chicago'],
            'rating': [0.8, 0.6, 0.7, 0.5],
            'review_count': [0.6, 0.4, 0.5, 0.3],
            'price': ['$$', '$', '$$', '$$$'],
            'address': ['123 Test St', '456 Mock Ave', '789 Sample Rd', '321 Demo Blvd'],
            'phone': ['1234567890', '0987654321', '1112223333', '4445556666'],
            'image_url': ['http://test1.com', 'http://test2.com', 'http://test3.com', 'http://test4.com'],
            'url': ['http://business1.com', 'http://business2.com', 'http://business3.com', 'http://business4.com']
        })
        
        # Create a sample similarity matrix
        self.sample_similarity_matrix = np.array([
            [1.0, 0.8, 0.6, 0.4],
            [0.8, 1.0, 0.7, 0.5],
            [0.6, 0.7, 1.0, 0.6],
            [0.4, 0.5, 0.6, 1.0]
        ])
        
        # Create RecommendationService instance with mock dependencies
        self.recommendation_service = RecommendationService(
            self.mock_redis_client, 
            self.mock_db, 
            self.sample_data, 
            self.sample_similarity_matrix
        )

    def test_get_recommendations_cache_hit(self):
        # Simulate a cache hit
        cached_response = pb2.RecommendationResponse()
        self.mock_redis_client.get.return_value = cached_response.SerializeToString()
        
        # Create request
        request = pb2.RecommendationRequest(
            category='Restaurant',
            city='New York',
            min_rating=4.0,
            min_review_count=50,
            price='$$'
        )
        context = Mock()
        
        # Call method
        response = self.recommendation_service.GetRecommendations(request, context)
        
        # Assertions
        self.mock_redis_client.get.assert_called_once()
        self.assertEqual(response, cached_response)

    def test_get_recommendations_success(self):
        # Mock redis cache miss
        self.mock_redis_client.get.return_value = None
        
        # Mock database max review count
        self.mock_db.fetch_one.return_value = {'max_review_count': 100}
        
        # Create request
        request = pb2.RecommendationRequest(
            category='Restaurant',
            city='New York',
            min_rating=3.5,
            min_review_count=50,
            price='$$'
        )
        context = Mock()
        
        # Call method
        response = self.recommendation_service.GetRecommendations(request, context)
        
        # Assertions
        self.assertTrue(len(response.recommendations) > 0)
        self.mock_redis_client.set.assert_called_once()

    def test_get_recommendations_invalid_rating(self):
        # Create request with invalid rating
        request = pb2.RecommendationRequest(
            category='Restaurant',
            city='New York',
            min_rating=6.0,  # Invalid rating
            min_review_count=50,
            price='$$'
        )
        context = Mock()
        
        # Call method
        response = self.recommendation_service.GetRecommendations(request, context)
        
        # Assertions
        context.set_code.assert_called_once_with(grpc.StatusCode.INVALID_ARGUMENT)
        context.set_details.assert_called_once_with("min_rating must be between 0 and 5.")

    # def test_get_recommendations_no_match(self):
    #     # Mock database max review count
    #     self.mock_db.fetch_one.return_value = {'max_review_count': 100}
        
    #     # Create request with no matching businesses
    #     request = pb2.RecommendationRequest(
    #         category='Spa',  # Category not in sample data
    #         city='London',   # City not in sample data
    #         min_rating=1.0,
    #         min_review_count=10,
    #         price='$$$'
    #     )
    #     context = Mock()
        
    #     # Call method
    #     response = self.recommendation_service.GetRecommendations(request, context)
        
    #     # Assertions
    #     context.set_code.assert_called_once_with(grpc.StatusCode.NOT_FOUND)
    #     context.set_details.assert_called_once_with("No businesses match the given preferences.")

    def test_get_recommendations_data_not_loaded(self):
        # Create service with None data and similarity matrix
        error_service = RecommendationService(
            self.mock_redis_client, 
            self.mock_db, 
            None, 
            None
        )
        
        # Create request
        request = pb2.RecommendationRequest(
            category='Restaurant',
            city='New York',
            min_rating=4.0,
            min_review_count=50,
            price='$$'
        )
        context = Mock()
        
        # Call method
        response = error_service.GetRecommendations(request, context)
        
        # Assertions
        context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
        context.set_details.assert_called_once_with("Data or similarity matrix not loaded.")

    def test_get_recommendations_db_error(self):
        # Mock redis cache miss
        self.mock_redis_client.get.return_value = None
        
        # Mock database error
        self.mock_db.fetch_one.side_effect = Exception("Database error")
        
        # Create request
        request = pb2.RecommendationRequest(
            category='Restaurant',
            city='New York',
            min_rating=4.0,
            min_review_count=50,
            price='$$'
        )
        context = Mock()
        
        # Call method
        response = self.recommendation_service.GetRecommendations(request, context)
        
        # Assertions
        context.set_code.assert_called_once_with(grpc.StatusCode.INTERNAL)
        self.assertTrue("Error fetching max review count" in context.set_details.call_args[0][0])

if __name__ == '__main__':
    unittest.main()
    