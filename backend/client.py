import grpc
from codegen import business_service_pb2 as pb2
from codegen import business_service_pb2_grpc as pb2_grpc
from codegen import recommendation_service_pb2 as rec_pb2
from codegen import recommendation_service_pb2_grpc as rec_pb2_grpc
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
                review_count=550,
                address="128 Main Street",
                category="Cafe",
                city="Boulder",
                state="CO",
                country="USA",
                zip_code="85884",
                latitude=77.7126,
                longitude=-24.0060,
                phone="685-456-4830",
                price="$$",
                image_url="http://example2.com/image2.jpg",
                url="http://example2.com",
                distance=1
            ))
            print("Added Business:")
            print(f"  ID: {response.id}")
            print(f"  Name: {response.name}")
            print(f"  Rating: {response.rating}")
            print(f"  Category: {response.category}")
            print(f"  City: {response.city}")
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
                preferences='{"category": ["Cafe", "Korean"], "city": "New York"}'
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

def test_get_business_by_location():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = pb2_grpc.BusinessServiceStub(channel)
        try:
            response = stub.GetBusinessByLocation(pb2.BusinessByLocationRequest(
                latitude=40.7128,
                longitude=-74.0060,
                radius=5.0  # 5 km
            ))
            print("Businesses by Location:", response)
        except grpc.RpcError as e:
            print(f"Error during GetBusinessByLocation RPC: {e.details()} (Code: {e.code()})")


def test_get_business_by_category():
    """
    Test the GetBusinessByCategory RPC by querying for businesses in a specific category.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = pb2_grpc.BusinessServiceStub(channel)
            response = stub.GetBusinessByCategory(pb2.CategoryRequest(category="Cafe"))
            print("Businesses by Category:", response)
    except grpc.RpcError as e:
        print(f"Error during GetBusinessByCategory RPC: {e.details()} (Code: {e.code()})")


def test_get_business_by_rating():
    """
    Test the GetBusinessByRating RPC by querying for businesses with a minimum rating.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = pb2_grpc.BusinessServiceStub(channel)
            response = stub.GetBusinessByRating(pb2.RatingRequest(min_rating=4.0))
            print("Businesses by Rating:", response)
    except grpc.RpcError as e:
        print(f"Error during GetBusinessByRating RPC: {e.details()} (Code: {e.code()})")


def test_get_business_by_proximity():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = pb2_grpc.BusinessServiceStub(channel)
        try:
            response = stub.GetBusinessByProximity(pb2.BusinessByProximityRequest(
                latitude=40.7128,
                longitude=-74.0060,
                limit=2  # Top 2 closest businesses
            ))
            print("Businesses by Proximity:", response)
        except grpc.RpcError as e:
            print(f"Error during GetBusinessByProximity RPC: {e.details()} (Code: {e.code()})")


def test_get_trending_businesses():
    """
    Test the GetTrendingBusinesses RPC by querying for trending businesses.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = pb2_grpc.BusinessServiceStub(channel)
            response = stub.GetTrendingBusinesses(pb2.TrendingRequest())
            print("Trending Businesses:", response)
    except grpc.RpcError as e:
        print(f"Error during GetTrendingBusinesses RPC: {e.details()} (Code: {e.code()})")


def test_get_recommendations():
    """
    Test the GetRecommendations RPC by sending a request with user preferences.
    """
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = rec_pb2_grpc.RecommendationServiceStub(channel)
            # Example: Recommendation request
            request = rec_pb2.RecommendationRequest(
                category=["Korean", "Tapas/Small Plates"],
                city="New York",
                min_rating=4.5,
                min_review_count=120,
                price="$$"
            )
            response = stub.GetRecommendations(request)
            if response.recommendations:
                print("Recommendations:")
                for rec in response.recommendations:
                    print(f"  Name: {rec.name}")
                    print(f"  Category: {rec.category}")
                    print(f"  Rating: {round(rec.rating, 2)}")
                    print(f"  Review Count: {rec.review_count}")
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
    #
    # print("\nTesting GetBusiness RPC:")
    # test_get_business()
    #
    # print("\nTesting GetBusinessByName RPC:")
    # test_get_business_by_name()
    #
    # print("\nTesting GetBusinessByLocation RPC:")
    # test_get_business_by_location()
    #
    # print("\nTesting GetBusinessByCategory RPC:")
    # test_get_business_by_category()
    #
    # print("\nTesting GetBusinessByRating RPC:")
    # test_get_business_by_rating()
    #
    # print("\nTesting GetBusinessByProximity RPC:")
    # test_get_business_by_proximity()
    #
    # print("\nTesting GetTrendingBusinesses RPC:")
    # test_get_trending_businesses()
    #
    # print("Testing RegisterUser RPC:")
    # test_register_user()
    #
    print("\nTesting LoginUser RPC:")
    test_login_user()
    #
    # if token:
    #     print("\nTesting GetUserProfile RPC:")
    #     test_get_user_profile(token, user_id)
    #
    #     print("\nTesting UpdateUserProfile RPC:")
    #     test_update_user_profile(token)
    #
    #     print("\nTesting DeleteUser RPC:")
    #     test_delete_user(token)
    # #
    # print("\nTesting GetRecommendations RPC:")
    # test_get_recommendations()