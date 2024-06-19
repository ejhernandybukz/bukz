import streamlit as st
import requests
import pandas as pd
import io
import os  #

def conversor_pedidos():
    
    st.title("Conversor COP-USD para pedidos")

    ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]
    SHOP_NAME = 'bukz-co'
    API_URL = 'https://v6.exchangerate-api.com/v6/e66a50170b1822d18a576b37/latest/USD'
    
    # Función para obtener la tasa de cambio
    def obtener_tasa_cambio(api_url, target_currency="COP"):
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            tasa_cambio = data["conversion_rates"].get(target_currency)
            if tasa_cambio:
                return tasa_cambio
            else:
                raise ValueError(f"No se encontró la tasa de cambio para {target_currency}.")
        else:
            raise ValueError(f"Error al acceder a la API: {response.status_code}")
    
    # Obtiene tasa de cambio una vez al cargar la aplicación
    tasa_cambio = obtener_tasa_cambio(API_URL)
    
    # Streamlit widgets para entrada de datos
    order_id = st.text_input('Ingrese el número de pedido', '')
    
    if st.button('Buscar pedido'):
        if order_id:
            # URL para la API de Shopify
            shopify_url = f'https://{SHOP_NAME}.myshopify.com/admin/api/2023-04/orders/{order_id}.json'
    
            # Encabezados para la solicitud
            headers = {
                "X-Shopify-Access-Token": ACCESS_TOKEN,
                "Content-Type": "application/json"
            }
    
            # Realiza la solicitud GET para obtener la información del pedido
            response = requests.get(shopify_url, headers=headers)
    
            # Verifica si la solicitud fue exitosa
            if response.status_code == 200:
                order_data = response.json()
                line_items = order_data['order']['line_items']
    
                # Crear DataFrame directamente desde los datos del pedido
                df = pd.DataFrame(line_items)
                df = df[['name', 'sku', 'quantity', 'price']]
                df.columns = ['Titulo', 'ISBN', 'Cantidad', 'PVP_COP']
                df['PVP_COP'] = df['PVP_COP'].astype(float)
    
                # Agrupar por ISBN
                grouped_df = df.groupby('ISBN').agg({
                    'Titulo': 'first',
                    'Cantidad': 'sum',
                    'PVP_COP': 'first'
                }).reset_index()
    
                # Realizar cálculos en USD
                grouped_df['PVP_USD'] = round(grouped_df['PVP_COP'] / tasa_cambio, 2)
                grouped_df['Precio_total_USD'] = round(grouped_df['PVP_USD'] * grouped_df['Cantidad'], 2)
                grouped_df['Descuento_por_unidad_USD'] = round(grouped_df['PVP_USD'] * 0.25, 2)
                grouped_df['Descuento_total_USD'] = round(grouped_df['Descuento_por_unidad_USD'] * grouped_df['Cantidad'], 2)
    
                # Mostrar tabla en Streamlit
                st.write(grouped_df)
    
                # Convertir DataFrame a Excel y permitir la descarga
                towrite = io.BytesIO()
                grouped_df.to_excel(towrite, index=False, header=True)  # Corregido aquí
                towrite.seek(0)
                file_name = f'pedido_{order_id}.xlsx'  # Personaliza el nombre del archivo con el número de pedido
                st.download_button(label='Descargar Excel', data=towrite, file_name=file_name)
            else:
                st.error(f"Error: {response.status_code}")
                st.json(response.text)
        else:
            st.error('Por favor ingrese un número de pedido válido.')
    
