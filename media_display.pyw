from flask import Flask, jsonify
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
from winsdk.windows.storage.streams import DataReader, Buffer
import asyncio
import base64
import re

app = Flask(__name__)
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)
_session_manager = None
_session = None

def simplify_title(title):
    if not title:
        return title
    patterns = [
        (r'\s*\([^)]+\)', ''),
        (r'\s*\[[^\]]+\]', ''),
        (r'\s*[-–]\s*(slowed|reverb|remix|remaster|remastered|official|official video|official audio|lyrics|extended|feat\..*|ft\..*|HD|HQ|4K).*$', ''),
        (r'\s+\d{3,4}k$', ''),
        (r'\s*[-–]\s*$', '')
    ]
    simplified = title
    for pattern, replacement in patterns:
        simplified = re.sub(pattern, replacement, simplified, flags=re.IGNORECASE)
    simplified = ' '.join(simplified.split())
    if not simplified.strip():
        return title
    return simplified

async def get_media_info():
    global _session_manager, _session
    if _session_manager is None:
        try:
            _session_manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        except Exception:
            _session_manager = None
    if _session_manager:
        try:
            current = _session_manager.get_current_session()
            if current:
                _session = current
        except Exception:
            _session = None
    if _session:
        info = await _session.try_get_media_properties_async()
        original_title = info.title
        simplified_title = simplify_title(original_title)
        thumbnail = None
        if info.thumbnail:
            thumbnail_stream = None
            reader = None
            try:
                thumbnail_stream = await info.thumbnail.open_read_async()
                buffer = Buffer(thumbnail_stream.size)
                await thumbnail_stream.read_async(buffer, buffer.capacity, 0)
                reader = DataReader.from_buffer(buffer)
                bytes_array = bytearray(buffer.length)
                reader.read_bytes(bytes_array)
                thumbnail = base64.b64encode(bytes_array).decode()
            except:
                thumbnail = None
            finally:
                if reader:
                    reader.close()
                if thumbnail_stream:
                    thumbnail_stream.close()
        info_dict = {
            "title": simplified_title,
            "artist": info.artist,
            "album": info.album_title,
            "thumbnail": thumbnail
        }
        return info_dict
    return {"title": "None", "artist": "None", "album": "None", "thumbnail": None}

def get_media_info_sync():
    return _loop.run_until_complete(get_media_info())

@app.route('/media-info')
def media_info():
    return jsonify(get_media_info_sync())

@app.route('/')
def home():
    return '''<html><head><title>Current Media</title><style>
:root{
    --bg-color:#ffffff;
    --text-color:#333333;
    --shadow:rgba(0,0,0,0.1);
    --album-size: 180px;     /* Adjust album art size here */
    --content-margin: -43px;   /* Adjust left margin here */
}
@media (prefers-color-scheme:dark){
    :root{
        --bg-color:#1a1a1a;
        --text-color:#ffffff;
        --shadow:rgba(0,0,0,0.3)
    }
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;width:100%;margin:0;padding:0;overflow-x:hidden}
body{
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,Cantarell,sans-serif;
    background-color:var(--bg-color);
    color:var(--text-color);
    display:flex;
    justify-content:center;
    align-items:center
}
.media-info{
    width:100%;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:2vw;
    padding:2vw;
    margin-left: var(--content-margin)  /* Adjustable margin */
}
.album-art-wrapper{
    width:100%;
    display:flex;
    justify-content:center;
    align-items:center
}
.album-art{
    width: var(--album-size);           /* Fixed album size */
    height: var(--album-size);          /* Fixed album size */
    border-radius:16px;
    overflow:hidden;
    background-color:var(--bg-color);
    box-shadow:0 8px 30px var(--shadow);
    display:flex;
    justify-content:center;
    align-items:center
}
.album-art img{
    width:100%;
    height:100%;
    object-fit:cover;
    image-rendering:auto;
    -webkit-font-smoothing:antialiased
}
.album-art.no-image::after{
    content:'♪';
    font-size: calc(var(--album-size) * 0.25);  /* Proportional to album size */
    opacity:0.5
}
.text-info{
    width:100%;
    display:flex;
    flex-direction:column;
    align-items:center;
    gap:1vh
}
.title{
    font-size:min(3.5vw,2rem);
    font-weight:600;
    text-align:center;
    max-width:90%;
    overflow-wrap:break-word;
    line-height:1.3
}
.artist,.album{
    font-size:min(2vw,1.5rem);
    opacity:0.8;
    text-align:center;
    max-width:90%;
    overflow-wrap:break-word
}
@media (max-width:768px){
    :root {
        --album-size: 300px;  /* Smaller size for mobile */
    }
    .title{font-size:5vw}
    .artist,.album{font-size:4vw}
}</style><script>function updateMedia(){fetch('/media-info').then(response=>response.json()).then(data=>{const albumArt=document.getElementById('album-art');const albumArtContainer=document.getElementById('album-art-container');if(data.thumbnail){albumArt.src='data:image/jpeg;base64,'+data.thumbnail;albumArtContainer.classList.remove('no-image')}else{albumArt.src='';albumArtContainer.classList.add('no-image')}document.getElementById('title').textContent=data.title;document.getElementById('artist').textContent=data.artist!=="None"?data.artist:"";document.getElementById('album').textContent=data.album!=="None"?data.album:"";})}setInterval(updateMedia,2000);updateMedia();</script></head><body><div class="media-info"><div class="album-art" id="album-art-container"><img id="album-art" src="" alt="Album Art"></div><div class="text-info"><h2 class="title" id="title">-</h2><p class="artist" id="artist">-</p><p class="album" id="album">-</p></div></div></body></html>'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, use_reloader=False, threaded=False)
