from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from api.auth.token import verify_token
from api.auth.schema import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return TokenData(username=username)