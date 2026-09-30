import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURACIÓN INICIAL Y ESTILOS (FONDO)
# ==========================================
st.set_page_config(
    page_title="Dashboard Ejecutivo 360° - Inversiones Noble",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Función para convertir la imagen local a base64 para el fondo CSS
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

img_path = "digital-presentation-related-performance-business-using-graph.jpg"
img_base64 = get_base64_of_bin_file(img_path)

# Estilos CSS avanzados con fondo corporativo y contraste optimizado
background_css = f"""
    <style>
        /* Fondo con imagen corporativa y capa oscura translúcida para legibilidad */
        .stApp {{
            background: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.90)), 
                        url("data:image/jpg;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Contenedores y contenedores de pestañas */
        .block-container {{ 
            padding-top: 1rem; 
            padding-bottom: 1rem; 
            max-width: 98%; 
        }}
        
        [data-testid="stMetricValue"] {{ 
            font-size: 1.8rem; 
            color: #ffffff !important;
        }}
        
        .stTabs [data-baseweb="tab-list"] {{ 
            gap: 8px; 
            flex-wrap: wrap; 
            background-color: rgba(30, 41, 59, 0.7);
            padding: 10px;
            border-radius: 10px;
        }}
        
        .stTabs [data-baseweb="tab"] {{ 
            padding-top: 8px; 
            padding-bottom: 8px; 
            color: #f8fafc !important;
            font-weight: 600;
        }}

        /* Tarjetas de resumen acumulado */
        .accumulated-card {{
            background-color: rgba(30, 41, 59, 0.85);
            border-left: 5px solid #3b82f6;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            color: #ffffff;
        }}

        /* Textos principales visibles sobre fondo oscuro */
        h1, h2, h3, h4, h5, h6, p, span, label {{
            color: #f1f5f9 !important;
        }}
    </style>
"""

st.markdown(background_css, unsafe_allow_html=True)

st.title("📊 Panel de Control Comercial: Portafolio 360° + Crecimiento YoY")
st.markdown("**Inversiones Noble S.A.C.** | Gestión Comercial y Seguimiento de Fuerza de Ventas")

PASSWORD_JEFE = "admin2026"
ARCHIVO_CUOTAS = "cuotas_config.csv"

# ==========================================
# 2. MOTOR INTELIGENTE DE DATOS
# ==========================================
@st.cache_data(show_spinner="Analizando base de datos comercial a alta velocidad...")
def load_all_data():
    def find_and_read(base_name):
        for ext in ['.csv', '.xlsx', '.xls']:
            fname = f"{base_name}{ext}"
            if os.path.exists(fname):
                if ext == '.csv':
                    for sep in [';', ',']:
                        for enc in ['utf-8-sig', 'latin-1']:
                            try:
                                df = pd.read_csv(fname, sep=sep, encoding=enc, low_memory=False)
                                if not df.empty and len(df.columns) > 1: return df
                            except Exception: pass
                else:
                    try:
                        xls = pd.ExcelFile(fname)
                        sheet = 'Ventas' if 'Ventas' in xls.sheet_names else xls.sheet_names[0]
                        return pd.read_excel(fname, sheet_name=sheet)
                    except Exception: pass
        return pd.DataFrame()

    def to_num(series):
        if series is None: return 0.0
        if series.dtype == object:
            series = series.astype(str).str.replace(' ', '').str.replace(',', '.')
        return pd.to_numeric(series, errors='coerce').fillna(0.0)

    df_m = find_and_read("BACKUS MAESTRO DE CLIENTESset")
    if df_m.empty: df_m = find_and_read("BACKUS MAESTRO DE CLIENTES")
    if df_m.empty: return None, "⚠️ No se encontró el Maestro de Clientes en la carpeta."

    df_m = df_m.loc[:, ~df_m.columns.duplicated()]
    df_m.columns = [str(c).replace('﻿', '').strip() for c in df_m.columns]
    
    col_zona_m = next((c for c in df_m.columns if 'ZONA VENDEDOR' in c.upper() or 'ZONA' in c.upper()), 'Zona Vendedor')
    col_codzona_m = next((c for c in df_m.columns if 'CODIGO ZONA' in c.upper() or 'COD ZONA' in c.upper()), 'Codigo Zona')
    col_cli_m = next((c for c in df_m.columns if 'CLIENTE' in c.upper() or 'RAZON' in c.upper()), 'Cliente')

    df_m['Codigo Zona'] = df_m[col_codzona_m].fillna('').astype(str).str.strip().str.upper()
    df_m['Zona Vendedor'] = df_m[col_zona_m].fillna('').astype(str).str.strip().str.upper()
    df_m['Cliente_ID'] = df_m[col_cli_m].fillna('').astype(str).str.strip().str.upper()
    
    mapping_bdr = df_m[['Codigo Zona', 'Zona Vendedor']].drop_duplicates().set_index('Codigo Zona')['Zona Vendedor'].to_dict()

    df_act_raw = find_and_read("EXPORTAR VENTAS BACKUS POR RANGO DE FECHAS29")
    if df_act_raw.empty: df_act_raw = find_and_read("VENTAS")
    if df_act_raw.empty: return None, "⚠️️ Falta el archivo de ventas actual."

    df_25_raw = find_and_read("HISTORIAL 2025")
    df_26_raw = find_and_read("HISTO26")

    zona_to_sucursal = {}
    if not df_act_raw.empty:
        df_act_raw.columns = [str(c).replace('﻿', '').strip() for c in df_act_raw.columns]
        if 'Cod Zona Venta' in df_act_raw.columns and 'Sucursal' in df_act_raw.columns:
            tmp_map = df_act_raw[['Cod Zona Venta', 'Sucursal']].dropna()
            tmp_map['Cod Zona Venta'] = tmp_map['Cod Zona Venta'].astype(str).str.strip().str.upper()
            tmp_map['Sucursal'] = tmp_map['Sucursal'].astype(str).str.strip().str.upper()
            zona_to_sucursal = tmp_map.drop_duplicates().set_index('Cod Zona Venta')['Sucursal'].to_dict()

    def clean_columns(df):
        if df.empty: return df
        df = df.loc[:, ~df.columns.duplicated()]
        df.columns = [str(c).replace('﻿', '').strip() for c in df.columns]
        
        col_map = {}
        for col in df.columns:
            u = col.upper()
            if 'SUBCAT' in u and 'SubCategoria' not in col_map.values(): col_map['SubCategoria'] = col
            elif 'MARCA' in u and 'Marca' not in col_map.values(): col_map['Marca'] = col
            elif ('DESCRIP' in u or 'PRODUCTO' in u) and 'DescripcionProducto' not in col_map.values(): col_map['DescripcionProducto'] = col
            elif 'CANAL' in u and 'Canal' not in col_map.values(): col_map['Canal'] = col
            elif ('ZONA VENTA' in u or 'COD ZONA' in u) and 'Cod Zona Venta' not in col_map.values(): col_map['Cod Zona Venta'] = col
            elif ('COD PROD' in u or 'CODIGO PRODUCTO' in u) and 'CodigoProducto' not in col_map.values(): col_map['CodigoProducto'] = col
            elif ('COD CLI' in u or 'CODIGO CLIENTE' in u) and 'CodigoCliente' not in col_map.values(): col_map['CodigoCliente'] = col
            elif ('MONTO' in u or 'VENTA' in u) and 'Item Monto' not in col_map.values(): col_map['Item Monto'] = col
            elif 'CAJA' in u and 'CajasConvertidas' not in col_map.values(): col_map['CajasConvertidas'] = col
            elif 'FECHA' in u and 'Fecha' not in col_map.values(): col_map['Fecha'] = col
            elif 'ESTADO' in u and 'Estado' not in col_map.values(): col_map['Estado'] = col
            elif 'SUCURSAL' in u and 'Sucursal' not in col_map.values(): col_map['Sucursal'] = col
            elif 'BDR' in u and 'bdr' not in col_map.values(): col_map['bdr'] = col

        df = df.rename(columns={v: k for k, v in col_map.items()})

        for c in ['SubCategoria', 'Marca', 'DescripcionProducto', 'Canal', 'Cod Zona Venta', 'CodigoCliente', 'Estado', 'Sucursal']:
            if c in df.columns:
                if isinstance(df[c], pd.DataFrame): df[c] = df[c].iloc[:, 0]
                df[c] = df[c].fillna('').astype(str).str.strip().str.upper()
            else: df[c] = ''
                
        if 'Item Monto' in df.columns:
            if isinstance(df['Item Monto'], pd.DataFrame): df['Item Monto'] = df['Item Monto'].iloc[:, 0]
            df['Item Monto_num'] = to_num(df['Item Monto'])
            df['Venta_Soles_Sin_IGV'] = df['Item Monto_num'] / 1.18
        else: df['Venta_Soles_Sin_IGV'] = 0
        
        if 'CajasConvertidas' in df.columns:
            if isinstance(df['CajasConvertidas'], pd.DataFrame): df['CajasConvertidas'] = df['CajasConvertidas'].iloc[:, 0]
            df['CajasConvertidas'] = to_num(df['CajasConvertidas'])
        else: df['CajasConvertidas'] = 0
            
        if 'Fecha' in df.columns:
            if isinstance(df['Fecha'], pd.DataFrame): df['Fecha'] = df['Fecha'].iloc[:, 0]
            dt = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True)
            df['Mes'] = dt.dt.month.fillna(9).astype(int)
            df['Anio'] = dt.dt.year.fillna(2026).astype(int)
        else:
            df['Mes'] = 9
            df['Anio'] = 2026

        if 'Estado' in df.columns and (df['Estado'] != '').any():
            df = df[df['Estado'] == 'EMITIDO']
            
        return df

    df_act_raw = clean_columns(df_act_raw)
    df_25_raw = clean_columns(df_25_raw)
    df_26_raw = clean_columns(df_26_raw)

    for d in [df_act_raw, df_25_raw, df_26_raw]:
        if not d.empty:
            if 'bdr' not in d.columns or d['bdr'].astype(str).str.strip().eq('').all():
                d['bdr'] = d['Cod Zona Venta'].map(mapping_bdr).fillna(d['Cod Zona Venta'])
            d['bdr'] = d['bdr'].fillna('').astype(str).str.strip().str.upper()
            
            mask_sin_bdr = ~d['bdr'].str.startswith('PE')
            if mask_sin_bdr.any():
                d.loc[mask_sin_bdr, 'bdr'] = d.loc[mask_sin_bdr, 'Cod Zona Venta'].map(mapping_bdr).fillna('PE07001')

            if 'Sucursal' not in d.columns or d['Sucursal'].astype(str).str.strip().eq('').all():
                d['Sucursal'] = d['Cod Zona Venta'].map(zona_to_sucursal).fillna('GENERAL')

    def aplicar_reglas(df):
        if df.empty:
            empty_dict = {}
            for k in ['BM', 'PREM', 'SS', 'NABS', 'MKTP', 'INN', 'CERV']:
                empty_dict[k] = pd.DataFrame(columns=['SubCategoria', 'Marca', 'DescripcionProducto', 'Canal', 'bdr', 'Cod Zona Venta', 'CodigoProducto', 'CodigoCliente', 'CajasConvertidas', 'Venta_Soles_Sin_IGV'])
            return empty_dict
            
        cond_cerv = df['SubCategoria'].str.contains('CERVEZA', case=False, na=False)
        cond_prem = (
            df['Marca'].str.contains('CUSQUEÑA|CORONA|BUDWEISER|STELLA ARTOIS', case=False, na=False) |
            df['DescripcionProducto'].str.contains('CUSQUEÑA|CORONA|BUDWEISER|STELLA ARTOIS', case=False, na=False)
        )
        ss_mar = ['PILSEN CALLAO', 'CUSQUEÑA', 'CRISTAL', 'GOLDEN']
        cond_ss = (
            df['Marca'].str.contains('|'.join(ss_mar), case=False, na=False) & 
            df['DescripcionProducto'].str.contains('3\\d{2}ML|4\\d{2}ML|LATA|CAN|SLEEK', regex=True, na=False)
        ) | df['Marca'].str.contains('BUDWEISER|CORONA|MIKES', case=False, na=False)

        return {
            'BM':   df[cond_cerv | df['Marca'].str.contains('MIKES|MIKE´S|MIKE\'S', case=False, na=False)],
            'PREM': df[cond_prem],
            'SS':   df[cond_ss],
            'NABS': df[df['Marca'].str.contains('GUARANÁ|GUARANA|VIVA|CRISTALINA', regex=True, case=False)],
            'MKTP': df[df['SubCategoria'].str.contains('MARKET PLACE', case=False, na=False)],
            'INN':  df[df['DescripcionProducto'].str.contains('FRESH|CORONA CERO|CERO TRIGO|FLYING|TRIGO CERO', case=False, na=False)],
            'CERV': df[cond_cerv]
        }

    bdrs_encontrados = sorted([b for b in df_act_raw['bdr'].unique() if str(b).startswith('PE')])
    if not bdrs_encontrados:
        bdrs_encontrados = [f"PE070{str(i).zfill(2)}" for i in range(1, 13)]

    return {
        'maestro': df_m, 
        'act': aplicar_reglas(df_act_raw), 
        'raw_act': df_act_raw,
        'raw_25': df_25_raw, 
        'raw_26': df_26_raw,
        'bdr_unicos': bdrs_encontrados
    }, None

