import grpc
from codegen import business_service_pb2 as pb2
from codegen import business_service_pb2_grpc as pb2_grpc
import uuid

def test_get_business():
    """
    Test the GetBusiness RPC by querying for a specific business by ID.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = pb2_grpc.BusinessServiceStub(channel)
            response = stub.GetBusiness(pb2.BusinessRequest(id=1))
            print("Business Details:", response)
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
                distance=0.5,
                business_hours="Mon-Fri: 9am-9pm"
            ))
            print("Added Business:", response)
    except grpc.RpcError as e:
        print(f"Error during AddBusiness RPC: {e.details()} (Code: {e.code()})")


if __name__ == "__main__":
    print("Testing AddBusiness RPC:")
    test_add_business()
    print("\nTesting GetBusiness RPC:")
    test_get_business()