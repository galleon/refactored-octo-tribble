import asyncio
import base64
import logging
import logging.handlers
import queue
import os
import random
import threading
import requests
import shutil
import tempfile
import urllib.request
from pathlib import Path
from typing import List, NamedTuple

import plotly.graph_objects as go

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore

import av
import io
import cv2
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from PIL import Image


HERE = Path(__file__).parent
BASE_URI = "https://drmaboule-ouh2vqtouq-ew.a.run.app"
# BASE_URI = "http://127.0.0.1:8000"

logger = logging.getLogger(__name__)


def rgb2yuv(rgb_image):
    return np.apply_along_axis(
        lambda x: 0.2126 * x[0] + 0.7152 * x[1] + 0.0722 * x[2], 2, rgb_image
    )


app_mode = st.sidebar.selectbox(
    f"WELCOME DOC",
    [
        "----",
        "Explore",
        "Predict",
        "Full View",
    ],
)

if app_mode == "Explore":
    st.subheader("Explore patient")
    response = requests.get(f"{BASE_URI}/patients").json()
    patient_id = st.selectbox("", response["patients"])
    if patient_id is not None:
        response = requests.get(f"{BASE_URI}/patients/{patient_id}").json()
        number_of_slices = int(response["number_of_slices"])
        slice_id = st.slider("SLICE #", min_value=1, max_value=number_of_slices + 1)
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

        # Placeholder for storing images
        values = np.empty((256, 256, number_of_slices))

        st_progress_bar = st.progress(0)

        for i in range(number_of_slices):
            st_progress_bar.progress(i / number_of_slices)
            response = requests.get(
                f"{BASE_URI}/patients/{patient_id}/{i+1}", allow_redirects=True
            )
            # unpack zip in temporary directory
            tmpdir = tempfile.TemporaryDirectory(
                suffix=None, prefix="tmp", dir=None
            ).name
            os.mkdir(tmpdir)
            file_path = f"{tmpdir}/tmp.zip"
            open(file_path, "wb").write(response.content)
            shutil.unpack_archive(file_path, tmpdir)
            # load image
            slice = Image.open(f"{tmpdir}/{patient_id}_{i+1}.tif").convert("RGB")
            values[:, :, i] = rgb2yuv(slice)

        st_progress_bar.progress(1)

        r, c = 256, 256

        fig = go.Figure(
            frames=[
                go.Frame(
                    data=go.Surface(
                        z=(k) * np.ones((r, c)),
                        surfacecolor=values[:, :, number_of_slices - k - 1],
                        cmin=0,
                        cmax=255,
                    ),
                    name=str(k),
                )
                for k in range(number_of_slices)
            ]
        )

        # Add data to be displayed before animation starts
        #fig.add_trace(
        #    go.Surface(
        #        z=(number_of_slices - k - 1) * np.ones((r, c)),
        #        surfacecolor=values[:, :, number_of_slices - k - 1],
        #        cmin=0,
        #        cmax=255,
        #        # colorbar=dict(thickness=20, ticklen=4)
        #    )
        #)

        def frame_args(duration):
            return {
                "frame": {"duration": duration},
                "mode": "immediate",
                "fromcurrent": True,
                "transition": {"duration": duration, "easing": "linear"},
            }

        sliders = [
            {
                "pad": {"b": 10, "t": 60},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": [
                    {
                        "args": [[f.name], frame_args(0)],
                        "label": str(k),
                        "method": "animate",
                    }
                    for k, f in enumerate(fig.frames)
                ],
            }
        ]

        # Layout
        fig.update_layout(
            title="Slices in volumetric data",
            width=600,
            height=600,
            scene=dict(
                zaxis=dict(range=[0, number_of_slices], autorange=False),
                aspectratio=dict(x=1, y=1, z=1),
            ),
            updatemenus=[
                {
                    "buttons": [
                        {
                            "args": [None, frame_args(50)],
                            "label": "&#9654;",  # play symbol
                            "method": "animate",
                        },
                        {
                            "args": [[None], frame_args(0)],
                            "label": "&#9724;",  # pause symbol
                            "method": "animate",
                        },
                    ],
                    "direction": "left",
                    "pad": {"r": 10, "t": 70},
                    "type": "buttons",
                    "x": 0.1,
                    "y": 0,
                }
            ],
            sliders=sliders,
        )

        st.plotly_chart(fig)
