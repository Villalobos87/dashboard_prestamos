import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import JsCode
from datetime import datetime


st.set_page_config(page_title="Dashboard Préstamos", layout="wide")

# --- Cargar Excel ---
df = pd.read_excel("prestamos.xlsx", sheet_name="Resumen")

# --- Preprocesamiento general ---
df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
df["Nombre y Apellido"] = df["Nombre y Apellido"].astype(str)
df["Campus"] = df["Campus"].astype(str)
df["Estado"] = df["Estado"].astype(str)
for col in ["Principal", "Interes", "Comisión", "Cuota"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# --- Sidebar filtros ---
st.sidebar.header("Filtros")
estado = st.sidebar.multiselect("Estado", df["Estado"].unique(), default=df["Estado"].unique())
campus = st.sidebar.multiselect("Campus", df["Campus"].unique(), default=df["Campus"].unique())
df_filtrado = df[(df["Estado"].isin(estado)) & (df["Campus"].isin(campus))]

st.title("📊 Dashboard de Préstamos")

# --- MÉTRICAS GENERALES ---
total_prestado  = df_filtrado["Principal"].sum()
total_interes   = df_filtrado["Interes"].sum()
total_comision  = df_filtrado["Comisión"].sum()
gan_total       = total_interes + total_comision

c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Prestado"   ,f"${total_prestado:,.2f}")
c2.metric("Total Comisión"   ,f"${total_comision:,.2f}")
c3.metric("Total Interés"    ,f"${total_interes:,.2f}")
c4.metric("Ganancias Totales",f"${gan_total:,.2f}")

st.markdown("---")

# --- Meses en español ---
meses_ingles  = ["January","February","March","April","May","June","July","August","September","October","November","December"]
meses_espanol = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
dic_meses     = dict(zip(meses_ingles, meses_espanol))

df_filtrado["Año"]      = df_filtrado["Fecha"].dt.year
df_filtrado["Mes_Num"]  = df_filtrado["Fecha"].dt.month
df_filtrado["Mes"]      = df_filtrado["Fecha"].dt.strftime("%B").map(dic_meses)
df_filtrado["Mes"]      = pd.Categorical(df_filtrado["Mes"], categories=meses_espanol, ordered=True)

# --- Resumen mensual (todos los años) ---
resumen_mensual = (
    df_filtrado
      .groupby(["Año","Mes_Num","Mes"], observed=True)[["Interes","Comisión"]]
      .sum()
      .reset_index()
)
resumen_mensual["Total_Ganancias"] = resumen_mensual["Interes"] + resumen_mensual["Comisión"]
resumen_mensual = resumen_mensual.sort_values(["Año","Mes_Num"])
resumen_mensual["Mes_Año"] = (
    resumen_mensual["Mes"].astype(str) + " " + resumen_mensual["Año"].astype(str)
)

# --- Selector de año con suma de ganancias ---
anos_disponibles = sorted(resumen_mensual['Año'].unique())
anio_actual      = datetime.now().year

# Layout en columnas
col1, col2 = st.columns([2,1])  # más espacio para el selectbox que para la suma

with col1:
    # Si el año actual está en la lista lo usamos como valor por defecto,
    # si no, usamos el último disponible
    if anio_actual in anos_disponibles:
        ano_seleccionado = st.selectbox("Selecciona el Año", anos_disponibles, index=anos_disponibles.index(anio_actual))
    else:
        ano_seleccionado = st.selectbox("Selecciona el Año", anos_disponibles, index=len(anos_disponibles)-1)

# Filtrar resumen por año seleccionado
resumen_filtrado = resumen_mensual[resumen_mensual['Año'] == ano_seleccionado]

# Calcular total de ganancias del año
total_ganancias_anual = resumen_filtrado["Total_Ganancias"].sum()

with col2:
    st.metric(label="💰 Total del Año", value=f"{total_ganancias_anual:,.2f}")

# --- Gráfico ---
fig_bar = px.bar(
    resumen_filtrado,
    x="Mes_Año",
    y="Total_Ganancias",
    text="Total_Ganancias",
    color="Total_Ganancias",
    title=f"📈 Ganancias Mensuales ({ano_seleccionado})"
)
fig_bar.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
fig_bar.update_layout(height=500, showlegend=False, coloraxis_showscale=False)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# --- MÉTRICAS ADICIONALES ---
total_cuota_cancelada = df[df["Estado"]=="Cancelado"]["Cuota"].sum()
Capital_Inicial       = 9000
Ganancias_Entregadas  = 3698.24 - 3698.24
Efectivo              = total_cuota_cancelada + Capital_Inicial - total_prestado - Ganancias_Entregadas
Pendiente_Recuperar   = df[df["Estado"]=="Pendiente"]["Cuota"].sum()

c1,c2,c3,c4 = st.columns(4)
c1.metric("Yanina Orochena",f"${Efectivo:,.2f}")
c2.metric("Por Recuperar" ,f"${Pendiente_Recuperar:,.2f}")
c3.metric("Capital"       ,f"${Capital_Inicial:,.2f}")
c4.metric("Rodrigo Gurdian",f"${Ganancias_Entregadas:,.2f}")

st.markdown("---")

# --- Detalle de Prestamos (solo pendientes + formato) ---
st.subheader("📋 Detalle de Préstamos")

df_detalle = df_filtrado[df_filtrado["Estado"]=="Pendiente"].copy()
df_detalle["Fecha"] = df_detalle["Fecha"].dt.strftime("%Y-%m-%d")
for col in ["Principal","Comisión","Interes","Cuota"]:
    df_detalle[col] = df_detalle[col].map(lambda x: f"{x:,.2f}")

cols_quitar = ["Cheque","Fecha de Inicio","Fecha de Finalización","Año","Mes_Num","Mes"]
df_detalle  = df_detalle.drop(columns=[c for c in cols_quitar if c in df_detalle.columns])

g = GridOptionsBuilder.from_dataframe(df_detalle)
g.configure_default_column(filter=True, sortable=True, resizable=True, editable=False)
g.configure_column(
    "Estado",
    cellStyle=JsCode("function(params){return {'backgroundColor':'#FFF3CD','color':'#856404'};}"))
g.configure_side_bar()
g.configure_pagination(paginationPageSize=20)
tbl_opts = g.build()

AgGrid(df_detalle, gridOptions=tbl_opts, enable_enterprise_modules=True,
       fit_columns_on_grid_load=True, allow_unsafe_jscode=True, theme="alpine", height=500)

st.markdown("---")

# --- Resumen (Cuotas Pendientes por Campus y Alumno) ---
st.subheader("📊 Resumen de Cuotas Pendientes por Campus")

df_pend = df_filtrado[df_filtrado["Estado"]=="Pendiente"][["Campus","Nombre y Apellido","Cuota"]].copy()
g = GridOptionsBuilder.from_dataframe(df_pend)
g.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True,
                           filter=True, sortable=True, resizable=True)

