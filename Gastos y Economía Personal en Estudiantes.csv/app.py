from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Gastos y economía personal en estudiantes",
    page_icon="📊",
    layout="wide",
)

TODAS = "Todas"
NOMBRES = [
    "marca_temporal",
    "frecuencia_ingreso",
    "ingreso_semanal",
    "actividad_remunerada",
    "gasto_principal",
    "gasto_comida",
    "gasto_transporte",
    "compra_impulsiva",
    "probabilidad_ahorro",
    "porcentaje_ahorro",
    "suficiencia_dinero",
    "compara_precios",
    "presupuesto",
]

TIPOS_VARIABLES = [
    "Temporal",
    "Cualitativa ordinal",
    "Cualitativa ordinal",
    "Cualitativa nominal",
    "Cualitativa nominal",
    "Cualitativa ordinal",
    "Cualitativa ordinal",
    "Cualitativa ordinal",
    "Cualitativa ordinal",
    "Cualitativa ordinal",
    "Cualitativa ordinal",
    "Cualitativa ordinal",
    "Cualitativa ordinal",
]

ESCALAS_VARIABLES = [
    "Fecha y hora",
    "Frecuencia",
    "Rangos monetarios semanales",
    "Tipo de actividad",
    "Categoría de gasto",
    "Rangos monetarios semanales",
    "Rangos monetarios semanales",
    "Frecuencia",
    "Nivel de ahorro",
    "Rangos porcentuales",
    "Suficiencia percibida",
    "Frecuencia",
    "Experiencia y seguimiento",
]

VARIABLES_FRECUENCIAS = [
    "frecuencia_ingreso",
    "actividad_remunerada",
    "gasto_principal",
    "gasto_comida",
    "gasto_transporte",
    "compra_impulsiva",
    "probabilidad_ahorro",
    "porcentaje_ahorro",
    "suficiencia_dinero",
    "compara_precios",
    "presupuesto",
]

VARIABLES_DESCRIPTIVAS = [
    ("frecuencia_ingreso", "Frecuencia de ingreso"),
    ("ingreso_semanal", "Rango de ingreso semanal"),
    ("gasto_principal", "Principal categoría de gasto"),
    ("suficiencia_dinero", "Suficiencia del dinero"),
]


@st.cache_data
def cargar_datos(ruta_csv: str):
    """Carga y prepara el CSV, manteniendo las respuestas originales."""
    encuesta_original = pd.read_csv(ruta_csv, encoding="utf-8-sig")
    if len(encuesta_original.columns) != len(NOMBRES):
        raise ValueError(
            f"Se esperaban {len(NOMBRES)} columnas y se encontraron "
            f"{len(encuesta_original.columns)}."
        )

    preguntas_originales = dict(enumerate(encuesta_original.columns, start=1))
    encuesta = encuesta_original.copy()
    encuesta.columns = NOMBRES
    encuesta["marca_temporal"] = pd.to_datetime(
        encuesta["marca_temporal"], format="mixed", errors="coerce"
    )
    for columna in encuesta.columns:
        if encuesta[columna].dtype == "object":
            encuesta[columna] = encuesta[columna].astype("string").str.strip()

    calidad = pd.DataFrame(
        {
            "indicador": [
                "Respuestas",
                "Variables",
                "Celdas nulas",
                "Filas duplicadas",
            ],
            "valor": [
                len(encuesta),
                encuesta.shape[1],
                int(encuesta.isna().sum().sum()),
                int(encuesta.duplicated().sum()),
            ],
        }
    )
    diccionario = pd.DataFrame(
        {
            "variable": NOMBRES,
            "pregunta_original": [preguntas_originales[i] for i in range(1, 14)],
            "tipo_de_variable": TIPOS_VARIABLES,
            "escala_unidad": ESCALAS_VARIABLES,
        }
    )
    return encuesta, calidad, diccionario


