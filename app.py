import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Ventas", page_icon="📊", layout="wide")
st.title("📊 Dashboard de Ventas - Empresa Alimentación")

@st.cache_data
def load_data():
    USECOLS = [
    "date","sales","transactions","store_nbr","family","state",
    "onpromotion","holiday_type","dcoilwtico"
    ]
    DTYPE = {
        "store_nbr": "int16",
        "onpromotion": "int16",
        "transactions": "int32",
        "sales": "float32",
        "dcoilwtico": "float32",
        "family": "category",
        "state": "category",
        "holiday_type": "category",
    }
    
    df1 = pd.read_csv("parte_1.zip", compression="zip", usecols=USECOLS, dtype=DTYPE, low_memory=False)
    df2 = pd.read_csv("parte_2.zip", compression="zip", usecols=USECOLS, dtype=DTYPE, low_memory=False)
    df = pd.concat([df1, df2], ignore_index=True)



    # Si existe una columna "basura" típica, se quita
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    #se convierte la fecha en formato fecha
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    #Por si faltaran estas columnas, se crean desde date
    df["year"] = df.get("year", df["date"].dt.year)
    df["month"] = df.get("month", df["date"].dt.month)
    df["week"] = df.get("week", df["date"].dt.isocalendar().week.astype(int))
    df["day_of_week"] = df.get("day_of_week", df["date"].dt.day_name())

    return df

try:
    df = load_data()
except Exception as e:
    st.error("Error cargando datos. Mira el mensaje debajo:")
    st.exception(e)
    st.stop()



def top10(df_in, group_col, value_col="sales"):
    """Devuelve un top 10 por suma."""
    return (df_in.groupby(group_col, as_index=False)[value_col]
            .sum()
            .sort_values(value_col, ascending=False)
            .head(10))

def mean_by(df_in, group_col, value_col="sales"):
    """Devuelve media por grupo."""
    return (df_in.groupby(group_col, as_index=False)[value_col]
            .mean()
            .sort_values(group_col))


tab1, tab2, tab3, tab4 = st.tabs([
    "Pestaña 1 · Global",
    "Pestaña 2 · Tienda",
    "Pestaña 3 · Estado",
    "Pestaña 4 · Extra"
])

#tab1 global
with tab1:
    st.subheader("Visión global")

    # KPIs (conteos generales)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tiendas", df["store_nbr"].nunique())
    c2.metric("Familias", df["family"].nunique())
    c3.metric("Estados", df["state"].nunique())
    c4.metric("Meses con datos", df[["year", "month"]].drop_duplicates().shape[0])

    st.divider()
    st.subheader("Rankings y distribución")

    #Top 10 productos más vendidos
    st.plotly_chart(
        px.bar(top10(df, "family"), x="sales", y="family", orientation="h",
               title="Top 10 productos más vendidos"),
        use_container_width=True
    )

    #Distribución de ventas por tienda (histograma)
    store_sales = df.groupby("store_nbr", as_index=False)["sales"].sum()
    st.plotly_chart(
        px.histogram(store_sales, x="sales", nbins=40,
                     title="Distribución de ventas totales por tienda"),
        use_container_width=True
    )

    #Top 10 tiendas por ventas con productos en promoción
    df_promo = df[df["onpromotion"] > 0]
    st.plotly_chart(
        px.bar(top10(df_promo, "store_nbr"), x="sales", y="store_nbr", orientation="h",
               title="Top 10 tiendas por ventas con productos en promoción"),
        use_container_width=True
    )

    st.divider()
    st.subheader("Estacionalidad")

    #Ventas medias por día de la semana
    dow = mean_by(df, "day_of_week")
    st.plotly_chart(
        px.bar(dow, x="day_of_week", y="sales",
               title="Ventas medias por día de la semana"),
        use_container_width=True
    )

    #Ventas medias por semana
    week_mean = mean_by(df, "week").sort_values("week")
    st.plotly_chart(
        px.line(week_mean, x="week", y="sales", markers=True,
                title="Ventas medias por semana del año"),
        use_container_width=True
    )

    # Ventas medias por mes
    month_mean = mean_by(df, "month").sort_values("month")
    st.plotly_chart(
        px.line(month_mean, x="month", y="sales", markers=True,
                title="Ventas medias por mes"),
        use_container_width=True
    )

#tab2 por tienda
with tab2:
    st.subheader("Análisis por tienda")

    # Selector de tienda
    store = st.selectbox("Selecciona una tienda:", sorted(df["store_nbr"].unique()))
    dstore = df[df["store_nbr"] == store]

    #Ventas totales por año (barra)
    sales_year = dstore.groupby("year", as_index=False)["sales"].sum().sort_values("year")
    st.plotly_chart(
        px.bar(sales_year, x="year", y="sales", title="Ventas totales por año"),
        use_container_width=True
    )

    #Total ventas (sales) y en promoción
    c1, c2 = st.columns(2)
    c1.metric("Total ventas (sales)", f"{dstore['sales'].sum():,.2f}")
    c2.metric("Total ventas en promoción", f"{dstore.loc[dstore['onpromotion']>0, 'sales'].sum():,.2f}")

#tab3 por estado
with tab3:
    st.subheader("Análisis por estado")

    # Selector de estado
    state = st.selectbox("Selecciona un estado:", sorted(df["state"].dropna().unique()))
    dstate = df[df["state"] == state]

    #Transacciones totales por año (línea)
    trans_year = dstate.groupby("year", as_index=False)["transactions"].sum().sort_values("year")
    st.plotly_chart(
        px.line(trans_year, x="year", y="transactions", markers=True,
                title="Transacciones totales por año"),
        use_container_width=True
    )

    #Top 10 tiendas con más ventas en ese estado
    st.plotly_chart(
        px.bar(top10(dstate, "store_nbr"), x="sales", y="store_nbr", orientation="h",
               title="Top 10 tiendas con más ventas en el estado"),
        use_container_width=True
    )

    #Producto más vendido en ese estado
    best = top10(dstate, "family").head(1)
    if not best.empty:
        st.success(f"Producto más vendido: **{best.iloc[0]['family']}** (sales: {best.iloc[0]['sales']:.2f})")

#tab4 : extra
with tab4:
    st.subheader("Extra (valor añadido)")

    colA, colB = st.columns(2)

    #Festivos vs no festivos (ventas medias)
    is_holiday = df["holiday_type"].notna()
    hol = df.groupby(is_holiday, as_index=False)["sales"].mean()
    hol.columns = ["is_holiday", "sales"]
    colA.plotly_chart(
        px.bar(hol, x="is_holiday", y="sales", title="Ventas medias: festivo vs no festivo"),
        use_container_width=True
    )

    #Petróleo vs ventas (sin trendline para no necesitar statsmodels)
    d = df.dropna(subset=["dcoilwtico"])
    if len(d) > 0:
        sample = d.sample(min(len(d), 4000), random_state=1)
        colB.plotly_chart(
            px.scatter(sample, x="dcoilwtico", y="sales",
                       title="Petróleo (dcoilwtico) vs ventas (sales)"),
            use_container_width=True
        )
    else:
        colB.info("No hay datos de dcoilwtico para graficar.")