datos_cacheados, error_msg = load_all_data()
if error_msg: st.error(error_msg); st.stop()

df_maestro = datos_cacheados['maestro']
dfs_act = datos_cacheados['act']
raw_act = datos_cacheados['raw_act']
raw_25 = datos_cacheados['raw_25']
raw_26 = datos_cacheados['raw_26']
bdrs_unicos = datos_cacheados['bdr_unicos']

# ==========================================
# 3. CONFIGURACIONES Y CUOTAS
# ==========================================
portafolios = {
    'BM':   {'name': "Beer + Mike's", 'col': 'CajasConvertidas', 'lbl': 'Cajas', 'fmt': '{:,.2f}', 'dis_col': 'CodigoProducto'},
    'PREM': {'name': "Premium", 'col': 'CajasConvertidas', 'lbl': 'Cajas', 'fmt': '{:,.2f}', 'dis_col': 'CodigoProducto'},
    'SS':   {'name': "Single Serve", 'col': 'CajasConvertidas', 'lbl': 'Cajas', 'fmt': '{:,.2f}', 'dis_col': 'CodigoProducto'},
    'NABS': {'name': "NABS", 'col': 'CajasConvertidas', 'lbl': 'Cajas', 'fmt': '{:,.2f}', 'dis_col': 'CodigoProducto'},
    'MKTP': {'name': "MarketPlace", 'col': 'Venta_Soles_Sin_IGV', 'lbl': 'Soles', 'fmt': 'S/ {:,.2f}', 'dis_col': 'CodigoProducto'},
    'INN':  {'name': "Innovaciones", 'col': 'CajasConvertidas', 'lbl': 'Cajas', 'fmt': '{:,.2f}', 'dis_col': 'Marca'}
}
coberturas = {'CERV': {'name': "Cerveza Total"}, 'NABS': {'name': "NABS"}, 'INN': {'name': "Innovaciones"}, 'MKTP': {'name': "MarketPlace"}}
zonas_hn01 = [b for b in bdrs_unicos if b in ['PE07001', 'PE07002', 'PE07003', 'PE07004', 'PE07005', 'PE07006', 'PE07007']]
zonas_ab01 = [b for b in bdrs_unicos if b in ['PE07008', 'PE07009', 'PE07010', 'PE07011', 'PE07012']]
if not zonas_hn01: zonas_hn01 = bdrs_unicos[:7]
if not zonas_ab01: zonas_ab01 = bdrs_unicos[7:]

