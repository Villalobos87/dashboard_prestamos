
import streamlit as st
import pandas as pd
import plotly.express as px
import st_aggrid as AgGrid

st.set_page_config(page_title="Dashboard Préstamos", layout="wide")

# --- Cargar Excel ---
df = pd.read_excel("prestamos.xlsx", sheet_name="Resumen")

# --- Preprocesamiento ---
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df["Nombre y Apellido"] = df["Nombre y Apellido"].astype(str)
df["Campus"] = df["Campus"].astype(str)
df["Estado"] = df["Estado"].astype(str)

# --- Sidebar filtros ---
st.sidebar.header("Filtros")
estado = st.sidebar.multiselect("Estado", df["Estado"].unique(), default=df["Estado"].unique())
campus = st.sidebar.multiselect("Campus", df["Campus"].unique(), default=df["Campus"].unique())

df_filtrado = df[(df["Estado"].isin(estado)) & (df["Campus"].isin(campus))]

# --- Título ---
st.title("📊 Dashboard de Préstamos")

# --- Métricas ---
# Calcular totales
total_prestado = df_filtrado['Principal'].sum()
total_interes = df_filtrado['Interes'].sum()
total_comision = df_filtrado['Comisión'].sum()
ganancias_proyectadas = total_interes + total_comision

# Crear columnas
col1, col2, col3, col4 = st.columns(4)

# Mostrar tarjetas estilo Power BI
col1.markdown(f"""
    <div style="background-color:#F0F2F6;padding:20px;border-radius:12px;text-align:center;box-shadow:2px 2px 10px rgba(0,0,0,0.1);">
        <h4>Total Prestado</h4>
        <p style="font-size:22px;font-weight:bold;color:#2E86C1;">${total_prestado:,.2f}</p>
    </div>
""", unsafe_allow_html=True)

col2.markdown(f"""
    <div style="background-color:#F0F2F6;padding:20px;border-radius:12px;text-align:center;box-shadow:2px 2px 10px rgba(0,0,0,0.1);">
        <h4>Total Interés</h4>
        <p style="font-size:22px;font-weight:bold;color:#27AE60;">${total_interes:,.2f}</p>
    </div>
""", unsafe_allow_html=True)

col3.markdown(f"""
    <div style="background-color:#F0F2F6;padding:20px;border-radius:12px;text-align:center;box-shadow:2px 2px 10px rgba(0,0,0,0.1);">
        <h4>Total Comisión</h4>
        <p style="font-size:22px;font-weight:bold;color:#E67E22;">${total_comision:,.2f}</p>
    </div>
""", unsafe_allow_html=True)

col4.markdown(f"""
    <div style="background-color:#F0F2F6;padding:20px;border-radius:12px;text-align:center;box-shadow:2px 2px 10px rgba(0,0,0,0.1);">
        <h4>Ganancias Totales</h4>
        <p style="font-size:22px;font-weight:bold;color:#8E44AD;">${ganancias_proyectadas:,.2f}</p>
    </div>
""", unsafe_allow_html=True)


# --- Gráfico: Ganancias Mensuales (Interes y Comisión) ---
df_filtrado['Fecha'] = pd.to_datetime(df_filtrado['Fecha'], errors='coerce')
df_filtrado['Mes'] = df_filtrado['Fecha'].dt.strftime('%B') # Nombre del mes

# Ordenar meses para el gráfico
orden_meses = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
df_filtrado['Mes'] = pd.Categorical(df_filtrado['Mes'], categories=orden_meses, ordered=True)

# Agrupar por Mes y calcular sumas
resumen_mensual = df_filtrado.groupby('Mes', observed=True)[['Interes', 'Comisión']].sum().reset_index()

# Calcular Total_Ganancias
resumen_mensual['Total_Ganancias'] = resumen_mensual['Interes'] + resumen_mensual['Comisión']
# --- FIN DEL NUEVO CÓDIGO ---

# Ahora, para tu gráfico:
fig= px.bar(resumen_mensual,
    x="Mes",
    y="Total_Ganancias", # Usamos la nueva columna combinada
    )


