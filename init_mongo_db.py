from pymongo import MongoClient

# MongoDB connection URI (edit if needed)
MONGODB_URI = 'mongodb://localhost:27017/'
DB_NAME = 'travel_management'

# Collections to create
collections = [
    'users',
    'trips',
    'payments',
    'notifications',
    'support_requests'
]

def main():
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    for col in collections:
        if col not in db.list_collection_names():
            db.create_collection(col)
            print(f"Created collection: {col}")
        else:
            print(f"Collection already exists: {col}")
    print(f"Database '{DB_NAME}' is ready.")

if __name__ == '__main__':
    main() 