if os.path.exists(ARCHIVO_CUOTAS):
    df_cuotas_orig = pd.read_csv(ARCHIVO_CUOTAS)
else:
    df_cuotas_orig = pd.DataFrame({
        'bdr': bdrs_unicos,
        'Cuota Mensual (Cajas)': [10000.0] * len(bdrs_unicos),
        'Meta Distro (Impactos)': [500.0] * len(bdrs_unicos),
        'Meta Innovacion (Impactos)': [89.0] * len(bdrs_unicos),
        'Dias_Pendientes': [1] * len(bdrs_unicos),
        'Dias_Transcurridos': [24] * len(bdrs_unicos)
    })

if 'df_cuotas' not in st.session_state: 
    st.session_state.df_cuotas = df_cuotas_orig

d_trans = int(st.session_state.df_cuotas['Dias_Transcurridos'].iloc[0] if 'Dias_Transcurridos' in st.session_state.df_cuotas.columns else 24)
d_pend = int(st.session_state.df_cuotas['Dias_Pendientes'].iloc[0] if 'Dias_Pendientes' in st.session_state.df_cuotas.columns else 1)

# ==========================================
# 4. CÁLCULO MAESTRO Y FÓRMULAS COMERCIALES
# ==========================================
def calcular_fila(nombre, lista_zonas, agrupa=False):
    r = {'bdr': nombre, 'Es_Agrupacion': agrupa}
    cuotas_sub = st.session_state.df_cuotas[st.session_state.df_cuotas['bdr'].isin(lista_zonas)]
    r['Universo_Cob'] = df_maestro[df_maestro['Zona Vendedor'].isin(lista_zonas)]['Cliente_ID'].nunique()
    
    for p, cfg in portafolios.items():
        s_act = dfs_act[p][dfs_act[p]['bdr'].isin(lista_zonas)]
        r[f'Av Vol {p}'] = s_act[cfg['col']].sum()
        r[f'Av Dis {p}'] = s_act[s_act['Canal'].str.contains('TRADICIONAL', na=False)][['CodigoCliente', cfg['dis_col']]].drop_duplicates().shape[0]
            
        if p == 'BM':
            r[f'Ct Vol {p}'] = cuotas_sub['Cuota Mensual (Cajas)'].sum() if 'Cuota Mensual (Cajas)' in cuotas_sub.columns else cuotas_sub.iloc[:, 1].sum()
        else:
            r[f'Ct Vol {p}'] = cuotas_sub['Cuota Mensual (Cajas)'].sum() * 0.2 if 'Cuota Mensual (Cajas)' in cuotas_sub.columns else 1000
            
        r[f'Mt Dis {p}'] = cuotas_sub['Meta Distro (Impactos)'].sum() if 'Meta Distro (Impactos)' in cuotas_sub.columns else 500
        
    for c in coberturas.keys():
        r[f'Activos Cob {c}'] = dfs_act[c][dfs_act[c]['bdr'].isin(lista_zonas)]['CodigoCliente'].nunique()
    return r

