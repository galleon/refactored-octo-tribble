import streamlit as st
import requests
import shutil
import os

import numpy as np
import pandas as pd
from PIL import Image


url = 'https://drmaboule-ouh2vqtouq-ew.a.run.app/patients'


def get_patient_id():
    st.markdown("""get patient""")
    r = requests.get(url).json()
    list_of_patients = r['patients']
    patient_id = st.selectbox("patient", list_of_patients, help="select the patient id")
    return patient_id

def get_slices(patient_id):
    st.markdown("""get slice number""")
    params={'patient_id':patient_id}
    r = requests.get(url+'/'+patient_id).json()
    number_of_slices = r['number_of_slices']
    return number_of_slices

def get_image(patient_id, slice_number):
    r = requests.get(url+'/'+patient_id+'/'+f'{slice_number}', allow_redirects=True)
    open('tmp.zip', 'wb').write(r.content)
    shutil.unpack_archive('tmp.zip', "tmp")

    image_path = f'tmp/{patient_id}_{slice_number}.tif' 
    mask_path  = f'tmp/{patient_id}_{slice_number}_mask.tif'
    pred_path  = f'tmp/{patient_id}_{slice_number}_mask.tif'
    image = Image.open(image_path).convert('RGB')
    mask  = Image.open(mask_path).convert('RGB')
    st.image([image, mask])
    shutil.rmtree('tmp/')
    os.remove('tmp.zip')
    return True
    

patient_id = get_patient_id()
number_of_slices = get_slices(patient_id)
slice_number = st.slider('Select a line count', 1, number_of_slices, 1)


if st.button('Download'):
    st.write('Clicked!!!')
    get_image(patient_id, slice_number)
else:
    st.write('Not clicked')
#download_file(patient_id, slice_number)





@st.cache
def get_select_box_data():
    print('get_select_box_data called')
    return pd.DataFrame({
          'first column': list(range(5, 11)),
          'second column': np.arange(5, 11, 1)
         })

# df = get_select_box_data()

# option = st.selectbox('Select a line to filter', df['first column'])

# filtered_df = df[df['first column'] == option]

# st.write(filtered_df)