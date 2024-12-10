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
        try:
            # Check if a similar business already exists
            check_query = """
            SELECT id FROM Business 
            WHERE businessid = %s OR 
                (name = %s AND address = %s AND city = %s AND state = %s AND country = %s)
            """
            existing_business = db.fetch_one(check_query, (
                request.businessid, request.name, request.address, request.city, request.state, request.country
            ))

            if existing_business:
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details('Business with this ID or similar details already exists')
                return pb2.BusinessResponse()

            # Insert new business if no duplicate exists
            query = """
            INSERT INTO Business (businessid, name, rating, review_count, address, category, 
                                city, state, country, zip_code, latitude, longitude, 
                                phone, price, image_url, url, distance, business_hours)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            business_id = db.fetch_one(query, (
                request.businessid, request.name, request.rating, request.review_count, request.address,
                request.category, request.city, request.state, request.country, request.zip_code,
                request.latitude, request.longitude, request.phone, request.price, request.image_url,
                request.url, request.distance, request.business_hours
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
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error')
            print("Exception occurred:", e)
            return pb2.BusinessResponse()

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
    

    def GetBusinessByLocation(self, request, context):
        try:
            query = """
            SELECT *
            FROM Business
            WHERE earth_box(ll_to_earth(%s, %s), %s) @> ll_to_earth(latitude, longitude) LIMIT 3
            """
            businesses = db.fetch_all(query, (request.latitude, request.longitude, request.radius * 1000))  # radius in meters

            if not businesses:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('No businesses found near the specified location')
                return pb2.BusinessListResponse(businesses=[])

            business_list = [
                pb2.BusinessResponse(
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
                    distance=request.radius
                )
                for business in businesses
            ]
            return pb2.BusinessListResponse(businesses=business_list)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error')
            return pb2.BusinessListResponse(businesses=[])

    def GetBusinessByCategory(self, request, context):
        query = "SELECT * FROM Business WHERE category ILIKE %s  LIMIT 3"
        businesses = db.fetch_all(query, (f"%{request.category}%",))
        if not businesses:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('No businesses found in the specified category')
            return pb2.BusinessListResponse()

        return pb2.BusinessListResponse(
            businesses=[self.map_to_business_response(business) for business in businesses]
        )

    def GetBusinessByRating(self, request, context):
        query = "SELECT * FROM Business WHERE rating >= %s  LIMIT 3"
        businesses = db.fetch_all(query, (request.min_rating,))
        if not businesses:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('No businesses found with the specified rating')
            return pb2.BusinessListResponse()

        return pb2.BusinessListResponse(
            businesses=[self.map_to_business_response(business) for business in businesses]
        )

    def GetBusinessByProximity(self, request, context):
        try:
            query = """
            SELECT *, (earth_distance(ll_to_earth(latitude, longitude), ll_to_earth(%s, %s))) AS calculated_distance
            FROM Business
            ORDER BY calculated_distance ASC
            LIMIT %s
            """
            businesses = db.fetch_all(query, (request.latitude, request.longitude, request.limit))

            if not businesses:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('No businesses found')
                return pb2.BusinessListResponse(businesses=[])

            business_list = [
                pb2.BusinessResponse(
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
                    distance=business['calculated_distance']
                )
                for business in businesses
            ]
            return pb2.BusinessListResponse(businesses=business_list)
        except Exception as e:
            print("Exception is: ", e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Internal server error')
            return pb2.BusinessListResponse(businesses=[])


    def GetTrendingBusinesses(self, request, context):
        query = "SELECT * FROM Business ORDER BY review_count DESC LIMIT 3"
        businesses = db.fetch_all(query)
        if not businesses:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('No trending businesses found')
            return pb2.BusinessListResponse()

        return pb2.BusinessListResponse(
            businesses=[self.map_to_business_response(business) for business in businesses]
        )

    @staticmethod
    def map_to_business_response(business):
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
            distance=business.get('distance', 0.0),
            business_hours=business.get('business_hours', '')
        )