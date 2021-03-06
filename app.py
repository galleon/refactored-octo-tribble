from base64 import b64decode
import io
import logging
import os
import random
import requests
import shutil
import tempfile
from pathlib import Path

from htbuilder import (
    HtmlElement,
    div,
    ul,
    li,
    br,
    hr,
    a,
    p,
    img,
    styles,
    classes,
    fonts,
)
from htbuilder.units import percent, px
from htbuilder.funcs import rgba, rgb

import numpy as np
from PIL import Image
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components


HERE = Path(__file__).parent
BASE_URI = "https://drmaboule-ouh2vqtouq-ew.a.run.app"
LOCAL_URI = "http://127.0.0.1:8000"

logger = logging.getLogger(__name__)


def tversky(y_true, y_pred, smooth=1.0e-7, alpha=0.7, beta=0.3):
    """
    Compute the Tversky score.
    The Tversky index, named after Amos Tversky, is an asymmetric similarity measure on sets
    that compares a prediction to a ground truth.
    :y_true: the ground truth mask
    :y_pred: the predicted mask
    :return: The tversky score
    :rtype: float
    :Example:
    >>> tversky([0, 0, 0], [1, 1, 1])
    smooth / (smooth + 3*alpha)
    >>> tversky([1, 1, 1], [1, 1, 1]))
    1
    .. seealso:: tensorflow.keras.metrics.MeanIoU
                 https://en.wikipedia.org/wiki/Tversky_index
    .. warning:: smooth needs to adapt to the size of the mask
    .. note:: Setting alpha=beta=0.5 produces the Sørensen–Dice coefficient.
              alpha=beta=1 produces the Tanimoto coefficient aka Jaccard index
    .. todo:: Better understand how to set the parameters
    """
    y_true_pos = y_true.flatten()
    y_pred_pos = y_pred.flatten()
    true_pos = np.sum(y_true_pos * y_pred_pos)
    false_neg = np.sum(y_true_pos * (1 - y_pred_pos))
    false_pos = np.sum((1 - y_true_pos) * y_pred_pos)

    return (true_pos + smooth) / (
        true_pos + alpha * false_neg + beta * false_pos + smooth
    )


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

st.set_page_config(
    page_title="Dr Maboule",
    page_icon=":brain:",
    layout="wide",
    initial_sidebar_state="expanded",
)


patient_dict = {
    "Darth Vader": "TCGA_HT_7473_19970826",
    "The Joker": "TCGA_HT_7690_19960312",
    "Hannibal Lecter": "TCGA_DU_6401_19831001",
    "Gollum": "TCGA_HT_7473_19970826",
    "Lord Voldemort": "TCGA_HT_7690_19960312",
    "Palpatine": "TCGA_DU_6401_19831001",
    "Dr Jekyll": "TCGA_HT_7473_19970826",
    "Frankenstein": "TCGA_HT_7690_19960312",
}

app_mode = st.sidebar.selectbox(
    f"WELCOME DOC MABOULE",
    [
        "----",
        "Validate New Model",
        "Diagnose",
        "Pre Surgery Analysis",
    ],
)


def get_patient_list(the_list):
    tmp_list = the_list.copy()
    for k in patient_dict.keys():
        tmp_list.insert(0, k)

    tmp_list.insert(0, "Patient ID")

    return tmp_list


def get_patient_id(list_id: str):
    if list_id in patient_dict.keys():
        return patient_dict[list_id]
    return list_id


def layout(*args):
    style = """
    <style>
        MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp { bottom: 60px; }
    </style>
    """

    style_div = styles(
        position="fixed",
        right=0,
        bottom=0,
        margin=px(0, 15, 0, 0),
        text_align="center",
        opacity=0.5,
    )

    body = p()
    foot = div(style=style_div)(body)

    st.markdown(style, unsafe_allow_html=True)

    for arg in args:
        if isinstance(arg, str):
            body(arg)
        elif isinstance(arg, HtmlElement):
            body(arg)

    st.markdown(str(foot), unsafe_allow_html=True)


def image(src_as_string, **style):
    return img(src=src_as_string, style=styles(**style))


def link(link, text, **style):
    return a(_href=link, _target="_blank", style=styles(**style))(text)


def footer():
    myargs = [
        "Made with ♥️ in Bordeaux",
    ]
    layout(*myargs)