def tabla_frecuencias(datos: pd.DataFrame, columna: str) -> pd.DataFrame:
    tabla = datos[columna].value_counts(dropna=False).rename("frecuencia").to_frame()
    tabla["porcentaje"] = (tabla["frecuencia"] / len(datos) * 100).round(1)
    return tabla.reset_index(names="categoria")


def grafico_barras(
    datos: pd.DataFrame,
    columna: str,
    titulo: str,
    eje_x: str = "Categoría",
):
    tabla = tabla_frecuencias(datos, columna)
    figura = px.bar(
        tabla,
        x="categoria",
        y="frecuencia",
        text="porcentaje",
        title=f"{titulo} ({len(datos)} respuestas)",
        labels={"categoria": eje_x, "frecuencia": "Número de respuestas"},
        color="frecuencia",
        color_continuous_scale="Blues",
    )
    figura.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        hovertemplate=(
            "%{x}<br>Respuestas: %{y}<br>"
            "Porcentaje: %{text:.1f}%<extra></extra>"
        ),
    )
    figura.update_layout(
        showlegend=False,
        xaxis_tickangle=-25,
        height=450,
        margin={"b": 130},
    )
    return figura


def grafico_suficiencia_por_actividad(datos: pd.DataFrame):
    cruce = (
        pd.crosstab(
            datos["actividad_remunerada"], datos["suficiencia_dinero"]
        )
        .reset_index()
        .melt(
            id_vars="actividad_remunerada",
            var_name="suficiencia_dinero",
            value_name="respuestas",
        )
    )
    figura = px.bar(
        cruce,
        x="actividad_remunerada",
        y="respuestas",
        color="suficiencia_dinero",
        barmode="group",
        title=(
            "Suficiencia del dinero según actividad remunerada "
            f"({len(datos)} respuestas)"
        ),
        labels={
            "actividad_remunerada": "Actividad remunerada",
            "respuestas": "Número de respuestas",
            "suficiencia_dinero": "¿Alcanza el dinero?",
        },
    )
    return figura.update_layout(height=500, xaxis_tickangle=-25, margin={"b": 150})


def grafico_cruce_porcentual(
    datos: pd.DataFrame,
    filas: str,
    columnas: str,
    titulo: str,
    etiqueta_filas: str,
    etiqueta_columnas: str,
):
    tabla = pd.crosstab(datos[filas], datos[columnas], normalize="index").mul(100)
    cruce = (
        tabla.round(1)
        .reset_index()
        .melt(id_vars=filas, var_name=columnas, value_name="porcentaje")
    )
    figura = px.bar(
        cruce,
        x=filas,
        y="porcentaje",
        color=columnas,
        barmode="group",
        text="porcentaje",
        title=f"{titulo} ({len(datos)} respuestas)",
        labels={
            filas: etiqueta_filas,
            columnas: etiqueta_columnas,
            "porcentaje": "Porcentaje dentro del grupo",
        },
    )
    figura.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    figura.update_layout(
        height=520,
        yaxis_range=[0, 100],
        xaxis_tickangle=-25,
        margin={"b": 150},
    )
    return figura


def categoria_mas_frecuente(datos: pd.DataFrame, columna: str):
    conteos = datos[columna].value_counts()
    categoria = conteos.index[0]
    cantidad = int(conteos.iloc[0])
    porcentaje = cantidad / len(datos) * 100
    return categoria, cantidad, porcentaje


def mostrar_kpis(datos: pd.DataFrame):
    kpis = [
        ("Respuestas", str(len(datos)), "subconjunto seleccionado"),
        ("Ingreso más frecuente", "ingreso_semanal", "rango original"),
        ("Gasto principal", "gasto_principal", "categoría modal"),
        ("Ahorro más frecuente", "probabilidad_ahorro", "respuesta modal"),
        ("Suficiencia más frecuente", "suficiencia_dinero", "percepción modal"),
    ]
    columnas = st.columns(len(kpis))
    for columna, (titulo, valor, ayuda) in zip(columnas, kpis):
        if valor in datos.columns:
            categoria, cantidad, porcentaje = categoria_mas_frecuente(datos, valor)
            columna.metric(
                titulo,
                categoria,
                f"{cantidad} respuestas ({porcentaje:.1f}%)",
                help=ayuda,
            )
        else:
            columna.metric(titulo, valor, help=ayuda)


