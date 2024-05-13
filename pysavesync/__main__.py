# https://fastapi.tiangolo.com/#create-it

import typing as t
import fastapi as f
import logging
from fastapi.concurrency import asynccontextmanager
from fastapi.security import OAuth2PasswordBearer
import uvicorn

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def get_user_id_from_token(token: str) -> str | None:
  return {
    "token1": "ichi",
    "token2": "steffo",
  }.get(token, None)


@asynccontextmanager
async def lifespan(app: f.FastAPI):
  log.info("Starting up")
  try:
    yield
  finally:
    log.info("Shutting down")


app = f.FastAPI(debug=__debug__, lifespan=lifespan)


@app.get("/")
def healthcheck() -> t.Literal[True]:
  """
  Returns `True` if pysavesync is running.
  """
  return True


@app.get("/saves/{game_id}/file")
def get_save(token: t.Annotated[str, f.Depends(oauth2_scheme)], game_id: str, q: str | None = None):
  """
  Download the save data for a game.
  """

  user_id = get_user_id_from_token(token)
  if not user_id:
    raise f.HTTPException(status_code=403, detail="Invalid token")
  
  # list files in save_data/user_id/game_id
  

  with open(f"save_data/{user_id}/{game_id}/{file.filename}", "rb") as disk_file:
    return {"game_id": game_id, "q": q}


@app.get("/saves/{game_id}/meta")
def get_save_meta(game_id: str):
  """
  Get information about the save data for a game.
  """
  return {"game_id": game_id, "meta": "some metadata"}


@app.put("/saves/{game_id}/file")
def upload_save(token: t.Annotated[str, f.Depends(oauth2_scheme)], game_id: str, file: f.UploadFile | None = None):
  """
  Upload a save file for a game.
  """
  user_id = get_user_id_from_token(token)
  if not user_id:
    raise f.HTTPException(status_code=403, detail="Invalid token")
  if not file:
    raise f.HTTPException(status_code=400, detail="Missing file")
  
  log.debug(file.filename)
  with open(f"save_data/{user_id}/{game_id}/{file.filename}", "wb") as disk_file:
    disk_file.write(file.file.read())

  return {"game_id": game_id, "filename": file.filename}


uvicorn.run(app, host="127.0.0.1", port=8080)
