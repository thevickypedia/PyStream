class CustomTemplate:
    """Initiates Template object which has the template for static html file stored.

    >>> CustomTemplate

    """

    source = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI video streaming</title>
    </head>
    <body>
        <video width="1200" controls muted="muted">
            <source src={{ VIDEO_HOST_URL }} type="video/mp4" />
        </video>
    </body>
</html>
"""