def filtrar_datos(encuesta, frecuencia, actividad, gasto):
    datos = encuesta.copy()
    if frecuencia != TODAS:
        datos = datos[datos["frecuencia_ingreso"] == frecuencia]
    if actividad != TODAS:
        datos = datos[datos["actividad_remunerada"] == actividad]
    if gasto != TODAS:
        datos = datos[datos["gasto_principal"] == gasto]
    return datos


def mostrar_hallazgo(encuesta, columna, descripcion):
    categoria, cantidad, porcentaje = categoria_mas_frecuente(encuesta, columna)
    st.markdown(
        f"- {descripcion}: **{categoria}** "
        f"({cantidad} de {len(encuesta)}, {porcentaje:.1f}%)."
    )


st.title("Dashboard estadístico: gastos y economía personal en estudiantes")
st.markdown(
    "Este dashboard analiza descriptivamente las respuestas reales de una encuesta "
    "a estudiantes sobre ingreso, gasto, ahorro y administración del dinero."
)
st.markdown(
    "La muestra contiene respuestas de estudiantes y no representa necesariamente a "
    "toda la población. Las categorías monetarias originales se conservan sin "
    "convertirlas en cantidades exactas."
)

ruta_csv = Path(__file__).resolve().parent / "encuesta.csv"
if not ruta_csv.exists():
    st.error(
        "No se encontró `encuesta.csv`. Coloca el archivo CSV en la misma carpeta "
        "que `app.py` para ejecutar el dashboard."
    )
    st.stop()

try:
    encuesta, calidad, diccionario = cargar_datos(str(ruta_csv))
except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(f"No fue posible cargar la encuesta: {error}")
    st.stop()

st.header("1. Introducción")
st.markdown(
    "La encuesta pregunta por la frecuencia y el rango aproximado de ingresos, "
    "la actividad remunerada, los principales gastos, el ahorro, la suficiencia "
    "del dinero, la comparación de precios y el uso de presupuestos."
)
st.markdown(
    "Las barras muestran frecuencias y porcentajes. Una asociación descriptiva "
    "entre variables no demuestra causalidad."
)

st.header("2. Panorama y calidad de los datos")
calidad_columnas = st.columns(4)
calidad_columnas[0].metric("Respuestas", len(encuesta))
calidad_columnas[1].metric("Variables", encuesta.shape[1])
calidad_columnas[2].metric("Valores faltantes", int(encuesta.isna().sum().sum()))
calidad_columnas[3].metric("Filas duplicadas", int(encuesta.duplicated().sum()))
st.dataframe(calidad, use_container_width=True, hide_index=True)

resumen_calidad = pd.DataFrame(
    {
        "verificación": ["Periodo de captura", "Tipos de respuesta"],
        "resultado": [
            f"{encuesta['marca_temporal'].min():%d/%m/%Y} a "
            f"{encuesta['marca_temporal'].max():%d/%m/%Y}",
            "Categóricas/ordinales y una variable temporal",
        ],
    }
)
st.dataframe(resumen_calidad, use_container_width=True, hide_index=True)

with st.expander("Valores faltantes por variable"):
    nulos_por_variable = encuesta.isna().sum().rename("valores_faltantes").to_frame()
    nulos_por_variable["porcentaje"] = (
        nulos_por_variable["valores_faltantes"] / len(encuesta) * 100
    ).round(1)
    st.dataframe(nulos_por_variable, use_container_width=True)

st.header("3. Diccionario de variables")
st.dataframe(diccionario, use_container_width=True, hide_index=True)

st.header("4. Análisis descriptivo")
st.markdown(
    "Las variables son principalmente categóricas u ordinales. Se utilizan "
    "frecuencias, porcentajes, barras y una dona; no se calculan medias de rangos monetarios."
)

