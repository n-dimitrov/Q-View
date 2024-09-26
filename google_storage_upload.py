import streamlit as st

from st_files_connection import FilesConnection


st.write("Hello Connection")

conn = st.connection('gcs', type=FilesConnection)
st.write(conn)

if (st.button("List files")):
    list = conn.fs.ls("gcs://q-view/")
    st.write(list)

if (st.button("upload file")):
    with (st.spinner("Uploading file...")):
        with conn.open("gcs://q-view/test.txt", "w") as f:
            f.write("this is a test message")
            st.write("File uploaded")