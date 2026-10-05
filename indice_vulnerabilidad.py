"""Cálculo único del índice de vulnerabilidad (misma lógica para Excel, dashboard y Word).

Mantiene las 5 dimensiones y ponderaciones originales (25/20/20/20/15) y enriquece
Socioeconómica (territorio) e Inclusión (grupos poblacionales y discapacidad bien leídos).
"""
import pandas as pd
import numpy as np

GRUPOS = ['Raizal', 'Palenquero', 'Afrocolombiano', 'Otra comunidad negra', 'ROM',
          'Campesinado', 'Victima desplazado', 'Victima ACR']
DISCAP = ['Sensorial', 'Fisica', 'Cognitiva']
# Territorios periféricos / de conflicto (criterio del analista, ajustable)
TERRITORIOS_PRIORITARIOS = ['Choco', 'Cauca', 'Nariño', 'Putumayo', 'Caquetá', 'Guaviare',
                            'Guainí?a', 'La Guajira', 'Vichada', 'Arauca']
FUERA_PAIS = ['Alabama', 'Florida', 'Pichincha', 'Valparaiso']


def si(s):
    return s.fillna('').astype(str).str.strip().eq('Sí')


def contiene(s, txt):
    return s.fillna('').astype(str).str.contains(txt, na=False)


def cargar(path='df_clean.csv'):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df['Indigena_flag'] = ~df['Indigena'].fillna('Ninguno').isin(['Ninguno', 'No'])
    df['Grupo_etnico'] = (si(df['Raizal']) | si(df['Palenquero']) | si(df['Afrocolombiano']) |
                          si(df['Otra comunidad negra']) | si(df['ROM']) | df['Indigena_flag'])
    df['Victima_conflicto'] = si(df['Victima desplazado']) | si(df['Victima ACR'])
    df['Grupo_poblacional'] = df['Grupo_etnico'] | df['Victima_conflicto'] | si(df['Campesinado'])
    df['Discapacidad'] = False
    for c in DISCAP:
        df['Discapacidad'] |= ~df[c].fillna('No').isin(['No', 'Ninguno'])
    df['Ajustes_razonables'] = ~df['Ajustes razonables'].fillna('Ninguno').isin(['Ninguno', 'No'])
    df['Territorio_prioritario'] = df['Departamento'].isin(TERRITORIOS_PRIORITARIOS)
    df['Sin_respuesta_caracterizacion'] = df['Computador portatil'].isna()
    return df


def indice(df):
    v = pd.DataFrame(index=df.index)
    # Socioeconómica (25%): estrato, zona rural, territorio prioritario
    eco = pd.DataFrame({'estrato': df['Estrato'].isin(['Uno', 'Dos']).astype(float),
                        'zona': (df['Zona de residencia'] == 'Rural').astype(float),
                        'territorio': df['Territorio_prioritario'].astype(float)})
    v['Socioeconomico'] = eco.mean(axis=1) * 0.25
    # Inclusión (20%): grupo poblacional, discapacidad, madre cabeza de hogar
    inc = pd.DataFrame({'grupo': df['Grupo_poblacional'].astype(float),
                        'discap': df['Discapacidad'].astype(float),
                        'madre': si(df['Es usted madre cabeza de hogar']).astype(float)})
    v['Inclusion'] = inc.mean(axis=1) * 0.20
    # Brecha digital (20%): faltante (no respondió) NO suma riesgo; se promedian solo los componentes con dato
    sin_dato_eq = df['Computador portatil'].isna() & df['Computador de escritorio'].isna()
    tiene_eq = si(df['Computador de escritorio']) | si(df['Computador portatil'])
    ic = df['El lugar donde reside cuenta con servicio de Internet']
    dig = pd.DataFrame({'equipo': (~tiene_eq).astype(float).mask(sin_dato_eq),
                        'internet': (~contiene(ic, 'Permanente')).astype(float).mask(ic.isna()),
                        'comp': contiene(df['Competencias digitales'], 'Bajo').astype(float).mask(df['Competencias digitales'].isna())})
    v['Brecha_Digital'] = dig.mean(axis=1).fillna(0) * 0.20
    # Académica (20%)
    tm = df['Con que tiempo cuenta para desarrollar las actividades academicas']
    lb = df['Cual es su situacion laboral actual']
    pr = df['El programa en el que se matriculo representa su primera opcion']
    aca = pd.DataFrame({'tiempo': contiene(tm, '1 a 4').astype(float).mask(tm.isna()),
                        'desempleo': contiene(lb, 'Desempleado').astype(float).mask(lb.isna()),
                        'no_primera': (pr == 'No').astype(float).mask(pr.isna())})
    v['Academica'] = aca.mean(axis=1).fillna(0) * 0.20
    # Competencias (15%)
    cd, lc = df['Competencias digitales'], df['Lectura critica']
    com = pd.DataFrame({'digital': contiene(cd, 'Bajo').astype(float).mask(cd.isna()),
                        'lectura': contiene(lc, 'Bajo').astype(float).mask(lc.isna())})
    v['Competencias'] = com.mean(axis=1).fillna(0) * 0.15
    v['INDICE'] = v.sum(axis=1)
    v['Nivel'] = pd.cut(v['INDICE'], [-1, 0.25, 0.45, 0.65, 2], right=False,
                        labels=['BAJO', 'MEDIO', 'ALTO', 'CRÍTICO']).astype(str)
    return v


if __name__ == '__main__':
    df = cargar()
    v = indice(df)
    print(v['Nivel'].value_counts())
    print(v['INDICE'].describe())
    print('grupo', df.Grupo_poblacional.sum(), 'etnico', df.Grupo_etnico.sum(), 'victima', df.Victima_conflicto.sum(),
          'indig', df.Indigena_flag.sum(), 'discap', df.Discapacidad.sum(), 'ajustes', df.Ajustes_razonables.sum(),
          'terr', df.Territorio_prioritario.sum(), 'sin_resp', df.Sin_respuesta_caracterizacion.sum())
