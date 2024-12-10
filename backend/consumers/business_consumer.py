from kafka import KafkaConsumer
from joblib import dump, load
import pandas as pd
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load existing data and similarity matrix
DATA_FILE = "data/data.pkl"
SIMILARITY_MATRIX_FILE = "data/similarity_matrix.pkl"

try:
    data = load(DATA_FILE)
    similarity_matrix = load(SIMILARITY_MATRIX_FILE)
    print("Data and similarity matrix loaded successfully.")
except FileNotFoundError:
    data = pd.DataFrame(columns=['id', 'businessid', 'name', 'rating', 'review_count', 'address', 'category', 'city', 'price'])
    similarity_matrix = None
    print("Initialized with empty data and similarity matrix.")


def update_similarity_matrix(new_data):
    """
    Update the similarity matrix dynamically when new data is added.
    """
    global data, similarity_matrix

    # Print current length of the similarity matrix
    current_length = len(data) if not data.empty else 0
    print(f"Current number of businesses: {current_length}")

    # Combine new data with the existing data
    data = pd.concat([data, pd.DataFrame([new_data])], ignore_index=True)

    # Recompute combined features and update similarity matrix
    data['combined_features'] = (
        data['category'] + ' ' +
        data['city'] + ' ' +
        data['price'] + ' ' +
        data['rating'].apply(lambda x: f"rating_{round(x, 1)}") + ' ' +
        data['review_count'].apply(lambda x: f"reviews_{int(x // 50)}")
    )

    tfidf = TfidfVectorizer(stop_words='english')
    feature_matrix = tfidf.fit_transform(data['combined_features'])
    similarity_matrix = cosine_similarity(feature_matrix)

    # Save updated data and matrix
    dump(data, DATA_FILE)
    dump(similarity_matrix, SIMILARITY_MATRIX_FILE)

    # Print updated length of the similarity matrix
    updated_length = similarity_matrix.shape[0]
    print(f"Updated number of businesses: {updated_length}")

    print("Similarity matrix updated successfully.")

def consume_business_messages():
    # Initialize Kafka Consumer
    consumer = KafkaConsumer(
        'new-business-data',
        bootstrap_servers='localhost:9092',
        group_id='my-consumer-group',
        auto_offset_reset='latest',
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )
    print("Kafka consumer listening for messages...")

    for message in consumer:
        try:
            new_business = message.value
            print(f"Received new business: {new_business}")
            update_similarity_matrix(new_business)
        except Exception as e:
            print(f"Error processing message: {e}")