import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder
import calendar
import locale

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

# --- Métricas generales ---
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

# --- Preparar datos para gráfico mensual ---
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Para Linux/mac
# Para Windows usar: 'Spanish_Spain.1252'

df_filtrado['Año'] = df_filtrado['Fecha'].dt.year
df_filtrado['Mes_Num'] = df_filtrado['Fecha'].dt.month
df_filtrado['Mes'] = df_filtrado['Fecha'].dt.strftime('%B')  # Mes en español

orden_meses = list(calendar.month_name)[1:]  # Enero a Diciembre
df_filtrado['Mes'] = pd.Categorical(df_filtrado['Mes'], categories=orden_meses, ordered=True)

resumen_mensual = df_filtrado.groupby(['Año','Mes_Num','Mes'], observed=True)[['Interes','Comisión']].sum().reset_index()
resumen_mensual['Total_Ganancias'] = resumen_mensual['Interes'] + resumen_mensual['Comisión']
resumen_mensual = resumen_mensual.sort_values(['Año','Mes_Num'])
resumen_mensual['Mes_Año'] = resumen_mensual['Mes'].astype(str) + ' ' + resumen_mensual['Año'].astype(str)

# --- Gráfico mensual interactivo ---
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

# --- Gráfico de pastel / sunburst interactivo ---
ganancias_campus = df_filtrado.groupby(['Campus','Estado'])[['Interes','Comisión']].sum().reset_index()
ganancias_campus['Total_Ganancias'] = ganancias_campus['Interes'] + ganancias_campus['Comisión']

fig_sunburst = px.sunburst(
    ganancias_campus,
    path=['Campus','Estado'],
    values='Total_Ganancias',
    color='Total_Ganancias',
    color_continuous_scale='Viridis',
    title="📊 Ganancias por Campus y Estado"
)
fig_sunburst.update_layout(height=600)
st.plotly_chart(fig_sunburst, use_container_width=True)

st.markdown("---")

# --- Tabla detalle de préstamos con AgGrid ---
st.subheader("📋 Detalle de Préstamos")
df_detalle = df_filtrado.copy()

gb = GridOptionsBuilder.from_dataframe(df_detalle)
gb.configure_default_column(
    filter=True,
    sortable=True,
    resizable=True,
    editable=False
)
# Resaltado condicional por estado
from st_aggrid.shared import JsCode
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
