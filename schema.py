from pydantic import BaseModel, EmailStr, constr
from datetime import datetime
class UserCreateSchema(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class ProjectCreateSchema(BaseModel):
    name: constr(min_length=1)

class TaskCreateSchema(BaseModel):
    title: constr(min_length=1)
    description: constr(min_length=1)
    deadline: datetime
    assignee_id: int
    project_id: int