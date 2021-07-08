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
from base64 import b64decode
import io
import cv2
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from PIL import Image


HERE = Path(__file__).parent
BASE_URI = "https://drmaboule-ouh2vqtouq-ew.a.run.app"
LOCAL_URI = "http://127.0.0.1:8000"

logger = logging.getLogger(__name__)


def rgb2yuv(rgb_image):
    return np.apply_along_axis(
        lambda x: 0.2126 * x[0] + 0.7152 * x[1] + 0.0722 * x[2], 2, rgb_image
    )


# Credits to https://gist.github.com/meain/6440b706a97d2dd71574769517e7ed32
waiting_messages = [
    "You seem like a nice person...",
    "Coffee at my place, tommorow at 10A.M. - don't be late!",
    "Work, work...",
    "Patience! This is difficult, you know...",
    "Discovering new ways of making you wait...",
    "Your time is very important to us. Please wait while we ignore you...",
    "Time flies like an arrow; fruit flies like a banana",
    "Two men walked into a bar; the third ducked...",
    "Sooooo... Have you seen my vacation photos yet?",
    "Sorry we are busy catching em' all, we're done soon",
    "TODO: Insert elevator music",
    "Still faster than Windows update",
    "Composer hack: Waiting for reqs to be fetched is less frustrating if you add -vvv to your command.",
    "Please wait while the minions do their work",
    "Grabbing extra minions",
    "Doing the heavy lifting",
    "We're working very Hard .... Really",
    "Waking up the minions",
    "You are number 2843684714 in the queue",
    "Please wait while we serve other customers...",
    "Our premium plan is faster",
    "Feeding unicorns...",
]


app_mode = st.sidebar.selectbox(
    f"WELCOME DOC MABOULE",
    [
        "----",
        "Validate New Model",
        "Diagnose",
        "3D View",
    ],
)

if app_mode == "Validate New Model":
    st.subheader("Validate New Model")
    response = requests.get(f"{BASE_URI}/patients").json()
    patient_list = response["patients"]
    patient_list.insert(0, "Patient ID")
    patient_id = st.selectbox("", response["patients"])

    if patient_id != "Patient ID":
        response = requests.get(f"{BASE_URI}/patients/{patient_id}").json()
        number_of_slices = int(response["number_of_slices"])
        slice_id = st.slider("SLICE #", min_value=1, max_value=number_of_slices + 1)
        response = requests.get(
            f"{BASE_URI}/patients/{patient_id}/{slice_id}", allow_redirects=True
        )

        tmpdir = tempfile.TemporaryDirectory(suffix=None, prefix="tmp", dir=None).name
        os.mkdir(tmpdir)
        file_path = f"{tmpdir}/tmp.zip"
        open(file_path, "wb").write(response.content)
        shutil.unpack_archive(file_path, tmpdir)

        image_path = f"{tmpdir}/{patient_id}_{slice_id}.tif"
        mask_path = f"{tmpdir}/{patient_id}_{slice_id}_mask.tif"
        pred_path = f"{tmpdir}/{patient_id}_{slice_id}_mask.tif"
        image = Image.open(image_path).convert("RGB")
        mask = Image.open(mask_path).convert("RGB")

        # response = requests.post(f"{BASE_URI}/predict", data=image)
        # print(response.content)
        files = {"file": open(image_path, "rb")}

        response = requests.post(
            f"{LOCAL_URI}/predict", files=files
        )  # , headers=headers)
        # response = requests.post(f"{BASE_URI}/predict", data=data)

        d = response.json()

        for key, value in d.items():
            # print(f"key: {key}\nlen: {len(value)}\nvalue: {value[:50]}")
            base64_bytes = base64.b64decode(value)
            img_data = io.BytesIO(base64_bytes)

            # import ipdb
            # ipdb.set_trace()
            img = Image.open(img_data)
            if key:
                img.save(key)

            # import ipdb
            # ipdb.set_trace()
            mask_p = Image.open(key).convert("RGB")

        # pred = Image.open(pred_path).convert("RGB")

        col1, col2, col3 = st.beta_columns(3)
        image_title = '<p style="font-family:sans-serif;text-align: center; color:Black; font-size: 20px;">Brain MRI</p>'
        col1.markdown(image_title, unsafe_allow_html=True)
        col1.image(image, use_column_width=True)
        mask_title = '<p style="font-family:sans-serif;text-align: center; color:Black; font-size: 20px;">Original Mask</p>'
        col2.markdown(mask_title, unsafe_allow_html=True)
        col2.image(mask, use_column_width=True)
        pred_title = '<p style="font-family:sans-serif;text-align: center; color:Black; font-size: 20px;">Predicted Mask</p>'
        col3.markdown(pred_title, unsafe_allow_html=True)
        col3.image(mask_p, use_column_width=True)

        shutil.rmtree(tmpdir)


