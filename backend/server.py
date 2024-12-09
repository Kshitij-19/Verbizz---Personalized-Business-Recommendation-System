from concurrent import futures
import grpc
from codegen import business_service_pb2_grpc as business_pb2_grpc
from codegen import user_service_pb2_grpc as user_pb2_grpc
from services.business.business_service import BusinessService
from services.user.user_service import UserService

def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add BusinessService to the server
    business_pb2_grpc.add_BusinessServiceServicer_to_server(BusinessService(), server)

    # Add UserService to the server
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)

    # Start the server on port 50051
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server is running on port 50051...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()