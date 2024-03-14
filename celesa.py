import streamlit as st
import pandas as pd

def actualizar_inventario_celesa():
    st.title("Actualización de inventario celesa")
    st.write("Cargar archivos CSV:")
    #st.set_option('deprecation.showfileUploaderEncoding', False)  # Evita el aviso de codificación

    st.markdown("<h3>Archivo Productos</h3>", unsafe_allow_html=True)
    uploaded_file1 = st.file_uploader("El archivo de producto debe tener las columnas: ID,  Variant ID,  Vendor,  Variant SKU,  Variant Barcode,  Inventory Available Dropshipping [España]", type=["csv"], key="archivo_productos")

    st.markdown("<h3>Archivo Azeta</h3>", unsafe_allow_html=True)
    uploaded_file2 = st.file_uploader("", type=["csv"], key="archivo_azeta")


    if uploaded_file1 is not None and uploaded_file2 is not None:
        st.write("Presiona el botón para continuar")
        if st.button("Continuar"):
            info_placeholder = st.empty()
            info_placeholder.info("Cargando...")

            df_products = pd.read_csv(uploaded_file1)
            df_azeta = pd.read_csv(uploaded_file2, sep=';', header=None)
            df_azeta.columns = ['Variant SKU', 'Stock_Azeta']
            df_azeta['Variant SKU'] = df_azeta['Variant SKU'].astype(str)


            try:
                
                df_products = df_products[['ID', 'Variant ID', 'Vendor', 'Variant SKU', 'Variant Barcode', 'Inventory Available: Dropshipping [España]']]
                df_products.insert(1, 'Command', 'UPDATE')
                # Paso 1: Identificar registros con '.0' al final en 'Variant SKU'
                tiene_punto_cero = df_products['Variant SKU'].astype(str).str.endswith('.0').fillna(False)
                
                # Paso 2: Crear un nuevo DataFrame con estos registros
                
                df_con_punto_cero = df_products.loc[tiene_punto_cero]
                
                df_products['Variant SKU'] = df_products['Variant SKU'].astype(str).str.replace('\.0$', '', regex=True)
                
                df_products = df_products.loc[df_products['Vendor'] == 'Bukz España']
                df_merged = pd.merge(df_products, df_azeta, on="Variant SKU", how='left')

                df_merged['Inventory Available: Dropshipping [España]'].fillna(0, inplace=True)
                df_merged['Stock_Azeta'].fillna(0, inplace=True)
                df_merged['Stock_Azeta'] = df_merged['Stock_Azeta'].astype(int)
                df_merged['Inventory Available: Dropshipping [España]'] = pd.to_numeric(df_merged['Inventory Available: Dropshipping [España]'], errors='coerce').fillna(0).astype(int)
                df_merged['Inventory Available: Dropshipping [España]'] = df_merged['Inventory Available: Dropshipping [España]'].astype(float).astype(int)
                df_merged['Stock_Azeta'] = df_merged['Stock_Azeta'].astype(float).astype(int)

                comparar_filas = lambda x: 1 if x['Inventory Available: Dropshipping [España]'] == x['Stock_Azeta'] else 0
                df_merged['Resultado'] = df_merged.apply(comparar_filas, axis=1)
                df_final = df_merged.loc[df_merged['Resultado'] == 0]
                df_final['Inventory Available: Dropshipping [España]'] = df_final['Stock_Azeta']
                            
                
                df_final.drop(['Stock_Azeta', 'Resultado'], axis=1, inplace=True)
                df_final = df_final.astype({'ID':str, 'Variant ID':str, 'Vendor':str, 'Variant SKU':str, 
                                           'Variant Barcode':str, 'Inventory Available: Dropshipping [España]':str})
                
                info_placeholder.empty()
                st.write(df_final)

                # Botón de descarga sin base64
                st.download_button(
                    label="Descargar CSV",
                    data=df_final.to_csv(index=False),
                    file_name="resultado_cruzado.csv",
                    mime="text/csv"
                )
            except Exception as e:
                info_placeholder.empty()
                st.error(f"Error: {str(e)}")
                
    else:
        st.info("Por favor, carga ambos archivos para continuar.")