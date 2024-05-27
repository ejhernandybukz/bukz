from sqlalchemy import create_engine
import pandas as pd
import streamlit as st
from psycopg2.extras import execute_values
from psycopg2 import sql
import mimetypes

def provedores_inventario():
    
    DATABASE_URL = "postgresql://postgres.tjcyemzauznhllboqulw:TifzZOBVidUBkoYk@aws-0-us-west-1.pooler.supabase.com/postgres"
    engine = create_engine(DATABASE_URL)

    def load_data(file):
        mime_type, _ = mimetypes.guess_type(file.name)
        if mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" or mime_type == "application/vnd.ms-excel":
            return pd.read_excel(file)
        elif mime_type == "text/csv":
            return pd.read_csv(file)
        else:
            st.error("Tipo de archivo no soportado")
            return pd.DataFrame()

    def standardize_columns(df, sku_col, name_col, quantity_col, vendor):
        return pd.DataFrame({
            'sku': df[sku_col].astype(str),
            'vendor': vendor,
            'title': df[name_col].astype(str),
            'stock': df[quantity_col].fillna(0).astype(int),  # Manejo de NaNs
            'recorded_date': pd.Timestamp.now().date(),
            'updated_at': pd.Timestamp.now().date()
        })

    def upsert_to_database(df, table_name):
        conn = engine.raw_connection()
        cursor = conn.cursor()
        sql_query = sql.SQL("""
            INSERT INTO {table} (sku, vendor, title, stock, recorded_date, updated_at)
            VALUES %s
            ON CONFLICT (sku, vendor) DO UPDATE SET
            title = EXCLUDED.title,
            stock = EXCLUDED.stock,
            updated_at = EXCLUDED.updated_at
        """).format(table=sql.Identifier(table_name))
        
        try:
            execute_values(cursor, sql_query, df.values.tolist(), template=None, page_size=100)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    st.title('Carga de Inventario de Proveedores')
    uploaded_file = st.file_uploader("Sube un archivo XLSX, XLS o CSV", type=['xlsx', 'xls', 'csv'])

    if uploaded_file:
        df = load_data(uploaded_file)
        if not df.empty:
            all_columns = df.columns.tolist()
            sku_col = st.selectbox('Selecciona la columna para SKU', all_columns, key='sku', on_change=None)
            name_col = st.selectbox('Selecciona la columna para Título del libro', all_columns, key='name', on_change=None)
            quantity_col = st.selectbox('Selecciona la columna para Cantidad', all_columns, key='quantity', on_change=None)
            proveedores_file = "lista_proveedores.xlsx"  # Ajusta la ruta del archivo si es necesario
            proveedores_df = pd.read_excel(proveedores_file)
            vendor_list = proveedores_df["proveedores"].tolist()  # Asumiendo lista fija de proveedores
            vendor = st.selectbox('Selecciona un proveedor', vendor_list)

            if st.button('Confirmar selecciones y procesar datos'):
                df_prepared = standardize_columns(df, sku_col, name_col, quantity_col, vendor)
                try:
                    upsert_to_database(df_prepared, 'provedores_inventario')
                    st.success('Datos cargados correctamente en la base de datos!')
                except Exception as e:
                    st.error(f'Error al cargar datos: {str(e)}')
