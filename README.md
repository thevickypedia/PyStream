# Video Streaming
Video streaming using FastAPI

### Env Variables
- **USERNAME**: Any username of choice.
- **PASSWORD**: Any password of choice.
- **VIDEO_HOST**: IP address to host the video. Defaults to `127.0.0.1`
- **VIDEO_SOURCE**: Source path for videos. Defaults to `source`
- **VIDEO_PORT**: Port number to host the application. Defaults to `8000`
- **WEBSITE**: Website to add to CORS configuration.
- **WORKERS**: Number of workers to spin up the `uvicorn` server. Defaults to 1.
