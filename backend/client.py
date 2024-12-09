import grpc
from codegen import business_service_pb2 as pb2
from codegen import business_service_pb2_grpc as pb2_grpc
from codegen import recommendation_service_pb2 as rec_pb2
from codegen import recommendation_service_pb2_grpc as rec_pb2_grpc
import uuid


def test_get_business():
    """
    Test the GetBusiness RPC by querying for a specific business by ID.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = pb2_grpc.BusinessServiceStub(channel)
            # Example: Fetch business with ID 1
            response = stub.GetBusiness(pb2.BusinessRequest(id=1))
            print("Business Details:")
            print(f"  ID: {response.id}")
            print(f"  Name: {response.name}")
            print(f"  Rating: {response.rating}")
            print(f"  Category: {response.category}")
            print(f"  City: {response.city}")
            print(f"  State: {response.state}")
    except grpc.RpcError as e:
        print(f"Error during GetBusiness RPC: {e.details()} (Code: {e.code()})")


def test_add_business():
    """
    Test the AddBusiness RPC by adding a new business with a unique businessid.
    """
    unique_businessid = str(uuid.uuid4())  # Generate a unique businessid
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = pb2_grpc.BusinessServiceStub(channel)
            response = stub.AddBusiness(pb2.NewBusinessRequest(
                businessid=unique_businessid,
                name="Test Cafe",
                rating=4.5,
                review_count=120,
                address="123 Main Street",
                category="Cafe",
                city="New York",
                state="NY",
                country="USA",
                zip_code="10001",
                latitude=40.7128,
                longitude=-74.0060,
                phone="123-456-7890",
                price="$$",
                image_url="http://example.com/image.jpg",
                url="http://example.com",
                distance=0.5
            ))
            print("Added Business:")
            print(f"  ID: {response.id}")
            print(f"  Name: {response.name}")
            print(f"  Rating: {response.rating}")
            print(f"  Category: {response.category}")
            print(f"  City: {response.city}")
    except grpc.RpcError as e:
        print(f"Error during AddBusiness RPC: {e.details()} (Code: {e.code()})")


def test_get_recommendations():
    """
    Test the GetRecommendations RPC by sending a request with user preferences.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = rec_pb2_grpc.RecommendationServiceStub(channel)
            # Example: Recommendation request
            request = rec_pb2.RecommendationRequest(
                category="Korean",
                city="New York",
                preferences="Asian",
                min_rating=4.0
            )
            response = stub.GetRecommendations(request)
            if response.recommendations:
                print("Recommendations:")
                for rec in response.recommendations:
                    print(f"  Name: {rec.name}")
                    print(f"  Category: {rec.category}")
                    print(f"  Rating: {rec.rating}")
                    print(f"  City: {rec.city}")
                    print(f"  Address: {rec.address}")
                    print(f"  Phone: {rec.phone}")
                    print(f"  Price: {rec.price}")
                    print(f"  Image URL: {rec.image_url}")
                    print(f"  Business URL: {rec.url}")
                    print("-" * 50)
            else:
                print("No recommendations found.")
    except grpc.RpcError as e:
        print(f"Error during GetRecommendations RPC: {e.details()} (Code: {e.code()})")


if __name__ == "__main__":
    # print("Testing AddBusiness RPC:")
    # test_add_business()
    # print("\nTesting GetBusiness RPC:")
    # test_get_business()
    print("\nTesting GetRecommendations RPC:")
    test_get_recommendations()