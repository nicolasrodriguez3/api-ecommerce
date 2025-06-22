# app/core/init.py
from app.core.database import engine, Base, async_session
from app.core.security import get_password_hash
from app.models.user import Role, User, UserRole
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.role import RoleRepository

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"


async def init_db():
    """Inicializar base de datos completa"""

    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Crear usuario admin si no existe
    async with async_session() as session:
        await init_roles(session)
        await create_default_admin(session)

    print("🎉 Base de datos inicializada correctamente.")


async def init_roles(db: AsyncSession):
    """Inicializar roles por defecto en la base de datos"""

    role_repo = RoleRepository(db)

    # Crear todos los roles definidos en el enum
    for role_enum in UserRole:
        role = await role_repo.get_by_name(role_enum)
        if not role:
            role = Role(name=role_enum, description=get_role_description(role_enum))
            db.add(role)
            print(f"  ➤ Rol '{role_enum.value}' creado")
        else:
            print(f"  ℹ️ Rol '{role_enum.value}' ya existe")

    await db.commit()
    print("✅ Roles inicializados correctamente.")


async def create_default_admin(session: AsyncSession):
    result = await session.execute(
        select(User).options(selectinload(User.roles)).where(User.email == ADMIN_EMAIL)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Obtener el rol ADMIN
        role_result = await session.execute(
            select(Role).where(Role.name == UserRole.ADMIN)
        )
        admin_role = role_result.scalar_one_or_none()
        
        if not admin_role:
            raise Exception("Rol ADMIN no encontrado. Asegúrate de ejecutar init_roles() primero.")
        
        # Crear usuario con rol
        new_user = User(
            email=ADMIN_EMAIL,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            is_active=True,
        )
        
        # Asignar rol ADMIN
        new_user.roles.append(admin_role)
        
        session.add(new_user)
        await session.commit()
        
        print(f"✅ Usuario administrador creado: {ADMIN_EMAIL}")
        print(f"  📧 Email: {ADMIN_EMAIL}")
        print(f"  🔑 Password: {ADMIN_PASSWORD}")
        print(f"  🏷️ Rol: {UserRole.ADMIN.value}")
    else:
        print(f"ℹ️ Usuario administrador ya existe: {ADMIN_EMAIL}")
        
        # Verificar si tiene rol ADMIN
        if not user.has_role(UserRole.ADMIN):
            print("  ⚠️ Usuario admin sin rol ADMIN. Asignando...")
            
            # Obtener el rol ADMIN
            role_result = await session.execute(
                select(Role).where(Role.name == UserRole.ADMIN)
            )
            admin_role = role_result.scalar_one_or_none()
            
            if admin_role:
                user.roles.append(admin_role)
                await session.commit()
                print("  ✅ Rol ADMIN asignado al usuario.")
            else:
                print("  ❌ Error: Rol ADMIN no encontrado.")
        else:
            print(f"  ✅ Usuario ya tiene rol ADMIN")

def get_role_description(role: UserRole) -> str:
    """Obtener descripción para cada rol"""
    descriptions = {
        UserRole.ADMIN: "Administrador del sistema con acceso completo",
        UserRole.OWNER: "Propietario del negocio con acceso administrativo",
        UserRole.SELLER: "Vendedor con acceso a gestión de ventas",
        UserRole.CUSTOMER: "Cliente con acceso básico a la plataforma"
    }
    return descriptions.get(role, "Rol de usuario")