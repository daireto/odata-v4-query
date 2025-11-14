from mongomock import Database, MongoClient


def get_client():
    return MongoClient()


def seed_data(db: Database):
    db.users.insert_many(
        [
            {
                'name': 'John',
                'email': 'john@example.com',
                'age': 25,
                'addresses': ['123 Main St', '456 Main St'],
                'profile': {'city': 'New York', 'country': 'USA'},
            },
            {
                'name': 'Jane',
                'email': 'jane@example.com',
                'age': 30,
                'addresses': ['456 Main St', '789 Main St'],
                'profile': {'city': 'Los Angeles', 'country': 'USA'},
            },
            {
                'name': 'Alice',
                'email': 'alice@example.com',
                'age': 35,
                'addresses': ['789 Main St', '101 Main St', '102 Main St'],
                'profile': {'city': 'Chicago', 'country': 'USA'},
            },
            {
                'name': 'Bob',
                'email': 'bob1@example.com',
                'age': 28,
                'addresses': ['101 Main St'],
                'profile': {'city': 'Houston', 'country': 'USA'},
            },
            {
                'name': 'Bob',
                'email': 'bob2@example.com',
                'age': 40,
                'addresses': ['102 Main St'],
                'profile': {'city': 'Phoenix', 'country': 'USA'},
            },
            {
                'name': 'Charlie',
                'email': 'charlie@example.com',
                'age': 32,
                'addresses': ['103 Main St', '104 Main St'],
                'profile': {'city': 'Philadelphia', 'country': 'USA'},
            },
            {
                'name': 'David',
                'email': 'david@example.com',
                'age': 41,
                'addresses': ['104 Main St'],
                'profile': {'city': 'San Antonio', 'country': 'USA'},
            },
            {
                'name': 'Eve',
                'email': 'eve@example.com',
                'age': 54,
                'addresses': ['105 Main St'],
                'profile': {'city': 'San Diego', 'country': 'USA'},
            },
            {
                'name': 'Frank',
                'email': 'frank@example.com',
                'age': 29,
                'addresses': ['106 Main St', '107 Main St', '108 Main St'],
                'profile': {'city': 'Dallas', 'country': 'USA'},
            },
            {
                'name': 'Grace',
                'email': 'grace@example.com',
                'age': 37,
                'addresses': ['107 Main St', '108 Main St'],
                'profile': {'city': 'San Jose', 'country': 'USA'},
            },
        ]
    )