filas = [calcular_fila('NOBLE (TOTAL)', zonas_hn01 + zonas_ab01, True), calcular_fila('HN01', zonas_hn01, True)]
for z in zonas_hn01:
    if z in bdrs_unicos: filas.append(calcular_fila(z, [z]))
filas.append(calcular_fila('AB01', zonas_ab01, True))
for z in zonas_ab01:
    if z in bdrs_unicos: filas.append(calcular_fila(z, [z]))

rpt = pd.DataFrame(filas).fillna(0)

for p in portafolios.keys():
    for met in ['Vol', 'Dis']:
        av = f'Av {met} {p}'
        me = f'Ct Vol {p}' if met == 'Vol' else f'Mt Dis {p}'
        rpt[f'% Av {met} {p}'] = np.where(rpt[me] > 0, (rpt[av] / rpt[me]) * 100, 0)
        prom = rpt[av] / d_trans if d_trans > 0 else 0
        rpt[f'Proy {met} {p}'] = rpt[av] + (prom * d_pend)
        rpt[f'% Proy {met} {p}'] = np.where(rpt[me] > 0, (rpt[f'Proy {met} {p}'] / rpt[me]) * 100, 0)
        rpt[f'Falt {met} {p}'] = (rpt[me] - rpt[av]).clip(lower=0)