for columna, titulo in VARIABLES_DESCRIPTIVAS:
    st.subheader(titulo)
    st.caption(
        "La gráfica muestra cuántas respuestas pertenecen a cada categoría y "
        "el porcentaje correspondiente dentro de la muestra."
    )
    st.plotly_chart(
        grafico_barras(encuesta, columna, titulo),
        use_container_width=True,
        key=f"descriptivo_{columna}",
    )

conteo_gasto = (
    encuesta["gasto_principal"]
    .value_counts()
    .rename_axis("categoria")
    .reset_index(name="frecuencia")
)
figura_dona = px.pie(
    conteo_gasto,
    names="categoria",
    values="frecuencia",
    hole=0.48,
    title="Composición de la principal categoría de gasto",
    labels={"categoria": "Categoría de gasto", "frecuencia": "Respuestas"},
)
figura_dona.update_traces(
    textposition="inside",
    textinfo="percent+label",
    hovertemplate=(
        "%{label}<br>Respuestas: %{value}<br>"
        "Porcentaje: %{percent}<extra></extra>"
    ),
)
figura_dona.update_layout(height=480)
st.plotly_chart(figura_dona, use_container_width=True, key="dona_gasto")

with st.expander("Tablas de frecuencias de todas las variables de respuesta"):
    for variable in VARIABLES_FRECUENCIAS:
        st.subheader(variable.replace("_", " ").title())
        st.dataframe(
            tabla_frecuencias(encuesta, variable),
            use_container_width=True,
            hide_index=True,
        )

st.header("5. Cruces y comparaciones entre variables")
st.markdown(
    "Los porcentajes se calculan dentro de cada grupo del eje horizontal. "
    "Los grupos pueden tener tamaños diferentes y los resultados no implican causalidad."
)
cruces = [
    (
        "actividad_suficiencia",
        grafico_cruce_porcentual(
            encuesta,
            "actividad_remunerada",
            "suficiencia_dinero",
            "Suficiencia del dinero según actividad remunerada",
            "Actividad remunerada",
            "Suficiencia percibida",
        ),
        "Compara la suficiencia percibida entre categorías de actividad remunerada.",
    ),
    (
        "actividad_ahorro",
        grafico_cruce_porcentual(
            encuesta,
            "actividad_remunerada",
            "probabilidad_ahorro",
            "Ahorro según actividad remunerada",
            "Actividad remunerada",
            "Probabilidad de ahorro",
        ),
        "Compara las respuestas de ahorro entre categorías de actividad remunerada.",
    ),
    (
        "frecuencia_suficiencia",
        grafico_cruce_porcentual(
            encuesta,
            "frecuencia_ingreso",
            "suficiencia_dinero",
            "Suficiencia del dinero según frecuencia de ingreso",
            "Frecuencia de ingreso",
            "Suficiencia percibida",
        ),
        "Compara la suficiencia percibida según la frecuencia declarada de ingreso.",
    ),
]
for clave, figura, explicacion in cruces:
    st.subheader(figura.layout.title.text.split(" (")[0])
    st.caption(explicacion)
    st.plotly_chart(figura, use_container_width=True, key=f"cruce_{clave}")

st.header("6. Dashboard interactivo")
st.markdown(
    "Los filtros conservan la lógica original del notebook. La opción `Todas` "
    "mantiene todas las respuestas y cada selección recalcula los indicadores y gráficos."
)

filtro_frecuencia = st.selectbox(
    "Ingreso:",
    [TODAS] + sorted(encuesta["frecuencia_ingreso"].dropna().unique().tolist()),
)
filtro_actividad = st.selectbox(
    "Actividad remunerada:",
    [TODAS] + sorted(encuesta["actividad_remunerada"].dropna().unique().tolist()),
)
filtro_gasto = st.selectbox(
    "Gasto principal:",
    [TODAS] + sorted(encuesta["gasto_principal"].dropna().unique().tolist()),
)

datos_filtrados = filtrar_datos(
    encuesta,
    filtro_frecuencia,
    filtro_actividad,
    filtro_gasto,
)

