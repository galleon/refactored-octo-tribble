import asyncio
import base64
import logging
import logging.handlers
import queue
import random
import threading
import requests
import urllib.request
from pathlib import Path
from typing import List, NamedTuple

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore

import av
import cv2
import matplotlib.pyplot as plt
import numpy as np
import pydub
import streamlit as st
from aiortc.contrib.media import MediaPlayer

from streamlit_webrtc import (
    AudioProcessorBase,
    ClientSettings,
    VideoProcessorBase,
    WebRtcMode,
    webrtc_streamer,
)

HERE = Path(__file__).parent

logger = logging.getLogger(__name__)


# This code is based on https://github.com/streamlit/demo-self-driving/blob/230245391f2dda0cb464008195a470751c01770b/streamlit_app.py#L48  # noqa: E501
def download_file(url, download_to: Path, expected_size=None):
    # Don't download the file twice.
    # (If possible, verify the download using the file length.)
    if download_to.exists():
        if expected_size:
            if download_to.stat().st_size == expected_size:
                return
        else:
            st.info(f"{url} is already downloaded.")
            if not st.button("Download again?"):
                return

    download_to.parent.mkdir(parents=True, exist_ok=True)

    # These are handles to two visual elements to animate.
    weights_warning, progress_bar = None, None
    try:
        weights_warning = st.warning("Downloading %s..." % url)
        progress_bar = st.progress(0)
        with open(download_to, "wb") as output_file:
            with urllib.request.urlopen(url) as response:
                length = int(response.info()["Content-Length"])
                counter = 0.0
                MEGABYTES = 2.0 ** 20.0
                while True:
                    data = response.read(8192)
                    if not data:
                        break
                    counter += len(data)
                    output_file.write(data)

                    # We perform animation by overwriting the elements.
                    weights_warning.warning(
                        "Downloading %s... (%6.2f/%6.2f MB)"
                        % (url, counter / MEGABYTES, length / MEGABYTES)
                    )
                    progress_bar.progress(min(counter / length, 1.0))
    # Finally, we remove these visual elements by calling .empty().
    finally:
        if weights_warning is not None:
            weights_warning.empty()
        if progress_bar is not None:
            progress_bar.empty()


WEBRTC_CLIENT_SETTINGS = ClientSettings(
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={
        "video": True,
        "audio": True,
    },
)


@st.cache
def load_image(path):
    with open(path, 'rb') as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    return encoded

def image_tag(path):
    encoded = load_image(path)
    tag = f'<img src="data:image/png;base64,{encoded}">'
    return tag

def background_image_style(path):
    encoded = load_image(path)
    style = f'''
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded}");
        background-size: cover;
    }}
    </style>
    '''
    return style


def main():
    if 'login' not in st.session_state:
	      st.session_state.login = None

    #app_mode = st.sidebar.selectbox(
    #    "Choose the app mode",
    #    list_options
    #)
    background_image_style('background.png')

    #while st.session_state.login == None:
    login()

    logger.debug("=== Alive threads ===")
    for thread in threading.enumerate():
        if thread.is_alive():
            logger.debug(f"  {thread.name} ({thread.ident})")

def login():
    """
    Face recognition demo with MobileNet SSD.
    """
    MODEL_URL = "https://github.com/robmarkcole/object-detection-app/raw/master/model/MobileNetSSD_deploy.caffemodel"  # noqa: E501
    MODEL_LOCAL_PATH = HERE / "./models/MobileNetSSD_deploy.caffemodel"

    download_file(MODEL_URL, MODEL_LOCAL_PATH, expected_size=23147564)

    frame_rate = 5
    WEBRTC_CLIENT_SETTINGS.update(
        ClientSettings(
            media_stream_constraints={
                "video": {"frameRate": {"ideal": frame_rate}},
            },
        )
    )

    webrtc_ctx = webrtc_streamer(
        key="video-sendonly",
        desired_playing_state=True,
        mode=WebRtcMode.SENDONLY,
        client_settings=WEBRTC_CLIENT_SETTINGS,
    )

    image_place = st.empty()
    
    _net = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    _i = 0
    _mri_team = False
    _name = None

    while not _mri_team:
        if webrtc_ctx.video_receiver:
            try:
                video_frame = webrtc_ctx.video_receiver.get_frame(timeout=1)
            except queue.Empty:
                logger.warning("Queue is empty. Abort.")
                break

            img_rgb = video_frame.to_ndarray(format="rgb24")

            cv2.imwrite(f"webcam{_i:04}.jpg", img_rgb)
            _i += 1

            gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
            # Detect the faces
            faces = _net.detectMultiScale(gray, 1.1, 4)
            # Draw the rectangle around each face
            for (x, y, w, h) in faces:
                cv2.rectangle(img_rgb, (x, y), (x+w, y+h), (255, 0, 0), 2)

            # Detect someone from the team
            # image_place.image(img_rgb)

            if random.random() > 0.95:
                 _mri_team = True
                 _name = "John"

            print(f"{_name} is here")
            
        else:
            logger.warning("Video Receiver is not set. Abort.")
            break

    # continue the app
    image_place = st.empty()

    option1 = (
        "option1"
    )
    option2 = (
        "option2"
    )

    app_mode = st.sidebar.selectbox(
        f"{_name}, choose action",
        [
            option1,
            option2,
        ],
    )
    st.subheader(app_mode)

    if app_mode == option1:
        app_option1()
    elif app_mode == option2:
        app_option2()

def app_option1():
    st.markdown("""Option 1""")
    r = requests.get('http://127.0.0.1:8000/patients').json()
    print(r)
    list_of_patients = r['patients']
    patient_id = st.selectbox("patient", list_of_patients, help="select the patient id")

def app_option2():
    st.markdown("""Option 2""")

if __name__ == "__main__":
    import os

    DEBUG = os.environ.get("DEBUG", "false").lower() not in ["false", "no", "0"]

    logging.basicConfig(
        format="[%(asctime)s] %(levelname)7s from %(name)s in %(pathname)s:%(lineno)d: "
        "%(message)s",
        force=True,
    )

    logger.setLevel(level=logging.DEBUG if DEBUG else logging.INFO)

    st_webrtc_logger = logging.getLogger("streamlit_webrtc")
    st_webrtc_logger.setLevel(logging.DEBUG)

    fsevents_logger = logging.getLogger("fsevents")
    fsevents_logger.setLevel(logging.WARNING)

    main()