g.configure_column("Campus", rowGroup=True,  rowGroupIndex=0)
g.configure_column("Nombre y Apellido", rowGroup=True, rowGroupIndex=1)
g.configure_column(
    "Cuota",
    value=True,
    aggFunc="sum",
    valueFormatter="function(params){return Number(params.value).toLocaleString('es-ES',{minimumFractionDigits:2,maximumFractionDigits:2});}"
)
# Ocultar columnas originales
g.configure_columns(["Campus","Nombre y Apellido"], hide=True)

g.configure_side_bar()
summary_opts = g.build()

AgGrid(df_pend, gridOptions=summary_opts, enable_enterprise_modules=True, 
       fit_columns_on_grid_load=True, allow_unsafe_jscode=True, theme="alpine", height=500)

st.markdown("---")

# --- Gráfico pastel: Ganancias por Campus ---
gan_campus = df_filtrado.groupby("Campus")[["Interes","Comisión"]].sum().reset_index()
gan_campus["Total_Ganancias"] = gan_campus["Interes"] + gan_campus["Comisión"]

fig_pie = px.pie(
    gan_campus,
    names="Campus",
    values="Total_Ganancias",
    title="📊 Distribución de Ganancias por Campus",
    color_discrete_sequence=px.colors.qualitative.Pastel,
    hole=0
)
fig_pie.update_traces(
    texttemplate="%{label}: %{value:,.2f} (%{percent})",
    hovertemplate="%{label}<br>Ganancias: %{value:,.2f}<br>%{percent}",
    pull=[0.05]*len(gan_campus)
)
fig_pie.update_layout(title_font_size=24, height=700)
st.plotly_chart(fig_pie, use_container_width=True)

