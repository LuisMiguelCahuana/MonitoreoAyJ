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
# ESTILOS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       TÍTULO
       ======================================================== */

    .titulo-principal {
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitulo {
        text-align: center;
        font-size: 14px;
        margin-bottom: 20px;
    }


    /* ========================================================
       BOTÓN ACTUALIZAR
       ======================================================== */

    div.stButton > button {
        width: 100%;
        font-weight: 700;
        border-radius: 8px;
    }


    /* ========================================================
       MÉTRICAS
       ======================================================== */

    .metric-box {
        border: 1px solid #d1d5db;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        background-color: #f9fafb;
    }

    .metric-titulo {
        font-size: 13px;
        font-weight: 600;
    }

    .metric-valor {
        font-size: 24px;
        font-weight: 800;
    }


    /* ========================================================
       CONTENEDOR DE TABLA
       ======================================================== */

    .contenedor-tabla {
        width: 100%;
        overflow-x: auto;
        margin-top: 10px;
    }


    /* ========================================================
       TABLA
       ======================================================== */

    .tabla-supervisor {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        min-width: 1800px;
    }


    /* ENCABEZADOS */

    .tabla-supervisor th {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        text-align: center !important;
        vertical-align: middle !important;
        padding: 10px 8px !important;
        border: 1px solid #4b5563 !important;
        white-space: nowrap !important;
    }


    /* CELDAS */

    .tabla-supervisor td {
        padding: 8px !important;
        border: 1px solid #d1d5db !important;
        white-space: nowrap !important;
        vertical-align: middle !important;
    }


    /* FILAS */

    .tabla-supervisor tr:nth-child(even) {
        background-color: #f9fafb;
    }

    .tabla-supervisor tr:hover {
        background-color: #e5e7eb;
    }


    /* ENLACES */

    .tabla-supervisor a {
        text-decoration: none !important;
        font-weight: 700 !important;
    }


    /* ========================================================
       MODO OSCURO
       ======================================================== */

    @media (prefers-color-scheme: dark) {

        .titulo-principal {
            color: #ffffff !important;
        }

        .subtitulo {
            color: #d1d5db !important;
        }

        .metric-box {
            background-color: #1f2937 !important;
            border-color: #4b5563 !important;
            color: #ffffff !important;
        }

        .metric-titulo {
            color: #d1d5db !important;
        }

        .metric-valor {
            color: #ffffff !important;
        }

        .tabla-supervisor {
            color: #ffffff !important;
        }

        .tabla-supervisor th {
            background-color: #111827 !important;
            color: #ffffff !important;
            border-color: #4b5563 !important;
        }

        .tabla-supervisor td {
            background-color: #1f2937 !important;
            color: #ffffff !important;
            border-color: #4b5563 !important;
        }

        .tabla-supervisor tr:nth-child(even) td {
            background-color: #374151 !important;
        }

        .tabla-supervisor tr:hover td {
            background-color: #4b5563 !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CONEXIÓN GOOGLE SHEETS
# ============================================================

@st.cache_resource
def conectar_google():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["GOOGLE_CREDENTIALS"],
        scopes=scopes
    )

    cliente = gspread.authorize(credentials)

    return cliente


# ============================================================
# LEER HOJA
# ============================================================

@st.cache_data(ttl=30)
def leer_datos():

    cliente = conectar_google()

    archivo = cliente.open("KM_DISTRIBUCION")

    hoja = archivo.worksheet("Distribucion")

    datos = hoja.get(
        "A:U",
        value_render_option="FORMATTED_VALUE"
    )

    if not datos:
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

    for fila in datos[1:]:

        fila = list(fila)

        while len(fila) < 21:
            fila.append("")

        filas.append(fila[:21])

    df = pd.DataFrame(
        filas,
        columns=encabezados
    )

    return df


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar_texto(valor):

    if valor is None:
        return ""

    if pd.isna(valor):
        return ""

    return str(valor).strip()


# ============================================================
# EXTRAER URL DE HYPERLINK
# ============================================================

def extraer_url(valor):

    valor = normalizar_texto(valor)

    if not valor:
        return ""

    # HYPERLINK("URL";"texto")
    patron_1 = r'HYPERLINK\("([^"]+)"'

    resultado = re.search(
        patron_1,
        valor,
        flags=re.IGNORECASE
    )

    if resultado:
        return resultado.group(1)

    # HYPERLINK("URL","texto")
    patron_2 = r'HYPERLINK\("([^"]+)"'

    resultado = re.search(
        patron_2,
        valor,
        flags=re.IGNORECASE
    )

    if resultado:
        return resultado.group(1)

    # URL directa
    patron_3 = r'(https?://[^\s"]+)'

    resultado = re.search(
        patron_3,
        valor
    )

    if resultado:
        return resultado.group(1)

    return ""


# ============================================================
# CREAR ENLACE HTML
# ============================================================

def crear_enlace(valor, texto):

    url = extraer_url(valor)

    if not url:
        return "—"

    return f'<a href="{url}" target="_blank">{texto}</a>'


# ============================================================
# TÍTULO
# ============================================================

st.markdown(
    '<div class="titulo-principal">🛻 MONITOR KM DISTRIBUCIÓN</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo">Seguimiento de kilometraje de vehículos - Distribución</div>',
    unsafe_allow_html=True
)


# ============================================================
# BOTÓN ACTUALIZAR
# ============================================================

col_actualizar, col_espacio = st.columns([1, 5])

with col_actualizar:

    if st.button(
        "🔄 Actualizar",
        use_container_width=True
    ):

        leer_datos.clear()

        st.rerun()


# ============================================================
# CARGAR DATOS
# ============================================================

df = leer_datos()


if df.empty:

    st.warning("No existen registros en la hoja Distribucion.")

    st.stop()


# ============================================================
# NORMALIZAR COLUMNAS
# ============================================================

for columna in df.columns:

    df[columna] = df[columna].apply(
        normalizar_texto
    )


# ============================================================
# ELIMINAR FILAS COMPLETAMENTE VACÍAS
# ============================================================

columnas_datos = [
    "Fecha",
    "Placa",
    "Hora Inicio",
    "Km Inicial",
    "Hora Fin",
    "Km Final",
    "Nom Personal"
]

df = df[
    df[columnas_datos]
    .fillna("")
    .astype(str)
    .apply(
        lambda fila: fila.str.strip().ne("").any(),
        axis=1
    )
].copy()


# ============================================================
# ESTADO
# ============================================================

df["Estado"] = df["Km Final"].apply(
    lambda x:
        "🟢 COMPLETADO"
        if normalizar_texto(x)
        else "🟠 PENDIENTE KM FINAL"
)


# ============================================================
# ORDENAR POR FECHA
# ============================================================

df["_fecha_orden"] = pd.to_datetime(
    df["Fecha"],
    errors="coerce",
    dayfirst=True
)

df = df.sort_values(
    "_fecha_orden",
    ascending=False
)

df.drop(
    columns=["_fecha_orden"],
    inplace=True
)


# ============================================================
# FILTROS
# ============================================================

st.markdown("### 🔎 Filtros")


col1, col2, col3, col4 = st.columns(4)


with col1:

    fechas = sorted(
        [
            x for x in df["Fecha"].unique()
            if normalizar_texto(x)
        ],
        reverse=True
    )

    filtro_fecha = st.multiselect(
        "Fecha",
        fechas
    )


with col2:

    placas = sorted(
        [
            x for x in df["Placa"].unique()
            if normalizar_texto(x)
        ]
    )

    filtro_placa = st.multiselect(
        "Placa",
        placas
    )


with col3:

    personal = sorted(
        [
            x for x in df["Nom Personal"].unique()
            if normalizar_texto(x)
        ]
    )

    filtro_personal = st.multiselect(
        "Personal",
        personal
    )


with col4:

    filtro_estado = st.multiselect(
        "Estado",
        [
            "🟢 COMPLETADO",
            "🟠 PENDIENTE KM FINAL"
        ]
    )


col5, col6, col7, col8 = st.columns(4)


with col5:

    unidades = sorted(
        [
            x for x in df["Unidad Negocio"].unique()
            if normalizar_texto(x)
        ]
    )

    filtro_unidad = st.multiselect(
        "Unidad de Negocio",
        unidades
    )


with col6:

    servicios = sorted(
        [
            x for x in df["Servicio Electrico"].unique()
            if normalizar_texto(x)
        ]
    )

    filtro_servicio = st.multiselect(
        "Servicio Eléctrico",
        servicios
    )


with col7:

    items = sorted(
        [
            x for x in df["Item"].unique()
            if normalizar_texto(x)
        ]
    )

    filtro_item = st.multiselect(
        "Ítem",
        items
    )


with col8:

    cecos = sorted(
        [
            x for x in df["CECO"].unique()
            if normalizar_texto(x)
        ]
    )

    filtro_ceco = st.multiselect(
        "CECO",
        cecos
    )


# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()


if filtro_fecha:

    df_filtrado = df_filtrado[
        df_filtrado["Fecha"].isin(filtro_fecha)
    ]


if filtro_placa:

    df_filtrado = df_filtrado[
        df_filtrado["Placa"].isin(filtro_placa)
    ]


if filtro_personal:

    df_filtrado = df_filtrado[
        df_filtrado["Nom Personal"].isin(filtro_personal)
    ]


if filtro_estado:

    df_filtrado = df_filtrado[
        df_filtrado["Estado"].isin(filtro_estado)
    ]


if filtro_unidad:

    df_filtrado = df_filtrado[
        df_filtrado["Unidad Negocio"].isin(filtro_unidad)
    ]


if filtro_servicio:

    df_filtrado = df_filtrado[
        df_filtrado["Servicio Electrico"].isin(filtro_servicio)
    ]


if filtro_item:

    df_filtrado = df_filtrado[
        df_filtrado["Item"].isin(filtro_item)
    ]


if filtro_ceco:

    df_filtrado = df_filtrado[
        df_filtrado["CECO"].isin(filtro_ceco)
    ]


# ============================================================
# MÉTRICAS
# ============================================================

total_registros = len(df_filtrado)

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
        df_filtrado["Estado"] ==
        "🟠 PENDIENTE KM FINAL"
    ]
)

