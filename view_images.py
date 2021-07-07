import streamlit as st
import requests
import shutil
import os
import tempfile
import numpy as np
import pandas as pd
from PIL import Image


root_url = 'https://drmaboule-ouh2vqtouq-ew.a.run.app'


def get_patient_id():
    url = f'{root_url}/patients'
    st.markdown("""get patient""")
    r = requests.get(url).json()
    list_of_patients = r['patients']
    list_of_patients.insert(0, 'Patient_Id')
    patient_id = st.selectbox("patient", list_of_patients, help="select the patient id")
    return patient_id

def get_number_of_slices(patient_id):
    st.markdown("""get slice number""")
    url = f'{root_url}/patients/{patient_id}'
    r = requests.get(url).json()
    number_of_slices = r['number_of_slices']
    return number_of_slices

def get_image(patient_id, slice_number):
    url = f'{root_url}/patients/{patient_id}/{slice_number}'
    r = requests.get(url, allow_redirects=True)
    tmpdir = tempfile.TemporaryDirectory(suffix=None, prefix='tmp', dir=None).name
    os.mkdir(tmpdir)
    file_path = f'{tmpdir}/tmp.zip'
    open(file_path, 'wb').write(r.content)
    shutil.unpack_archive(file_path, tmpdir)

    image_path = f'{tmpdir}/{patient_id}_{slice_number}.tif' 
    mask_path  = f'{tmpdir}/{patient_id}_{slice_number}_mask.tif'
    pred_path  = f'{tmpdir}/{patient_id}_{slice_number}_mask.tif'
    image = Image.open(image_path).convert('RGB')
    mask  = Image.open(mask_path).convert('RGB')
    pred  = Image.open(pred_path).convert('RGB')
    
    col1, col2, col3 = st.beta_columns(3)
    image_title = '<p style="font-family:sans-serif;text-align: center; color:Black; font-size: 20px;">Brain MRI</p>'
    col1.markdown(image_title, unsafe_allow_html=True)
    col1.image(image, use_column_width=True)    
    mask_title = '<p style="font-family:sans-serif;text-align: center; color:Black; font-size: 20px;">Original Mask</p>'
    col2.markdown(mask_title, unsafe_allow_html=True)
    col2.image(mask, use_column_width=True)    
    pred_title = '<p style="font-family:sans-serif;text-align: center; color:Black; font-size: 20px;">Predicted Mask</p>'
    col3.markdown(pred_title, unsafe_allow_html=True)
    col3.image(pred, use_column_width=True)     
    
    shutil.rmtree(tmpdir)
 #   os.remove('tmpdir')
    return True
    




url = f'{root_url}/predict'
files = {'media': open('tmp/TCGA_CS_5396_20010302_18.tif', 'rb')}
r = requests.post(url, files=files)
print(r)






patient_id = get_patient_id()

if patient_id != 'Patient_Id':
    number_of_slices = get_number_of_slices(patient_id)
    slice_number = st.slider('Select a line count', 0, number_of_slices, 0)
    if slice_number != 0:
        get_image(patient_id, slice_number)





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