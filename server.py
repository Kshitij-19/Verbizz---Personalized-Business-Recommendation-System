from concurrent import futures
import grpc
from codegen import business_service_pb2_grpc as pb2_grpc
from services.business.business_service import BusinessService

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_BusinessServiceServicer_to_server(BusinessService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server is running on port 50051...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()