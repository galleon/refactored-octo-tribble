import streamlit as st
import requests

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


patient_id = get_patient_id()
number_of_slices = get_slices(patient_id)
slice_number = st.slider('Select a line count', 1, number_of_slices, 1)




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