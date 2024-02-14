Release Notes
=============

v2.0 (02/13/2024)
-----------------
- Redefines authentication allowing multi-user signon
- Validates each user's session-token using symmetric encryption
- Uses signature-authentication for username and password validation
- Includes other minor bug fixes and performance improvements

v1.1 (01/28/2024)
-----------------
- Fix missing navigation buttons due to unsupported files in directory

v1.0 (01/25/2024)
-----------------
- Improved security with session-based authentication
- Increased server-side control, robust session management and sensitive data protection
- Improves user experience with HTML responses instead of JSON objects and plain text
- Includes support for subtitles, along with auto-converting ``.srt`` to ``.vtt``
- Supports multiple video file formats, and websites for CORS
- Includes more options in the video player with seek, next and previous buttons

v0.0.2 (12/10/2023)
-------------------
- Includes performance improvements
- Redefine the UI with playback options and enforced video display page to night mode
- Includes bug fixes for cert video file names broken in the UI

v0.0.1 (12/04/2023)
-------------------
- Let the streaming begin

v0.0.1b (12/04/2023)
--------------------
- Install ``ngrok`` as an exteion package only if needed
- Remove ``ip_hosted`` flag
- Add utils package to get public IP and local IP

v0.0.1a (12/03/2023)
--------------------
- Release alpha version of ``stream-localhost``
