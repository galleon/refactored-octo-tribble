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
import io
import cv2
import matplotlib.pyplot as plt
import numpy as np
import pydub
import streamlit as st
from aiortc.contrib.media import MediaPlayer
from PIL import Image


HERE = Path(__file__).parent
BASE_URI = "https://drmaboule-ouh2vqtouq-ew.a.run.app"
#BASE_URI = "http://127.0.0.1:8000"

logger = logging.getLogger(__name__)

app_mode = st.sidebar.selectbox( f"WELCOME DOC", [ "Explore", "Predict", "Full View", ],)

if app_mode == "Explore":
    st.subheader("Explore patient")
    response = requests.get(f"{BASE_URI}/patients").json()
    patient_id = st.selectbox("", response["patients"])
    if patient_id is not None:
        response = requests.get(f"{BASE_URI}/patients/{patient_id}").json()
        number_of_slices = int(response["number_of_slices"])
        slice_id = st.slider("SLICE #", min_value=1, max_value=number_of_slices+1)
        response = requests.get(f"{BASE_URI}/patients/{patient_id}/{slice_id}")
        

if app_mode == "Predict":
    st.subheader("Analyze new image")
    image_file = st.file_uploader("")
    if image_file is not None:
        data = image_file.read()
        st.image(Image.open(image_file))

        response = requests.post(f"{BASE_URI}/predict", data=data)

        try:
            print(response.status_code, response.ok)
            print(response.content)
        except requests.exceptions.RequestException:
            print(response.text)


if app_mode == "Full View":
    st.subheader("Full View")
    response = requests.get(f"{BASE_URI}/patients").json()
    patient_id = st.selectbox("", response["patients"])
    if patient_id is not None:
        response = requests.get(f"{BASE_URI}/patients/{patient_id}").json()
        number_of_slices = int(response["number_of_slices"])


        for i in range(number_of_slices):
            st.progress(i/number_of_slices)
            response = requests.get(f"{BASE_URI}/patients/{patient_id}/{i+1}")
        
