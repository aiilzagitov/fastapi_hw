import random
import string
from sqlalchemy.orm import Session
from api.models import Link

def generate_short_code(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_unique_short_code(db: Session):
    for _ in range(5):
        code = generate_short_code()
        if not db.query(Link).filter(Link.short_code == code).first():
            return code
    raise ValueError("Could not generate unique code")