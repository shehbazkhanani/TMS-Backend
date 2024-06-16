from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask_cors import CORS
from pydantic import ValidationError
from config import Config
from models import Project, db, User, Task 
from schema import UserCreateSchema, UserLoginSchema, ProjectCreateSchema,TaskCreateSchema
from datetime import datetime
import logging
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
# Initialize CORS with specific origins, methods, and headers
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})


app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# register 
@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()

    try:
        # Validate incoming JSON data against UserCreateSchema
        user_data = UserCreateSchema(**data)  # Use schema to parse and validate data
    except ValidationError as e:
        app.logger.error(f"Validation error: {e}")
        return jsonify({'error': e.errors()}), 400  # Return validation errors as JSON

    # Check if user with the same email already exists
    existing_user = User.query.filter_by(email=user_data.email).first()
    if existing_user:
        app.logger.error(f"User already exists: {user_data.email}")
        return jsonify({'message': 'Email already exists'}), 400

    # Create a new User object and add it to the database
    new_user = User(username=user_data.username, email=user_data.email)
    new_user.set_password(user_data.password)
    db.session.add(new_user)
    db.session.commit()

    app.logger.info(f"User created: {user_data.username}")

    return jsonify({'message': 'User created successfully'}), 201

# login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    try:
        # Validate incoming JSON data against UserLoginSchema
        user_data = UserLoginSchema(**data)
    except ValidationError as e:
        app.logger.error(f"Validation error: {e}")
        return jsonify({'error': e.errors()}), 400  # Return validation errors as JSON

    email = user_data.email
    password = user_data.password

    # Retrieve the user from the database based on email
    user = User.query.filter_by(email=email).first()

   

    # Check if the user exists and verify password
    if user and user.check_password(password):
        # Generate JWT token
        access_token = create_access_token(identity=user.id,expires_delta=False)
        app.logger.error(f"Users: {user}")
        return jsonify({'access_token': access_token, 'user_id': user.id}), 200
    else:
        app.logger.error(f"Invalid credentials for email: {email}")
        return jsonify({'message': 'Invalid credentials'}), 401
    
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# for create project
@app.route('/create_project', methods=['POST'])
@jwt_required()
def create_project():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    print("current user id: %s" % current_user_id)
    try:
        project_data = ProjectCreateSchema(**data)
    except ValidationError as e:
        app.logger.error(f"Validation error: {e}")
        return jsonify({'error': e.errors()}), 400

    new_project = Project(
        name=project_data.name,
        user_id=current_user_id
    )
    db.session.add(new_project)
    db.session.commit()

    app.logger.info(f"Project created: {project_data.name} by User ID: {current_user_id}")

    return jsonify({'id': new_project.id, 'name' : new_project.name}), 201

# for delete project
@app.route('/delete_project/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    current_user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=current_user_id).first()

    if not project:
        app.logger.error(f"Project not found or unauthorized: Project ID {project_id}, User ID {current_user_id}")
        return jsonify({'message': 'Project not found or unauthorized'}), 404

    try:
        db.session.delete(project)
        db.session.commit()
        return jsonify({'message': 'Project deleted successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()  
        app.logger.error(f"Failed to delete project: {str(e)}")
        return jsonify({'message': 'Failed to delete project', 'error': str(e)}), 500

# for get Project
@app.route('/get_projects', methods=['GET'])
@jwt_required()
def get_projects():
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id).first()

    if not user:
        app.logger.error(f"User not found for email: {current_user_id}")
        return jsonify({'message': 'User not found'}), 404

    projects = Project.query.filter_by(user_id=user.id).all()
    
    if not projects:
        app.logger.info(f"No projects found for user_id: {user.id}")

    projects_data = [{'id': project.id, 'name': project.name} for project in projects]
    
    app.logger.info(f"Projects data: {projects_data}")

    return jsonify(projects_data), 200

# for fetching users
@app.route('/get_users', methods=['GET'])
@jwt_required()
def get_users():
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id).first()

    if not user:
        app.logger.error(f"User not found for email: {current_user_id}")
        return jsonify({'message': 'User not found'}), 404

    users = User.query.all()
    
    if not users:
        app.logger.info(f"No users found")

    users_data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
    
    app.logger.info(f"Users data: {users_data}")

    return jsonify(users_data), 200

# for add task
@app.route('/add_task', methods=['POST'])
@jwt_required()
def create_task():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    print("current user id: %s" % current_user_id)
    try:
        task_data = TaskCreateSchema(**data)
    except ValidationError as e:
        app.logger.error(f"Validation error: {e}")
        return jsonify({'error': e.errors()}), 400

    new_task = Task(
        title=task_data.title,
        assignee_id=task_data.assignee_id,
        description=task_data.description,
        project_id=task_data.project_id,
        deadline= task_data.deadline
    )
    db.session.add(new_task)
    db.session.commit()

    app.logger.info(f"Task created: {new_task.title} by User ID: {current_user_id}")

    return jsonify({'message': 'Project created successfully', 'task_id': new_task.id, 'task_title' : new_task.title}), 201

# for get tasks
@app.route('/get_tasks/<int:project_id>', methods=['GET'])
@jwt_required()
def get_tasks(project_id):
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id).first()

    if not user:
        app.logger.error(f"User not found for email: {current_user_id}")
        return jsonify({'message': 'User not found'}), 404
    
    project = Project.query.filter_by(id=project_id).first()
    
    if not project:
        app.logger.error(f"Project not found: {project_id}")
        return jsonify({'message': 'Project not found'}), 404

    tasks = Task.query.filter_by(project_id=project_id).all()
    
    if not tasks:
        app.logger.info(f"No tasks found for user_id: {user.id}")

    tasks_data = [{'id': task.id, 'title': task.title, 'description': task.description, 'deadline': task.deadline, "assignee_id": task.assignee.username, "project_id":task.project.name } for task in tasks]
    
    app.logger.info(f"Tasks data: {tasks_data}")

    return jsonify(tasks_data), 200

#for delete tasks
@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id).first()

    if not user:
        app.logger.error(f"User not found for ID: {current_user_id}")
        return jsonify({'message': 'User not found'}), 404

    task = Task.query.filter_by(id=task_id).first()

    if not task:
        app.logger.error(f"Task not found: {task_id}")
        return jsonify({'message': 'Task not found'}), 404

    if task.project.user_id != current_user_id:  # Ensure user can only delete their own tasks
        app.logger.error(f"User {current_user_id} not authorized to delete task {task_id}")
        return jsonify({'message': 'Not authorized to delete this task'}), 403

    try:
        db.session.delete(task)
        db.session.commit()

        app.logger.info(f"Task {task_id} deleted by user {current_user_id}")
        return jsonify({'message': 'Task deleted successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback changes in case of error
        app.logger.error(f"Failed to delete task: {str(e)}")
        return jsonify({'message': 'Failed to delete task', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

