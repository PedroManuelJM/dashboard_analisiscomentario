import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import requests
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns

# URL API DE NODEJS
url_api="https://store-apirest-production.up.railway.app/api/auditproductscomments/"

# streamlit run dashboard.py
# pip install streamlit requests pandas matplotlib seaborn plotly
# pip install streamlit-aggrid

# Función para obtener los comentarios desde la API
def obtener_comentarios():
    # Hacer la solicitud GET a la API
    response = requests.get(url_api)
    
    if response.status_code == 200:
        return response.json()  # Retorna la respuesta JSON de la API
    else:
        st.error("Error al obtener los comentarios.")
        return None
    
# Función para mostrar el gráfico de clasificaciones
def mostrar_grafico_pastel(data):
    #Pasando los datos a un DataFrame
    comentarios_df= pd.DataFrame(data)
    #Contar la cantidad de comentarios por clasificacion
    #selecciono la columna "clasificacion_comentario", value_conts() cuenta las veces , 
    #reset_index -> convierte los valores unicos de cada clasificación a un número
    clasificacion_contar= comentarios_df['clasificacion_comentario'].value_counts().reset_index() 
    #Cambia los nombres de las columnas para que sean más descriptivos
    clasificacion_contar.columns=['Clasificación','Cantidad']
    #print(clasificacion_contar)
    # Crear una nueva columna con etiquetas que incluyen el conteo
    clasificacion_contar['Etiqueta'] = clasificacion_contar['Clasificación'] + ' (' + clasificacion_contar['Cantidad'].astype(str) + ')'
    # Creando el gráfico pastel
    figura= px.pie(clasificacion_contar,
                   names='Etiqueta', 
                   values='Cantidad',
                   title='Clasificación de los comentarios')
    # Mostrar el gráfico 
    st.plotly_chart(figura)

def mostrar_grafico_barras_apiladas(data):
    # Procesar los datos
    # Inicializar un diccionario para contar las clasificaciones por producto
    productos = {}
    for comentario in data:
        nombre_producto = comentario['nombre_producto']
        clasificacion = comentario['clasificacion_comentario']
        
        if nombre_producto not in productos:
            productos[nombre_producto] = {'Positivo': 0, 'Neutro': 0, 'Negativo': 0,'Invalido':0}
        
        # Incrementar el contador según la clasificación
        if clasificacion == 'Positivo':
            productos[nombre_producto]['Positivo'] += 1
        elif clasificacion == 'Neutro':
            productos[nombre_producto]['Neutro'] += 1
        elif clasificacion == 'Negativo':
            productos[nombre_producto]['Negativo'] += 1
        elif clasificacion == 'Invalido':
            productos[nombre_producto]['Invalido'] += 1

    # Convertir los datos procesados en un DataFrame
    df = pd.DataFrame(productos).T  # `.T` para transponer y hacer que los productos sean filas
    df.fillna(0, inplace=True)  # Rellenar posibles valores NaN con 0

    # Mostrar el ComboBox para seleccionar un producto
    productos_disponibles = df.index.tolist()  # Obtener la lista de productos
    selected_producto = st.selectbox("Selecciona un producto", productos_disponibles)

    # Filtrar los datos para el producto seleccionado
    datos_producto = df.loc[selected_producto]

    # Crear el gráfico de barras apiladas para el producto seleccionado
    fig, ax = plt.subplots()
    datos_producto.plot(kind='bar', stacked=True, ax=ax)

    # Personalizar el gráfico
    ax.set_title(f'Producto: {selected_producto}')
    ax.set_xlabel('Clasificación de Comentarios')
    ax.set_ylabel('Cantidad de comentarios')
    plt.xticks(rotation=0)  # Las etiquetas del eje X no se rotan para mejorar la visibilidad

    # Agregar los números sobre las barras
    for p in ax.patches:
        height = p.get_height()
        width = p.get_width()
        x, y = p.get_xy()  # Get the x and y position of the bar
        ax.text(x + width / 2, y + height / 2, str(int(height)), 
                ha='center', va='center', color='white', fontsize=10, fontweight='bold')

    # Calcular el total de comentarios para el producto seleccionado
    total_comentarios = datos_producto.sum()
    
    # Agregar el total de comentarios encima del gráfico
    ax.text(0.5, 1.15, f'Total de comentarios: {int(total_comentarios)}', 
            ha='center', va='center', fontsize=12, fontweight='bold', color='black', transform=ax.transAxes)

    # Mostrar el gráfico en Streamlit
    st.pyplot(fig)

def mostrar_tabla(data):
    # Convertir los datos a un DataFrame de pandas
    df = pd.DataFrame(data)

    # Seleccionar solo las columnas que quieres mostrar
    columnas_a_mostrar = ['nombre_producto', 'nombre_usuario', 'comentario', 'clasificacion_comentario', 'puntaje', 'fecha']
    df = df[columnas_a_mostrar]

    # Formatear la columna 'fecha' para que tenga únicamente el formato 'YYYY-MM-DD'
    df['fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%Y-%m-%d')

    # Configurar opciones de AgGrid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationPageSize=10)  # Paginación de 10 filas
    gb.configure_default_column(resizable=True)  # Columnas ajustables
    gb.configure_grid_options(quickFilter=True)  # Activar filtro rápido
    grid_options = gb.build()

    # Cuadro de texto para búsqueda en tiempo real
    buscador = st.text_input("Buscar:", placeholder="Escribe para filtrar...")

    # Agregar filtro dinámico (sin Enter)
    if buscador:
       grid_options['quickFilterText'] = buscador  # Sincronizar filtro

    # Mostrar tabla con AgGrid
    AgGrid(
      df,
      gridOptions=grid_options,
      height=400,
      fit_columns_on_grid_load=True,
      allow_unsafe_jscode=True  # Permitir actualizaciones dinámicas
    )
 
def main():
    st.title("Análisis de los comentarios")
    # Obtener los comentarios desde la API
    comentarios = obtener_comentarios()
    # FILA 1: Gráfico en dos columnas
    with st.container():
        tab1, tab2 = st.tabs(["📊 Clasificación comentario ", "🍺 Producto"])
        # Pestaña 1 - Gráfico
        with tab1:
            # Mostrar gráfico de clasificaciones
            mostrar_grafico_pastel(comentarios)
        # Pestaña 2 - Datos
        with tab2:
            st.subheader("Comentarios por producto")
            df = pd.DataFrame(comentarios)
            # Mostrar el total de comentarios en un cuadro
            st.metric(label="Total de comentarios", value=len(df))
            # Mostrar gráfico de barras apiladas
            mostrar_grafico_barras_apiladas(comentarios)
    # FILA 2: Tabla de comentarios con paginación
    with st.container():  # Segunda fila
             st.subheader(" Tabla de los comentarios ")
             mostrar_tabla(comentarios)
    
if __name__ == "__main__":
    main()