for c in coberturas.keys():
    rpt[f'% Prod Cob {c}'] = np.where(rpt['Universo_Cob'] > 0, (rpt[f'Activos Cob {c}'] / rpt['Universo_Cob']) * 100, 0)
    rpt[f'Faltante Cob {c}'] = (rpt['Universo_Cob'] - rpt[f'Activos Cob {c}']).clip(lower=0)

rpt = rpt.fillna(0)
dat_nob = rpt[rpt['bdr'] == 'NOBLE (TOTAL)'].iloc[0] if not rpt[rpt['bdr'] == 'NOBLE (TOTAL)'].empty else rpt.iloc[0]

# Colores clásicos: Verde (#4caf50), Amarillo (#ffe680), Rojo (#ff4d4d) con texto negro
def cls(x): return 'background-color:#ff4d4d;color:black;' if x < 85 else ('background-color:#ffe680;color:black;' if x < 100 else 'background-color:#4caf50;color:black;')

def pintar_kpi(row, col_pct1, col_pct2=None):
    c1 = '#ff4d4d' if row[col_pct1] < 85 else ('#ffe680' if row[col_pct1] < 100 else '#4caf50')
    c2 = '#ff4d4d' if col_pct2 and row[col_pct2] < 85 else ('#ffe680' if col_pct2 and row[col_pct2] < 100 else '#4caf50')
    est = []
    for col in row.index:
        cel = 'background-color: #FFFF00; font-weight: bold; color: black;' if row['Es_Agrupacion'] else ''
        if col == col_pct1: cel = f'background-color: {c1}; font-weight: bold; color: black; text-align: center;'
        if col_pct2 and col == col_pct2: cel = f'background-color: {c2}; font-weight: bold; color: black; text-align: center;'
        est.append(cel)
    return est

# ==========================================
# 5. INTERFAZ Y PESTAÑAS DEL DASHBOARD
# ==========================================
tabs = st.tabs(["🌐 Resumen 360°"] + [f"📊 {p['name']}" for p in portafolios.values()] + ["🌍 Productividad Neta", "🔒 Configuración y Cuotas"])

