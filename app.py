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

# --- Tabla detallada de préstamos (solo pendientes) ---
st.subheader("📋 Detalle de Préstamos")

# Filtrar solo pendientes
df_detalle = df_filtrado[df_filtrado["Estado"]=="Pendiente"].copy()

# Quitar columnas innecesarias
cols_a_ocultar = ["Cheque", "Fecha de Inicio", "Fecha de Finalización", "Año", "Mes_Num", "Mes"]
df_detalle = df_detalle.drop(columns=[col for col in cols_a_ocultar if col in df_detalle.columns])

# Formatear columnas
df_detalle["Fecha"] = df_detalle["Fecha"].dt.strftime("%Y-%m-%d")
for col in ["Principal", "Comisión", "Interes", "Cuota"]:
    df_detalle[col] = df_detalle[col].map("{:,.2f}".format)

# Construir AgGrid
gb = GridOptionsBuilder.from_dataframe(df_detalle)
gb.configure_default_column(filter=True, sortable=True, resizable=True, editable=False)

# Resaltado condicional por estado (todos pendientes)
from st_aggrid.shared import JsCode
cell_style = JsCode("""
function(params) {
    return {'backgroundColor':'#FFF3CD','color':'#856404'};
}
""")
gb.configure_column("Estado", cellStyle=cell_style)

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

# --- Tabla resumen por campus y alumno ---
st.subheader("📊 Resumen de Cuotas Pendientes por Campus")
df_pendientes = df_filtrado[df_filtrado["Estado"]=="Pendiente"].copy()
df_resumen = df_pendientes[["Campus", "Nombre y Apellido", "Cuota"]].copy()

gb = GridOptionsBuilder.from_dataframe(df_resumen)
gb.configure_default_column(
    enablePivot=True,
    enableValue=True,
    enableRowGroup=True,
    filter=True,
    sortable=True,
    resizable=True
)
gb.configure_column("Campus", rowGroup=True, rowGroupIndex=0)
gb.configure_column("Nombre y Apellido", rowGroup=True, rowGroupIndex=1)
gb.configure_column("Cuota", value=True, aggFunc="sum")
gb.configure_column("Campus", pinned="left")
gb.configure_column("Nombre y Apellido", pinned="left")
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

st.markdown("---")

# --- Gráfico de pastel: Ganancias por Campus ---
ganancias_campus = df_filtrado.groupby("Campus")[['Interes', 'Comisión']].sum().reset_index()
ganancias_campus['Total_Ganancias'] = ganancias_campus['Interes'] + ganancias_campus['Comisión']

fig_pie = px.pie(
    ganancias_campus,
    names='Campus',
    values='Total_Ganancias',
    title='<b>📊 Distribución de Ganancias por Campus</b>',
    color_discrete_sequence=px.colors.qualitative.Pastel,
    hole=0
)
fig_pie.update_traces(
    texttemplate="%{label}: %{value:,.2f} (%{percent})",
    textfont=dict(size=14, color='black'),
    pull=[0.05]*len(ganancias_campus),
    hovertemplate="%{label}<br>Ganancias: %{value:,.2f}<br>%{percent}"
)
fig_pie.update_layout(title=dict(font=dict(size=24)), height=700)
st.plotly_chart(fig_pie, use_container_width=True)