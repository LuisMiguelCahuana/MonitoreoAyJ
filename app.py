import streamlit as st
import gspread
import pandas as pd
import re

from google.oauth2.service_account import Credentials


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="MONITOR KM_DISTRIBUCION",
    page_icon="🛻",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CONFIGURACIÓN GOOGLE SHEETS
# ============================================================

NOMBRE_ARCHIVO = "KM_DISTRIBUCION"

NOMBRE_HOJA = "Distribucion"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# ============================================================
# CONEXIÓN GOOGLE SHEETS
# ============================================================

@st.cache_resource
def conectar_google():

    credenciales = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    cliente = gspread.authorize(
        credenciales
    )

    return cliente


@st.cache_resource
def obtener_hoja():

    cliente = conectar_google()

    spreadsheet = cliente.open(
        NOMBRE_ARCHIVO
    )

    hoja = spreadsheet.worksheet(
        NOMBRE_HOJA
    )

    return hoja


# ============================================================
# LEER DATOS
# ============================================================

def cargar_datos():

    hoja = obtener_hoja()

    valores = hoja.get(
        "A:U",
        value_render_option="FORMATTED_VALUE"
    )

    if not valores:

        return pd.DataFrame()


    encabezados = [
        "Fecha",
        "Placa",
        "Hora Inicio",
        "Km Inicial",
        "Hora Fin",
        "Km Final",
        "Tot Recorrido",
        "Nom Personal",
        "Celular",
        "Cuadrilla",
        "Item",
        "Unidad Negocio",
        "Servicio Electrico",
        "Nº OM | Cod. Recibo",
        "Descripcion Actividad",
        "CECO",
        "Foto KM Inicial",
        "Foto KM Final",
        "Ubicacion Inicial",
        "Ubicacion Final",
        "Observacion"
    ]


    filas = []


    for fila in valores[1:]:

        fila = list(fila)


        if len(fila) < 21:

            fila += [""] * (
                21 - len(fila)
            )


        filas.append(
            fila[:21]
        )


    df = pd.DataFrame(
        filas,
        columns=encabezados
    )


    # ========================================================
    # ELIMINAR FILAS COMPLETAMENTE VACÍAS
    # ========================================================

    df = df[
        df.astype(str)
        .apply(
            lambda x:
            x.str.strip().ne("").any(),
            axis=1
        )
    ].copy()


    return df


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar_texto(valor):

    if pd.isna(valor):

        return ""


    return str(
        valor
    ).strip()


# ============================================================
# PREPARAR DATOS
# ============================================================

def preparar_datos(df):

    if df.empty:

        return df


    columnas_texto = [

        "Fecha",
        "Placa",
        "Hora Inicio",
        "Km Inicial",
        "Hora Fin",
        "Km Final",
        "Tot Recorrido",
        "Nom Personal",
        "Celular",
        "Cuadrilla",
        "Item",
        "Unidad Negocio",
        "Servicio Electrico",
        "Nº OM | Cod. Recibo",
        "Descripcion Actividad",
        "CECO",
        "Foto KM Inicial",
        "Foto KM Final",
        "Ubicacion Inicial",
        "Ubicacion Final",
        "Observacion"

    ]


    for columna in columnas_texto:

        df[columna] = (
            df[columna]
            .apply(normalizar_texto)
        )


    # ========================================================
    # ESTADO
    # ========================================================

    df["Estado"] = df.apply(

        lambda fila:

        "🟢 COMPLETADO"

        if fila["Km Final"] != ""

        else "🟠 PENDIENTE KM FINAL",

        axis=1

    )


    return df


# ============================================================
# EXTRAER URL
# ============================================================

def extraer_url(valor):

    valor = normalizar_texto(
        valor
    )


    if valor == "":

        return ""


    # ========================================================
    # GOOGLE SHEETS HYPERLINK
    # ========================================================

    if "HYPERLINK" in valor.upper():

        encontrado = re.search(
            r'"(https?://[^"]+)"',
            valor
        )


        if encontrado:

            return encontrado.group(1)


    # ========================================================
    # URL DIRECTA
    # ========================================================

    if (
        valor.startswith("http://")
        or
        valor.startswith("https://")
    ):

        return valor


    return ""