# --- TAB 0: RESUMEN 360° Y TENDENCIA YoY ---
with tabs[0]:
    st.header("Visión General Ejecutiva: INVERSIONES NOBLE S.A.C.")
    st.markdown(f"**Días Transcurridos:** {d_trans} | **Días Pendientes:** {d_pend} | **Universo Total de Clientes:** {dat_nob['Universo_Cob']:,.0f} Bodegas")
    
    meses_dict = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    
    max_mes_actual = 9  # Hasta septiembre
    def filtrar_por_portafolio_raw(df, p_key):
        if df.empty: return df
        cond_cerv = df['SubCategoria'].str.contains('CERVEZA', case=False, na=False)
        cond_prem = (
            df['Marca'].str.contains('CUSQUEÑA|CORONA|BUDWEISER|STELLA ARTOIS', case=False, na=False) |
            df['DescripcionProducto'].str.contains('CUSQUEÑA|CORONA|BUDWEISER|STELLA ARTOIS', case=False, na=False)
        )
        ss_mar = ['PILSEN CALLAO', 'CUSQUEÑA', 'CRISTAL', 'GOLDEN']
        cond_ss = (
            df['Marca'].str.contains('|'.join(ss_mar), case=False, na=False) & 
            df['DescripcionProducto'].str.contains('3\\d{2}ML|4\\d{2}ML|LATA|CAN|SLEEK', regex=True, na=False)
        ) | df['Marca'].str.contains('BUDWEISER|CORONA|MIKES', case=False, na=False)

        if p_key == 'BM': return df[cond_cerv | df['Marca'].str.contains('MIKES|MIKE´S|MIKE\'S', case=False, na=False)]
        elif p_key == 'PREM': return df[cond_prem]
        elif p_key == 'SS': return df[cond_ss]
        elif p_key == 'NABS': return df[df['Marca'].str.contains('GUARANÁ|GUARANA|VIVA|CRISTALINA', regex=True, case=False)]
        elif p_key == 'MKTP': return df[df['SubCategoria'].str.contains('MARKET PLACE', case=False, na=False)]
        else: return df[df['DescripcionProducto'].str.contains('FRESH|CORONA CERO|CERO TRIGO|FLYING|TRIGO CERO', case=False, na=False)]

    raw_26_full = pd.concat([raw_26, raw_act], ignore_index=True) if not raw_act.empty else raw_26
    
    f25_bm_ytd = filtrar_por_portafolio_raw(raw_25, 'BM')
    f25_bm_ytd = f25_bm_ytd[(f25_bm_ytd['Mes'] <= max_mes_actual) & (f25_bm_ytd['bdr'].isin(zonas_hn01 + zonas_ab01))]['CajasConvertidas'].sum()
    
    f26_bm_ytd = filtrar_por_portafolio_raw(raw_26_full, 'BM')
    f26_bm_ytd = f26_bm_ytd[(f26_bm_ytd['Mes'] <= max_mes_actual) & (f26_bm_ytd['bdr'].isin(zonas_hn01 + zonas_ab01))]['CajasConvertidas'].sum()
    
    crec_bm_ytd = ((f26_bm_ytd / f25_bm_ytd) - 1) * 100 if f25_bm_ytd > 0 else 0

    st.markdown(f"""
        <div class="accumulated-card">
            <h4>📈 Crecimiento Acumulado YTD (Enero - Septiembre 2025 vs 2026)</h4>
            <p><b>Beer + Mike's:</b> 2025: {f25_bm_ytd:,.2f} cjs | 2026: {f26_bm_ytd:,.2f} cjs | <b>Crecimiento Acumulado: <span style="color: {'#4ade80' if crec_bm_ytd >= 0 else '#f87171'};">{crec_bm_ytd:+.2f}%</span></b></p>
        </div>
    """, unsafe_allow_html=True)

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        sel_port = st.selectbox("🎯 Portafolio / SKU para Curva Anual:", list(portafolios.keys()), format_func=lambda x: portafolios[x]['name'])
    with col_sel2:
        mes_seleccionado = st.selectbox("📅 Seleccionar Mes para Comparativa YoY (Mes vs Mes):", list(meses_dict.keys()), format_func=lambda x: meses_dict[x], index=8)

    regla_cfg = portafolios[sel_port]
    c_val = regla_cfg['col']

    f25_tot = filtrar_por_portafolio_raw(raw_25, sel_port)
    f26_tot = filtrar_por_portafolio_raw(raw_26_full, sel_port)
    
    curva_25_sku = f25_tot[f25_tot['bdr'].isin(zonas_hn01 + zonas_ab01)].groupby('Mes')[c_val].sum() if not f25_tot.empty else pd.Series(dtype=float)
    curva_26_sku = f26_tot[f26_tot['bdr'].isin(zonas_hn01 + zonas_ab01)].groupby('Mes')[c_val].sum() if not f26_tot.empty else pd.Series(dtype=float)

    fig = go.Figure()
    meses_nombres = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    if not curva_25_sku.empty: fig.add_trace(go.Scatter(x=curva_25_sku.index, y=curva_25_sku.values, mode='lines+markers', name='2025', line=dict(color='#94a3b8', width=3, shape='spline')))
    if not curva_26_sku.empty: fig.add_trace(go.Scatter(x=curva_26_sku.index, y=curva_26_sku.values, mode='lines+markers', name='2026', line=dict(color='#3b82f6', width=4, shape='spline')))
    fig.update_layout(
        title=f"📈 Tendencia Anual YoY - {portafolios[sel_port]['name']}", 
        xaxis_title="", 
        yaxis_title=portafolios[sel_port]['lbl'], 
        hovermode="x unified", 
        height=300, 
        margin=dict(t=30, b=10, l=10, r=10),
        paper_bgcolor='rgba(30,41,59,0.7)',
        plot_bgcolor='rgba(15,23,42,0.6)',
        font=dict(color='#f8fafc')
    )
    fig.update_xaxes(tickvals=list(range(1, 13)), ticktext=meses_nombres, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"📦 Volumen / Facturación ({meses_dict[mes_seleccionado]} 2025 vs 2026)")
        d_vol = []
        for k, v in portafolios.items():
            f_p25 = filtrar_por_portafolio_raw(raw_25, k)
            f_p26 = filtrar_por_portafolio_raw(raw_26_full, k)
            
            val_25 = f_p25[(f_p25['Mes'] == mes_seleccionado) & (f_p25['bdr'].isin(zonas_hn01 + zonas_ab01))][v['col']].sum() if not f_p25.empty else 0
            val_26 = f_p26[(f_p26['Mes'] == mes_seleccionado) & (f_p26['bdr'].isin(zonas_hn01 + zonas_ab01))][v['col']].sum() if not f_p26.empty else 0
            
            crec_yoy = ((val_26 / val_25) - 1) * 100 if val_25 > 0 else 0
            d_vol.append({
                'Portafolio': v['name'], f'{meses_dict[mes_seleccionado]} 2025': val_25, f'{meses_dict[mes_seleccionado]} 2026': val_26,
                'Crec YoY (%)': crec_yoy, 'Meta': dat_nob[f'Ct Vol {k}'], '% Avance': dat_nob[f'% Av Vol {k}']
            })
        st.dataframe(pd.DataFrame(d_vol).style.apply(lambda r: [cls(x) if i in [3, 5] else ('color: #15803d; font-weight: bold;' if i==3 and x>0 else 'color: #b91c1c; font-weight: bold;' if i==3 else '') for i, x in enumerate(r)], axis=1)\
            .format({f'{meses_dict[mes_seleccionado]} 2025': '{:,.2f}', f'{meses_dict[mes_seleccionado]} 2026': '{:,.2f}', 'Crec YoY (%)': '{:.2f}%', 'Meta': '{:,.2f}', '% Avance': '{:.2f}%'}), use_container_width=True, hide_index=True)
        
        st.subheader("🌍 Productividad de Clientes (Cobertura)")
        d_cob = [{'Categoría': v['name'], 'Universo Base': dat_nob['Universo_Cob'], 'Clientes con Compra': dat_nob[f'Activos Cob {k}'], '% Productividad': dat_nob[f'% Prod Cob {k}'], 'Faltantes': dat_nob[f'Faltante Cob {k}']} for k, v in coberturas.items()]
        st.dataframe(pd.DataFrame(d_cob).style.format({'Universo Base': '{:,.0f}', 'Clientes con Compra': '{:,.0f}', '% Productividad': '{:.2f}%', 'Faltantes': '{:,.0f}'}), use_container_width=True, hide_index=True)

    with c2:
        st.subheader(f"🎯 BrandDistro ({meses_dict[mes_seleccionado]} 2025 vs 2026)")
        d_dis = []
        for k, v in portafolios.items():
            f_p25 = filtrar_por_portafolio_raw(raw_25, k)
            f_p26 = filtrar_por_portafolio_raw(raw_26_full, k)
            
            s25_m = f_p25[(f_p25['Mes'] == mes_seleccionado) & (f_p25['bdr'].isin(zonas_hn01 + zonas_ab01))] if not f_p25.empty else pd.DataFrame()
            s26_m = f_p26[(f_p26['Mes'] == mes_seleccionado) & (f_p26['bdr'].isin(zonas_hn01 + zonas_ab01))] if not f_p26.empty else pd.DataFrame()
            
            d25_val = s25_m[s25_m['Canal'].str.contains('TRADICIONAL', na=False)][['CodigoCliente', v['dis_col']]].drop_duplicates().shape[0] if not s25_m.empty else 0
            d26_val = s26_m[s26_m['Canal'].str.contains('TRADICIONAL', na=False)][['CodigoCliente', v['dis_col']]].drop_duplicates().shape[0] if not s26_m.empty else 0
            
            crec_dis = ((d26_val / d25_val) - 1) * 100 if d25_val > 0 else 0
            d_dis.append({
                'Portafolio': v['name'], f'Imp {meses_dict[mes_seleccionado]} 25': d25_val, f'Imp {meses_dict[mes_seleccionado]} 26': d26_val, 'Crec YoY (%)': crec_dis,
                'Meta Imp': dat_nob[f'Mt Dis {k}'], '% Avance': dat_nob[f'% Av Dis {k}']
            })
        st.dataframe(pd.DataFrame(d_dis).style.apply(lambda r: [cls(x) if i in [3, 5] else ('color: #15803d; font-weight: bold;' if i==3 and x>0 else 'color: #b91c1c; font-weight: bold;' if i==3 else '') for i, x in enumerate(r)], axis=1)\
            .format({f'Imp {meses_dict[mes_seleccionado]} 25': '{:,.0f}', f'Imp {meses_dict[mes_seleccionado]} 26': '{:,.0f}', 'Crec YoY (%)': '{:.2f}%', 'Meta Imp': '{:,.0f}', '% Avance': '{:.2f}%'}), use_container_width=True, hide_index=True)

