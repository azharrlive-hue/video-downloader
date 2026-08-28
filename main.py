from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import tempfile
import os
import uuid

app = FastAPI(
    title="Vidora API",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VideoRequest(BaseModel):
    url: str


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Vidora backend is running"
    }


@app.post("/info")
def get_info(request: VideoRequest):

    if not request.url.startswith(
        ("https://www.youtube.com/", "https://youtu.be/")
    ):
        raise HTTPException(
            status_code=400,
            detail="Please provide a supported YouTube URL."
        )

   options = {
    "quiet": True,
    "no_warnings": False,
    "noplaylist": True,
    "skip_download": True,
    "js_runtimes": {
        "deno": {}
    },
}

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                request.url,
                download=False
            )

        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "channel": info.get("channel"),
            "available_qualities": [
                360,
                480,
                720,
                1080
            ]
        }

   except Exception as e:
    print(f"YT-DLP ERROR: {repr(e)}")
    raise HTTPException(
        status_code=400,
        detail=f"Unable to read video information: {str(e)}"
    )


@app.post("/download")
def download_video(request: VideoRequest):

    if not request.url.startswith(
        ("https://www.youtube.com/", "https://youtu.be/")
    ):
        raise HTTPException(
            status_code=400,
            detail="Please provide a supported YouTube URL."
        )

    download_id = str(uuid.uuid4())
    temp_dir = os.path.join(
        tempfile.gettempdir(),
        download_id
    )

    os.makedirs(temp_dir, exist_ok=True)

    output_template = os.path.join(
        temp_dir,
        "%(title)s.%(ext)s"
    )

    options = {
        "format": "bv*[height<=1080]+ba/b[height<=1080]",
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                request.url,
                download=True
            )

            filename = ydl.prepare_filename(info)

        # After merging, yt-dlp normally produces an MP4.
        mp4_file = os.path.splitext(filename)[0] + ".mp4"

        if os.path.exists(mp4_file):
            filename = mp4_file

        if not os.path.exists(filename):
            raise Exception("Downloaded file was not created.")

        return FileResponse(
            filename,
            media_type="video/mp4",
            filename=os.path.basename(filename)
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Download could not be completed."
        )
