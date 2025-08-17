import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import JsCode

st.set_page_config(page_title="Dashboard Préstamos", layout="wide")

# --- Cargar Excel ---
df = pd.read_excel("prestamos.xlsx", sheet_name="Resumen")

# --- Preprocesamiento ---
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df["Nombre y Apellido"] = df["Nombre y Apellido"].astype(str)
df["Campus"] = df["Campus"].astype(str)
df["Estado"] = df["Estado"].astype(str)
df["Principal"] = pd.to_numeric(df["Principal"], errors="coerce")
df["Interes"] = pd.to_numeric(df["Interes"], errors="coerce")
df["Comisión"] = pd.to_numeric(df["Comisión"], errors="coerce")
df["Cuota"] = pd.to_numeric(df["Cuota"], errors="coerce")

# --- Sidebar filtros ---
st.sidebar.header("Filtros")
estado = st.sidebar.multiselect("Estado", df["Estado"].unique(), default=df["Estado"].unique())
campus = st.sidebar.multiselect("Campus", df["Campus"].unique(), default=df["Campus"].unique())
df_filtrado = df[(df["Estado"].isin(estado)) & (df["Campus"].isin(campus))]

# --- Título ---
st.title("📊 Dashboard de Préstamos")

# --- BLOQUE 1: Métricas generales ---
total_prestado = df_filtrado['Principal'].sum()
total_interes = df_filtrado['Interes'].sum()
total_comision = df_filtrado['Comisión'].sum()
ganancias_proyectadas = total_interes + total_comision

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Prestado", f"${total_prestado:,.2f}")
col2.metric("Total Comisión", f"${total_comision:,.2f}")
col3.metric("Total Interés", f"${total_interes:,.2f}")
col4.metric("Ganancias Totales", f"${ganancias_proyectadas:,.2f}")

st.markdown("---")

# --- Meses en español ---
meses_ingles = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]
meses_espanol = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
dicc_meses = dict(zip(meses_ingles, meses_espanol))

df_filtrado['Año'] = df_filtrado['Fecha'].dt.year
df_filtrado['Mes_Num'] = df_filtrado['Fecha'].dt.month
df_filtrado['Mes'] = df_filtrado['Fecha'].dt.strftime('%B')
df_filtrado['Mes'] = df_filtrado['Mes'].map(dicc_meses)
df_filtrado['Mes'] = pd.Categorical(df_filtrado['Mes'], categories=meses_espanol, ordered=True)

# --- Resumen mensual ---
resumen_mensual = df_filtrado.groupby(['Año','Mes_Num','Mes'], observed=True)[['Interes','Comisión']].sum().reset_index()
resumen_mensual['Total_Ganancias'] = resumen_mensual['Interes'] + resumen_mensual['Comisión']
resumen_mensual = resumen_mensual.sort_values(['Año','Mes_Num'])
resumen_mensual['Mes_Año'] = resumen_mensual['Mes'].astype(str) + ' ' + resumen_mensual['Año'].astype(str)

# --- Gráfico mensual ---
fig_bar = px.bar(
    resumen_mensual,
    x='Mes_Año',
    y='Total_Ganancias',
    color='Total_Ganancias',
    text='Total_Ganancias',
    labels={'Total_Ganancias':'Ganancias'},
    title="📈 Ganancias Mensuales"
)
fig_bar.update_traces(texttemplate='%{text:,.2f}', textposition='outside')
fig_bar.update_layout(height=500)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# --- BLOQUE 2: Métricas adicionales ---
total_cuota_cancelada = df[df["Estado"]=="Cancelado"]["Cuota"].sum()
Capital_Inicial = 9000
Ganancias_Entregadas = 3698.24 - 698.24
Efectivo = total_cuota_cancelada + Capital_Inicial - total_prestado - Ganancias_Entregadas
Pendiente_Recuperar = df[df["Estado"]=="Pendiente"]["Cuota"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Yanina Orochena", f"${Efectivo:,.2f}")
col2.metric("Por Recuperar", f"${Pendiente_Recuperar:,.2f}")
col3.metric("Capital", f"${Capital_Inicial:,.2f}")
col4.metric("Rodrigo Gurdian", f"${Ganancias_Entregadas:,.2f}")

st.markdown("---")

# --- Tabla detallada de préstamos (simplificada) ---
st.subheader("📋 Detalle de Préstamos")
df_detalle = df_filtrado.copy()
cols_a_ocultar = ["Cheque", "Fecha de Inicio", "Fecha de Finalización", "Año", "Mes_Num", "Mes"]
df_detalle = df_detalle.drop(columns=[col for col in cols_a_ocultar if col in df_detalle.columns])

gb = GridOptionsBuilder.from_dataframe(df_detalle)
gb.configure_default_column(filter=True, sortable=True, resizable=True, editable=False)

# Resaltado condicional por estado
cell_style = JsCode("""
function(params) {
    if (params.value === 'Pendiente') {
        return {'backgroundColor':'#FFF3CD','color':'#856404'};
    } else if (params.value === 'Cancelado') {
        return {'backgroundColor':'#D4EDDA','color':'#155724'};
    }
}
""")
gb.configure_column("Estado", cellStyle=cell_style)

# --- FILTRO POR DEFECTO: Estado = Pendiente ---
default_filter_model = {
    "Estado": {
        "filterType": "set",
        "values": ["Pendiente"]
    }
}
gb.configure_grid_options(defaultColFilterModel=default_filter_model)

gb.configure_side_bar()
gb.configure_pagination(paginationPageSize=20)
grid_options = gb.build()

AgGrid(
    df_detalle,
    gridOptions=grid_options,
    enable_enterprise_modules=True,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
    theme='alpine',
    height=500
)
st.subheader("📊 Resumen de Cuotas Pendientes")

# Filtrar solo pendientes
df_pendientes = df_filtrado[df_filtrado["Estado"]=="Pendiente"].copy()

# Seleccionar solo columnas necesarias
df_resumen = df_pendientes[["Campus", "Nombre y Apellido", "Cuota"]].copy()

# Construir AgGrid con agrupación
gb = GridOptionsBuilder.from_dataframe(df_resumen)
gb.configure_default_column(
    enablePivot=True,
    enableValue=True,
    enableRowGroup=True,
    filter=True,
    sortable=True,
    resizable=True
)

# Agrupar por Campus y luego Alumno
gb.configure_column("Campus", rowGroup=True, rowGroupIndex=0)
gb.configure_column("Nombre y Apellido", rowGroup=True, rowGroupIndex=1)
gb.configure_column("Cuota", value=True, aggFunc="sum")

# Pinned columns
gb.configure_column("Campus", pinned="left")
gb.configure_column("Nombre y Apellido", pinned="left")

# Ocultar columnas que no se necesitan
gb.configure_columns([], hide=True)

gb.configure_side_bar()
grid_options = gb.build()

AgGrid(
    df_resumen,
    gridOptions=grid_options,
    enable_enterprise_modules=True,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
    theme="alpine",
    height=500
)