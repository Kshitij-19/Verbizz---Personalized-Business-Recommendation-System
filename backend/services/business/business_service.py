from concurrent import futures
import grpc
from codegen import business_service_pb2 as pb2
from codegen import business_service_pb2_grpc as pb2_grpc

from db.db import Database

# Initialize database connection
db = Database(db_name="postgres", user="postgres", password="rootpass123")
print("")

class BusinessService(pb2_grpc.BusinessServiceServicer):

    def GetBusiness(self, request, context):
        query = """
        SELECT * FROM Business WHERE id = %s
        """
        business = db.fetch_one(query, (request.id,))
        if not business:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Business not found')
            return pb2.BusinessResponse()

        return pb2.BusinessResponse(
            id=business['id'],
            businessid=business['businessid'],
            name=business['name'],
            rating=business['rating'],
            review_count=business['review_count'],
            address=business['address'],
            category=business['category'],
            city=business['city'],
            state=business['state'],
            country=business['country'],
            zip_code=business['zip_code'],
            latitude=business['latitude'],
            longitude=business['longitude'],
            phone=business['phone'],
            price=business['price'],
            image_url=business['image_url'],
            url=business['url'],
            distance=business['distance']
        )

    def AddBusiness(self, request, context):
        # Check if the businessid already exists
        check_query = "SELECT id FROM Business WHERE businessid = %s"
        existing_business = db.fetch_one(check_query, (request.businessid,))
        if existing_business:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details('Business with this businessid already exists')
            return pb2.BusinessResponse()

        # Insert new business if no duplicate exists
        query = """
        INSERT INTO Business (businessid, name, rating, review_count, address, category, 
                            city, state, country, zip_code, latitude, longitude, 
                            phone, price, image_url, url, distance)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        business_id = db.fetch_one(query, (
            request.businessid, request.name, request.rating, request.review_count, request.address,
            request.category, request.city, request.state, request.country, request.zip_code,
            request.latitude, request.longitude, request.phone, request.price, request.image_url,
            request.url, request.distance
        ))
        return pb2.BusinessResponse(
            id=business_id['id'],
            businessid=request.businessid,
            name=request.name,
            rating=request.rating,
            review_count=request.review_count,
            address=request.address,
            category=request.category,
            city=request.city,
            state=request.state,
            country=request.country,
            zip_code=request.zip_code,
            latitude=request.latitude,
            longitude=request.longitude,
            phone=request.phone,
            price=request.price,
            image_url=request.image_url,
            url=request.url,
            distance=request.distance,
        )

    def GetBusinessByName(self, request, context):
        query = """
        SELECT * FROM Business WHERE name = %s
        """
        business = db.fetch_one(query, (request.name,))
        if not business:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Business not found')
            return pb2.BusinessResponse()

        return pb2.BusinessResponse(
            id=business['id'],
            businessid=business['businessid'],
            name=business['name'],
            rating=business['rating'],
            review_count=business['review_count'],
            address=business['address'],
            category=business['category'],
            city=business['city'],
            state=business['state'],
            country=business['country'],
            zip_code=business['zip_code'],
            latitude=business['latitude'],
            longitude=business['longitude'],
            phone=business['phone'],
            price=business['price'],
            image_url=business['image_url'],
            url=business['url'],
            distance=business['distance']
        )