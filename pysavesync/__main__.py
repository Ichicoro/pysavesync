# https://fastapi.tiangolo.com/#create-it

import datetime
import json
from pathlib import Path
import typing as t
import fastapi as f
import logging
from fastapi.concurrency import asynccontextmanager
import uvicorn

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def get_token_from_req(req: f.Request):
    token = req.headers["Authorization"]

    # Extract token from "Bearer <token>" string
    [bearer_str, token_str] = token.split(" ")
    if bearer_str != "Bearer":
        raise f.HTTPException(status_code=400, detail="Invalid token")
    if not token_str:
        raise f.HTTPException(status_code=400, detail="Missing token")

    return token_str


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
def get_save(token: t.Annotated[str, f.Depends(get_token_from_req)], game_id: str, q: str | None = None):
    """
    Download the save data for a game.
    """

    user_id = get_user_id_from_token(token)
    if not user_id:
        raise f.HTTPException(status_code=403, detail="Invalid token")

    with open(f"save_data/{user_id}/{game_id}/meta.json", "r") as meta_file:
        meta = json.load(meta_file)
        return f.responses.FileResponse(
            f"save_data/{user_id}/{game_id}/data",
            headers={
                "Content-Disposition": f'attachment; filename="{meta["filename"]}"',
            },
        )


@app.get("/saves/{game_id}/meta")
def get_save_meta(req: f.Request, token: t.Annotated[str, f.Depends(get_token_from_req)], game_id: str):
    """
    Get information about the save data for a game.
    """
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise f.HTTPException(status_code=403, detail="Invalid token")

    user_game_path = Path(f"save_data/{user_id}/{game_id}/meta.json")
    if not user_game_path.exists():
        raise f.HTTPException(status_code=404, detail="Save data not found")

    metadata_obj = json.loads(user_game_path.read_text())

    return metadata_obj


@app.put("/saves/{game_id}")
def upload_save(req: f.Request, token: t.Annotated[str, f.Depends(get_token_from_req)], game_id: str, file: f.UploadFile | None = None):
    """
    Upload a save file for a game.
    """
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise f.HTTPException(status_code=403, detail="Invalid token")
    if not file:
        raise f.HTTPException(status_code=400, detail="Missing file")

    log.debug(file.filename)

    user_game_path = Path(f"save_data/{user_id}/{game_id}")
    if not user_game_path.exists():
        user_game_path.mkdir(parents=True)

    user_game_path.joinpath("data").write_bytes(file.file.read())
    game_metadata = {
        "game_id": game_id,
        "filename": file.filename,
        "updated_at": int(datetime.datetime.now().timestamp()),
        "filesize": file.size,
    }
    user_game_path.joinpath("meta.json").write_text(json.dumps(game_metadata, indent=4))

    return game_metadata


uvicorn.run(app, host="127.0.0.1", port=8080)
