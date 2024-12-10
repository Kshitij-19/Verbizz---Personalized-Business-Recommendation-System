import grpc
from codegen import business_service_pb2 as pb2
from codegen import business_service_pb2_grpc as pb2_grpc
import uuid
from codegen import user_service_pb2 as user_pb2
from codegen import user_service_pb2_grpc as user_pb2_grpc

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

def test_register_user():
    """
    Test the RegisterUser RPC by registering a new user.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = user_pb2_grpc.UserServiceStub(channel)
            response = stub.RegisterUser(user_pb2.RegisterUserRequest(
                email="testuser@example.com",
                password="securepassword123",
                name="Test User",
                preferences='{"category": ["Cafe", "Restaurant"], "location": "New York"}'
            ))
            print("RegisterUser Response:", response)
    except grpc.RpcError as e:
        print(f"Error during RegisterUser RPC: {e.details()} (Code: {e.code()})")


def test_get_user_profile(token, user_id):
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = user_pb2_grpc.UserServiceStub(channel)
            metadata = [('authorization', token)]
            response = stub.GetUserProfile(user_pb2.GetUserProfileRequest(user_id=user_id), metadata=metadata)
            print("GetUserProfile Response:", response)
    except grpc.RpcError as e:
        print(f"Error during GetUserProfile RPC: {e.details()} (Code: {e.code()})")



def test_update_user_profile(token):
    """
    Test the UpdateUserProfile RPC by updating the user's name and preferences.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = user_pb2_grpc.UserServiceStub(channel)
            # Set the token in metadata
            metadata = [('authorization', token)]
            response = stub.UpdateUserProfile(user_pb2.UpdateUserProfileRequest(
                user_id=1,
                name="Updated User",
                preferences='{"category": ["Gym", "Spa"], "location": "Los Angeles"}'
            ), metadata=metadata)
            print("UpdateUserProfile Response:", response)
    except grpc.RpcError as e:
        print(f"Error during UpdateUserProfile RPC: {e.details()} (Code: {e.code()})")


def test_delete_user(token):
    """
    Test the DeleteUser RPC by deleting the user account.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = user_pb2_grpc.UserServiceStub(channel)
            # Set the token in metadata
            metadata = [('authorization', token)]
            response = stub.DeleteUser(user_pb2.DeleteUserRequest(user_id=1), metadata=metadata)
            print("DeleteUser Response:", response)
    except grpc.RpcError as e:
        print(f"Error during DeleteUser RPC: {e.details()} (Code: {e.code()})")

def test_login_user():
    """
    Test the LoginUser RPC by logging in a registered user.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = user_pb2_grpc.UserServiceStub(channel)
            response = stub.LoginUser(user_pb2.LoginUserRequest(
                email="testuser@example.com",
                password="securepassword123"
            ))
            print("LoginUser Response:", response)
            return response.token, response.user_id  # Return token and user_id
    except grpc.RpcError as e:
        print(f"Error during LoginUser RPC: {e.details()} (Code: {e.code()})")

def test_get_business_by_name():
    """
    Test the GetBusinessByName RPC by querying for a business by its name.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = pb2_grpc.BusinessServiceStub(channel)
            response = stub.GetBusinessByName(pb2.BusinessByNameRequest(name="Test Cafe"))
            print("Business Details by Name:", response)
    except grpc.RpcError as e:
        print(f"Error during GetBusinessByName RPC: {e.details()} (Code: {e.code()})")

if __name__ == "__main__":
    print("Testing AddBusiness RPC:")
    test_add_business()
    print("\nTesting GetBusiness RPC:")
    test_get_business()
    print("\nTesting GetBusinessByName RPC:")
    test_get_business_by_name()

    print("Testing RegisterUser RPC:")
    test_register_user()

    print("\nTesting LoginUser RPC:")
    token, user_id = test_login_user()

    if token:
        print("\nTesting GetUserProfile RPC:")
        test_get_user_profile(token, user_id)

        print("\nTesting UpdateUserProfile RPC:")
        test_update_user_profile(token)

        print("\nTesting DeleteUser RPC:")
        test_delete_user(token)