# --- TABS PORTAFOLIOS DETALLADOS ---
for i, (p_key, p_data) in enumerate(portafolios.items()):
    with tabs[i+1]:
        st.subheader(f"Desempeño Operativo: {p_data['name']}")
        metrica = st.radio(f"Ver ({p_data['name']}):", [f"📦 Volumen", "🎯 BrandDistro"], horizontal=True, key=f"rad_{p_key}")
        m = 'Vol' if "Volumen" in metrica else 'Dis'
        av_col, me_col = f'Av {m} {p_key}', (f'Ct Vol {p_key}' if m == 'Vol' else f'Mt Dis {p_key}')
        
        c_vis = ['bdr', me_col, av_col, f'% Av {m} {p_key}', f'Proy {m} {p_key}', f'% Proy {m} {p_key}', f'Falt {m} {p_key}', 'Es_Agrupacion']
        fmt = p_data['fmt'] if m == 'Vol' else '{:,.0f}'
        formato = {c: fmt for c in c_vis if c not in ['bdr', f'% Av {m} {p_key}', f'% Proy {m} {p_key}', 'Es_Agrupacion']}
        formato.update({f'% Av {m} {p_key}': '{:.2f}%', f'% Proy {m} {p_key}': '{:.2f}%'})
        
        st.dataframe(rpt[c_vis].style.apply(lambda r: pintar_kpi(r, f'% Av {m} {p_key}', f'% Proy {m} {p_key}'), axis=1).format(formato).hide(subset=['Es_Agrupacion'], axis='columns').hide(axis='index'), use_container_width=True, height=580)

