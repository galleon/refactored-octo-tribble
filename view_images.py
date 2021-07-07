import streamlit as st
import requests
import shutil

import numpy as np
import pandas as pd


url = 'https://drmaboule-ouh2vqtouq-ew.a.run.app/patients'


def get_patient_id():
    st.markdown("""get patient""")
    r = requests.get(url).json()
    list_of_patients = r['patients']
#    print(list_of_patients)
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
    open('test.zip', 'wb').write(r.content)
    import shutil
    shutil.unpack_archive('test.zip', "test")


# def download_file(patient_id, slice_number):
#     url_image = url+'/'+patient_id+'/'+f'{slice_number}'
#     local_filename = url.split('/')[-1]
#     r = requests.get(url, stream=True)
#     with v as r:
#         with open(test.tif, 'wb') as f:
#             shutil.copyfileobj(r.raw, f)

#     return local_filename


patient_id = get_patient_id()
number_of_slices = get_slices(patient_id)
slice_number = st.slider('Select a line count', 1, number_of_slices, 1)

if st.button('Download'):
    st.write('Clicked!!!')
    image = get_image(patient_id, slice_number)
    print(image)
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