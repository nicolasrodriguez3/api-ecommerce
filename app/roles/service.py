from app.users.roles import RoleEnum


def get_roles() -> list[str]:
    return [role.value for role in RoleEnum]
