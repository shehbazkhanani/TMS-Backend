from app import app, db  
from models import User 

def insert_user(username, email, password):
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    print("User added successfully")

def query_users():
    users = User.query.all()
    for user in users:
        print(f"Username: {user.username}, Email: {user.email}")

# Example usage
if __name__ == '__main__':
    insert_user('alice', 'alice@example.com', 'alicepassword')
    query_users()
