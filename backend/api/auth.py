from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from models.auth import (
    Token,
    UserCreate,
    UserResponse,
    AuthResponse,
    ChangePassword,
    MessageResponse,
)
from middleware.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from config.settings import settings

logger = __import__("logging").getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    logger.info(f"Registration attempt for user: {user_data.username}")

    from db.mongodb import MongoDB
    from bson import ObjectId

    existing_user = await MongoDB.db.users.find_one({
        "$or": [
            {"email": user_data.email},
            {"username": user_data.username}
        ]
    })

    if existing_user:
        logger.warning(f"Registration failed: user already exists - {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

    hashed_password = get_password_hash(user_data.password)

    user_doc = {
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "hashed_password": hashed_password,
        "role": "analyst",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = await MongoDB.db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    access_token = create_access_token(
        data={
            "sub": str(user_doc["_id"]),
            "email": user_doc["email"],
            "username": user_doc["username"],
            "role": user_doc["role"]
        }
    )

    logger.info(f"User registered successfully: {user_data.username}")

    return AuthResponse(
        user=UserResponse(
            id=str(user_doc["_id"]),
            email=user_doc["email"],
            username=user_doc["username"],
            full_name=user_doc.get("full_name"),
            role=UserResponse.__fields__["role"].type_(user_doc["role"]),
            is_active=user_doc["is_active"],
            created_at=user_doc["created_at"]
        ),
        token=Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return access token."""
    logger.info(f"Login attempt for user: {form_data.username}")

    from db.mongodb import MongoDB

    user = await MongoDB.db.users.find_one({
        "$or": [
            {"email": form_data.username},
            {"username": form_data.username}
        ]
    })

    if not user:
        logger.warning(f"Login failed: user not found - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user["hashed_password"]):
        logger.warning(f"Login failed: invalid password - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        logger.warning(f"Login failed: inactive user - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        data={
            "sub": str(user["_id"]),
            "email": user["email"],
            "username": user["username"],
            "role": user.get("role", "viewer")
        }
    )

    logger.info(f"User logged in successfully: {form_data.username}")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user's information."""
    from db.mongodb import MongoDB

    user = await MongoDB.db.users.find_one({"_id": ObjectId(current_user.user_id)})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        username=user["username"],
        full_name=user.get("full_name"),
        role=UserResponse.__fields__["role"].type_(user.get("role", "viewer")),
        is_active=user.get("is_active", True),
        created_at=user["created_at"],
        last_login=user.get("last_login")
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePassword,
    current_user: dict = Depends(get_current_user)
):
    """Change user's password."""
    from db.mongodb import MongoDB
    from bson import ObjectId

    user = await MongoDB.db.users.find_one({"_id": ObjectId(current_user.user_id)})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not verify_password(password_data.current_password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    hashed_password = get_password_hash(password_data.new_password)

    await MongoDB.db.users.update_one(
        {"_id": ObjectId(current_user.user_id)},
        {
            "$set": {
                "hashed_password": hashed_password,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    )

    logger.info(f"Password changed for user: {current_user.user_id}")

    return MessageResponse(message="Password changed successfully")


@router.post("/logout", response_model=MessageResponse)
async def logout():
    """Logout user (client-side token removal)."""
    return MessageResponse(message="Successfully logged out")
