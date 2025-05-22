import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from app.app import app
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.users.schemas import (
    UserResponse,
    UserCreate,
    UserUpdate,
)  # UserCreate and UserUpdate are used for payload
from app.core.exceptions import BadRequestException, NotFoundException

# Initialize TestClient
client = TestClient(app)

# --- Mock Data ---
# Use a fixed, timezone-aware datetime for reproducibility
MOCK_DATETIME_OBJ = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
MOCK_DATETIME_STR = MOCK_DATETIME_OBJ.isoformat()

# Data for creating User model instances (e.g., for get_current_user mocks)
mock_user_model_data_1 = {
    "id": 1,
    "username": "testuser1",
    "email": "test1@example.com",
    "is_active": True,
    "role_id": 2,  # Regular user
    "created_at": MOCK_DATETIME_OBJ,
    "updated_at": MOCK_DATETIME_OBJ,
    "hashed_password": "fakepassword1",
}
mock_user_model_data_2 = {
    "id": 2,
    "username": "testuser2",
    "email": "test2@example.com",
    "is_active": True,
    "role_id": 2,
    "created_at": MOCK_DATETIME_OBJ,
    "updated_at": MOCK_DATETIME_OBJ,
    "hashed_password": "fakepassword2",
}
mock_admin_model_data = {
    "id": 99,
    "username": "admin",
    "email": "admin@example.com",
    "is_active": True,
    "role_id": 1,  # Admin user
    "created_at": MOCK_DATETIME_OBJ,
    "updated_at": MOCK_DATETIME_OBJ,
    "hashed_password": "fakepasswordadmin",
}

# Expected UserResponse objects (service layer mocks will return these)
mock_user_response_1 = UserResponse(
    id=mock_user_model_data_1["id"],
    username=mock_user_model_data_1["username"],
    email=mock_user_model_data_1["email"],
    is_active=mock_user_model_data_1["is_active"],
    created_at=MOCK_DATETIME_OBJ,
    updated_at=MOCK_DATETIME_OBJ,
)
mock_user_response_2 = UserResponse(
    id=mock_user_model_data_2["id"],
    username=mock_user_model_data_2["username"],
    email=mock_user_model_data_2["email"],
    is_active=mock_user_model_data_2["is_active"],
    created_at=MOCK_DATETIME_OBJ,
    updated_at=MOCK_DATETIME_OBJ,
)
mock_admin_response = (
    UserResponse(  # Though admin might not be returned by typical user routes often
        id=mock_admin_model_data["id"],
        username=mock_admin_model_data["username"],
        email=mock_admin_model_data["email"],
        is_active=mock_admin_model_data["is_active"],
        created_at=MOCK_DATETIME_OBJ,
        updated_at=MOCK_DATETIME_OBJ,
    )
)


# --- Pytest Fixture to Clear Overrides ---
@pytest.fixture(autouse=True)
def clear_dependency_overrides_auto():  # Renamed for clarity
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = {}


# --- Helper Functions for Dependency Overrides ---
def override_get_current_admin_user():
    return User(**mock_admin_model_data)


def override_get_current_regular_user_1():
    return User(**mock_user_model_data_1)


# --- Test Cases ---


# POST /users/ (Create User)
def test_create_user_success(mocker):
    mock_service_create = mocker.patch(
        "app.users.router.service_create_user", return_value=mock_user_response_1
    )
    user_data = {
        "username": "testuser1",
        "email": "test1@example.com",
        "password": "password123",
    }
    response = client.post("/users/", json=user_data)

    assert response.status_code == 201
    api_response = response.json()
    assert api_response["username"] == user_data["username"]
    assert api_response["email"] == user_data["email"]
    assert (
        api_response["created_at"] == MOCK_DATETIME_STR
    )  # Check string format from UserResponse
    mock_service_create.assert_called_once()
    # Ensure the service was called with a UserCreate model
    call_args = mock_service_create.call_args[1]  # kwargs
    assert isinstance(call_args["user_data"], UserCreate)


def test_create_user_duplicate_username(mocker):
    mocker.patch(
        "app.users.router.service_create_user",
        side_effect=BadRequestException("Username already registered"),
    )
    user_data = {
        "username": "existinguser",
        "email": "new@example.com",
        "password": "password123",
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


# GET /users/ (List Users)
def test_list_users_as_admin(mocker):
    mock_service_get_users = mocker.patch(
        "app.users.router.service_get_users",
        return_value=[mock_user_response_1, mock_user_response_2],
    )
    app.dependency_overrides[get_current_user] = override_get_current_admin_user

    response = client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) == 2
    mock_service_get_users.assert_called_once()


def test_list_users_as_non_admin(mocker):
    mock_service_get_users = mocker.patch("app.users.router.service_get_users")
    app.dependency_overrides[get_current_user] = override_get_current_regular_user_1

    response = client.get("/users/")
    assert response.status_code == 403
    mock_service_get_users.assert_not_called()


