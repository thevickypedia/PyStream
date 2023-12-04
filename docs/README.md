# Video Streaming
Video streaming using FastAPI

### Env Variables
**Mandatory**
- **USERNAME**: Any username of choice.
- **PASSWORD**: Any password of choice.
- **VIDEO_SOURCE**: Source path for videos.

**Optional**
- **IP_HOSTED**: Boolean flag to specify if the API is hosted via public IP
- **VIDEO_HOST**: IP address to host the video. Defaults to `127.0.0.1`
- **VIDEO_PORT**: Port number to host the application. Defaults to `8000`
- **WEBSITE**: Website to add to CORS configuration.
- **WORKERS**: Number of workers to spin up the `uvicorn` server. Defaults to 1.

> - `IP_HOSTED` is typically set to `True` if port forwarding is used to expose the API
> - This will allow the application to host the API on local IP instead of `localhost` (if `VIDEO_HOST` is `None`)
> - This can also be done by specifying the local IP for the env var `VIDEO_HOST` manually
