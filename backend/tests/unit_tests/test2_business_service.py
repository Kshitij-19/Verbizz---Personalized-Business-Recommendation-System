import unittest
from unittest.mock import Mock, patch
import grpc
from codegen import business_service_pb2 as pb2
from services.business.business_service import BusinessService

class TestBusinessService(unittest.TestCase):
    def setUp(self):
        # Create mock dependencies
        self.mock_db = Mock()
        self.mock_kafka_producer = Mock()
        
        # Create BusinessService instance with mock dependencies
        self.business_service = BusinessService(self.mock_db, self.mock_kafka_producer)

    def test_get_business_success(self):
        # Mock database response for a business
        mock_business = {
            'id': 1,
            'businessid': 'biz123',
            'name': 'Test Business',
            'rating': 4.5,
            'review_count': 100,
            'address': '123 Test St',
            'category': 'Restaurant',
            'city': 'Test City',
            'state': 'TS',
            'country': 'TestLand',
            'zip_code': '12345',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'phone': '1234567890',
            'price': '$$',
            'image_url': 'http://test.com/image.jpg',
            'url': 'http://test.com',
            'distance': 0.5
        }
        
        self.mock_db.fetch_one.return_value = mock_business
        
        # Create request
        request = pb2.BusinessRequest(id=1)
        context = Mock()
        
        # Call method
        response = self.business_service.GetBusiness(request, context)
        
        # Assertions
        self.assertEqual(response.id, mock_business['id'])
        self.assertEqual(response.name, mock_business['name'])
        self.mock_db.fetch_one.assert_called_once()

    def test_get_business_not_found(self):
        # Mock database return for non-existent business
        self.mock_db.fetch_one.return_value = None
        
        # Create request
        request = pb2.BusinessRequest(id=999)
        context = Mock()
        
        # Call method
        response = self.business_service.GetBusiness(request, context)
        
        # Assertions
        context.set_code.assert_called_once_with(grpc.StatusCode.NOT_FOUND)
        context.set_details.assert_called_once_with('Business not found')
        self.assertEqual(response, pb2.BusinessResponse())

    def test_add_business_success(self):
        # Mock database to return no existing business and a new business ID
        self.mock_db.fetch_one.side_effect = [None, {'id': 1}]
        
        # Create request
        request = pb2.NewBusinessRequest(
            businessid='biz123',
            name='New Business',
            rating=4.0,
            review_count=50,
            address='456 New St',
            category='Cafe',
            city='New City',
            state='NS',
            country='NewLand'
        )
        context = Mock()
        
        # Call method
        response = self.business_service.AddBusiness(request, context)
        
        # Assertions
        self.assertEqual(response.id, 1)
        self.assertEqual(response.name, 'New Business')
        self.mock_kafka_producer.send.assert_called_once()

    def test_add_business_already_exists(self):
        # Mock database to return an existing business
        self.mock_db.fetch_one.return_value = {'id': 1}
        
        # Create request
        request = pb2.NewBusinessRequest(
            businessid='biz123',
            name='Existing Business',
            address='123 Exist St',
            city='Exist City',
            state='ES',
            country='ExistLand'
        )
        context = Mock()
        
        # Call method
        response = self.business_service.AddBusiness(request, context)
        
        # Assertions
        context.set_code.assert_called_once_with(grpc.StatusCode.ALREADY_EXISTS)
        context.set_details.assert_called_once_with('Business with this ID or similar details already exists')
        self.assertEqual(response, pb2.BusinessResponse())

    # def test_get_business_by_name_success(self):
    #     # Mock database response for a business
    #     mock_business = {
    #         'id': 1,
    #         'name': 'Test Business',
    #         'businessid': 'biz123',
    #         'rating': 4.5,
    #         'review_count': 100,
    #         'address': '123 Test St'
    #     }
        
    #     self.mock_db.fetch_one.return_value = mock_business
        
    #     # Create request
    #     request = pb2.BusinessByNameRequest(name='Test Business')
    #     context = Mock()
        
    #     # Call method
    #     response = self.business_service.GetBusinessByName(request, context)
        
    #     # Assertions
    #     self.assertEqual(response.name, 'Test Business')
    #     self.mock_db.fetch_one.assert_called_once()

    def test_get_business_by_name_not_found(self):
        # Mock database return for non-existent business
        self.mock_db.fetch_one.return_value = None
        
        # Create request
        request = pb2.BusinessByNameRequest(name='Nonexistent Business')
        context = Mock()
        
        # Call method
        response = self.business_service.GetBusinessByName(request, context)
        
        # Assertions
        context.set_code.assert_called_once_with(grpc.StatusCode.NOT_FOUND)
        context.set_details.assert_called_once_with('Business not found')
        self.assertEqual(response, pb2.BusinessResponse())

    # def test_get_business_by_location_success(self):
    #     # Mock database response for businesses near a location
    #     mock_businesses = [
    #         {
    #             'id': 1,
    #             'businessid': 'biz1',
    #             'name': 'Business 1',
    #             'latitude': 40.7128,
    #             'longitude': -74.0060
    #         },
    #         {
    #             'id': 2,
    #             'businessid': 'biz2',
    #             'name': 'Business 2',
    #             'latitude': 40.7129,
    #             'longitude': -74.0061
    #         }
    #     ]
        
    #     self.mock_db.fetch_all.return_value = mock_businesses
        
    #     # Create request
    #     request = pb2.BusinessByLocationRequest(
    #         latitude=40.7128,
    #         longitude=-74.0060,
    #         radius=1
    #     )
    #     context = Mock()
        
    #     # Call method
    #     response = self.business_service.GetBusinessByLocation(request, context)
        
    #     # Assertions
    #     self.assertEqual(len(response.businesses), 2)
    #     self.mock_db.fetch_all.assert_called_once()

    def test_get_business_by_location_not_found(self):
        # Mock database return for no businesses near location
        self.mock_db.fetch_all.return_value = []
        
        # Create request
        request = pb2.BusinessByLocationRequest(
            latitude=0,
            longitude=0,
            radius=1
        )
        context = Mock()
        
        # Call method
        response = self.business_service.GetBusinessByLocation(request, context)
        
        # Assertions
        context.set_code.assert_called_once_with(grpc.StatusCode.NOT_FOUND)
        context.set_details.assert_called_once_with('No businesses found near the specified location')
        self.assertEqual(len(response.businesses), 0)

if __name__ == '__main__':
    unittest.main()