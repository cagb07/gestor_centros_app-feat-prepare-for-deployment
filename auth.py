from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """Genera un hash seguro para una contraseña."""
    return generate_password_hash(password)

def check_password(password, hashed_password):
    """Verifica una contraseña contra un hash existente."""
    # Handle the case where the hash is in the old binary format
    if isinstance(hashed_password, memoryview):
        return False  # Old format is incompatible, so authentication fails
    return check_password_hash(hashed_password, password)
