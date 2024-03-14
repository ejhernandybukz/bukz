import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
import zipfile
from io import BytesIO
from datetime import datetime, timedelta
from calendar import month_name


def sugerido():
    st.title("Actualización de inventario celesa")
    st.write("Cargar archivos CSV:")
    #st.set_option('deprecation.showfileUploaderEncoding', False)  # Evita el aviso de codificación

    st.markdown("<h3>Archivo Productos</h3>", unsafe_allow_html=True)
    uploaded_file1 = st.file_uploader("")

    st.markdown("<h3>Archivo ventas</h3>", unsafe_allow_html=True)
    uploaded_file2 = st.file_uploader("", type=["csv"], key="archivo_azeta")
    
    # Lista de meses en inglés
    months = list(month_name)[1:]
    
    # Obtener la entrada del usuario
    selected_month = st.selectbox("Selecciona el mes del análisis:", months)

     # Verificar si se ha seleccionado un mes
    if selected_month:
        # Obtener el índice del mes seleccionado
        selected_month_index = months.index(selected_month)
        
        # Obtener el índice del mes hace 6 meses
        start_index = (selected_month_index - 5) % 12
        
        # Obtener los últimos 6 meses en inglés
        months = [months[(start_index + i) % 12] for i in range(6)]

        if uploaded_file1 is not None and uploaded_file2 is not None:
            st.write("Presiona el botón para continuar")
            if st.button("Continuar"):
                info_placeholder = st.empty()
                info_placeholder.info("Cargando...")
                    
                inventario_original_1 = pd.read_csv(uploaded_file1)
                df1 = pd.read_csv(uploaded_file2)
                
                columns_to_update = [
                    'Inventory Available: Bukz Bogota 109',
                    'Inventory Available: Bukz Las Lomas',
                    'Inventory Available: Bukz Mattelsa',
                    'Inventory Available: Bukz Tesoro',
                    'Inventory Available: Cedi Lomas']
                
                # Aplicar una función que convierte valores negativos a 0
                for column in columns_to_update:
                    inventario_original_1[column] = pd.to_numeric(inventario_original_1[column], errors='coerce').apply(lambda x: 0 if x < 0 else x)
    
                    
                inventario_original_1[columns_to_update] = inventario_original_1[columns_to_update].fillna(0)
                
                inventario_original_2 = inventario_original_1[['ID','Title']].copy()
                rename_columns = {'ID': 'product_id'}
                inventario_original_2 = inventario_original_2.rename(columns=rename_columns)
                
                inventario_original_1 = inventario_original_1.loc[:, ~inventario_original_1.columns.duplicated()]
                
                inventario_original = inventario_original_1.loc[~inventario_original_1['Vendor'].isin(['Bukz USA', 'Bukz España'])].copy()
                inventario_original = inventario_original.loc[inventario_original['Type'].isin(['Libro', 'Libros', 'Libros impresos'])]
                inventario_original['ID'] = inventario_original['ID'].astype('Int64')
                
                
                # Calcula el promedio de ventas basado en el número de meses de creación
                def compute_sales_based_on_creation(row):
                    total_sales = row[months].sum()
                    return total_sales / row['meses de creación']
                
                # Detecta si un producto ha tenido ventas de manera intermitente (i.e., ha tenido ventas, luego no ventas, y luego ventas nuevamente)
                def is_intermittent(s):
                    had_sales = False
                    had_no_sales = False
                    for sale in s:
                        if sale > 0:
                            if had_no_sales:
                                return True
                            had_sales = True
                        else:
                            if had_sales:
                                had_no_sales = True
                    return False
                
                # Calcula el promedio de ventas para aquellos registros que tienen ventas intermitentes
                def compute_average(s):
                    months_with_sales = len(s[s > 0])
                    if months_with_sales == 0:
                        return 0
                    return s.sum() / months_with_sales
                
                
                # Calcula el promedio de ventas solo para los meses en los que hubo ventas
                def compute_average_sales(row):
                    months_with_sales = row[months].loc[row[months] > 0]
                    return months_with_sales.mean()
                
                # Calcula el promedio total de ventas considerando todos los meses
                def compute_total_average(row, months):
                    return row[months].sum() / len(months)
                
                # Calcula el promedio de ventas de los últimos 6 meses
                def compute_six_month_average(row):
                    return row[months].mean()
                
                # Asigna un valor sugerido y una descripción de caso a los registros del dataframe basado en una condición
                def set_suggested_and_case(df, condition, suggested_value, case_description):
                    df.loc[condition, 'sugerido'] = suggested_value
                    df.loc[condition, 'tipo_caso'] = case_description
                    return df
                
                # Asigna un valor sugerido para libros antiguos con ventas bajas
                def set_suggested_for_old_books(df):
                    condition = (df['meses de creación'] >= 5) & (df['Total'].isin([1, 2]))
                    return set_suggested_and_case(df, condition, 1, "Mas de 5 meses de creación y 2 o menos libros vendidos")
                
                # Asigna un valor sugerido basado en el promedio de ventas para aquellos registros que han vendido durante 5 o 6 meses
                def set_suggested_for_months_with_sales(df):
                    condition = df['MonthsWithSales'].isin([5, 6])
                    suggested_value = (df['Total'] / df['MonthsWithSales']).mul(1).round(0).astype(float)
                    return set_suggested_and_case(df, condition, suggested_value, "5 o 6 meses de venta")
                
                # Asigna un valor sugerido para productos creados recientemente
                def set_suggested_for_recent_creation(df):
                    condition = (df['meses de creación'] <= 4) & (df['sugerido'].isna())
                    suggested_value = df.apply(compute_sales_based_on_creation, axis=1).round(0).fillna(0).astype(int)
                    return set_suggested_and_case(df, condition, suggested_value, "Creado hace menos de 4 meses")
                
                # Asigna un valor sugerido para productos con ventas intermitentes
                def set_suggested_for_intermittent_sales(df, month_columns):
                    df['intermittent'] = df[month_columns].apply(is_intermittent, axis=1)
                    condition = df['intermittent'] & df['sugerido'].isna()
                    suggested_value = df[month_columns].apply(compute_average, axis=1).mul(1).round(0)
                    return set_suggested_and_case(df, condition, suggested_value, "Ventas intermitentes (posibles agotados)")
                
                # Asigna un valor sugerido para productos que actualmente no tienen inventario
                def set_suggested_for_no_inventory(df, inv_sede):
                    ultimo_elemento = months[-1]
                    condition = (df[inv_sede] == 0) & (df[ultimo_elemento] == 0) & df['sugerido'].isna()
                    suggested_value = df.apply(compute_average_sales, axis=1).round(0)
                    return set_suggested_and_case(df, condition, suggested_value, "Productos sin inventario en bodega actualmente")
                
                # Asigna un valor sugerido para productos de reciente creación con ventas bajas
                def set_suggested_for_recent_creation_with_low_sales(df):
                    condition = (df['meses de creación'] < 5) & df['Total'].isin([1, 2, 3, 4]) & df['sugerido'].isna()
                    return set_suggested_and_case(df, condition, 1, "Meses de creación menor a 5 y promedio de ventas 0,8 o menos, 1 predeterminado")
                
                # Asigna un valor sugerido basado en el promedio de ventas de los últimos 6 meses
                def set_suggested_for_average_sales(df, months):
                    condition = (df['meses de creación'] > 4) & df['MonthsWithSales'].isin([3, 4]) & df['sugerido'].isna()
                    suggested_value = df.apply(lambda row: compute_total_average(row, months), axis=1).round(0)
                    return set_suggested_and_case(df, condition, suggested_value, "Promedio de ventas de 6 meses")
                
                #No ventas con inventario
                def calcular_envio(row, col_inventario):
                    meses = row["meses de creación"]
                    inventario = row[col_inventario]
                    
                    if meses <= 1:
                        return 0
                    elif 1 < meses <= 3:
                        if inventario > 3:
                            return inventario - 3
                        else:
                            return 0
                    elif 3 < meses <= 6:
                        if inventario > 2:
                            return inventario - 2
                        else:
                            return 0
                    else: # si meses > 6
                        if inventario > 1:
                            return inventario - 1
                        else:
                            return 0
                        
                        
                def compute_values(row):
                    caso = row['tipo_caso']
                    sugerido = row['sugerido']
                    total = row['Total']
                
                    # Por defecto, mantendremos sugerido_2 y meses de inventario como NaN
                    sugerido_2 = np.nan
                    meses_de_inventario = np.nan
                
                    if caso == "5 o 6 meses de venta":
                        sugerido_2 = sugerido * 4 if sugerido >= 5 else sugerido * 2
                        meses_de_inventario = 4 if sugerido >= 5 else 2
                
                    elif caso == "Creado hace menos de 4 meses":
                        sugerido_2 = sugerido * 3 if sugerido >= 5 else sugerido * 2
                        meses_de_inventario = 3 if sugerido >= 5 else 2
                
                    elif caso == "Mas de 5 meses de creación y 2 o menos libros vendidos":
                        sugerido_2 = sugerido
                        meses_de_inventario = ""
                
                    elif caso == "Meses de creación menor a 5 y promedio de ventas 0,8 o menos, 1 predeterminado":
                        sugerido_2 = sugerido * 2
                        meses_de_inventario = 2
                
                    elif caso == "Productos sin inventario en bodega actualmente":
                        sugerido_2 = sugerido 
                        meses_de_inventario = ''
                
                    elif caso == "Promedio de ventas de 6 meses":
                        sugerido_2 = sugerido * 2 if total >= 5 else sugerido
                        meses_de_inventario = 2 if total >= 5 else ""
                
                    elif caso == "Ventas intermitentes (posibles agotados)":
                        sugerido_2 = sugerido * 2
                        meses_de_inventario = 2
                
                    return pd.Series([sugerido_2, meses_de_inventario], index=['sugerido_2', 'meses de inventario'])
                
                
                sedes = ['Bukz Bogota 109', 'Bukz Las Lomas', 'Bukz Mattelsa' ] 
                
                resultados = {}  # Diccionario vacío para almacenar los DataFrames
                
                for sede in sedes:
                    inventario2 = inventario_original.copy()
                    inv_sede = "Inventory Available: " + sede
                    
                
                    #months = [ 'September','October', 'November', 'December', 'January','February']
                
                    # Filtrar las filas que cumplan con el criterio
                    df = df1.loc[~df1['product_vendor'].isin(['Bukz USA', 'Bukz España'])]
                    df = df.loc[df['product_type'].isin(['Libro', 'Libros', 'Libros impresos'])]
                    df["net_quantity"] = df["net_quantity"].apply(lambda x: abs(x))
                    df.loc[df['net_quantity'] > 3, 'net_quantity'] = 1
                    df['pos_location_name'] = df['pos_location_name'].replace('Libreria Provenza', 'Bukz Las Lomas')
                    df = df.loc[df['api_client_title'].isin(['Point of Sale'])]
                    df = df.loc[df['pos_location_name'].isin([sede])]
                
                        # Convertir la columna 'day' a formato de fecha
                    df['day'] = pd.to_datetime(df['day'], format='%Y-%m-%d')
                
                    # Agrupar por día y product_id y sumar las cantidades
                    df = df.groupby(['day', 'product_id', 'variant_sku']).sum().reset_index()
                    
                    def categorize_quantity(qty):
                        if qty <= 2:
                            return qty
                        elif 3 <= qty < 7:
                            return 1
                        elif 7 <= qty <= 10:
                            return 2
                        elif qty >= 11:
                            return 3
                
                    df['net_quantity'] = df['net_quantity'].apply(categorize_quantity)
                
                    # Agregar una columna 'month_name' con los nombres de los meses
                    df['month_name'] = df['day'].dt.strftime('%B')
                
                    # Pivotear el DataFrame para tener los nombres de los meses como columnas
                    pivot_df = df.pivot_table(index=['product_id','variant_sku'], columns='month_name', values='net_quantity', aggfunc='sum', fill_value=0).reset_index()
                
                    # Reorganizar el DataFrame con las columnas por meses
                    ordered_columns = ["product_id", "variant_sku"] + months 
                    pivot_df = pivot_df[ordered_columns]
                
                    # Organizar el DataFrame pivotado según la cantidad total de ventas por SKU
                    pivot_df['Total'] = pivot_df[months].sum(axis=1)
                    pivot_df = pivot_df.sort_values(by='Total', ascending=False)  # Ordenar de mayor a menor según la suma total
                
                    # Calcular la cantidad de meses con ventas         
                    pivot_df["MonthsWithSales"] = pivot_df.apply(lambda row: sum(1 for month in months if row[month] > 0), axis=1) 
                
                    df_filtered = pivot_df[~(pivot_df[months] == 0).all(axis=1)]
                
                    inventario = inventario2
                
                    # Convierte ambas columnas a tipo de dato str
                    pivot_df['product_id'] = pivot_df['product_id'].astype('Int64')
                    inventario['ID'] = inventario['ID'].astype('Int64')
                
                    columnas_deseadas_inventario = ['ID', 'Vendor', 'Title', 'Type', 'Variant SKU', 'Created At', 'Inventory Available: Bukz Bogota 109','Inventory Available: Bukz Mattelsa', 'Inventory Available: Bukz Las Lomas', 'Inventory Available: Cedi Lomas']
                    inventario = inventario[columnas_deseadas_inventario].copy()  # Añade .copy() aquí
                    inventario[[  'Inventory Available: Bukz Mattelsa', 'Inventory Available: Bukz Las Lomas','Inventory Available: Bukz Bogota 109', 
                                'Inventory Available: Cedi Lomas']] = inventario[[  'Inventory Available: Bukz Mattelsa', 
                                'Inventory Available: Bukz Las Lomas', 'Inventory Available: Bukz Bogota 109', 
                                'Inventory Available: Cedi Lomas']].apply(lambda x: abs(x))
                
                    # Realiza el cruce con las columnas convertidas
                    df_resultado = pd.merge(pivot_df, inventario, left_on='product_id', right_on='ID', how='left')
                    df_resultado = df_resultado.dropna(subset=['Variant SKU'])
                
                    # Convierte la columna "Created At" al tipo de datos datetime si aún no lo está
                    df_resultado['Created At'] = pd.to_datetime(df_resultado['Created At'])
                
                    # Obtiene la fecha actual
                    fecha_actual = datetime.now()
                
                    # Calcula la diferencia en meses entre la fecha actual y la columna "Created At" en formato decimal
                    df_resultado['meses de creación'] = ((fecha_actual - df_resultado['Created At']).dt.total_seconds() / (30 * 24 * 60 * 60)).round(1)
                
                    # Aplicar todas las reglas en secuencia:
                    def apply_all_rules(df, months, inv_sede):
                        month_columns = [col for col in df.columns if col in months]
                        df['sugerido'] = np.nan
                        df['tipo_caso'] = ""
                
                        df = set_suggested_for_old_books(df)
                        df = set_suggested_for_months_with_sales(df)
                        df = set_suggested_for_recent_creation(df)
                        df = set_suggested_for_intermittent_sales(df, month_columns)
                        df = set_suggested_for_no_inventory(df, inv_sede)
                        df = set_suggested_for_recent_creation_with_low_sales(df)
                        df = set_suggested_for_average_sales(df, months)
                
                        # Handle NaNs in 'sugerido'
                        mask_sugerido_nan = df['sugerido'].isna()
                        df.loc[mask_sugerido_nan, 'sugerido'] = df[mask_sugerido_nan].apply(compute_six_month_average, axis=1).round(0)
                        df.loc[mask_sugerido_nan, 'tipo_caso'] = "Promedio de ventas de 6 meses"
                
                        df.loc[df['sugerido'] == 0, 'sugerido'] = 1
                        df = df.drop("intermittent", axis=1)
                
                        return df
                
                    df_resultado = apply_all_rules(df_resultado, months, inv_sede)
                
                    # Crear la columna 'sugerido_2' inicialmente con NaNs
                    df_resultado['sugerido_2'] = np.nan
                    df_resultado['meses de inventario'] = ""
                
                    # Aplicamos la función y asignamos los resultados al DataFrame
                    df_resultado[['sugerido_2', 'meses de inventario']] = df_resultado.apply(compute_values, axis=1)
                
                    # Realizar la operación de resta
                    df_resultado['Estado_inventario'+sede] = df_resultado[inv_sede] - df_resultado['sugerido_2']
                    
                    #df_resultado.to_excel(f"resultado_{sede}.xlsx")
                    resultados[sede] = df_resultado.copy()
                    
                df_Bogota = resultados['Bukz Bogota 109']
                
                # Seleccionar solo las dos columnas deseadas
                df_filtrado = inventario_original_1[['Variant SKU','Title','Vendor','Type','Inventory Available: Bukz Bogota 109', 'Created At']]
                
                # Filtrar para que 'Inventory Available: Bukz Bogota 109' sea solo positivo
                df_filtrado = df_filtrado[df_filtrado['Inventory Available: Bukz Bogota 109'] > 0]
                df_filtrado['Created At'] = pd.to_datetime(df_filtrado['Created At'])
                df_filtrado['meses de creación'] = ((fecha_actual - df_filtrado['Created At']).dt.total_seconds() / (30 * 24 * 60 * 60)).round(1)
    
                #Bogotá ventas sugerido
                columnas_deseadas_bogota = ['ID', 'Variant SKU', 'Title','Vendor', 'sugerido_2', 'meses de inventario', 'Estado_inventarioBukz Bogota 109']
                df_Bogota = df_Bogota[columnas_deseadas_bogota]
                df_Bogota.loc[df_Bogota['Estado_inventarioBukz Bogota 109'] < 0, 'Pedir Bogota'] = df_Bogota['Estado_inventarioBukz Bogota 109'].apply(lambda x: abs(x))
                df_Bogota.loc[df_Bogota['Estado_inventarioBukz Bogota 109'] > 0, 'Devolver Bogota'] = df_Bogota['Estado_inventarioBukz Bogota 109'].apply(lambda x: x)
                
                # Para Bogotá no ventas a nivel general
                df_filtrado["Devolver"] = df_filtrado.apply(calcular_envio, args=("Inventory Available: Bukz Bogota 109",), axis=1)
                no_ventas_bogota = df_filtrado.merge(df_Bogota[['Variant SKU']], on='Variant SKU', how='left', indicator=True)
                no_ventas_bogota = no_ventas_bogota[no_ventas_bogota['_merge'] == 'left_only']
                no_ventas_bogota = no_ventas_bogota.drop(columns=['_merge'])
                no_ventas_bogota = no_ventas_bogota.loc[no_ventas_bogota['Type'].isin(['Libro', 'Libros', 'Libros impresos'])]
                
                df_Mattelsa = resultados['Bukz Mattelsa']
                df_Lomas = resultados['Bukz Las Lomas']
                
                df_Mattelsa = df_Mattelsa.drop_duplicates(subset=['product_id'])
                df_Lomas = df_Lomas.drop_duplicates(subset=['product_id'])
                
                df_Mattelsa = df_Mattelsa[df_Mattelsa['meses de creación'] > 1]
                df_Lomas = df_Lomas[df_Lomas['meses de creación'] > 1]
                
                result = pd.concat([df_Mattelsa, df_Lomas])
                
                def first_non_nan(series):
                    return series.dropna().iloc[0] if not series.dropna().empty else np.nan
                
                # Obtener valores únicos para las columnas de interés
                unique_values = result.groupby('product_id').agg({
                    'Estado_inventarioBukz Las Lomas': first_non_nan,
                    'Estado_inventarioBukz Mattelsa': first_non_nan
                    
                }).reset_index()
                
                # Eliminar duplicados y combinar con los valores únicos
                result = result.drop_duplicates(subset='product_id').drop(columns=['Estado_inventarioBukz Mattelsa', 'Estado_inventarioBukz Las Lomas'])
                result = pd.merge(result, unique_values, on='product_id')
                
                columns_to_copy = ['product_id', 'variant_sku', 'Inventory Available: Cedi Lomas','Estado_inventarioBukz Mattelsa', 'Estado_inventarioBukz Las Lomas']
                df = result[columns_to_copy].copy()
                
                # Define the columns to work with 
                inventory_cols = [ 'Estado_inventarioBukz Mattelsa', 'Estado_inventarioBukz Las Lomas']
                
                # Function to redistribute inventory based on specific rules and track transfers
                def redistribute_inventory_with_transfers(df, inventory_cols):
                    # Create new columns to track redistribution without modifying the original values
                    for col in inventory_cols:
                        df['new_' + col] = df[col]
                        
                    # Create new columns to track transfers between stores with shorter column names
                    for source_col in inventory_cols:
                        for dest_col in inventory_cols:
                            if source_col != dest_col:
                                source_sede = source_col.split("_")[-1]
                                dest_sede = dest_col.split("_")[-1]
                                df[f'{source_sede}_to_{dest_sede}'] = 0
                        
                    # Iterate over each row of the DataFrame to apply the redistribution logic
                    for i, row in df.iterrows():
                        # Separate surplus and deficit stores
                        surplus_stores = {col: row[col] for col in inventory_cols if row[col] > 0}
                        deficit_stores = {col: abs(row[col]) for col in inventory_cols if row[col] < 0}
                        
                        # If there's exactly one deficit store and at least one surplus store
                        if len(deficit_stores) == 1 and surplus_stores:
                            deficit_col, deficit_value = list(deficit_stores.items())[0]
                
                            # Check if there are two surplus stores
                            if len(surplus_stores) == 2:
                                surplus_store1, surplus_value1 = max(surplus_stores.items(), key=lambda x: x[1])
                                surplus_store2, surplus_value2 = min(surplus_stores.items(), key=lambda x: x[1])
                
                                # If both surplus stores have equal or greater surplus than the deficit
                                if surplus_value1 >= deficit_value and surplus_value2 >= deficit_value:
                                    # Transfer from the store with the greatest surplus
                                    df.at[i, 'new_' + surplus_store1] -= deficit_value
                                    df.at[i, 'new_' + deficit_col] += deficit_value
                                    source_sede = surplus_store1.split("_")[-1]
                                    dest_sede = deficit_col.split("_")[-1]
                                    df.at[i, f'{source_sede}_to_{dest_sede}'] = deficit_value
                                else:
                                    # Transfer from the store with the greatest surplus
                                    transfer_amount = min(surplus_value1, deficit_value)
                                    df.at[i, 'new_' + surplus_store1] -= transfer_amount
                                    df.at[i, 'new_' + deficit_col] += transfer_amount
                                    source_sede = surplus_store1.split("_")[-1]
                                    dest_sede = deficit_col.split("_")[-1]
                                    df.at[i, f'{source_sede}_to_{dest_sede}'] = transfer_amount
                                    deficit_value -= transfer_amount
                
                                    # Transfer from the store with the second greatest surplus if needed
                                    if deficit_value > 0:
                                        transfer_amount = min(surplus_value2, deficit_value)
                                        df.at[i, 'new_' + surplus_store2] -= transfer_amount
                                        df.at[i, 'new_' + deficit_col] += transfer_amount
                                        source_sede = surplus_store2.split("_")[-1]
                                        dest_sede = deficit_col.split("_")[-1]
                                        df.at[i, f'{source_sede}_to_{dest_sede}'] = transfer_amount
                            else:
                                # Only one surplus store, handle as before
                                surplus_col, surplus_value = list(surplus_stores.items())[0]
                                # If a surplus store can cover the entire deficit
                                if surplus_value >= deficit_value:
                                    df.at[i, 'new_' + surplus_col] -= deficit_value
                                    df.at[i, 'new_' + deficit_col] += deficit_value
                                    source_sede = surplus_col.split("_")[-1]
                                    dest_sede = deficit_col.split("_")[-1]
                                    df.at[i, f'{source_sede}_to_{dest_sede}'] = deficit_value
                                else:
                                    df.at[i, 'new_' + surplus_col] = 0
                                    df.at[i, 'new_' + deficit_col] += surplus_value
                                    source_sede = surplus_col.split("_")[-1]
                                    dest_sede = deficit_col.split("_")[-1]
                                    df.at[i, f'{source_sede}_to_{dest_sede}'] = surplus_value
                
                        # If there are multiple deficit stores
                        elif len(deficit_stores) > 1:
                            while surplus_stores and deficit_stores:
                                # Sort surplus stores by value
                                  surplus_store = max(surplus_stores, key=surplus_stores.get)
                                  surplus_amount = surplus_stores[surplus_store]
                
                                  # Create a list of deficit stores to iterate over
                                  deficit_store_list = list(deficit_stores.keys())
                
                                  for deficit_store in deficit_store_list:
                                      # Skip if surplus is exhausted
                                      if surplus_amount == 0:
                                          break
                
                                      # Calculate the amount to be transferred
                                      transfer_amount = min(deficit_stores[deficit_store], surplus_amount, 1)
                                      df.at[i, 'new_' + surplus_store] -= transfer_amount
                                      df.at[i, 'new_' + deficit_store] += transfer_amount
                                      source_sede = surplus_store.split("_")[-1]
                                      dest_sede = deficit_store.split("_")[-1]
                                      df.at[i, f'{source_sede}_to_{dest_sede}'] += transfer_amount
                                      surplus_amount -= transfer_amount
                                      deficit_stores[deficit_store] -= transfer_amount
                
                                      # Remove the deficit store if its deficit is covered
                                      if deficit_stores[deficit_store] == 0:
                                          deficit_stores.pop(deficit_store)
                
                                  # Update or remove the surplus store from the dictionary
                                  if surplus_amount == 0:
                                      surplus_stores.pop(surplus_store)
                                  else:
                                      surplus_stores[surplus_store] = surplus_amount
                    return df
                
                # Apply the redistribution function to the dataframe with transfers
                redistributed_df_with_transfers = redistribute_inventory_with_transfers(df, inventory_cols)
                
                # Define the mapping of old column names to new column names
                rename_columns = {
                    'inventarioBukz Mattelsa_to_inventarioBukz Las Lomas': 'Mattelsa_to_Lomas',
                    'inventarioBukz Las Lomas_to_inventarioBukz Mattelsa': 'Lomas_to_Mattelsa'
                }
                
                redistributed_df_with_transfers = redistributed_df_with_transfers.rename(columns=rename_columns)
                
                # Function to redistribute inventory from Cedi Lomas to stores with deficit, preserving original columns
                def redistribute_cedi_lomas_inventory_preserving(df):
                    inventory_cols = [ 'new_Estado_inventarioBukz Mattelsa', 'new_Estado_inventarioBukz Las Lomas']
                    
                    # Create new columns for updated inventory and transfers
                    for col in inventory_cols:
                        df[f'updated_{col}'] = df[col]
                        df[f'CEDI_to_{col.split("_")[-1]}'] = 0
                
                    # Redistribute inventory
                    for i, row in df.iterrows():
                        cedi_lomas_inventory = row['Inventory Available: Cedi Lomas']
                        
                        for col in inventory_cols:
                            if row[col] < 0 and cedi_lomas_inventory > 0:
                                transfer_amount = min(cedi_lomas_inventory, abs(row[col]))
                                df.at[i, f'updated_{col}'] += transfer_amount
                                df.at[i, f'CEDI_to_{col.split("_")[-1]}'] = transfer_amount
                                cedi_lomas_inventory -= transfer_amount
                
                    # Update the 'Inventory Available: Cedi Lomas' column to reflect the new inventory after transfers
                    df['updated_Inventory Available: Cedi Lomas'] = df['Inventory Available: Cedi Lomas'] - \
                                                                     df[[f'CEDI_to_{col.split("_")[-1]}' for col in inventory_cols]].sum(axis=1)
                
                    return df
                
                # Apply the function to redistribute inventory while preserving original columns
                redistributed_df_preserving = redistribute_cedi_lomas_inventory_preserving(redistributed_df_with_transfers)
                
                # Determina cuántos libros hay que pedir basado en los negativos del inventario final
                redistributed_df_preserving['Pedir Lomas'] = redistributed_df_preserving['updated_new_Estado_inventarioBukz Las Lomas'].apply(lambda x: abs(x) if x < 0 else 0)
                redistributed_df_preserving['Pedir Mattelsa'] = redistributed_df_preserving['updated_new_Estado_inventarioBukz Mattelsa'].apply(lambda x: abs(x) if x < 0 else 0)
                
                # Determina cuántos libros hay que devolver basado en los positivos del inventario final
                redistributed_df_preserving['Devolver Lomas'] = redistributed_df_preserving['updated_new_Estado_inventarioBukz Las Lomas'].apply(lambda x: x if x > 0 else 0)
                redistributed_df_preserving['Devolver Mattelsa'] = redistributed_df_preserving['updated_new_Estado_inventarioBukz Mattelsa'].apply(lambda x: x if x > 0 else 0)
                
                selected_columns_mattelsa = ['product_id', 'variant_sku', 'Vendor', 'sugerido_2','meses de inventario','Estado_inventarioBukz Mattelsa']
                df_Mattelsa_new = df_Mattelsa[selected_columns_mattelsa].copy()
                
                selected_columns_lomas = ['product_id', 'variant_sku', 'Vendor','sugerido_2','meses de inventario','Estado_inventarioBukz Las Lomas']
                df_Lomas_new = df_Lomas[selected_columns_lomas].copy()
                
                # Selecciona solo las columnas deseadas de df2
                selected_columns = ['product_id', 'Lomas_to_Mattelsa','CEDI_to_inventarioBukz Las Lomas', 'Devolver Lomas', 'Pedir Lomas']
                cruzar_lomas = redistributed_df_preserving[selected_columns].copy()
                # Realiza el merge
                Lomas_final = pd.merge(df_Lomas_new, cruzar_lomas, on='product_id', how='left')
                
                # Selecciona solo las columnas deseadas de df2
                selected_columns_mattelsa = ['product_id', 'Mattelsa_to_Lomas','CEDI_to_inventarioBukz Mattelsa', 'Devolver Mattelsa', 'Pedir Mattelsa']
                cruzar_Mattelsa = redistributed_df_preserving[selected_columns_mattelsa].copy()
                # Realiza el merge
                Mattelsa_final = pd.merge(df_Mattelsa_new, cruzar_Mattelsa, on='product_id', how='left')
                
                def procesar_inventario(df_original, columna_inventario, df_final):
                    vendors_excluidos = ['Bukz USA', 'Bukz España']
                    
                    # Filtrar el DataFrame por los criterios deseados
                    filtered_df = df_original[df_original[columna_inventario].notna() & 
                                              (df_original[columna_inventario] > 0) & 
                                              (~df_original['Vendor'].isin(vendors_excluidos))]  # Esta línea excluye las filas con los Vendors especificados
                    
                    filtered_df = filtered_df[filtered_df['Type'].isin(['Libro', 'Libros', 'Libros impresos'])].copy()
                    filtered_df[columna_inventario] = filtered_df[columna_inventario].apply(lambda x: 0 if x < 0 else x)
                    filtered_df.rename(columns={'ID': 'product_id'}, inplace=True)
                    
                    no_ventas = filtered_df.merge(df_final, on='product_id', how='left', indicator=True)
                    no_ventas = no_ventas[no_ventas['_merge'] == 'left_only']
                    no_ventas = no_ventas.drop(columns=['_merge'])
                    
                    no_ventas['Created At'] = pd.to_datetime(no_ventas['Created At'])
                    fecha_actual = datetime.now()
                    no_ventas['meses de creación'] = ((fecha_actual - no_ventas['Created At']).dt.total_seconds() / (30 * 24 * 60 * 60)).round(1)
                    
                    return no_ventas
                
                # Aplicar la función para cada sede
                no_ventas_lomas = procesar_inventario(inventario_original, 'Inventory Available: Bukz Las Lomas', Lomas_final)
                no_ventas_Mattelsa = procesar_inventario(inventario_original, 'Inventory Available: Bukz Mattelsa', Mattelsa_final)
                
                # Para Lomas
                no_ventas_lomas["Lomas_to_CEDI"] = no_ventas_lomas.apply(calcular_envio, args=("Inventory Available: Bukz Las Lomas",), axis=1)
                
                # Para Mattelsa
                no_ventas_Mattelsa["Mattelsa_to_CEDI"] = no_ventas_Mattelsa.apply(calcular_envio, args=("Inventory Available: Bukz Mattelsa",), axis=1)  # Asumiendo que esta es la columna correcta
                
                no_ventas_lomas_final = no_ventas_lomas[['product_id', 'Title','Variant SKU','Vendor_x', 'Inventory Available: Bukz Las Lomas',
                                                        'Lomas_to_CEDI']].copy()
                
                no_ventas_Mattelsa_final = no_ventas_Mattelsa[['product_id', 'Title','Variant SKU','Vendor_x', 'Inventory Available: Bukz Mattelsa',
                                                        'Mattelsa_to_CEDI']].copy()
                
                
                Mattelsa_final['product_id'] = pd.to_numeric(Mattelsa_final['product_id'], errors='coerce').fillna(0).astype('int64')
                Lomas_final['product_id'] = pd.to_numeric(Lomas_final['product_id'], errors='coerce').fillna(0).astype('int64')
                inventario_original_2['product_id'] =  pd.to_numeric(inventario_original_2['product_id'], errors='coerce').fillna(0).astype('int64')
                
                resultado_merge_mattelsa = pd.merge(Mattelsa_final, inventario_original_2, on='product_id', how='inner')
                resultado_merge_lomas = pd.merge(Lomas_final, inventario_original_2, on='product_id', how='inner')
                
                resultado_merge_mattelsa = resultado_merge_mattelsa[['product_id', 'variant_sku', 'Title','Vendor', 'sugerido_2',
                       'meses de inventario', 'Estado_inventarioBukz Mattelsa', 'Mattelsa_to_Lomas',
                       'CEDI_to_inventarioBukz Mattelsa', 'Devolver Mattelsa', 'Pedir Mattelsa']]
                
                resultado_merge_lomas = resultado_merge_lomas[['product_id', 'variant_sku', 'Title', 'Vendor', 'sugerido_2',
                       'meses de inventario', 'Estado_inventarioBukz Las Lomas',
                      'Lomas_to_Mattelsa',
                       'CEDI_to_inventarioBukz Las Lomas', 'Devolver Lomas', 'Pedir Lomas']]
                
    
                # Crear un objeto BytesIO para almacenar los datos del archivo Excel en la memoria
                excel_data_bogota = BytesIO()
                excel_data_lomas = BytesIO()
                excel_data_mattelsa = BytesIO()
                
                # Escribir los datos en los objetos BytesIO
                with pd.ExcelWriter(excel_data_bogota, engine='openpyxl') as writer:
                    df_Bogota.to_excel(writer, sheet_name='Ventas', index=False)
                    no_ventas_bogota.to_excel(writer, sheet_name='No_ventas', index=False)
                
                with pd.ExcelWriter(excel_data_lomas, engine='openpyxl') as writer:
                    resultado_merge_lomas.to_excel(writer, sheet_name='Ventas', index=False)
                    no_ventas_lomas_final.to_excel(writer, sheet_name='No_ventas', index=False)
                
                with pd.ExcelWriter(excel_data_mattelsa, engine='openpyxl') as writer:
                    resultado_merge_mattelsa.to_excel(writer, sheet_name='Ventas', index=False)
                    no_ventas_Mattelsa_final.to_excel(writer, sheet_name='No_ventas', index=False)
                
                # Crear un archivo ZIP en memoria y agregar los datos del archivo Excel
                zip_data = BytesIO()
                with zipfile.ZipFile(zip_data, 'w') as zipf:
                    zipf.writestr('Bogota.xlsx', excel_data_bogota.getvalue())
                    zipf.writestr('Lomas.xlsx', excel_data_lomas.getvalue())
                    zipf.writestr('Mattelsa.xlsx', excel_data_mattelsa.getvalue())
                
                # Botón de descarga
                st.write("Descargar archivos Excel como ZIP")
                
                # Enlace para descargar el archivo ZIP
                st.download_button(
                    label="Descargar",
                    data=zip_data.getvalue(),
                    file_name='Sugerido.zip',
                    mime='application/zip'
                )