# --- TAB PRODUCTIVIDAD NETA ---
with tabs[-2]:
    st.subheader("Productividad Real de Clientes (Cobertura por Zona)")
    cob_sel = st.radio("Categoría:", list(coberturas.keys()), format_func=lambda x: coberturas[x]['name'], horizontal=True)
    c_vis = ['bdr', 'Universo_Cob', f'Activos Cob {cob_sel}', f'% Prod Cob {cob_sel}', f'Faltante Cob {cob_sel}', 'Es_Agrupacion']
    formato_c = {'Universo_Cob': '{:,.0f}', f'Activos Cob {cob_sel}': '{:,.0f}', f'Faltante Cob {cob_sel}': '{:,.0f}', f'% Prod Cob {cob_sel}': '{:.2f}%'}
    st.dataframe(rpt[c_vis].style.apply(lambda r: pintar_kpi(r, f'% Prod Cob {cob_sel}'), axis=1).format(formato_c).hide(subset=['Es_Agrupacion'], axis='columns').hide(axis='index'), use_container_width=True, height=580)

# --- TAB ADMINISTRACIÓN Y CUOTAS ---
with tabs[-1]:
    st.subheader("🔒 Panel de Administración y Configuración de Cuotas")
    password_ingresada = st.text_input("Ingrese contraseña de Jefe Comercial:", type="password")
    if password_ingresada == PASSWORD_JEFE:
        st.success("Acceso autorizado.")
        c1, c2 = st.columns(2)
        n_t = c1.number_input("Días trabajados en el mes:", min_value=1, value=d_trans)
        n_p = c2.number_input("Días pendientes para el cierre:", min_value=1, value=d_pend)
        
        st.markdown("### ✏️ Editor de Cuotas e Impactos por BDR")
        edt = st.data_editor(st.session_state.df_cuotas, use_container_width=True, hide_index=True)
        
        if st.button("💾 Guardar Cambios y Actualizar Tablero"):
            st.session_state.df_cuotas = edt
            if 'Dias_Transcurridos' in st.session_state.df_cuotas.columns:
                st.session_state.df_cuotas['Dias_Transcurridos'] = n_t
            if 'Dias_Pendientes' in st.session_state.df_cuotas.columns:
                st.session_state.df_cuotas['Dias_Pendientes'] = n_p
            st.session_state.df_cuotas.to_csv(ARCHIVO_CUOTAS, index=False)
            st.cache_data.clear()
            st.success("¡Configuración guardada exitosamente! Presiona 'R' o recarga la página para refrescar.")
    elif password_ingresada != "":
        st.error("Contraseña incorrecta.")