total_completados = len(
    df_filtrado[
        df_filtrado["Estado"] ==
        "🟢 COMPLETADO"
    ]
)


# ============================================================
# MOSTRAR MÉTRICAS
# ============================================================

st.markdown("### 📊 Resumen")


m1, m2, m3, m4, m5 = st.columns(5)


with m1:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-titulo">Registros</div>
            <div class="metric-valor">{total_registros}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with m2:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-titulo">Vehículos</div>
            <div class="metric-valor">{total_vehiculos}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with m3:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-titulo">Personal</div>
            <div class="metric-valor">{total_personal}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with m4:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-titulo">Pendientes</div>
            <div class="metric-valor">{total_pendientes}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with m5:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-titulo">Completados</div>
            <div class="metric-valor">{total_completados}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# PREPARAR TABLA PARA MOSTRAR
# ============================================================

df_mostrar = df_filtrado.copy()


# ============================================================
# ENLACES DE FOTOS
# ============================================================

df_mostrar["Foto KM Inicial"] = df_mostrar[
    "Foto KM Inicial"
].apply(
    lambda x: crear_enlace(
        x,
        "📷 Ver foto"
    )
)


df_mostrar["Foto KM Final"] = df_mostrar[
    "Foto KM Final"
].apply(
    lambda x: crear_enlace(
        x,
        "📷 Ver foto"
    )
)


