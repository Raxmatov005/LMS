from fastapi import APIRouter, status, HTTPException
from model import model
from database import db_dependency
from model import  Users, Roles, LessonRatings, CourseRatings, Enrollments
from routers.users import user_dependency
from utils import is_admin

router = APIRouter(
    prefix='/admin',
    tags=['Admin']
)


@router.get('/get-all-users', status_code=status.HTTP_200_OK)
async def get_all(db: db_dependency,
                  user: user_dependency
                  ):

    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    if not is_admin(db, user):
        raise HTTPException(status_code=403, detail="Forbidden")

    users = db.query(Users, Roles).join(Roles, Users.role_id == Roles.id).all()

    response = [
        {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "name": user.name,
            "phone_number": user.phone_number,
            "created_at": user.created_at,
            "is_active": user.is_active,
            "user_photo": user.user_photo,
            "role_id": user.role_id,
            "role_name": role.role_name
        }
        for user, role in users
    ]

    return response


# @router.put('/edit-users-infos')
# async def edit_users_info(db: db_dependency,
#                   user: user_dependency,
#                   user_id: int,
#                   user_email: str,
#                   user_phone: str,
#                   is_active: bool):



@router.delete('/delete-user',)
async def delete_user(db: db_dependency,
                  user: user_dependency,
                  user_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    if not is_admin(db, user):
        raise HTTPException(status_code=403, detail="Forbidden")

    user_to_delete = db.query(Users).filter(Users.id == user_id).first()

    if user_to_delete is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(LessonRatings).filter(LessonRatings.user_id == user_to_delete.id).delete()
    db.query(CourseRatings).filter(CourseRatings.user_id == user_to_delete.id).delete()
    db.query(Enrollments).filter(Enrollments.user_id == user_to_delete.id).delete()
    db.delete(user_to_delete)
    db.commit()
    return {"detail": "User deleted successfully"}