# GET /users/{user_id} (Get User by ID)
def test_get_user_by_id_as_admin(mocker):
    mock_service_get_user = mocker.patch(
        "app.users.router.service_get_user", return_value=mock_user_response_1
    )
    app.dependency_overrides[get_current_user] = override_get_current_admin_user

    response = client.get(f"/users/{mock_user_response_1.id}")
    assert response.status_code == 200
    assert response.json()["id"] == mock_user_response_1.id
    mock_service_get_user.assert_called_with(
        db=mocker.ANY, user_id=mock_user_response_1.id
    )


def test_get_own_user_by_id_as_regular_user(mocker):
    mock_service_get_user = mocker.patch(
        "app.users.router.service_get_user", return_value=mock_user_response_1
    )
    app.dependency_overrides[get_current_user] = override_get_current_regular_user_1

    response = client.get(
        f"/users/{mock_user_response_1.id}"
    )  # User 1 requests their own data
    assert response.status_code == 200
    assert response.json()["id"] == mock_user_response_1.id
    mock_service_get_user.assert_called_with(
        db=mocker.ANY, user_id=mock_user_response_1.id
    )


def test_get_other_user_by_id_as_non_admin(mocker):
    mock_service_get_user = mocker.patch("app.users.router.service_get_user")
    app.dependency_overrides[get_current_user] = (
        override_get_current_regular_user_1  # User 1
    )

    response = client.get(
        f"/users/{mock_user_response_2.id}"
    )  # User 1 trying to get User 2
    assert response.status_code == 403
    mock_service_get_user.assert_not_called()


def test_get_non_existent_user_as_admin(mocker):
    mocker.patch(
        "app.users.router.service_get_user",
        side_effect=NotFoundException("User not found"),
    )
    app.dependency_overrides[get_current_user] = override_get_current_admin_user

    response = client.get("/users/777")  # Non-existent ID
    assert response.status_code == 404


# PUT /users/{user_id} (Update User)
update_payload = {
    "username": "updated_name",
    "email": "updated_email@example.com",
    "is_active": False,
}
updated_user_obj = UserResponse(
    id=mock_user_model_data_1["id"],
    username=update_payload["username"],
    email=update_payload["email"],
    is_active=update_payload["is_active"],
    created_at=mock_user_model_data_1["created_at"],  # created_at should not change
    updated_at=datetime.now(timezone.utc),  # updated_at will change
)


def test_update_user_as_admin(mocker):
    mock_service_update = mocker.patch(
        "app.users.router.service_update_user", return_value=updated_user_obj
    )
    app.dependency_overrides[get_current_user] = override_get_current_admin_user

    response = client.put(f"/users/{mock_user_model_data_1['id']}", json=update_payload)
    assert response.status_code == 200
    api_response = response.json()
    assert api_response["username"] == update_payload["username"]
    mock_service_update.assert_called_once()
    call_args = mock_service_update.call_args[1]
    assert isinstance(call_args["user_update"], UserUpdate)
    assert (
        call_args["user_update"].model_dump(exclude_unset=False) == update_payload
    )  # Check all fields sent


def test_update_own_user_as_regular_user(mocker):
    mock_service_update = mocker.patch(
        "app.users.router.service_update_user", return_value=updated_user_obj
    )
    app.dependency_overrides[get_current_user] = override_get_current_regular_user_1

    response = client.put(f"/users/{mock_user_model_data_1['id']}", json=update_payload)
    assert response.status_code == 200
    mock_service_update.assert_called_once()


def test_update_other_user_as_regular_user(mocker):
    mock_service_update = mocker.patch("app.users.router.service_update_user")
    app.dependency_overrides[get_current_user] = override_get_current_regular_user_1

    response = client.put(f"/users/{mock_user_model_data_2['id']}", json=update_payload)
    assert response.status_code == 403
    mock_service_update.assert_not_called()


def test_update_non_existent_user_as_admin(mocker):
    mocker.patch(
        "app.users.router.service_update_user",
        side_effect=NotFoundException("User not found"),
    )
    app.dependency_overrides[get_current_user] = override_get_current_admin_user

    response = client.put("/users/777", json=update_payload)
    assert response.status_code == 404


def test_update_user_causing_conflict_as_admin(mocker):
    mocker.patch(
        "app.users.router.service_update_user",
        side_effect=BadRequestException("Username already taken"),
    )
    app.dependency_overrides[get_current_user] = override_get_current_admin_user
    response = client.put(
        f"/users/{mock_user_model_data_1['id']}", json={"username": "conflicting_name"}
    )
    assert response.status_code == 400


# DELETE /users/{user_id} (Delete User)
def test_delete_user_as_admin(mocker):
    mock_service_delete = mocker.patch(
        "app.users.router.service_delete_user", return_value=mock_user_response_1
    )  # Service returns deleted user data
    app.dependency_overrides[get_current_user] = override_get_current_admin_user

    response = client.delete(f"/users/{mock_user_response_1.id}")
    assert response.status_code == 200
    assert response.json()["id"] == mock_user_response_1.id
    mock_service_delete.assert_called_with(
        db=mocker.ANY, user_id=mock_user_response_1.id
    )