st.plotly_chart(fig, use_container_width=True) # Asegúrate de que estás mostrando el gráfico

# --- Tabla ---

# Filtrar solo los prestamos pendientes
df_pendiente = df[df["Estado"]=="Pendiente"]

from st_aggrid import AgGrid, GridOptionsBuilder

st.subheader("  Detalle de Préstamos ")

# Construir opciones del grid
gb = GridOptionsBuilder.from_dataframe(df_pendiente)

# Ajuste manual de ancho para una columna especifica
gb.configure_column("Nombre y Apellido", width=750)
gb.configure_column("#", width=200)
gb.configure_column("Principal", width=200)
gb.configure_column("Comisión", width=200)
gb.configure_column("Interes", width=200)
gb.configure_column("Cuota", width=200)
gb.configure_column("Cheque", width=200)
gb.configure_column("Campus", width=200)
gb.configure_column("Estado", width=200)
gb.configure_column("Cod", width=200)

# Ocultar columnas que no quieres mostrar
gb.configure_columns("Fecha de Inicio",hide=True)
gb.configure_columns("Fecha de Finalización",hide=True)
gb.configure_columns("Cheque",hide=True)

gb.configure_default_column(
    filter=True,     #  Activa filtros por columna
    sortable=True,   #  Ordenable
    resizable=True,  #  Ajustable
    editable=False
)
gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
gb.configure_side_bar()  # Agrega barra lateral con filtros

# Opcional: formatear columna de fecha
gb.configure_column("Fecha", type=["dateColumnFilter", "customDateTimeFormat"], custom_format_string="yyyy-MM-dd")

# Construir la configuración
grid_options = gb.build()

# Mostrar la tabla
AgGrid( 
    df_filtrado,
    gridOptions=grid_options,
    height=400,
    width='100%',
    theme='alpine',  # También puedes usar: balham, material, blue, alpine etc.
    enable_enterprise_modules=True,
    fit_columns_on_grid_load=True
)
# --- Métricas ---
# Calcular totales

total_cuota_cancelada = df[df["Estado"]=="Cancelado"]["Cuota"].sum()
Capital_Inicial = 9000
Ganancias_Entregadas =3698.24
Efectivo = total_cuota_cancelada + Capital_Inicial - total_prestado - Ganancias_Entregadas
Pendiente_Recuperar = df[df["Estado"]=="Pendiente"]["Cuota"].sum()

# Crear columnas

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

# Mostrar tarjetas estilo Power BI
col1.markdown(f"""
    <div style="background-color:#F0F2F6;padding:20px;border-radius:12px;text-align:center;box-shadow:2px 2px 10px rgba(0,0,0,0.1);">
        <h4>Yanina Orochena</h4>
        <p style="font-size:22px;font-weight:bold;color:#2E86C1;">${Efectivo:,.2f}</p>
    </div>
""", unsafe_allow_html=True)

col2.markdown(f"""
    <div style="background-color:#F0F2F6;padding:20px;border-radius:12px;text-align:center;box-shadow:2px 2px 10px rgba(0,0,0,0.1);">
        <h4>Por Recuperar</h4>
        <p style="font-size:22px;font-weight:bold;color:#27AE60;">${Pendiente_Recuperar:,.2f}</p>
    </div>
""", unsafe_allow_html=True)

col3.markdown(f"""
    <div style="background-color:#F0F2F6;padding:20px;border-radius:12px;text-align:center;box-shadow:2px 2px 10px rgba(0,0,0,0.1);">
        <h4>Capital</h4>
        <p style="font-size:22px;font-weight:bold;color:#E67E22;">${Capital_Inicial:,.2f}</p>
    </div>
""", unsafe_allow_html=True)

col4.markdown(f"""
    <div style="background-color:#F0F2F6;padding:20px;border-radius:12px;text-align:center;box-shadow:2px 2px 10px rgba(0,0,0,0.1);">
        <h4>Rodrigo Gurdian</h4>
        <p style="font-size:22px;font-weight:bold;color:#8E44AD;">${Ganancias_Entregadas:,.2f}</p>
    </div>
""", unsafe_allow_html=True)