if datos_filtrados.empty:
    st.warning("No hay respuestas para esta combinación de filtros.")
else:
    st.subheader(f"Resumen de la selección: {len(datos_filtrados)} respuestas")
    mostrar_kpis(datos_filtrados)

    dashboard_graficos = [
        (
            "Frecuencia con que recibe dinero",
            "Las categorías originales muestran cómo se distribuye la frecuencia de ingreso dentro de la selección.",
            grafico_barras(
                datos_filtrados,
                "frecuencia_ingreso",
                "Frecuencia con que recibe dinero",
                "Frecuencia de ingreso",
            ),
        ),
        (
            "Principal categoría de gasto",
            "La gráfica indica qué categoría concentra más respuestas en la selección.",
            grafico_barras(
                datos_filtrados,
                "gasto_principal",
                "Principal categoría de gasto",
                "Categoría de gasto",
            ),
        ),
        (
            "Frecuencia del ahorro semanal",
            "La gráfica compara las respuestas sobre ahorrar y conserva sus categorías originales.",
            grafico_barras(
                datos_filtrados,
                "probabilidad_ahorro",
                "Frecuencia del ahorro semanal",
                "Respuesta sobre ahorro",
            ),
        ),
        (
            "Suficiencia del dinero según actividad remunerada",
            "El cruce compara frecuencias y no demuestra una relación causal.",
            grafico_suficiencia_por_actividad(datos_filtrados),
        ),
        (
            "Porcentaje de ingresos que se guarda",
            "Muestra la composición de los rangos de ahorro declarados.",
            grafico_barras(
                datos_filtrados,
                "porcentaje_ahorro",
                "Porcentaje de ingresos que se guarda",
                "Rango de ahorro",
            ),
        ),
    ]
    for numero, (titulo, explicacion, figura) in enumerate(dashboard_graficos, start=1):
        st.subheader(f"{numero}. {titulo}")
        st.caption(explicacion)
        st.plotly_chart(
            figura,
            use_container_width=True,
            key=f"dashboard_{numero}",
        )

st.header("7. Principales hallazgos")
st.markdown(
    "Los siguientes resultados se calculan directamente a partir de las 37 respuestas "
    "y se limitan a esta muestra."
)
mostrar_hallazgo(encuesta, "frecuencia_ingreso", "La frecuencia de ingreso más común es")
mostrar_hallazgo(encuesta, "ingreso_semanal", "La categoría de ingreso más frecuente es")
mostrar_hallazgo(encuesta, "actividad_remunerada", "La situación laboral más frecuente es")
mostrar_hallazgo(encuesta, "gasto_principal", "La categoría de gasto más frecuente es")
mostrar_hallazgo(encuesta, "probabilidad_ahorro", "La respuesta más frecuente sobre ahorrar es")
mostrar_hallazgo(encuesta, "porcentaje_ahorro", "El rango de ahorro más frecuente es")
mostrar_hallazgo(encuesta, "suficiencia_dinero", "La respuesta más frecuente sobre suficiencia es")
mostrar_hallazgo(encuesta, "presupuesto", "La experiencia más frecuente con presupuestos es")

st.header("8. Conclusiones")
st.markdown(
    "En esta muestra, el dashboard permite observar cómo se distribuyen los ingresos, "
    "los gastos, el ahorro y la percepción de suficiencia del dinero, además de comparar "
    "esas respuestas entre grupos definidos por variables de la propia encuesta. Los "
    "resultados muestran patrones predominantes, pero no permiten afirmar que una actividad "
    "remunerada, una frecuencia de ingreso o una categoría de gasto cause otra respuesta."
)
st.markdown(
    "La principal limitación es que se trata de 37 respuestas de una encuesta y no de un "
    "diseño probabilístico; por ello los resultados no deben generalizarse a todos los "
    "estudiantes. Además, los ingresos y gastos fueron capturados en rangos categóricos, "
    "así que el análisis evita calcular promedios monetarios artificiales. Los cruces deben "
    "leerse como asociaciones descriptivas y considerando el tamaño desigual de los grupos."
)
