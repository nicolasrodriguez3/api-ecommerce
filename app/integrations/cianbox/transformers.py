from app.users.models import User
from app.customers.models import Customer


def user_to_cianbox_payload(user: Customer, ) -> dict:
    return {
        "razon": f"{user.first_name} {user.last_name}",
        "condicion": user.tax_condition,
        "tipo_documento": user.document_type,
        "numero_documento": user.document_number,
        "telefono": user.phone,
        "celular": user.mobile,
        "email": user.email,
        "domicilio": user.address,
        "localidad": user.city,
        "provincia": user.province,
        "codigo_postal": int(user.postal_code) if user.postal_code else None,
        "observaciones": user.notes,
    }
