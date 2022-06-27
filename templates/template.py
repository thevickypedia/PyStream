class CustomTemplate:
    """Initiates Template object which has the template for static html file stored.

    >>> CustomTemplate

    """

    source = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>FastAPI video streaming</title>
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
        <meta http-equiv="Pragma" content="no-cache">
        <meta http-equiv="Expires" content="0">
        <!-- Disables 404 for favicon.ico which is a logo on top of the webpage tab -->
        <link rel="shortcut icon" href="#">
    </head>
    <style type="text/css">
        @import url('//netdna.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css');
        body{
            font-family: 'PT Serif', serif;
            background-color: #ececec;
        }
        video {
            margin-left: auto;
            margin-right: auto;
            display: block
        }
        .night{
            background-color: #151515;
        }
        .toggler{
            font-size: 28px;
            border-radius: 100px;
            background-color: #111111;
            padding: 15px;
            color:#fcfcfc;
            box-shadow: 1px 2px 6px rgba(0,0,0,.3);
            cursor: pointer;
            position: fixed;
            bottom:20px;
            right: 20px;
            -webkit-transition: all 0.2s;
            -moz-transition: all 0.2s;
            transition: all 0.2s;
        }
        .fa-moon-o:before{
            padding:0 2px;
        }
        .fa-sun-o{
            background-color: #212121;
            color:#ccc;
        }
        /* Optional */
        .content{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 4px 24px 0 #ddd;
            box-sizing: border-box;
            padding: 20px;
            font-family: arial;
        }
        .content h1{
            font-size: 58px;
            font-weight: 100;
            margin: 0 0 20px;
        }
        .content .text{
            line-height: 23px;
            font-size: 15px;
            color: #444;
        }
        .night *{
            color: #f0f0f0 !important;
            box-shadow: none;
        }
        .night .content{
            border: 1px solid #999;
        }
    </style>
    <style>
        .tab {
            margin-left: 40px;
        }
        p.center {
            text-align: center;
        }
        div {
            height: 1em;
        }
        .dotted {
            border-bottom: 3px dotted #757575;
            margin-bottom: 1px;
        }
        .cent {
            margin-top: 1%;
            text-align: center;
            font-size: 120%;
        }
    </style>
    <body translate="no">
        <div class="toggler fa fa-moon-o"></div>
        <p class="center">{{ TITLE }}</p>
        <video width="1200" controls muted="muted">
            <source src={{ VIDEO_HOST_URL }} type="video/mp4" />
        </video>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.2.2/jquery.min.js"></script>
    <script id="rendered-js">
        var theme = window.localStorage.currentTheme;
        $('body').addClass(theme);
        if ($("body").hasClass("night")) {
            $('.toggler').addClass('fa-sun-o');
            $('.toggler').removeClass('fa-moon-o');
        } else {
            $('.toggler').removeClass('fa-sun-o');
            $('.toggler').addClass('fa-moon-o');
        }
        $('.toggler').click(function () {
        $('.toggler').toggleClass('fa-sun-o');
        $('.toggler').toggleClass('fa-moon-o');
        if ($("body").hasClass("night")) {
            $('body').toggleClass('night');
            localStorage.removeItem('currentTheme');
            localStorage.currentTheme = "day";
        } else {
            $('body').toggleClass('night');
            localStorage.removeItem('currentTheme');
            localStorage.currentTheme = "night";
        }
        });
        //# sourceURL=pen.js
    </script>
    </body>
</html>
"""
