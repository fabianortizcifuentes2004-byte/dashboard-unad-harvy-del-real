import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
from indice_vulnerabilidad import cargar, indice, TERRITORIOS_PRIORITARIOS, FUERA_PAIS, si
warnings.filterwarnings('ignore')

# ============ CONFIGURACIÓN ============
st.set_page_config(
    page_title="Dashboard Estudiantes UNAD - Sociología",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    :root {
        --primary-color: #1F4E78;
        --secondary-color: #4472C4;
        --success-color: #00B050;
        --warning-color: #FFC000;
        --danger-color: #FF0000;
    }

    .main {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f26 100%);
    }

    .metric-box {
        background: linear-gradient(135deg, rgba(31, 78, 120, 0.15) 0%, rgba(68, 114, 196, 0.15) 100%);
        border: 2px solid #4472C4;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }

    .section-title {
        font-size: 24px;
        font-weight: bold;
        color: #4472C4;
        border-bottom: 3px solid #1F4E78;
        padding-bottom: 10px;
        margin: 20px 0;
    }

    .stat-value {
        font-size: 32px;
        font-weight: bold;
        color: #4472C4;
    }

    .stat-label {
        font-size: 14px;
        color: #888;
        margin-top: 5px;
    }

    .risk-critical {
        background: rgba(255, 0, 0, 0.1);
        border-left: 5px solid #FF0000;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }

    .risk-high {
        background: rgba(255, 192, 0, 0.1);
        border-left: 5px solid #FFC000;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }

    .risk-medium {
        background: rgba(255, 255, 0, 0.1);
        border-left: 5px solid #FFFF00;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }

    .risk-low {
        background: rgba(0, 176, 80, 0.1);
        border-left: 5px solid #00B050;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============ CARGA DE DATOS ============
@st.cache_data
def load_data():
    return cargar('df_clean.csv')

@st.cache_data
def create_vulnerability_index(df):
    v = indice(df)
    return v.rename(columns={'INDICE': 'ÍNDICE_TOTAL', 'Nivel': 'Nivel_Riesgo'})

df = load_data()
vuln_score = create_vulnerability_index(df)

# ============ FUNCIONES DE VISUALIZACIÓN ============
def create_metric_card(label, value, suffix="", color="#4472C4"):
    return f"""
    <div style="background: linear-gradient(135deg, rgba(31, 78, 120, 0.15) 0%, rgba(68, 114, 196, 0.15) 100%);
                border: 2px solid {color};
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                margin: 10px 0;">
        <div style="font-size: 32px; font-weight: bold; color: {color};">{value}{suffix}</div>
        <div style="font-size: 14px; color: #888; margin-top: 5px;">{label}</div>
    </div>
    """

def plot_risk_distribution():
    risk_counts = vuln_score['Nivel_Riesgo'].value_counts().reindex(['CRÍTICO', 'ALTO', 'MEDIO', 'BAJO'], fill_value=0)
    colors_map = {'CRÍTICO': '#FF0000', 'ALTO': '#FFC000', 'MEDIO': '#FFFF00', 'BAJO': '#00B050'}

    fig = go.Figure(data=[go.Bar(
        x=risk_counts.index,
        y=risk_counts.values,
        marker=dict(color=[colors_map[x] for x in risk_counts.index]),
        text=risk_counts.values,
        textposition='outside',
        texttemplate='<b>%{text}</b><br>(%{customdata:.1f}%)',
        customdata=(risk_counts.values / len(df) * 100),
        hovertemplate='<b>%{x}</b><br>Estudiantes: %{text}<br>Porcentaje: %{customdata:.1f}%<extra></extra>'
    )])

    fig.update_layout(
        title="<b>Distribución de Estudiantes por Nivel de Riesgo</b>",
        xaxis_title="Nivel de Riesgo",
        yaxis_title="Número de Estudiantes",
        template="plotly_dark",
        hovermode='x unified',
        height=400,
        showlegend=False
    )

    return fig

def plot_vulnerability_dimensions():
    dimensions = ['Socioeconomico', 'Inclusion', 'Brecha_Digital', 'Academica', 'Competencias']
    maximos = {'Socioeconomico': .25, 'Inclusion': .20, 'Brecha_Digital': .20, 'Academica': .20, 'Competencias': .15}
    avg_scores = [vuln_score[dim].mean() / maximos[dim] for dim in dimensions]

    fig = go.Figure(data=[go.Bar(
        x=dimensions,
        y=avg_scores,
        marker=dict(color=avg_scores, colorscale='Reds', showscale=False),
        text=[f"{x:.2f}" for x in avg_scores],
        textposition='outside',
        texttemplate='<b>%{text}</b>',
        hovertemplate='<b>%{x}</b><br>Índice: %{y:.2f}<extra></extra>'
    )])

    fig.update_layout(
        title="<b>Vulnerabilidad Promedio por Dimensión (% del máximo de cada dimensión)</b>",
        xaxis_title="Dimensión",
        yaxis_title="Índice de Vulnerabilidad",
        template="plotly_dark",
        height=400,
        showlegend=False,
        yaxis=dict(range=[0, 1])
    )

    return fig

def plot_demographic_age():
    fig = go.Figure(data=[go.Histogram(
        x=df['Edad'].dropna(),
        nbinsx=20,
        marker=dict(color='#4472C4'),
        name='',
        hovertemplate='Edad: %{x}<br>Estudiantes: %{y}<extra></extra>'
    )])

    fig.update_layout(
        title="<b>Distribución de Edad de Estudiantes</b>",
        xaxis_title="Edad (años)",
        yaxis_title="Número de Estudiantes",
        template="plotly_dark",
        height=400,
        showlegend=False
    )

    return fig

def plot_socioeconomic():
    estrato_order = ['Uno', 'Dos', 'Tres', 'Cuatro', 'Cinco', 'Seis']
    estrato_counts = df['Estrato'].value_counts().reindex(estrato_order, fill_value=0)

    fig = go.Figure(data=[go.Pie(
        labels=estrato_counts.index,
        values=estrato_counts.values,
        marker=dict(colors=['#FF0000', '#FF6B35', '#FFC000', '#FFFF00', '#8FFF00', '#00B050']),
        textposition='auto',
        texttemplate='%{label}<br>%{percent}',
        hovertemplate='<b>Estrato %{label}</b><br>Estudiantes: %{value}<br>Porcentaje: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title="<b>Distribución por Estrato Socioeconómico</b>",
        template="plotly_dark",
        height=400
    )

    return fig

def plot_technology_access():
    equipos = {
        'Computador de Escritorio': (df['Computador de escritorio'].fillna('').str.contains('Sí', na=False)).sum(),
        'Computador Portátil': (df['Computador portatil'].fillna('').str.contains('Sí', na=False)).sum(),
        'Tablet': (df['Tableta'].fillna('').str.contains('Sí', na=False)).sum(),
        'Teléfono Inteligente': (df['Telefono inteligente'].fillna('').str.contains('Sí', na=False)).sum()
    }

    fig = go.Figure(data=[go.Bar(
        y=list(equipos.keys()),
        x=list(equipos.values()),
        orientation='h',
        marker=dict(color='#4472C4'),
        text=[f"{v} ({v/len(df)*100:.1f}%)" for v in equipos.values()],
        textposition='outside',
        texttemplate='<b>%{text}</b>',
        hovertemplate='<b>%{y}</b><br>Estudiantes: %{x}<extra></extra>'
    )])

    fig.update_layout(
        title="<b>Equipamiento Tecnológico Disponible</b>",
        xaxis_title="Número de Estudiantes",
        template="plotly_dark",
        height=400,
        showlegend=False
    )

    return fig

def plot_connectivity():
    internet = df['El lugar donde reside cuenta con servicio de Internet'].value_counts()

    fig = go.Figure(data=[go.Pie(
        labels=internet.index,
        values=internet.values,
        marker=dict(colors=['#00B050', '#FFC000', '#FF6B35']),
        texttemplate='%{label}<br>%{value}<br>%{percent}',
        hovertemplate='<b>%{label}</b><br>Estudiantes: %{value}<br>Porcentaje: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title="<b>Acceso a Internet en la Vivienda</b>",
        template="plotly_dark",
        height=400
    )

    return fig

def plot_employment():
    empleo = df['Cual es su situacion laboral actual'].value_counts()
    colors_emp = {'Empleado': '#00B050', 'Desempleado': '#FF0000', 'Independiente': '#4472C4', 'Pensionado': '#888888', 'Empresario': '#FFD700'}

    fig = go.Figure(data=[go.Bar(
        x=empleo.index,
        y=empleo.values,
        marker=dict(color=[colors_emp.get(x, '#4472C4') for x in empleo.index]),
        text=empleo.values,
        textposition='outside',
        texttemplate='<b>%{text}</b><br>(%{customdata:.1f}%)',
        customdata=(empleo.values / len(df) * 100),
        hovertemplate='<b>%{x}</b><br>Estudiantes: %{text}<br>Porcentaje: %{customdata:.1f}%<extra></extra>'
    )])

    fig.update_layout(
        title="<b>Situación Laboral de Estudiantes</b>",
        yaxis_title="Número de Estudiantes",
        template="plotly_dark",
        height=400,
        showlegend=False
    )

    return fig

def plot_competencies():
    digital = df['Competencias digitales'].value_counts().reindex(['Bajo', 'Medio', 'Alto'], fill_value=0)
    lectura = df['Lectura critica'].value_counts().reindex(['Bajo', 'Medio', 'Alto'], fill_value=0)

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type':'pie'}, {'type':'pie'}]],
        subplot_titles=("Competencias Digitales", "Lectura Crítica")
    )

    colors_comp = {'Bajo': '#FF0000', 'Medio': '#FFC000', 'Alto': '#00B050'}

    fig.add_trace(go.Pie(
        labels=digital.index,
        values=digital.values,
        marker=dict(colors=[colors_comp[x] for x in digital.index]),
        name='Digital'
    ), row=1, col=1)

    fig.add_trace(go.Pie(
        labels=lectura.index,
        values=lectura.values,
        marker=dict(colors=[colors_comp[x] for x in lectura.index]),
        name='Lectura'
    ), row=1, col=2)

    fig.update_layout(
        title_text="<b>Niveles de Competencias</b>",
        template="plotly_dark",
        height=400
    )

    return fig

def plot_time_dedication():
    tiempo = df['Con que tiempo cuenta para desarrollar las actividades academicas'].value_counts()

    fig = go.Figure(data=[go.Bar(
        x=tiempo.index,
        y=tiempo.values,
        marker=dict(color=['#FF0000' if x == '1 a 4 horas por semana' else '#FFC000' if x == '5 a 9 horas por semana' else '#00B050' for x in tiempo.index]),
        text=tiempo.values,
        textposition='outside',
        texttemplate='<b>%{text}</b>',
        hovertemplate='<b>%{x}</b><br>Estudiantes: %{text}<extra></extra>'
    )])

    fig.update_layout(
        title="<b>Tiempo Disponible para Actividades Académicas por Semana</b>",
        yaxis_title="Número de Estudiantes",
        template="plotly_dark",
        height=400,
        showlegend=False
    )

    return fig

def plot_risk_heatmap():
    # Crear matriz de riesgo por estrato y zona
    risk_data = pd.DataFrame({
        'Estrato': df['Estrato'],
        'Zona': df['Zona de residencia'],
        'Riesgo': vuln_score['ÍNDICE_TOTAL']
    })

    pivot_risk = risk_data.pivot_table(values='Riesgo', index='Estrato', columns='Zona', aggfunc='mean')
    pivot_risk = pivot_risk.reindex(['Uno', 'Dos', 'Tres', 'Cuatro', 'Cinco', 'Seis'], fill_value=np.nan)

    fig = go.Figure(data=go.Heatmap(
        z=pivot_risk.values,
        x=pivot_risk.columns,
        y=pivot_risk.index,
        colorscale='Reds',
        text=np.round(pivot_risk.values, 2),
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Índice<br>Riesgo"),
        hovertemplate='Estrato: %{y}<br>Zona: %{x}<br>Índice: %{z:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title="<b>Mapa de Calor: Riesgo por Estrato y Zona</b>",
        xaxis_title="Zona de Residencia",
        yaxis_title="Estrato Socioeconómico",
        template="plotly_dark",
        height=450
    )

    return fig

def plot_intervention_profiles():
    profiles = {
        'Brecha Digital': (df['Computador portatil'].notna() & ((~((df['Computador de escritorio'].fillna('').str.contains('Sí', na=False)) |
                              (df['Computador portatil'].fillna('').str.contains('Sí', na=False)))) |
                          (~(df['El lugar donde reside cuenta con servicio de Internet'].fillna('').str.contains('Permanente', na=False))))).sum(),
        'Trabajador Sobrecargado': (df['Con que tiempo cuenta para desarrollar las actividades academicas'].fillna('').str.contains('1 a 4 horas', na=False) &
                                    df['Cual es su situacion laboral actual'].fillna('').str.contains('Empleado', na=False)).sum(),
        'Con Discapacidad': df['Discapacidad'].sum(),
        'Desmotivados': ((df['El programa en el que se matriculo representa su primera opcion'] == 'No') &
                         (df['Cual es su situacion laboral actual'].fillna('').str.contains('Desempleado', na=False))).sum(),
        'Bajo Desempeño': ((df['Competencias digitales'].fillna('').str.contains('Bajo', na=False)) |
                          (df['Lectura critica'].fillna('').str.contains('Bajo', na=False))).sum(),
        'Víctima del Conflicto': df['Victima_conflicto'].sum(),
        'Pertenencia Étnica': df['Grupo_etnico'].sum(),
        'Territorio Prioritario': df['Territorio_prioritario'].sum()
    }

    fig = go.Figure(data=[go.Bar(
        x=list(profiles.keys()),
        y=list(profiles.values()),
        marker=dict(color=['#FF6B35', '#FF0000', '#FFC000', '#FFFF00', '#FF0000', '#7E57C2', '#26A69A', '#5C6BC0']),
        text=list(profiles.values()),
        textposition='outside',
        texttemplate='<b>%{text}</b><br>(%{customdata:.1f}%)',
        customdata=(np.array(list(profiles.values())) / len(df) * 100),
        hovertemplate='<b>%{x}</b><br>Estudiantes: %{text}<br>Porcentaje: %{customdata:.1f}%<extra></extra>'
    )])

    fig.update_layout(
        title="<b>Estudiantes por Perfil de Intervención</b>",
        yaxis_title="Número de Estudiantes",
        template="plotly_dark",
        height=400,
        showlegend=False,
        xaxis_tickangle=-45
    )

    return fig

# ============ INTERFAZ PRINCIPAL ============
st.markdown("""
<div style="background: linear-gradient(135deg, #1F4E78 0%, #4472C4 100%);
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;">
    <h1 style="color: white; margin: 0;">📊 Dashboard de Caracterización de Estudiantes</h1>
    <h3 style="color: #E8F0F8; margin: 10px 0 0 0;">Programa de Sociología - UNAD</h3>
    <p style="color: #B0D0E8; font-size: 14px; margin: 10px 0 0 0;">Análisis Integral de Vulnerabilidad · con enfoque territorial, poblacional y de discapacidad</p>
</div>
""", unsafe_allow_html=True)

# RESUMEN EJECUTIVO
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(create_metric_card("Total de Estudiantes", len(df), color="#4472C4"), unsafe_allow_html=True)

with col2:
    edad_prom = df['Edad'].mean()
    st.markdown(create_metric_card("Edad Promedio", f"{edad_prom:.1f}", " años", color="#70AD47"), unsafe_allow_html=True)

with col3:
    riesgo_alto = (vuln_score['Nivel_Riesgo'].isin(['CRÍTICO', 'ALTO'])).sum()
    pct = (riesgo_alto / len(df) * 100)
    st.markdown(create_metric_card("En Riesgo Alto/Crítico", f"{riesgo_alto}", f" ({pct:.0f}%)", color="#FF0000"), unsafe_allow_html=True)

with col4:
    resp = df['Computador portatil'].notna()   # 80 'Antiguos' no respondieron: no cuentan como brecha
    brecha_digital = (resp & ~((df['Computador de escritorio'].fillna('').str.contains('Sí', na=False)) |
                        (df['Computador portatil'].fillna('').str.contains('Sí', na=False)))).sum()
    pct_bd = (brecha_digital / resp.sum() * 100)
    st.markdown(create_metric_card("Brecha Digital (de quienes respondieron)", f"{brecha_digital}", f" ({pct_bd:.0f}%)", color="#FFC000"), unsafe_allow_html=True)

# ============ TABS PRINCIPALES ============
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "🚨 Mapa de Riesgo",
    "👥 Demografía",
    "💻 Tecnología",
    "💼 Laboral",
    "🎓 Académico",
    "📈 Perfiles",
    "🗺️ Territorio",
    "🧬 Grupos Poblacionales",
    "♿ Discapacidad"
])

# TAB 1: MAPA DE RIESGO
with tab1:
    st.markdown("<div class='section-title'>Análisis de Riesgo y Vulnerabilidad</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(plot_risk_distribution(), use_container_width=True)

    with col2:
        st.plotly_chart(plot_vulnerability_dimensions(), use_container_width=True)

    st.plotly_chart(plot_risk_heatmap(), use_container_width=True)

    # Alertas por nivel de riesgo
    st.markdown("<div class='section-title'>Alertas y Recomendaciones</div>", unsafe_allow_html=True)

    critico_count = (vuln_score['Nivel_Riesgo'] == 'CRÍTICO').sum()
    alto_count = (vuln_score['Nivel_Riesgo'] == 'ALTO').sum()

    if critico_count > 0:
        st.markdown(f"""
        <div class="risk-critical">
            <b>🔴 RIESGO CRÍTICO ({critico_count} estudiantes)</b><br>
            Estudiantes con alto riesgo de deserción. Requieren intervención inmediata con acceso a tecnología,
            apoyo psicosocial y flexibilidad académica.
        </div>
        """, unsafe_allow_html=True)

    if alto_count > 0:
        st.markdown(f"""
        <div class="risk-high">
            <b>🟠 RIESGO ALTO ({alto_count} estudiantes)</b><br>
            Múltiples factores de vulnerabilidad. Necesitan seguimiento intensivo y acciones preventivas.
        </div>
        """, unsafe_allow_html=True)

# TAB 2: DEMOGRAFÍA
with tab2:
    st.markdown("<div class='section-title'>Análisis Demográfico y Socioeconómico</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(plot_demographic_age(), use_container_width=True)

    with col2:
        st.plotly_chart(plot_socioeconomic(), use_container_width=True)

    # Datos detallados
    col1, col2, col3 = st.columns(3)

    with col1:
        sexo_counts = df['Sexo'].value_counts()
        st.write("**Distribución por Sexo:**")
        for sex, count in sexo_counts.items():
            pct = count / len(df) * 100
            st.write(f"- {sex}: {count} ({pct:.1f}%)")

    with col2:
        zona_counts = df['Zona de residencia'].value_counts()
        st.write("**Zona de Residencia:**")
        for zona, count in zona_counts.items():
            pct = count / len(df) * 100
            st.write(f"- {zona}: {count} ({pct:.1f}%)")

    with col3:
        estado_counts = df['Estado civil'].value_counts()
        st.write("**Estado Civil:**")
        for estado, count in estado_counts.items():
            pct = count / len(df) * 100
            st.write(f"- {estado}: {count} ({pct:.1f}%)")

# TAB 3: TECNOLOGÍA
with tab3:
    st.markdown("<div class='section-title'>Acceso Tecnológico y Conectividad</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(plot_technology_access(), use_container_width=True)

    with col2:
        st.plotly_chart(plot_connectivity(), use_container_width=True)

    # KPIs tecnológicos
    st.markdown("<div class='section-title'>Indicadores Clave de Tecnología</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        con_computador = ((df['Computador de escritorio'].fillna('').str.contains('Sí', na=False)) |
                         (df['Computador portatil'].fillna('').str.contains('Sí', na=False))).sum()
        pct = con_computador / df['Computador portatil'].notna().sum() * 100
        st.markdown(create_metric_card("Con Computador", f"{pct:.1f}%", color="#4472C4"), unsafe_allow_html=True)

    with col2:
        con_internet = (df['El lugar donde reside cuenta con servicio de Internet'].fillna('').str.contains('Permanente', na=False)).sum()
        pct = con_internet / df['Computador portatil'].notna().sum() * 100
        st.markdown(create_metric_card("Internet Permanente", f"{pct:.1f}%", color="#70AD47"), unsafe_allow_html=True)

    with col3:
        plataformas = (df['Ha usado plataformas virtuales con anterioridad'].fillna('').str.contains('Sí', na=False)).sum()
        pct = plataformas / df['Computador portatil'].notna().sum() * 100
        st.markdown(create_metric_card("Exp. Plataformas", f"{pct:.1f}%", color="#FFC000"), unsafe_allow_html=True)

    with col4:
        office = (df['Maneja paquetes ofimaticos como Office (Word Excel Powerpoint) o similares'].fillna('').str.contains('Sí', na=False)).sum()
        pct = office / df['Computador portatil'].notna().sum() * 100
        st.markdown(create_metric_card("Maneja Office", f"{pct:.1f}%", color="#70AD47"), unsafe_allow_html=True)

# TAB 4: LABORAL
with tab4:
    st.markdown("<div class='section-title'>Perfil Laboral y Dedicación</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(plot_employment(), use_container_width=True)

    with col2:
        st.plotly_chart(plot_time_dedication(), use_container_width=True)

    # Sectores económicos
    st.markdown("<div class='section-title'>Distribución por Sector Económico</div>", unsafe_allow_html=True)

    sector = df['A que sector economico pertenece'].value_counts().head(10)
    fig_sector = go.Figure(data=[go.Bar(
        x=sector.values,
        y=sector.index,
        orientation='h',
        marker=dict(color='#4472C4'),
        text=sector.values,
        textposition='outside'
    )])

    fig_sector.update_layout(
        title="<b>Principales Sectores Económicos</b>",
        xaxis_title="Número de Estudiantes",
        template="plotly_dark",
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig_sector, use_container_width=True)

# TAB 5: ACADÉMICO
with tab5:
    st.markdown("<div class='section-title'>Perfil Académico y Competencias</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(plot_competencies(), use_container_width=True)

    with col2:
        # Motivación para estudiar
        motivo = df['Cual es la principal razon para elegir el programa academico en el que se matriculo'].value_counts()
        fig_motivo = go.Figure(data=[go.Pie(
            labels=motivo.index,
            values=motivo.values,
            texttemplate='%{label}<br>%{percent}',
            hovertemplate='<b>%{label}</b><br>Estudiantes: %{value}<extra></extra>'
        )])

        fig_motivo.update_layout(
            title="<b>Motivación para Elegir el Programa</b>",
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(fig_motivo, use_container_width=True)

    # Educación previa
    st.markdown("<div class='section-title'>Trayectoria Académica Previa</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        colegio = df['Tipo de colegio donde termino su bachillerato'].value_counts()
        st.write("**Tipo de Colegio:**")
        for tipo, count in colegio.items():
            pct = count / len(df) * 100
            if pd.notna(tipo):
                st.write(f"- {tipo}: {pct:.1f}%")

    with col2:
        modalidad = df['La modalidad en la que obtuvo su grado de bachiller es'].value_counts()
        st.write("**Modalidad del Bachillerato:**")
        for mod, count in modalidad.items():
            pct = count / len(df) * 100
            if pd.notna(mod):
                st.write(f"- {mod}: {pct:.1f}%")

    with col3:
        tiempo = df['Cuanto tiempo lleva sin estudiar'].value_counts()
        st.write("**Tiempo Sin Estudiar:**")
        for t, count in tiempo.items():
            pct = count / len(df) * 100
            if pd.notna(t):
                st.write(f"- {t}: {pct:.1f}%")

# TAB 6: PERFILES DE INTERVENCIÓN
with tab6:
    st.markdown("<div class='section-title'>Perfiles de Intervención Personalizada</div>", unsafe_allow_html=True)

    st.plotly_chart(plot_intervention_profiles(), use_container_width=True)

    st.markdown("<div class='section-title'>Recomendaciones por Perfil</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🔴 Brecha Digital Severa**
        - Proporcionar acceso a equipamiento tecnológico
        - Capacitación en herramientas digitales básicas
        - Conectividad gratuita o subsidios
        - Módulos offline disponibles

        **🟠 Trabajador-Estudiante Sobrecargado**
        - Flexibilidad en horarios de entregas
        - Tutorías asincrónicas
        - Mentorías de estudiantes avanzados
        - Reconocimiento de competencias laborales
        """)

    with col2:
        st.markdown("""
        **🟡 Con Discapacidad**
        - Implementar ajustes razonables específicos
        - Apoyo psicosocial especializado
        - Acompañamiento académico personalizado
        - Accesibilidad en plataforma digital

        **🟢 Desmotivados/Bajo Desempeño**
        - Sesiones de reorientación académica
        - Talleres de habilidades de estudio
        - Conexión con oportunidades laborales
        - Mentoría de pares
        """)

# Footer
st.markdown("""
---
<div style="text-align: center; color: #888; font-size: 12px; margin-top: 30px;">
    <p>Dashboard de Caracterización de Estudiantes - Sociología UNAD<br>
    Datos actualizados al período 2025-I | Análisis de Vulnerabilidad Multidimensional</p>
</div>
""", unsafe_allow_html=True)


D = pd.concat([df, vuln_score], axis=1)
ORDEN = ['CRÍTICO', 'ALTO', 'MEDIO', 'BAJO']

def kpi_riesgo(mask):
    sub = D[mask]
    return len(sub), (sub['Nivel_Riesgo'].isin(['CRÍTICO', 'ALTO'])).sum(), sub['ÍNDICE_TOTAL'].mean()

st.caption('Nota: 80 estudiantes "Antiguos" no respondieron la caracterización digital/académica; los porcentajes de tecnología se calculan sobre los 413 que sí respondieron y su índice se calcula solo con territorio, estrato e inclusión.')

# TAB 7: TERRITORIO
with tab7:
    st.markdown("<div class='section-title'>Análisis Territorial: Departamento, Ciudad y Zona</div>", unsafe_allow_html=True)
    st.info("Zona rural y territorio prioritario son componentes del índice (dimensión socioeconómica), por lo que parte de la brecha territorial es esperable por construcción. "
            "Departamentos con pocos estudiantes (n<10) son indicativos, no concluyentes.")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(create_metric_card("Departamentos", D['Departamento'].nunique(), color="#4472C4"), unsafe_allow_html=True)
    c2.markdown(create_metric_card("Ciudades", D['Ciudad'].nunique(), color="#70AD47"), unsafe_allow_html=True)
    rur = (D['Zona de residencia'] == 'Rural').sum()
    c3.markdown(create_metric_card("Zona Rural", rur, f" ({rur/len(D)*100:.0f}%)", color="#FFC000"), unsafe_allow_html=True)
    tp = D['Territorio_prioritario'].sum()
    c4.markdown(create_metric_card("Territorio Prioritario", tp, f" ({tp/len(D)*100:.0f}%)", color="#FF0000"), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        z = D.groupby('Zona de residencia')['ÍNDICE_TOTAL'].mean().reset_index()
        fig = px.bar(z, x='Zona de residencia', y='ÍNDICE_TOTAL', text=z['ÍNDICE_TOTAL'].round(3), template='plotly_dark',
                     title='<b>Índice promedio: Rural vs Urbana</b>', color='Zona de residencia')
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        zr = pd.crosstab(D['Zona de residencia'], D['Nivel_Riesgo']).reindex(columns=ORDEN, fill_value=0)
        fig = px.bar(zr, barmode='stack', template='plotly_dark', title='<b>Nivel de riesgo por zona</b>',
                     color_discrete_map={'CRÍTICO': '#FF0000', 'ALTO': '#FFC000', 'MEDIO': '#FFFF00', 'BAJO': '#00B050'})
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    min_n = st.slider("Mínimo de estudiantes por departamento", 1, 20, 5)
    dep = D.groupby('Departamento').agg(Estudiantes=('ÍNDICE_TOTAL', 'size'), Indice=('ÍNDICE_TOTAL', 'mean'),
                                        Riesgo_alto=('Nivel_Riesgo', lambda x: x.isin(['CRÍTICO', 'ALTO']).sum())).reset_index()
    dep = dep[dep['Estudiantes'] >= min_n].sort_values('Indice')
    fig = px.bar(dep, x='Indice', y='Departamento', orientation='h', color='Indice', color_continuous_scale='Reds',
                 hover_data=['Estudiantes', 'Riesgo_alto'], template='plotly_dark',
                 title=f'<b>Índice promedio por departamento (n ≥ {min_n})</b>')
    fig.update_layout(height=max(380, 28 * len(dep)))
    st.plotly_chart(fig, use_container_width=True)

    ciu = D.groupby('Ciudad').agg(Estudiantes=('ÍNDICE_TOTAL', 'size'), Indice=('ÍNDICE_TOTAL', 'mean')).reset_index().sort_values('Estudiantes', ascending=False).head(15)
    st.markdown("**Top 15 ciudades por número de estudiantes**")
    st.dataframe(ciu.round(3), use_container_width=True, hide_index=True)

    raros = D[D['Departamento'].isin(FUERA_PAIS)]
    if len(raros):
        st.warning(f"Calidad de datos: {len(raros)} registros con departamento fuera de Colombia o dudoso "
                   f"({', '.join(sorted(raros['Departamento'].unique()))}). Conviene depurarlos en la fuente.")

# TAB 8: GRUPOS POBLACIONALES
with tab8:
    st.markdown("<div class='section-title'>Grupos Poblacionales y Enfoque Diferencial</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, (etq, m, color) in zip([c1, c2, c3, c4], [
            ("Algún Grupo Poblacional", D['Grupo_poblacional'], "#4472C4"),
            ("Víctima del Conflicto", D['Victima_conflicto'], "#FF0000"),
            ("Pertenencia Étnica", D['Grupo_etnico'], "#70AD47"),
            ("Pueblo Indígena", D['Indigena_flag'], "#FFC000")]):
        col.markdown(create_metric_card(etq, int(m.sum()), f" ({m.mean()*100:.0f}%)", color=color), unsafe_allow_html=True)

    cat = {'Víctima de desplazamiento': si(D['Victima desplazado']), 'Afrocolombiano': si(D['Afrocolombiano']),
           'Indígena': D['Indigena_flag'], 'Otra comunidad negra': si(D['Otra comunidad negra']),
           'Campesinado': si(D['Campesinado']), 'Raizal': si(D['Raizal']), 'ROM': si(D['ROM']),
           'Palenquero': si(D['Palenquero']), 'Víctima ACR': si(D['Victima ACR'])}
    filas = []
    for nombre, m in cat.items():
        n, alto, idx = kpi_riesgo(m)
        filas.append({'Grupo': nombre, 'Estudiantes': n, '% del total': round(n / len(D) * 100, 1),
                      'Índice promedio': round(idx, 3), 'En riesgo alto/crítico': int(alto)})
    gdf = pd.DataFrame(filas).sort_values('Estudiantes', ascending=False)
    sin = kpi_riesgo(~D['Grupo_poblacional'])
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(gdf.sort_values('Estudiantes'), x='Estudiantes', y='Grupo', orientation='h', color='Índice promedio',
                     color_continuous_scale='Reds', template='plotly_dark', title='<b>Estudiantes por grupo poblacional</b>')
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        comp = pd.DataFrame({'Condición': ['Con algún grupo poblacional', 'Sin grupo poblacional'],
                             'Índice promedio': [D[D['Grupo_poblacional']]['ÍNDICE_TOTAL'].mean(), sin[2]]})
        fig = px.bar(comp, x='Condición', y='Índice promedio', text=comp['Índice promedio'].round(3), template='plotly_dark',
                     title='<b>Índice promedio con y sin grupo poblacional</b>', color='Condición')
        fig.update_layout(showlegend=False, height=420)
        st.plotly_chart(fig, use_container_width=True)
    st.caption("Un estudiante puede pertenecer a varios grupos; las categorías no suman 100%. Pertenecer a un grupo es componente del índice (dimensión de inclusión).")
    st.dataframe(gdf, use_container_width=True, hide_index=True)

    pueblos = D.loc[D['Indigena_flag'], 'Indigena'].value_counts().reset_index()
    pueblos.columns = ['Pueblo indígena', 'Estudiantes']
    st.markdown("**Pueblos indígenas declarados**")
    st.dataframe(pueblos, use_container_width=True, hide_index=True)

# TAB 9: DISCAPACIDAD
with tab9:
    st.markdown("<div class='section-title'>Discapacidad y Ajustes Razonables</div>", unsafe_allow_html=True)
    nd = int(D['Discapacidad'].sum()); na = int(D['Ajustes_razonables'].sum())
    c1, c2, c3 = st.columns(3)
    c1.markdown(create_metric_card("Con Discapacidad Declarada", nd, f" ({nd/len(D)*100:.1f}%)", color="#FFC000"), unsafe_allow_html=True)
    c2.markdown(create_metric_card("Piden Ajustes Razonables", na, f" ({na/len(D)*100:.1f}%)", color="#4472C4"), unsafe_allow_html=True)
    c3.markdown(create_metric_card("Sensorial · Física · Cognitiva",
                                   f"{(D['Sensorial'].fillna('No')!='No').sum()} · {(D['Fisica'].fillna('No')!='No').sum()} · {(D['Cognitiva'].fillna('No')!='No').sum()}",
                                   color="#70AD47"), unsafe_allow_html=True)
    st.warning("Con solo 5 casos no se calculan promedios comparativos: se muestra el detalle caso a caso. "
               "Probable subregistro; se recomienda cruzar con la Oficina de Inclusión.")
    det = D[D['Discapacidad'] | D['Ajustes_razonables']][['Edad', 'Sexo', 'Departamento', 'Zona de residencia', 'Sensorial', 'Fisica',
                                                          'Cognitiva', 'Ajustes razonables', 'ÍNDICE_TOTAL', 'Nivel_Riesgo']].round(3)
    st.dataframe(det, use_container_width=True, hide_index=True)
    aj = D.loc[D['Ajustes_razonables'], 'Ajustes razonables'].value_counts().reset_index()
    aj.columns = ['Ajuste solicitado', 'Estudiantes']
    fig = px.bar(aj, x='Estudiantes', y='Ajuste solicitado', orientation='h', template='plotly_dark', title='<b>Ajustes razonables solicitados</b>')
    st.plotly_chart(fig, use_container_width=True)