if app_mode == "Diagnose":
    st.subheader("Analyze Patient Data")
    image_file = st.file_uploader("")
    if image_file is not None:
        data = image_file.read()
        # st.image(Image.open(image_file))

        files = {"file": image_file.getvalue()}
        response = requests.post(
            f"{LOCAL_URI}/predict", files=files
        )  # , headers=headers)
        # response = requests.post(f"{BASE_URI}/predict", data=data)

        d = response.json()

        for key, value in d.items():
            # print(f"key: {key}\nlen: {len(value)}\nvalue: {value[:50]}")
            base64_bytes = base64.b64decode(value)
            img_data = io.BytesIO(base64_bytes)

            # import ipdb
            # ipdb.set_trace()
            img = Image.open(img_data)
            if key:
                img.save(key)

            # import ipdb
            # ipdb.set_trace()
            mask_p = Image.open(key).convert("RGB")

        col1, col2 = st.beta_columns(2)
        col1.markdown(
            '<p style="font-family:sans-serif;text-align: center; color:Black; font-size: 20px;">Brain MRI</p>',
            unsafe_allow_html=True,
        )
        col1.image(Image.open(image_file), use_column_width=True)
        col2.markdown(
            '<p style="font-family:sans-serif;text-align: center; color:Black; font-size: 20px;">Diagnostic</p>',
            unsafe_allow_html=True,
        )
        col2.image(mask_p, use_column_width=True)


if app_mode == "3D View":
    st.subheader("3D View")
    response = requests.get(f"{BASE_URI}/patients").json()
    patient_list = response["patients"]
    patient_id = st.selectbox(
        "", patient_list, index=patient_list.index("TCGA_HT_7884_19980913")
    )
    if patient_id is not None:
        response = requests.get(f"{BASE_URI}/patients/{patient_id}").json()
        number_of_slices = int(response["number_of_slices"])

        # Placeholder for storing images
        values = np.empty((128, 128, number_of_slices))

        st_progress_bar = st.progress(0)
        st_waiting_message = st.empty()

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
            slice = slice.resize((128, 128), Image.ANTIALIAS)
            values[:, :, i] = rgb2yuv(slice)
            # Delete file
            shutil.rmtree(tmpdir)
            if i % 5 == 0:
                st_waiting_message.markdown(random.choice(waiting_messages))

        st_progress_bar.progress(1.0)
        st_waiting_message.empty()

        st_progress_bar.empty()

        r, c = 128, 128

        X, Y, Z = np.mgrid[0:128, 0:128, 0:number_of_slices]

        fig = go.Figure(
            data=go.Volume(
                x=X.flatten(),
                y=Y.flatten(),
                z=Z.flatten(),
                value=values.flatten(),
                opacity=0.2,
                isomin=0,
                isomax=255,
                colorscale="RdBu",
            )
        )

        # fig.update_layout(
        #     title="Slices in volumetric data",
        #     width=600,
        #     height=600,
        # )

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
        fig.add_trace(
            go.Surface(
                z=(number_of_slices - 10 - 1) * np.ones((r, c)),
                surfacecolor=values[:, :, number_of_slices - 10 - 1],
                cmin=0,
                cmax=255,
                # colorbar=dict(thickness=20, ticklen=4)
            )
        )

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
                        "args": [[f.name], frame_args(2)],
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