st.sidebar.title("Contribute")
st.sidebar.info(
    "This an open source project and you are very welcome to **contribute** your awesome "
    "comments, questions, resources and apps as "
    "[issues](https://github.com/galleon/refactored-octo-tribble/issues) of or "
    "[pull requests](https://github.com/galleon/refactored-octo-tribble/pulls) "
    "to the [source code](https://github.com/galleon/refactored-octo-tribble). "
)
st.sidebar.title("About")

st.sidebar.write(
    f"""
    <div class='st-ae st-af st-ag st-ah st-ai st-aj st-ak st-al st-am st-bb st-ao st-ap st-aq st-ar st-as st-at st-au st-av st-aw st-ax st-ay st-az st-b9 st-b1 st-b2 st-b3 st-b4 st-b5 st-b6'>
        <img src='https://avatars.githubusercontent.com/u/5470001?s=200&v=4' width=50 class='logo-wagon'>
        <span class='text-presentation'>This app was developped during batch-633.</span>
    </div>
    """,
    unsafe_allow_html=True,
)

CSS = """
.logo-wagon {
    margin-right: 5px;
}
.text-presentation {
    font-size: 16px;
    color: #1E6777;
}
"""
st.write(f"<style>{CSS}</style>", unsafe_allow_html=True)


footer()

if app_mode == "Validate New Model":
    st.subheader("Validate New Model")

    response = requests.get(f"{BASE_URI}/patients").json()
    # Build fake patient list
    patient_list = get_patient_list(response["patients"])
    # Select patient id
    patient_id = st.selectbox("", patient_list)
    # Get actual patient id
    patient_id = get_patient_id(patient_id)

    if patient_id != "Patient ID":
        response = requests.get(f"{BASE_URI}/patients/{patient_id}").json()
        number_of_slices = int(response["number_of_slices"])
        slice_id = st.slider("SLICE #", min_value=1, max_value=number_of_slices)
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
        mask = Image.open(mask_path).convert("L")

        files = {"file": open(image_path, "rb")}

        response = requests.post(f"{BASE_URI}/predict", files=files)

        d = response.json()

        for key, value in d.items():
            # print(f"key: {key}\nlen: {len(value)}\nvalue: {value[:50]}")
            base64_bytes = b64decode(value)
            img_data = io.BytesIO(base64_bytes)

            # import ipdb
            # ipdb.set_trace()
            img = Image.open(img_data)
            if key:
                img.save(key)

            # import ipdb
            # ipdb.set_trace()
            mask_p = Image.open(key).convert("L")

        # np_masp = np.squeeze(np.array(mask))
        # np_mask_p = np.squeeze(np.array(mask_p))
        # np_0 = np.zeros((256, 256))

        # print(np_masp.shape, np_mask_p.shape, np_0.shape)

        # rgb = np.stack(
        #     [
        #         np.squeeze(np.array(mask)) / 255,
        #         np.squeeze(np.array(mask_p)) / 255,
        #         np.zeros((256, 256)),
        #     ],
        #     axis=2,
        # )

        # print(rgb.shape, rgb.min(), rgb.max())
        # print(rgb[:, :, 0].max(), rgb[:, :, 1].max(), rgb[:, :, 2].max())

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

        # st.image(Image.fromarray(rgb, "RGB"))
        mask_p_binary = np.squeeze(np.array(mask_p)) / 255 >= 1.0
        mask_p_binary = np.float32(mask_p_binary)
        mask_binary = np.squeeze(np.array(mask)) / 255 >= 1.0
        mask_binary = np.float32(mask_binary)

        score = np.round(tversky(mask_binary, mask_p_binary), 2)

        st.warning(f"The current score is:  {score}")

        shutil.rmtree(tmpdir)


if app_mode == "Diagnose":
    st.subheader("Analyze Patient Data")
    image_file = st.file_uploader("")
    if image_file is not None:
        data = image_file.read()
        # st.image(Image.open(image_file))

        files = {"file": image_file.getvalue()}
        response = requests.post(f"{BASE_URI}/predict", files=files)

        d = response.json()

        for key, value in d.items():
            # print(f"key: {key}\nlen: {len(value)}\nvalue: {value[:50]}")
            base64_bytes = b64decode(value)
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


if app_mode == "Pre Surgery Analysis":
    st.subheader("Pre Surgery Analysis")

    response = requests.get(f"{BASE_URI}/patients").json()
    # Build fake patient list

    patient_list = get_patient_list(response["patients"])
    # Select patient id
    patient_id = st.selectbox("", patient_list)
    # Get actual patient id
    patient_id = get_patient_id(patient_id)

    if patient_id != "Patient ID":
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
