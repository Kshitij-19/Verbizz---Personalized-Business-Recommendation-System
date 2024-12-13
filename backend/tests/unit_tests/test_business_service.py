import unittest
from unittest.mock import MagicMock, patch
from services.business.business_service import BusinessService
from codegen import business_service_pb2 as pb2
import grpc


class TestBusinessService(unittest.TestCase):

    def setUp(self):
        # Mock the database and Kafka producer
        self.mock_db = MagicMock()
        self.mock_kafka_producer = MagicMock()
        self.service = BusinessService(db=self.mock_db, kafka_producer=self.mock_kafka_producer)
        self.context = MagicMock()

    def test_get_business_success(self):
        # Mock database response
        self.mock_db.fetch_one.return_value = {
            "id": 1,
            "businessid": "test-id",
            "name": "Test Business",
            "rating": 4.5,
            "review_count": 10,
            "address": "123 Test St",
            "category": "Cafe",
            "city": "Test City",
            "state": "Test State",
            "country": "Test Country",
            "zip_code": "12345",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "phone": "123-456-7890",
            "price": "$$",
            "image_url": "http://example.com/image.jpg",
            "url": "http://example.com",
            "distance": 2.0
        }

        request = pb2.BusinessRequest(id=1)
        response = self.service.GetBusiness(request, self.context)

        # Assertions
        self.assertEqual(response.id, 1)
        self.assertEqual(response.name, "Test Business")
        # self.mock_db.fetch_one.assert_called_once_with("SELECT * FROM Business WHERE id = %s", (1,))
        self.mock_db.fetch_one.assert_called_once_with("SELECT * FROM Business WHERE id = %s".strip(), (1,))

    def test_get_business_not_found(self):
        # Mock no result in the database
        self.mock_db.fetch_one.return_value = None

        request = pb2.BusinessRequest(id=1)
        response = self.service.GetBusiness(request, self.context)

        # Assertions
        self.assertEqual(response.id, 0)
        self.context.set_code.assert_called_once_with(grpc.StatusCode.NOT_FOUND)
        self.context.set_details.assert_called_once_with("Business not found")

    def test_add_business_success(self):
        # Mock no existing business and successful insert
        self.mock_db.fetch_one.side_effect = [None, {"id": 1}]

        request = pb2.NewBusinessRequest(
            businessid="test-id",
            name="Test Business",
            rating=4.5,
            review_count=10,
            address="123 Test St",
            category="Cafe",
            city="Test City",
            state="Test State",
            country="Test Country",
            zip_code="12345",
            latitude=40.7128,
            longitude=-74.0060,
            phone="123-456-7890",
            price="$$",
            image_url="http://example.com/image.jpg",
            url="http://example.com",
            distance=2.0,
            business_hours="9am-5pm"
        )
        response = self.service.AddBusiness(request, self.context)

        # Assertions
        self.assertEqual(response.id, 1)
        self.mock_db.fetch_one.assert_called()
        self.mock_kafka_producer.send.assert_called_once_with(
            'new-business-data',
            value={
                "id": 1,
                "businessid": "test-id",
                "name": "Test Business",
                "rating": 4.5,
                "review_count": 10,
                "address": "123 Test St",
                "category": "Cafe",
                "city": "Test City",
                "price": "$$"
            }
        )

    def test_add_business_duplicate(self):
        # Mock existing business in the database
        self.mock_db.fetch_one.return_value = {"id": 1}

        request = pb2.NewBusinessRequest(
            businessid="test-id",
            name="Test Business",
            rating=4.5,
            review_count=10,
            address="123 Test St",
            category="Cafe",
            city="Test City",
            state="Test State",
            country="Test Country",
            zip_code="12345",
            latitude=40.7128,
            longitude=-74.0060,
            phone="123-456-7890",
            price="$$",
            image_url="http://example.com/image.jpg",
            url="http://example.com",
            distance=2.0,
            business_hours="9am-5pm"
        )
        response = self.service.AddBusiness(request, self.context)

        # Assertions
        self.assertEqual(response.id, 0)
        self.context.set_code.assert_called_once_with(grpc.StatusCode.ALREADY_EXISTS)
        self.context.set_details.assert_called_once_with("Business with this ID or similar details already exists")