# ============================================================
# CONVERTIR FOTO EN ENLACE
# ============================================================

def convertir_enlace_foto(valor):

    url = extraer_url(
        valor
    )


    if url == "":

        return "—"


    return (
        f'<a href="{url}" '
        f'target="_blank">'
        f'📷 Ver foto'
        f'</a>'
    )


# ============================================================
# CONVERTIR UBICACIÓN EN ENLACE
# ============================================================

def convertir_enlace_ubicacion(valor):

    valor = normalizar_texto(
        valor
    )


    if valor == "":

        return "—"


    if (
        valor.startswith("http://")
        or
        valor.startswith("https://")
    ):

        return (
            f'<a href="{valor}" '
            f'target="_blank">'
            f'📍 Ver ubicación'
            f'</a>'
        )


    return valor


# ============================================================
# TÍTULO
# ============================================================

st.markdown(
    """
    <h1 style="
        text-align:center;
        margin-bottom:0;
    ">
        🛻 MONITOR DE KILOMETRAJE DISTRIBUCIÓN
    </h1>

    <p style="
        text-align:center;
        color:#666;
        font-size:16px;
        margin-top:0;
    ">
        Supervisión de registros de KM_DISTRIBUCION
    </p>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CARGAR DATOS
# ============================================================

try:

    df = cargar_datos()

except Exception as e:

    st.error(
        "❌ No se pudo conectar con Google Sheets."
    )

    st.exception(e)

    st.stop()


# ============================================================
# VALIDAR DATOS
# ============================================================

if df.empty:

    st.info(
        "ℹ️ No existen registros en la hoja Distribucion."
    )

    st.stop()


# ============================================================
# PREPARAR DATOS
# ============================================================

df = preparar_datos(
    df
)


# ============================================================
# FILTROS
# ============================================================

st.markdown(
    "### 🔎 FILTROS"
)


# ============================================================
# PRIMERA FILA
# ============================================================

col1, col2, col3, col4 = st.columns(4)


# ============================================================
# FECHA
# ============================================================

fechas = sorted(

    [
        x
        for x in
        df["Fecha"]
        .dropna()
        .unique()
        .tolist()

        if str(x).strip() != ""
    ],

    reverse=True

)


with col1:

    fecha_filtro = st.selectbox(

        "📅 Fecha",

        [
            "TODAS"
        ]
        +
        fechas

    )


# ============================================================
# PLACA
# ============================================================

placas = sorted(

    [
        x
        for x in
        df["Placa"]
        .dropna()
        .unique()
        .tolist()

        if str(x).strip() != ""
    ]

)


with col2:

    placa_filtro = st.selectbox(

        "🛻 Placa",

        [
            "TODAS"
        ]
        +
        placas

    )


# ============================================================
# PERSONAL
# ============================================================

personales = sorted(

    [
        x
        for x in
        df["Nom Personal"]
        .dropna()
        .unique()
        .tolist()

        if str(x).strip() != ""
    ]

)


with col3:

    personal_filtro = st.selectbox(

        "👷 Personal",

        [
            "TODOS"
        ]
        +
        personales

    )


# ============================================================
# ESTADO
# ============================================================

with col4:

    estado_filtro = st.selectbox(

        "📌 Estado",

        [
            "TODOS",
            "🟠 PENDIENTE KM FINAL",
            "🟢 COMPLETADO"
        ]

    )


# ============================================================
# SEGUNDA FILA
# ============================================================

col5, col6, col7, col8 = st.columns(4)


# ============================================================
# UNIDAD
# ============================================================

unidades = sorted(

    [
        x
        for x in
        df["Unidad Negocio"]
        .dropna()
        .unique()
        .tolist()

        if str(x).strip() != ""
    ]

)


with col5:

    unidad_filtro = st.selectbox(

        "🏢 Unidad de Negocio",

        [
            "TODAS"
        ]
        +
        unidades

    )


# ============================================================
# SERVICIO
# ============================================================

servicios = sorted(

    [
        x
        for x in
        df["Servicio Electrico"]
        .dropna()
        .unique()
        .tolist()

        if str(x).strip() != ""
    ]

)


with col6:

    servicio_filtro = st.selectbox(

        "⚡ Servicio Eléctrico",

        [
            "TODOS"
        ]
        +
        servicios

    )


# ============================================================
# ITEM
# ============================================================

items = sorted(

    [
        x
        for x in
        df["Item"]
        .dropna()
        .unique()
        .tolist()

        if str(x).strip() != ""
    ]

)


with col7:

    item_filtro = st.selectbox(

        "📋 Ítem",

        [
            "TODOS"
        ]
        +
        items

    )


# ============================================================
# CECO
# ============================================================

cecos = sorted(

    [
        x
        for x in
        df["CECO"]
        .dropna()
        .unique()
        .tolist()

        if str(x).strip() != ""
    ]

)


with col8:

    ceco_filtro = st.selectbox(

        "🏷️ CECO",

        [
            "TODOS"
        ]
        +
        cecos

    )


# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()


if fecha_filtro != "TODAS":

    df_filtrado = df_filtrado[
        df_filtrado["Fecha"]
        == fecha_filtro
    ]


if placa_filtro != "TODAS":

    df_filtrado = df_filtrado[
        df_filtrado["Placa"]
        == placa_filtro
    ]


if personal_filtro != "TODOS":

    df_filtrado = df_filtrado[
        df_filtrado["Nom Personal"]
        == personal_filtro
    ]


if estado_filtro != "TODOS":

    df_filtrado = df_filtrado[
        df_filtrado["Estado"]
        == estado_filtro
    ]


if unidad_filtro != "TODAS":

    df_filtrado = df_filtrado[
        df_filtrado["Unidad Negocio"]
        == unidad_filtro
    ]


if servicio_filtro != "TODOS":

    df_filtrado = df_filtrado[
        df_filtrado["Servicio Electrico"]
        == servicio_filtro
    ]


if item_filtro != "TODOS":

    df_filtrado = df_filtrado[
        df_filtrado["Item"]
        == item_filtro
    ]


if ceco_filtro != "TODOS":

    df_filtrado = df_filtrado[
        df_filtrado["CECO"]
        == ceco_filtro
    ]


# ============================================================
# RESUMEN
# ============================================================

total_registros = len(
    df_filtrado
)


total_vehiculos = (

    df_filtrado["Placa"]
    .replace("", pd.NA)
    .dropna()
    .nunique()

)


total_personal = (

    df_filtrado["Nom Personal"]
    .replace("", pd.NA)
    .dropna()
    .nunique()

)


total_pendientes = len(

    df_filtrado[
        df_filtrado["Km Final"] == ""
    ]

)


total_completados = len(

    df_filtrado[
        df_filtrado["Km Final"] != ""
    ]

)


# ============================================================
# MOSTRAR RESUMEN
# ============================================================

st.markdown(
    "### 📊 RESUMEN"
)


k1, k2, k3, k4, k5 = st.columns(5)


with k1:

    st.metric(
        "📋 Registros",
        total_registros
    )


with k2:

    st.metric(
        "🛻 Vehículos",
        total_vehiculos
    )


with k3:

    st.metric(
        "👷 Personal",
        total_personal
    )


with k4:

    st.metric(
        "🟠 Pendientes",
        total_pendientes
    )


with k5:

    st.metric(
        "🟢 Completados",
        total_completados
    )


# ============================================================
# TABLA PRINCIPAL
# ============================================================

st.markdown(
    "### 📋 REGISTROS"
)


if df_filtrado.empty:

    st.warning(
        "No existen registros con "
        "los filtros seleccionados."
    )

else:

    df_mostrar = df_filtrado.copy()


    # ========================================================
    # FOTOS
    # ========================================================

    df_mostrar[
        "📷 KM Inicial"
    ] = (

        df_mostrar[
            "Foto KM Inicial"
        ]

        .apply(
            convertir_enlace_foto
        )

    )


    df_mostrar[
        "📷 KM Final"
    ] = (

        df_mostrar[
            "Foto KM Final"
        ]

        .apply(
            convertir_enlace_foto
        )

    )


    # ========================================================
    # UBICACIONES
    # ========================================================

    df_mostrar[
        "📍 Ubicación Inicial"
    ] = (

        df_mostrar[
            "Ubicacion Inicial"
        ]

        .apply(
            convertir_enlace_ubicacion
        )

    )


    df_mostrar[
        "📍 Ubicación Final"
    ] = (

        df_mostrar[
            "Ubicacion Final"
        ]

        .apply(
            convertir_enlace_ubicacion
        )

    )


    # ========================================================
    # COLUMNAS QUE SE MOSTRARÁN
    # ========================================================

    columnas_mostrar = [

        "Fecha",
        "Placa",
        "Hora Inicio",
        "Km Inicial",
        "Hora Fin",
        "Km Final",
        "Tot Recorrido",
        "Nom Personal",
        "Celular",
        "Cuadrilla",
        "Item",
        "Unidad Negocio",
        "Servicio Electrico",
        "Nº OM | Cod. Recibo",
        "Descripcion Actividad",
        "CECO",
        "Estado",
        "📷 KM Inicial",
        "📷 KM Final",
        "📍 Ubicación Inicial",
        "📍 Ubicación Final",
        "Observacion"

    ]


    tabla = df_mostrar[
        columnas_mostrar
    ].copy()


    # ========================================================
    # ESTILO DE TABLA
    # ========================================================

    st.markdown(
        """
        <style>

        /* ====================================================
           CONTENEDOR
           ==================================================== */

        .tabla-supervisor {

            width: 100%;

            overflow-x: auto;

            margin-top: 10px;

        }


        /* ====================================================
           TABLA
           ==================================================== */

        .tabla-supervisor table {

            width: 100%;

            border-collapse: collapse;

            font-size: 13px;

            min-width: 1800px;

        }


        /* ====================================================
           ENCABEZADOS
           ==================================================== */

        .tabla-supervisor th {

            background-color: #1f2937 !important;

            color: #ffffff !important;

            padding: 8px;

            border: 1px solid #4b5563 !important;

            text-align: center;

            white-space: nowrap;

            font-weight: 700;

        }


        /* ====================================================
           CELDAS
           ==================================================== */

        .tabla-supervisor td {

            padding: 8px;

            border: 1px solid #4b5563 !important;

            white-space: nowrap;

            text-align: left;

        }


        /* ====================================================
           ENLACES
           ==================================================== */

        .tabla-supervisor a {

            text-decoration: none;

            font-weight: bold;

        }


        /* ====================================================
           MODO OSCURO
           ==================================================== */

        @media (prefers-color-scheme: dark) {

            .tabla-supervisor th {

                background-color: #111827 !important;

                color: #ffffff !important;

                border-color: #4b5563 !important;

            }


            .tabla-supervisor td {

                color: #f3f4f6 !important;

                border-color: #4b5563 !important;

                background-color: #1f2937 !important;

            }


            .tabla-supervisor a {

                color: #60a5fa !important;

            }

        }


        /* ====================================================
           MODO CLARO
           ==================================================== */

        @media (prefers-color-scheme: light) {

            .tabla-supervisor th {

                background-color: #1f2937 !important;

                color: #ffffff !important;

            }


            .tabla-supervisor td {

                color: #111827 !important;

                background-color: #ffffff !important;

            }


            .tabla-supervisor a {

                color: #2563eb !important;

            }

        }

        </style>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # GENERAR HTML
    # ========================================================

    html = tabla.to_html(

        index=False,

        escape=False,

        classes="tabla-supervisor"

    )


    # ========================================================
    # MOSTRAR TABLA
    # ========================================================

    st.markdown(

        f"""
        <div class="tabla-supervisor">

            {html}

        </div>
        """,

        unsafe_allow_html=True

    )


# ============================================================
# BOTÓN ACTUALIZAR
# ============================================================

st.markdown("---")


col_actualizar, col_info = st.columns(
    [1, 4]
)


with col_actualizar:

    if st.button(
        "🔄 Actualizar",
        use_container_width=True
    ):

        st.rerun()


with col_info:

    st.caption(
        "📡 Los datos se consultan directamente "
        "desde la hoja Distribucion. Presione "
        "«Actualizar» para consultar los registros "
        "más recientes."
    )
