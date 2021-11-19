import os, sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unforeseen.config import setup_loader

# This code is inspired heavely from http://4youngpadawans.com/stream-live-video-to-browser-using-gstreamer/

setup = setup_loader()

hls_sink_port = f'{setup.get("device").get("ip")}:{str(setup.get("server").get("hls_sink_port"))}'
name = f'{setup.get("device").get("name")}'
height = str(480)
width = str(640) 
# Video stream is most likely larger or smaller, but this height and width fits very well into grafana
html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset=utf-8 />
<title>{name}</title>
  <link href="https://unpkg.com/video.js/dist/video-js.css" rel="stylesheet">
</head>
<body> 
<video-js id="video" class="vjs-default-skin" controls preload="auto" width="{width}" height="{height}">
    <source src="http://{hls_sink_port}/storage/streaming/playlist.m3u8" type="application/x-mpegURL">
  </video-js>
  <script src="https://unpkg.com/video.js/dist/video.js"></script>
  <script src="https://unpkg.com/@videojs/http-streaming/dist/videojs-http-streaming.js"></script>
  <script>
    var player = videojs('video');
  </script>
</body>
</html>'''

file = open("index.html","w")
file.write(html)
file.close()
