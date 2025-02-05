from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from model.model import Users, Roles
from database import db_dependency
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from auth.scheme import CreateUserRequest,Token
from utils import hash_password,authenticate_user,create_access_token, get_current_user,verify_password
from model.model import Users as users
import re


router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


@router.post("/registration")
async def create_user(db: db_dependency,
                      create_user_request: CreateUserRequest):

    if create_user_request.password != create_user_request.confirm_password:
        raise HTTPException(status_code=401, detail='Passwords are not the same!')

    user_email = db.query(Users).filter(Users.email == create_user_request.email).first()
    user_username = db.query(Users).filter(Users.username == create_user_request.username).first()
    user_phone = db.query(Users).filter(Users.phone_number == create_user_request.phone_number).first()

    if user_email is not None:
        raise HTTPException(status_code=409, detail='Email already exist')

    if user_username is not None:
        raise HTTPException(status_code=409, detail='Username already exist')

    if user_phone is not None:
        raise HTTPException(status_code=409, detail='Phone already exist')

    user_count = db.query(users).count()

    user_role = db.query(Roles).filter(Roles.role_name == "user").first()
    if user_role is None:
        create_role = Roles(
            role_name="user"
        )
        db.add(create_role)
        db.commit()
    admin_role = db.query(Roles).filter(Roles.role_name == 'admin').first()
    if admin_role is None:
        create_admin_role = Roles(
            role_name="admin"
        )
        db.add(create_admin_role)
        db.commit()

    admin_role_query = db.query(Roles).filter(Roles.role_name == 'admin').first()
    user_role_query = db.query(Roles).filter(Roles.role_name == "user").first()

    if user_count == 0:
        create_user_model = Users(
            email=create_user_request.email,
            name=create_user_request.name,
            role_id=admin_role_query.id,
            username=create_user_request.username,
            hashed_password=hash_password(create_user_request.password),
            phone_number=create_user_request.phone_number,
        )
        db.add(create_user_model)
        db.commit()
        return {'message': 'Account created successfully as admin'}
    else:
        create_user_model = Users(
            email=create_user_request.email,
            name=create_user_request.name,
            role_id=user_role_query.id,
            username=create_user_request.username,
            hashed_password=hash_password(create_user_request.password),
            phone_number=create_user_request.phone_number,
        )

        db.add(create_user_model)
        db.commit()
        return {'massage': 'Account created successfully'}


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')
    token = create_access_token(user.username, user.id, timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'bearer'}


@router.put("/password")
async def change_password(
        db: db_dependency,
        current_password: str,
        password: str,
        password2: str,
        user: dict = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    user_id = user.get('id')
    user_model = db.query(users).filter(users.id == user_id).first()

    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")

    if password!= password2:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if not verify_password(current_password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect current password")

    if len(password2) < 6:
        raise HTTPException(status_code=400,detail="Password must be at least 6 characters long!")
    if not re.search(r"[A-Z]", password2):
        raise HTTPException(status_code=400, detail='There must be at least one Capital letter')

    user_model.hashed_password = hash_password(password2)
    db.add(user_model)
    db.commit()
    return {'message': 'Password changed successfully'}