def test_delete_user_as_non_admin(mocker):
    mock_service_delete = mocker.patch("app.users.router.service_delete_user")
    app.dependency_overrides[get_current_user] = override_get_current_regular_user_1

    response = client.delete(
        f"/users/{mock_user_response_2.id}"
    )  # User 1 tries to delete User 2
    assert response.status_code == 403
    mock_service_delete.assert_not_called()


def test_delete_non_existent_user_as_admin(mocker):
    mocker.patch(
        "app.users.router.service_delete_user",
        side_effect=NotFoundException("User not found"),
    )
    app.dependency_overrides[get_current_user] = override_get_current_admin_user

    response = client.delete("/users/777")
    assert response.status_code == 404


# GET /users/me (Get Current User)
def test_get_me_success(mocker):
    # get_current_user returns a User model instance. Route converts to UserResponse.
    app.dependency_overrides[get_current_user] = override_get_current_regular_user_1

    response = client.get("/users/me")
    assert response.status_code == 200
    api_response = response.json()
    assert api_response["id"] == mock_user_model_data_1["id"]
    assert api_response["username"] == mock_user_model_data_1["username"]
    assert (
        api_response["created_at"] == MOCK_DATETIME_STR
    )  # Ensure datetime is serialized correctly


def test_get_me_unauthenticated(mocker):
    from fastapi import HTTPException  # Import locally for this test

    def mock_get_current_user_unauthenticated():  # Simulates actual dependency behavior
        raise HTTPException(status_code=401, detail="Not authenticated")

    app.dependency_overrides[get_current_user] = mock_get_current_user_unauthenticated

    response = client.get("/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


# Pydantic schema validation by FastAPI (implicitly tests UserCreate)
def test_create_user_invalid_payload_bad_email(mocker):
    user_data = {"username": "testuser", "email": "bademail", "password": "password123"}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 422  # Unprocessable Entity


# Test skip and limit parameters for list_users
def test_list_users_as_admin_with_skip_limit(mocker):
    mock_service_get_users = mocker.patch(
        "app.users.router.service_get_users", return_value=[mock_user_response_1]
    )
    app.dependency_overrides[get_current_user] = override_get_current_admin_user

    response = client.get("/users/?skip=5&limit=10")
    assert response.status_code == 200
    mock_service_get_users.assert_called_once_with(db=mocker.ANY, skip=5, limit=10)


# Test update with partial data (implicitly tests UserUpdate)
def test_update_user_partial_data_as_admin(mocker):
    partial_update_payload = {"username": "partial_update_name"}

    expected_service_response = UserResponse(
        id=mock_user_model_data_1["id"],
        username=partial_update_payload["username"],
        email=mock_user_model_data_1["email"],
        is_active=mock_user_model_data_1["is_active"],
        created_at=mock_user_model_data_1["created_at"],
        updated_at=datetime.now(timezone.utc),
    )
    mock_service_update = mocker.patch(
        "app.users.router.service_update_user", return_value=expected_service_response
    )
    app.dependency_overrides[get_current_user] = override_get_current_admin_user

    response = client.put(
        f"/users/{mock_user_model_data_1['id']}", json=partial_update_payload
    )
    assert response.status_code == 200
    api_response = response.json()
    assert api_response["username"] == partial_update_payload["username"]

    call_args = mock_service_update.call_args[1]
    assert isinstance(call_args["user_update"], UserUpdate)
    assert (
        call_args["user_update"].model_dump(exclude_unset=True)
        == partial_update_payload
    )


# Test that role_id cannot be updated via the UserUpdate schema
def test_update_user_cannot_change_role_id(mocker):
    mock_service_update = mocker.patch(
        "app.users.router.service_update_user", return_value=mock_user_response_1
    )
    app.dependency_overrides[get_current_user] = override_get_current_admin_user

    update_data_with_role = {"username": "newname", "role_id": 100}
    response = client.put(
        f"/users/{mock_user_model_data_1['id']}", json=update_data_with_role
    )
    assert response.status_code == 200

    call_args = mock_service_update.call_args[1]
    assert "role_id" not in call_args["user_update"].model_dump(exclude_unset=True)
    assert call_args["user_update"].model_dump(exclude_unset=True) == {
        "username": "newname"
    }


# Test password is not returned in UserResponse (schema check)
def test_password_not_in_user_response_on_create(mocker):
    mocker.patch(
        "app.users.router.service_create_user", return_value=mock_user_response_1
    )
    user_data = {
        "username": "testuser1",
        "email": "test1@example.com",
        "password": "password123",
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    assert "hashed_password" not in response.json()
    assert (
        "password" not in response.json()
    )  # UserCreate has password, UserResponse does not.


# Final check: ensure no overrides persist (redundant due to autouse fixture but good for sanity)
def test_final_check_no_overrides_persist():
    assert not app.dependency_overrides