# ============================================================
# ENLACES DE UBICACIONES
# ============================================================

df_mostrar["Ubicacion Inicial"] = df_mostrar[
    "Ubicacion Inicial"
].apply(
    lambda x: crear_enlace(
        x,
        "📍 Ver ubicación"
    )
)


df_mostrar["Ubicacion Final"] = df_mostrar[
    "Ubicacion Final"
].apply(
    lambda x: crear_enlace(
        x,
        "📍 Ver ubicación"
    )
)


# ============================================================
# ORDEN DE COLUMNAS
# ============================================================

columnas_tabla = [
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
    "Foto KM Inicial",
    "Foto KM Final",
    "Ubicacion Inicial",
    "Ubicacion Final",
    "Observacion"
]


df_mostrar = df_mostrar[
    columnas_tabla
]


# ============================================================
# TÍTULO DE TABLA
# ============================================================

st.markdown(
    f"### 📋 Registros ({len(df_mostrar)})"
)


# ============================================================
# SI NO HAY RESULTADOS
# ============================================================

if df_mostrar.empty:

    st.info(
        "No existen registros con los filtros seleccionados."
    )

    st.stop()


# ============================================================
# GENERAR TABLA HTML
# ============================================================

tabla_html = df_mostrar.to_html(
    index=False,
    escape=False,
    classes="tabla-supervisor",
    border=0
)


# ============================================================
# MOSTRAR TABLA REAL
# ============================================================

st.markdown(
    f"""
    <div class="contenedor-tabla">
        {tabla_html}
    </div>
    """,
    unsafe_allow_html=True
)
