# main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import os
from datetime import datetime
import torch

from sadtalker_wrapper import generate_talking_video

app = FastAPI(root_path="/sadtalker_api")  # サブパスで動かす

@app.post("/generate")
async def generate(source_image: UploadFile = File(...), driven_audio: UploadFile = File(...)):
    try:
        # ./working_dir/YYYYMMDD_HHMMSS に保存
        base_dir = os.path.join(os.getcwd(), "working_dir")
        os.makedirs(base_dir, exist_ok=True)
        session_dir = os.path.join(base_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(session_dir, exist_ok=True)

        image_path = os.path.join(session_dir, "input.png")
        audio_path = os.path.join(session_dir, "input.wav")

        with open(image_path, "wb") as f:
            f.write(await source_image.read())
        with open(audio_path, "wb") as f:
            f.write(await driven_audio.read())

        # SadTalker呼び出し
        result_path = generate_talking_video(
            source_image=image_path,
            driven_audio=audio_path,
            checkpoint_dir="./checkpoints",
            result_dir=session_dir,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )

        return FileResponse(result_path, media_type="video/mp4", filename="talking_face.mp4")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
