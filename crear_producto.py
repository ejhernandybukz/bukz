import streamlit as st
import pandas as pd
from unidecode import unidecode
import json
import numpy as np
import io
from openpyxl.utils import get_column_letter


def crear_productos():
    st.title("Creación de productos")
    st.markdown("<h3>Plantilla creación de productos</h3>", unsafe_allow_html=True)
   
    #st.set_option('deprecation.showfileUploaderEncoding', False)  # Evita el aviso de codificación

    # Ruta del archivo local
    file_path = "plantilla_creacion_productos.xlsx"
    
    # Botón de descarga
    def download_file():
        with open(file_path, "rb") as file:
            btn = st.download_button(label="Descargar archivo", data=file, file_name="plantilla_creacion_productos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        return btn
    # Llamar a la función para mostrar el botón de descarga
    download_file()
    
    st.write("Cargar archivo XLSX (Formato Excel):")
    st.markdown("<h3>Archivo con datos</h3>", unsafe_allow_html=True)
    uploaded_file3 = st.file_uploader("Los nombres de las columnas del archivo debe conservar el mismo nombre de la plantilla de creación de productos", type=["xlsx"], key="archivo_productos")
    if uploaded_file3 is not None:
        st.write("Presiona el botón para continuar")
        if st.button("Continuar"):
            info_placeholder = st.empty()
            info_placeholder.info("Cargando...")

            df2 = pd.read_excel(uploaded_file3, sheet_name='Products', engine='openpyxl')

            try:  
                df = pd.DataFrame()
                df['Title'] = df2['Titulo'].str.title()
                
                df['Command'] = 'NEW'
                
                df['Body HTML'] = df2['Sipnosis']
                
                df2['Variant SKU'] = df2['SKU'].apply(lambda x: str(x).replace('.0', ''))
                
                df['Handle'] = df['Title'].str.lower().apply(lambda x: unidecode(x) if isinstance(x, str) else x).str.replace(r'[^\w\s]+', '', regex=True).str.replace(' ', '-') + '-' + df2['Variant SKU']
                
                #Vendor
                df['Vendor'] = df2['Vendor']
                
                #Vendor
                df['Type'] = 'Libro'
                
                #tags
                df['Tags'] = pd.Series(dtype=str)
                
                #Status
                df['Status'] = 'Active'
                
                #Published
                df['Published'] = 'TRUE'
                
                #Published Scope
                df['Published Scope'] = 'global'
                
                #Gift Card
                df['Gift Card'] = 'FALSE'
                
                #Row #
                df['Row #'] = 1
                
                #Top Row
                df['Top Row'] = 'TRUE'
                
                # Option1 Name
                df['Option1 Name'] = 'Title'
                
                #Option1 Value
                df['Option1 Value'] = 'Default Title'
                
                # Option2 Name
                df['Option2 Name'] = pd.Series(dtype=str)
                
                # Option2 Value
                df['Option2 Value'] = pd.Series(dtype=str)
                
                # Option3 Name
                df['Option3 Name'] = pd.Series(dtype=str)
                
                # Option3 Value
                df['Option3 Value'] = pd.Series(dtype=str)
                
                #Variant Position
                df['Variant Position'] = pd.Series(dtype=str)
                
                #Variant SKU
                df['Variant SKU'] = df2['SKU'].apply(lambda x: str(x).replace('.0', ''))
                #Variant Barcode
                df['Variant Barcode'] = df['Variant SKU']
                
                #Variant Image
                df['Image Src'] = df2['Portada (URL)']
                
                df['Variant Price'] = df2["Precio"]
                
                df['Variant Compare At Price'] = df2["Precio de comparacion"]
                
                #Variant Taxable
                df['Variant Taxable'] = 'FALSE'
                
                #Variant Tax Code
                df['Variant Tax Code'] = pd.Series(dtype=str)
                
                #Variant Inventory Tracker
                df['Variant Inventory Tracker'] = 'shopify'
                
                #Variant Inventory Policy
                df['Variant Inventory Policy'] = 'deny'
                
                #Variant Inventory Tracker
                df['Variant Fulfillment Service'] = 'manual'
                
                #Variant Requires Shipping
                df['Variant Requires Shipping'] = 'TRUE'
                #Variant Weight
                df['Variant Weight'] = df2['peso (kg)']
                
                #Variant Weight Unit
                df['Variant Weight Unit'] = df['Variant Weight'].apply(lambda x: 'kg' if pd.notnull(x) else np.nan)
                
                #Metafield: custom.autor [single_line_text_field]
                df['Metafield: custom.autor [single_line_text_field]'] = df2["Autor"].fillna("").str.title()
                
                replacements2 = {'Español' : '["Español"]', 'Ingles' : '["Ingles"]', 'Frances' : '["Frances"]', 'Italiano' : '["Italiano"]', 'Portugues' : '["Portugues"]', 
                    'Aleman' : '["Aleman"]', 'Bilingue (Español-Ingles)' : '["Bilingue (Español-Ingles)"]', 'Bilingue (Español-Portugues)' : '["Bilingue (Español-Portugues)"]', 
                    'Vasco' : '["Vasco"]', 'Gallego' : '["Gallego"]', 'Latin' : '["Latin"]', 'Ruso' : '["Ruso"]', 'Arabe' : '["Arabe"]', 'Chino' : '["Chino"]', 
                    'Japones' : '["Japones"]', 'Catalan' : '["Catalan"]', 'Rumano' : '["Rumano"]', 'Holandes' : '["Holandes"]', 'Bulgaro' : '["Bulgaro"]', 'Griego' : '["Griego"]', 
                    'Polaco' : '["Polaco"]', 'Checo' : '["Checo"]', 'Sueco' : '["Sueco"]'}
                
                df['Metafield: custom.idioma [list.single_line_text_field]'] = df2['Idioma'].apply(lambda x: replacements2.get(x, x))
                
                replacements = {
                    'Tapa Dura' : '["Tapa Dura"]', 'Tapa Blanda' : '["Tapa Blanda"]', 'Bolsillo' : '["Bolsillo"]', 'Libro de lujo' : '["Libro de lujo"]', 
                    'Espiral' : '["Espiral"]', 'Tela' : '["Tela"]', 'Grapado' : '["Grapado"]', 'Fasciculo Encuadernable' : '["Fasciculo Encuadernable"]', 
                    'Troquelado' : '["Troquelado"]', 'Anillas' : '["Anillas"]', 'Otros' : '["Otros"]'}
                
                df['Metafield: custom.formato [list.single_line_text_field]'] = df2['Formato'].apply(lambda x: replacements.get(x, x))
                
                df['Metafield: custom.alto [dimension]'] = df2['Alto'].apply(lambda x: np.nan if np.isnan(x) else json.dumps({"value": x, "unit": "cm"}))
                
                df['Metafield: custom.ancho [dimension]'] = df2['Ancho'].apply(lambda x: np.nan if np.isnan(x) else json.dumps({"value": x, "unit": "cm"}))
                
                df['Metafield: custom.editorial [single_line_text_field]'] = df2['Editorial'].str.title()
                
                df['Metafield: custom.numero_de_paginas [number_integer]'] = df2['Numero de paginas']
                
                df['Metafield: custom.ilustrador [single_line_text_field]'] = df2['Ilustrador']
                
                df['Image Alt Text'] = 'Libro ' + df['Title']+' '+ df['Variant SKU']
                df_crear = df
                
                info_placeholder.empty()
                st.write(df_crear)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_crear.to_excel(writer, index=False)
        
                # Mostrar el botón de descarga
                st.download_button(
                    label="Descargar archivo xlsx",
                    data=output.getvalue(),
                    file_name="resultado_crear_productos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                
            except Exception as e:
                info_placeholder.empty()
                st.error(f"Error: {str(e)}")
    else:
        st.info("Por favor, carga el archivo para continuar.")
