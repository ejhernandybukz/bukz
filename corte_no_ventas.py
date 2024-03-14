import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit as st
import io
from openpyxl.utils import get_column_letter

def corte_provedores_no_ventas():
    st.title("Corte Proveedores - No ventas")

    st.markdown("<h3>Archivo con correo de provedores</h3>", unsafe_allow_html=True)
    proveedores_df_1 = st.file_uploader("El archivo debe tener las columnas: Proveedores y Correo Medellin", type=["xlsx"], key="archivo_proveedores")
    
    st.markdown("<h3>Archivo estado de envío proveeedores con ventas</h3>", unsafe_allow_html=True)
    uploaded_file_ventas_mesuales = st.file_uploader("", type=["xlsx"], key="archivo_productos")
    
    if uploaded_file_ventas_mesuales is not None and proveedores_df_1 is not None:
        if st.button("Continuar"):
            with st.spinner("Procesando datos..."):
                st.session_state['archivo_cargado'] = True
    
    if st.session_state.get('archivo_cargado', False):
        proveedores_df = pd.read_excel(proveedores_df_1)
        provedores_con_ventas = pd.read_excel(uploaded_file_ventas_mesuales)
        
        no_ventas = proveedores_df.merge(provedores_con_ventas, right_on='Proveedor', left_on='Proveedores', how='left', indicator=True)
        no_ventas = no_ventas[no_ventas['_merge'] == 'left_only']
        no_ventas = no_ventas.drop(columns=['_merge'])
        
        df_proveedores = no_ventas.copy()
        
        # DataFrame para almacenar los proveedores a los que se les envía correo
        proveedores_enviados_df = pd.DataFrame(columns=['Proveedor', 'Correo Medellin'])
        
        # Configuración de las credenciales SMTP
        # Widgets para ingresar datos del usuario
        st.session_state.smtp_user = st.text_input("Ingrese el usuario SMTP:", value=st.session_state.smtp_user)
        st.session_state.smtp_password = st.text_input("Ingrese la contraseña SMTP:", type="password", value=st.session_state.smtp_password)
        
        mes = st.text_input("Ingrese el mes:")  # No hay valor predeterminado
        año = st.text_input("Ingrese el año:")  # No hay valor predeterminado
        
        if 'nombre_remitente' not in st.session_state:
            st.session_state['nombre_remitente'] = "Sebastian Barrios - Bukz"  # Valor por defecto
        
        #Otros campos de texto
        remitente_default = "Sebastian Barrios - Bukz"
        remitente_otros = "Otro (escriba abajo)"
        nombre_remitente_seleccion = st.selectbox("Seleccione el nombre del remitente:", [remitente_default, remitente_otros])
        
        # Actualizar el valor de nombre_remitente en st.session_state
        if nombre_remitente_seleccion == remitente_otros:
            if 'nombre_remitente_personalizado' not in st.session_state:
                st.session_state['nombre_remitente_personalizado'] = ''
            st.session_state['nombre_remitente'] = st.text_input("Ingrese el nombre del remitente:", key="nombre_remitente_personalizado")
        else:
            st.session_state['nombre_remitente'] = remitente_default
            
        # Firma
        firma_default = "Sebastian Barrios - Analista de Operaciones"
        firma_otros = "Otra (escriba abajo)"
        firma_seleccion = st.selectbox("Seleccione la firma:", [firma_default, firma_otros])
        
        # Configuración del servidor de correo
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587                
        # Conexión al servidor SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(st.session_state.smtp_user, st.session_state.smtp_password)
        
        imagen_url = "https://ci3.googleusercontent.com/mail-sig/AIorK4zk7DTZK_4Nl0qLnpmzJnoAhaN3t08JpWQmDUdtbhe-nJySTGmVsdjlqZr7sVzEJzCFTSGzHY8" 
                 
        if st.button("Procesar archivo y enviar correos"):
            with st.spinner("Enviando correos..."):
                def enviar_correo_a_proveedor(correos_proveedor, nombre_proveedor, nombre_remitente):
                    # Dividir la cadena de correos en una lista
                    lista_correos = correos_proveedor.split(';')
                    
                    for correo_proveedor in lista_correos:
                        try:
                
                            # Crear el mensaje de correo electrónico
                            msg = MIMEMultipart('alternative')
                            msg['From'] = f"{nombre_remitente}"
                            msg['To'] = correo_proveedor.strip()
                            msg['Subject'] = f"Corte {mes} {año} - {nombre_proveedor}"
                            
                            # Cuerpo del mensaje
                            body_message =  f"""
                            <p>Buenos días,</p>
                        
                            <p>El presente correo es para informarle que no se registraron ventas durante el mes de {mes}.</p>
                        
                            <p>Para cualquier consulta o asunto adicional, no dude en ponerse en contacto con nosotros:</p>
                            <ul>
                                <li>Facturación: facturacion@bukz.co</li>
                                <li>Bodega y Devoluciones: cedi@bukz.co</li>
                            </ul>
                        
                        
                            <p>Saludos cordiales,</p>
                        
                            <p><strong style="color: gray;">{firma_seleccion}</strong></p>
                            <p><img src="{imagen_url}" alt="Logo Bukz" style="width: 150px;"></p>
                            """
                        
                            msg.attach(MIMEText(body_message, 'html'))
                        
                            # Enviar el correo
                            server = smtplib.SMTP(smtp_server, smtp_port)
                            server.starttls()
                            server.login(st.session_state.smtp_user, st.session_state.smtp_password)
                            server.send_message(msg)
                            server.quit()
                            print(f"Correo enviado exitosamente a {correo_proveedor.strip()} ({nombre_proveedor})")
                            
                            # Agregar el proveedor a los enviados al DataFrame
                            proveedores_enviados_df.loc[len(proveedores_enviados_df)] = [nombre_proveedor, correo_proveedor.strip()]
                        except Exception as e:
                            print(f"Error al enviar correo a {correo_proveedor.strip()} ({nombre_proveedor}): {e}")
            
                # Iterar sobre cada proveedor en el DataFrame y enviar el correo
                for index, row in df_proveedores.iterrows():
                    enviar_correo_a_proveedor(row['Correo Medellin'], row['Proveedores'], st.session_state['nombre_remitente'])
                
                # Guardar el DataFrame de proveedores enviados a un archivo CSV
                proveedores_enviados_df.to_csv("proveedores_enviados.csv", index=False)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    proveedores_enviados_df.to_excel(writer, index=False)
        
                # Mostrar el botón de descarga
                st.download_button(
                    label="Descargar archivo xlsx",
                    data=output.getvalue(),
                    file_name="Correo_proveedores_no_ventas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


