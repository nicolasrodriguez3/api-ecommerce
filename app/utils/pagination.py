
class CursorUtils:
    """Utilidades para manejar cursors"""

    @staticmethod
    def create_cursor(obj_id: int, timestamp: str) -> str:
        """Crea un cursor basado en ID y timestamp."""
        import base64

        cursor_data = f"{obj_id}:{timestamp}"
        return base64.b64encode(cursor_data.encode()).decode()

    @staticmethod
    def decode_cursor(cursor: str) -> int:
        """Decodifica un cursor."""
        import base64

        try:
            decoded = base64.b64decode(cursor.encode()).decode()
            # obj_id, timestamp = decoded.split(':', 1)
            obj_id = decoded.split(":", 1)[0]
            return int(obj_id)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid cursor: {cursor}") from e
