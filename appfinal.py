import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
from celesa import actualizar_inventario_celesa
from crear_producto import crear_productos
from corte_provedores import corte_provedores
from corte_no_ventas import corte_provedores_no_ventas
from sugerido import sugerido
from provedores import provedores_inventario


# Cargar la imagen
logo_image = Image.open("LOGO_BUKZ.webp")  # Reemplaza con la ruta o nombre de archivo correcto

resized_image = logo_image.resize((200, 50))  # Especifica las dimensiones deseadas

# Mostrar la imagen redimensionada en la barra lateral
st.sidebar.image(resized_image)


with st.sidebar:
    choose = option_menu("Menú de opciones", ['Actualización de inventario celesa', 'Creación de productos', 
                                              'Corte - Ventas', 'Corte - No Ventas', 'Sugerido Inventario', 'Proveedores Stock'],
    icons=["list check", "database up", 'envelope at', 'envelope at',"check2 square", "list check" ], menu_icon="cast", default_index=0,
    styles={ "container": {"padding": "5!important", "background-color": "#fafafa"},
        "icon": { "font-size": "25px"}, 
        "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee", "color": "black"},
        "nav-link-selected": {"background-color": "#F9CB00"}})
    
if 'smtp_user' not in st.session_state:
    st.session_state['smtp_user'] = ''
if 'smtp_password' not in st.session_state:
    st.session_state['smtp_password'] = ''
if 'archivo_cargado' not in st.session_state:
    st.session_state['archivo_cargado'] = False
if 'procesado' not in st.session_state:
    st.session_state['procesado'] = False
    
if choose == 'Actualización de inventario celesa':
    actualizar_inventario_celesa()
    
elif choose == 'Creación de productos':
    crear_productos()
    
elif choose == 'Corte - Ventas':
    corte_provedores()
    
elif choose == 'Corte - No Ventas':
    corte_provedores_no_ventas()
    
elif choose == 'Sugerido Inventario':
    sugerido()
    
elif choose == 'Proveedores Stock':
    provedores_inventario()
