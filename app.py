import base64
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN INICIAL Y ESTILOS (FONDO)
# ==========================================
st.set_page_config(
    page_title="Dashboard Ejecutivo 360° - Inversiones Noble",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def get_base64_of_bin_file(bin_file):
  if os.path.exists(bin_file):
    with open(bin_file, "rb") as f:
      data = f.read()
    return base64.b64encode(data).decode()
  return ""

img_path = "digital-presentation-related-performance-business-using-graph.jpg"
img_base64 = get_base64_of_bin_file(img_path)

background_css = f"""
    <style>
        .stApp {{
            background: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.90)), 
                        url("data:image/jpg;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .block-container {{ padding-top: 1rem; padding-bottom: 1rem; max-width: 98%; }}
        [data-testid="stMetricValue"] {{ font-size: 1.8rem; color: #ffffff !important; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; flex-wrap: wrap; background-color: rgba(30, 41, 59, 0.7); padding: 10px; border-radius: 10px; }}
        .stTabs [data-baseweb="tab"] {{ padding-top: 8px; padding-bottom: 8px; color: #f8fafc !important; font-weight: 600; }}
        .accumulated-card {{
            background-color: rgba(30, 41, 59, 0.85);
            border-left: 5px solid #3b82f6;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            color: #ffffff;
        }}
        h1, h2, h3, h4, h5, h6, p, span, label {{ color: #f1f5f9 !important; }}
        
        /* Ajustes para tabla sin scroll horizontal: Títulos angostos */
        table {{ font-size: 11px !important; width: 100% !important; table-layout: fixed; }}
        th {{ text-align: center !important; white-space: pre-wrap !important; line-height: 1.2 !important; padding: 4px !important; }}
        td {{ padding: 4px !important; text-align: center !important; }}
    </style>
"""

st.markdown(background_css, unsafe_allow_html=True)

st.title("📊 Panel de Control Comercial: Portafolio 360° + Crecimiento YoY")
st.markdown("**Inversiones Noble S.A.C.** | Gestión Comercial y Seguimiento de Fuerza de Ventas")

# --- CONTRASENAS DEL SISTEMA ---
PASSWORD_JEFE = "admin2026"
PASSWORD_SV1 = "sv1_2026"    
PASSWORD_SV2 = "sv2_2026"    
ARCHIVO_CUOTAS = "cuotas_config.csv"

# ==========================================
# 2. MOTOR INTELIGENTE DE DATOS
# ==========================================
@st.cache_data(show_spinner="Analizando base de datos comercial a alta velocidad...")
def load_all_data():
  def find_and_read(base_name):
    parquet_map = {
        "BACKUS MAESTRO DE CLIENTESset": "BACKUS_MAESTRO_DE_CLIENTESset.parquet",
        "BACKUS MAESTRO DE CLIENTES": "BACKUS_MAESTRO_DE_CLIENTESset.parquet",
        "EXPORTAR VENTAS BACKUS POR RANGO DE FECHAS29": "EXPORTAR_VENTAS_BACKUS_POR_RANGO_DE_FECHAS29.parquet",
        "VENTAS": "EXPORTAR_VENTAS_BACKUS_POR_RANGO_DE_FECHAS29.parquet",
        "HISTORIAL 2025": "HISTORIAL_2025.parquet",
        "HISTO26": "HISTO26.parquet",
    }
    target_parquet = parquet_map.get(base_name, base_name.replace(" ", "_") + ".parquet")
    if os.path.exists(target_parquet):
      try:
        return pd.read_parquet(target_parquet)
      except Exception:
        pass

    for ext in [".csv", ".xlsx", ".xls"]:
      fname = f"{base_name}{ext}"
      if os.path.exists(fname):
        if ext == ".csv":
          for sep in [";", ","]:
            for enc in ["utf-8-sig", "latin-1"]:
              try:
                df = pd.read_csv(fname, sep=sep, encoding=enc, low_memory=False)
                if not df.empty and len(df.columns) > 1:
                  return df
              except Exception:
                pass
        else:
          try:
            xls = pd.ExcelFile(fname)
            sheet = "Ventas" if "Ventas" in xls.sheet_names else xls.sheet_names[0]
            return pd.read_excel(fname, sheet_name=sheet)
          except Exception:
            pass
    return pd.DataFrame()

  def to_num(series):
    if series is None: return 0.0
    if series.dtype == object: series = series.astype(str).str.replace(" ", "").str.replace(",", ".")
    return pd.to_numeric(series, errors="coerce").fillna(0.0)

  df_m = find_and_read("BACKUS MAESTRO DE CLIENTESset")
  if df_m.empty: df_m = find_and_read("BACKUS MAESTRO DE CLIENTES")
  if df_m.empty: return None, "⚠️ No se encontró el Maestro de Clientes en la carpeta."

  df_m = df_m.loc[:, ~df_m.columns.duplicated()]
  df_m.columns = [str(c).replace("﻿", "").strip() for c in df_m.columns]

  col_zona_m = next((c for c in df_m.columns if "ZONA VENDEDOR" in c.upper() or "ZONA" in c.upper()), "Zona Vendedor")
  col_codzona_m = next((c for c in df_m.columns if "CODIGO ZONA" in c.upper() or "COD ZONA" in c.upper()), "Codigo Zona")
  
  col_cli_m = None
  for c in df_m.columns:
      if 'COD' in c.upper() and 'CLI' in c.upper():
          col_cli_m = c
          break
  if not col_cli_m:
      for c in df_m.columns:
          if 'CLIENTE' in c.upper() and 'NOM' not in c.upper() and 'RAZ' not in c.upper():
              col_cli_m = c
              break
  if not col_cli_m: col_cli_m = df_m.columns[0]

  df_m["Codigo Zona"] = df_m[col_codzona_m].fillna("").astype(str).str.strip().str.upper()
  df_m["Zona Vendedor"] = df_m[col_zona_m].fillna("").astype(str).str.strip().str.upper()
  df_m["Cliente_ID"] = df_m[col_cli_m].fillna("").astype(str).str.replace(r'\.0+$', '', regex=True).str.strip().str.upper()

  mapping_bdr = df_m[["Codigo Zona", "Zona Vendedor"]].drop_duplicates().set_index("Codigo Zona")["Zona Vendedor"].to_dict()

  df_act_raw = find_and_read("EXPORTAR VENTAS BACKUS POR RANGO DE FECHAS29")
  if df_act_raw.empty: df_act_raw = find_and_read("VENTAS")
  if df_act_raw.empty: return None, "⚠️ Falta el archivo de ventas actual."

  df_25_raw = find_and_read("HISTORIAL 2025")
  df_26_raw = find_and_read("HISTO26")

  file_preventa = "DIMANICA - DETALLE DE VENTAS (SOBRE PEDIDOS)29.0202.xlsx"
  df_preventa = pd.DataFrame()
  if os.path.exists(file_preventa):
    try:
      df_preventa = pd.read_excel(file_preventa, sheet_name="vista1")
      df_preventa = df_preventa.dropna(subset=["Sucursal", "ClienteCod"]).copy()
      df_preventa["VendedorNombre"] = df_preventa["VendedorNombre"].fillna("").astype(str).str.strip()
      df_preventa["Sucursal"] = df_preventa["Sucursal"].fillna("").astype(str).str.strip().str.upper()
      df_preventa["Zona"] = df_preventa["Zona"].fillna("").astype(str).str.strip().str.upper()
      df_preventa["ClaseN4"] = df_preventa["ClaseN4"].fillna("").astype(str).str.strip().str.upper()
      df_preventa["PLATAFORMA"] = df_preventa["PLATAFORMA"].fillna("").astype(str).str.strip().str.upper()
      df_preventa["Cantidad"] = pd.to_numeric(df_preventa["Cantidad"], errors="coerce").fillna(0.0)
      df_preventa["Total"] = pd.to_numeric(df_preventa["Total"], errors="coerce").fillna(0.0)
      df_preventa["bdr"] = df_preventa["Zona"].map(mapping_bdr).fillna("PE07001")
    except Exception:
      pass

  zona_to_sucursal = {}
  if not df_act_raw.empty:
    df_act_raw.columns = [str(c).replace("﻿﻿", "").strip() for c in df_act_raw.columns]
    if "Cod Zona Venta" in df_act_raw.columns and "Sucursal" in df_act_raw.columns:
      tmp_map = df_act_raw[["Cod Zona Venta", "Sucursal"]].dropna()
      tmp_map["Cod Zona Venta"] = tmp_map["Cod Zona Venta"].astype(str).str.strip().str.upper()
      tmp_map["Sucursal"] = tmp_map["Sucursal"].astype(str).str.strip().str.upper()
      zona_to_sucursal = tmp_map.drop_duplicates().set_index("Cod Zona Venta")["Sucursal"].to_dict()

  def clean_columns(df):
    if df.empty: return df
    df = df.loc[:, ~df.columns.duplicated()]
    df.columns = [str(c).replace("﻿", "").strip() for c in df.columns]
    col_map = {}
    for col in df.columns:
      u = col.upper()
      if "SUBCAT" in u and "SubCategoria" not in col_map.values(): col_map["SubCategoria"] = col
      elif "MARCA" in u and "Marca" not in col_map.values(): col_map["Marca"] = col
      elif ("DESCRIP" in u or "PRODUCTO" in u) and "DescripcionProducto" not in col_map.values(): col_map["DescripcionProducto"] = col
      elif "CANAL" in u and "Canal" not in col_map.values(): col_map["Canal"] = col
      elif ("ZONA VENTA" in u or "COD ZONA" in u) and "Cod Zona Venta" not in col_map.values(): col_map["Cod Zona Venta"] = col
      elif ("COD PROD" in u or "CODIGO PRODUCTO" in u) and "CodigoProducto" not in col_map.values(): col_map["CodigoProducto"] = col
      elif ("COD CLI" in u or "CODIGO CLIENTE" in u) and "CodigoCliente" not in col_map.values(): col_map["CodigoCliente"] = col
      elif ("MONTO" in u or "VENTA" in u) and "Item Monto" not in col_map.values(): col_map["Item Monto"] = col
      elif "CAJA" in u and "CajasConvertidas" not in col_map.values(): col_map["CajasConvertidas"] = col
      elif "FECHA" in u and "Fecha" not in col_map.values(): col_map["Fecha"] = col
      elif "ESTADO" in u and "Estado" not in col_map.values(): col_map["Estado"] = col
      elif "SUCURSAL" in u and "Sucursal" not in col_map.values(): col_map["Sucursal"] = col
      elif "BDR" in u and "bdr" not in col_map.values(): col_map["bdr"] = col

    df = df.rename(columns={v: k for k, v in col_map.items()})
    for c in ["SubCategoria", "Marca", "DescripcionProducto", "Canal", "Cod Zona Venta", "CodigoCliente", "Estado", "Sucursal"]:
      if c in df.columns:
        if isinstance(df[c], pd.DataFrame): df[c] = df[c].iloc[:, 0]
        df[c] = df[c].fillna("").astype(str).str.strip().str.upper()
      else: df[c] = ""
      
    if "Item Monto" in df.columns:
      if isinstance(df["Item Monto"], pd.DataFrame): df["Item Monto"] = df["Item Monto"].iloc[:, 0]
      df["Item Monto_num"] = to_num(df["Item Monto"])
      df["Venta_Soles_Sin_IGV"] = df["Item Monto_num"] / 1.18
    else: df["Venta_Soles_Sin_IGV"] = 0
    
    if "CajasConvertidas" in df.columns:
      if isinstance(df["CajasConvertidas"], pd.DataFrame): df["CajasConvertidas"] = df["CajasConvertidas"].iloc[:, 0]
      df["CajasConvertidas"] = to_num(df["CajasConvertidas"])
    else: df["CajasConvertidas"] = 0
    
    if "Fecha" in df.columns:
      if isinstance(df["Fecha"], pd.DataFrame): df["Fecha"] = df["Fecha"].iloc[:, 0]
      dt = pd.to_datetime(df["Fecha"], errors="coerce", dayfirst=True)
      df["Mes"] = dt.dt.month.fillna(9).astype(int)
      df["Anio"] = dt.dt.year.fillna(2026).astype(int)
    else:
      df["Mes"] = 9
      df["Anio"] = 2026
      
    if "Estado" in df.columns and (df["Estado"] != "").any():
      df = df[df["Estado"] == "EMITIDO"]
    return df

  df_act_raw = clean_columns(df_act_raw)
  df_25_raw = clean_columns(df_25_raw)
  df_26_raw = clean_columns(df_26_raw)

  for d in [df_act_raw, df_25_raw, df_26_raw]:
    if not d.empty:
      if "bdr" not in d.columns or d["bdr"].astype(str).str.strip().eq("").all():
        d["bdr"] = d["Cod Zona Venta"].map(mapping_bdr).fillna(d["Cod Zona Venta"])
      d["bdr"] = d["bdr"].fillna("").astype(str).str.strip().str.upper()
      mask_sin_bdr = ~d["bdr"].str.startswith("PE")
      if mask_sin_bdr.any():
        d.loc[mask_sin_bdr, "bdr"] = d.loc[mask_sin_bdr, "Cod Zona Venta"].map(mapping_bdr).fillna("PE07001")
      if "Sucursal" not in d.columns or d["Sucursal"].astype(str).str.strip().eq("").all():
        d["Sucursal"] = d["Cod Zona Venta"].map(zona_to_sucursal).fillna("GENERAL")

  def aplicar_reglas(df):
    if df.empty:
      empty_dict = {}
      for k in ["BM", "PREM", "SS", "NABS", "MKTP", "INN", "CERV"]:
        empty_dict[k] = pd.DataFrame(columns=["SubCategoria", "Marca", "DescripcionProducto", "Canal", "bdr", "Cod Zona Venta", "CodigoProducto", "CodigoCliente", "CajasConvertidas", "Venta_Soles_Sin_IGV"])
      return empty_dict
      
    cond_cerv = df["SubCategoria"].str.contains("CERVEZA", case=False, na=False)
    cond_prem = df["Marca"].str.contains("CUSQUEÑA|CORONA|BUDWEISER|STELLA ARTOIS", case=False, na=False) | df["DescripcionProducto"].str.contains("CUSQUEÑA|CORONA|BUDWEISER|STELLA ARTOIS", case=False, na=False)
    ss_mar = ["PILSEN CALLAO", "CUSQUEÑA", "CRISTAL", "GOLDEN"]
    cond_ss = (df["Marca"].str.contains("|".join(ss_mar), case=False, na=False) & df["DescripcionProducto"].str.contains("3\\d{2}ML|4\\d{2}ML|LATA|CAN|SLEEK", regex=True, na=False)) | df["Marca"].str.contains("BUDWEISER|CORONA|MIKES", case=False, na=False)
    return {
        "BM": df[cond_cerv | df["Marca"].str.contains("MIKES|MIKE´S|MIKE\'S", case=False, na=False)],
        "PREM": df[cond_prem],
        "SS": df[cond_ss],
        "NABS": df[df["Marca"].str.contains("GUARANÁ|GUARANA|VIVA|CRISTALINA", regex=True, case=False)],
        "MKTP": df[df["SubCategoria"].str.contains("MARKET PLACE", case=False, na=False)],
        "INN": df[df["DescripcionProducto"].str.contains("FRESH|CORONA CERO|CERO TRIGO|FLYING|TRIGO CERO", case=False, na=False)],
        "CERV": df[cond_cerv],
    }

  bdrs_encontrados = sorted([b for b in df_act_raw["bdr"].unique() if str(b).startswith("PE")])
  if not bdrs_encontrados:
    bdrs_encontrados = [f"PE070{str(i).zfill(2)}" for i in range(1, 13)]

  return {
      "maestro": df_m,
      "act": aplicar_reglas(df_act_raw),
      "raw_act": df_act_raw,
      "raw_25": df_25_raw,
      "raw_26": df_26_raw,
      "preventa": df_preventa,
      "bdr_unicos": bdrs_encontrados,
  }, None


datos_cacheados, error_msg = load_all_data()
if error_msg:
  st.error(error_msg)
  st.stop()

df_maestro = datos_cacheados["maestro"]
dfs_act = datos_cacheados["act"]
raw_act = datos_cacheados["raw_act"]
raw_25 = datos_cacheados["raw_25"]
raw_26 = datos_cacheados["raw_26"]
df_preventa = datos_cacheados["preventa"]
bdrs_unicos = datos_cacheados["bdr_unicos"]

# ==========================================
# 3. CONFIGURACIONES Y CUOTAS
# ==========================================
portafolios = {
    "BM": {"name": "Beer + Mike's", "col": "CajasConvertidas", "lbl": "Cajas", "fmt": "{:,.2f}", "dis_col": "CodigoProducto"},
    "PREM": {"name": "Premium", "col": "CajasConvertidas", "lbl": "Cajas", "fmt": "{:,.2f}", "dis_col": "CodigoProducto"},
    "SS": {"name": "Single Serve", "col": "CajasConvertidas", "lbl": "Cajas", "fmt": "{:,.2f}", "dis_col": "CodigoProducto"},
    "NABS": {"name": "NABS", "col": "CajasConvertidas", "lbl": "Cajas", "fmt": "{:,.2f}", "dis_col": "CodigoProducto"},
    "MKTP": {"name": "MarketPlace", "col": "Venta_Soles_Sin_IGV", "lbl": "Soles", "fmt": "S/ {:,.2f}", "dis_col": "CodigoProducto"},
    "INN": {"name": "Innovaciones", "col": "CajasConvertidas", "lbl": "Cajas", "fmt": "{:,.2f}", "dis_col": "Marca"},
}
coberturas = {
    "CERV": {"name": "Cerveza Total"},
    "NABS": {"name": "NABS"},
    "INN": {"name": "Innovaciones"},
    "MKTP": {"name": "MarketPlace"},
}
zonas_hn01 = [b for b in bdrs_unicos if b in ["PE07001", "PE07002", "PE07003", "PE07004", "PE07005", "PE07006", "PE07007"]]
zonas_ab01 = [b for b in bdrs_unicos if b in ["PE07008", "PE07009", "PE07010", "PE07011", "PE07012"]]
if not zonas_hn01: zonas_hn01 = bdrs_unicos[:7]
if not zonas_ab01: zonas_ab01 = bdrs_unicos[7:]

if os.path.exists(ARCHIVO_CUOTAS):
  df_cuotas_orig = pd.read_csv(ARCHIVO_CUOTAS)
else:
  df_cuotas_orig = pd.DataFrame({
      "bdr": bdrs_unicos,
      "Cuota Mensual (Cajas)": [10000.0] * len(bdrs_unicos),
      "Meta Distro (Impactos)": [500.0] * len(bdrs_unicos),
      "Meta Innovacion (Impactos)": [89.0] * len(bdrs_unicos),
      "Dias_Pendientes": [1] * len(bdrs_unicos),
      "Dias_Transcurridos": [24] * len(bdrs_unicos),
  })

if "df_cuotas" not in st.session_state:
  st.session_state.df_cuotas = df_cuotas_orig

d_trans = int(st.session_state.df_cuotas["Dias_Transcurridos"].iloc[0] if "Dias_Transcurridos" in st.session_state.df_cuotas.columns else 24)
d_pend = int(st.session_state.df_cuotas["Dias_Pendientes"].iloc[0] if "Dias_Pendientes" in st.session_state.df_cuotas.columns else 1)


# ==========================================
# 4. CÁLCULO MAESTRO Y FÓRMULAS COMERCIALES
# ==========================================
def calcular_fila(nombre, lista_zonas, agrupa=False):
  r = {"bdr": nombre, "Es_Agrupacion": agrupa}
  cuotas_sub = st.session_state.df_cuotas[st.session_state.df_cuotas["bdr"].isin(lista_zonas)]
  r["Universo_Cob"] = df_maestro[df_maestro["Zona Vendedor"].isin(lista_zonas)]["Cliente_ID"].nunique()

  for p, cfg in portafolios.items():
    s_act = dfs_act[p][dfs_act[p]["bdr"].isin(lista_zonas)]
    r[f"Av Vol {p}"] = s_act[cfg["col"]].sum()
    r[f"Av Dis {p}"] = s_act[s_act["Canal"].str.contains("TRADICIONAL", na=False)][["CodigoCliente", cfg["dis_col"]]].drop_duplicates().shape[0]

    if p == "BM":
      r[f"Ct Vol {p}"] = cuotas_sub["Cuota Mensual (Cajas)"].sum() if "Cuota Mensual (Cajas)" in cuotas_sub.columns else cuotas_sub.iloc[:, 1].sum()
    else:
      r[f"Ct Vol {p}"] = cuotas_sub["Cuota Mensual (Cajas)"].sum() * 0.2 if "Cuota Mensual (Cajas)" in cuotas_sub.columns else 1000
    r[f"Mt Dis {p}"] = cuotas_sub["Meta Distro (Impactos)"].sum() if "Meta Distro (Impactos)" in cuotas_sub.columns else 500

  for c in coberturas.keys():
    r[f"Activos Cob {c}"] = dfs_act[c][dfs_act[c]["bdr"].isin(lista_zonas)]["CodigoCliente"].nunique()
  return r

filas = [calcular_fila("NOBLE (TOTAL)", zonas_hn01 + zonas_ab01, True), calcular_fila("HN01", zonas_hn01, True)]
for z in zonas_hn01:
  if z in bdrs_unicos: filas.append(calcular_fila(z, [z]))
filas.append(calcular_fila("AB01", zonas_ab01, True))
for z in zonas_ab01:
  if z in bdrs_unicos: filas.append(calcular_fila(z, [z]))

rpt = pd.DataFrame(filas).fillna(0)

for p in portafolios.keys():
  for met in ["Vol", "Dis"]:
    av, me = f"Av {met} {p}", f"Ct Vol {p}" if met == "Vol" else f"Mt Dis {p}"
    rpt[f"% Av {met} {p}"] = np.where(rpt[me] > 0, (rpt[av] / rpt[me]) * 100, 0)
    prom = rpt[av] / d_trans if d_trans > 0 else 0
    rpt[f"Proy {met} {p}"] = rpt[av] + (prom * d_pend)
    rpt[f"% Proy {met} {p}"] = np.where(rpt[me] > 0, (rpt[f"Proy {met} {p}"] / rpt[me]) * 100, 0)
    rpt[f"Falt {met} {p}"] = (rpt[me] - rpt[av]).clip(lower=0)

for c in coberturas.keys():
  rpt[f"% Prod Cob {c}"] = np.where(rpt["Universo_Cob"] > 0, (rpt[f"Activos Cob {c}"] / rpt["Universo_Cob"]) * 100, 0)
  rpt[f"Faltante Cob {c}"] = (rpt["Universo_Cob"] - rpt[f"Activos Cob {c}"]).clip(lower=0)

rpt = rpt.fillna(0)
dat_nob = rpt[rpt["bdr"] == "NOBLE (TOTAL)"].iloc[0] if not rpt[rpt["bdr"] == "NOBLE (TOTAL)"].empty else rpt.iloc[0]

def cls(x):
  return "background-color:#ff4d4d;color:black;" if x < 85 else ("background-color:#ffe680;color:black;" if x < 100 else "background-color:#4caf50;color:black;")

def pintar_kpi(row, col_pct1, col_pct2=None):
  c1 = "#ff4d4d" if row[col_pct1] < 85 else ("#ffe680" if row[col_pct1] < 100 else "#4caf50")
  c2 = "#ff4d4d" if col_pct2 and row[col_pct2] < 85 else ("#ffe680" if col_pct2 and row[col_pct2] < 100 else "#4caf50")
  est = []
  for col in row.index:
    cel = "background-color: #FFFF00; font-weight: bold; color: black;" if row["Es_Agrupacion"] else ""
    if col == col_pct1: cel = f"background-color: {c1}; font-weight: bold; color: black; text-align: center;"
    if col_pct2 and col == col_pct2: cel = f"background-color: {c2}; font-weight: bold; color: black; text-align: center;"
    est.append(cel)
  return est


# ==========================================
# 5. INTERFAZ Y PESTAÑAS DEL DASHBOARD
# ==========================================
tabs = st.tabs(
    ["🌐 Resumen 360°", "🎯 Focos del Día"]
    + [f"📊 {p['name']}" for p in portafolios.values()]
    + ["🌍 Productividad Neta", "🔒 Configuración y Cuotas"]
)

# --- TAB 0: RESUMEN 360° ---
with tabs[0]:
  st.header("Visión General Ejecutiva: INVERSIONES NOBLE S.A.C.")
  st.markdown(f"**Días Transcurridos:** {d_trans} | **Días Pendientes:** {d_pend} | **Universo Total de Clientes:** {dat_nob['Universo_Cob']:,.0f} Bodegas")

  meses_dict = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
  max_mes_actual = 9

  def filtrar_por_portafolio_raw(df, p_key):
    if df.empty: return df
    cond_cerv = df["SubCategoria"].str.contains("CERVEZA", case=False, na=False)
    cond_prem = df["Marca"].str.contains("CUSQUEÑA|CORONA|BUDWEISER|STELLA ARTOIS", case=False, na=False) | df["DescripcionProducto"].str.contains("CUSQUEÑA|CORONA|BUDWEISER|STELLA ARTOIS", case=False, na=False)
    ss_mar = ["PILSEN CALLAO", "CUSQUEÑA", "CRISTAL", "GOLDEN"]
    cond_ss = (df["Marca"].str.contains("|".join(ss_mar), case=False, na=False) & df["DescripcionProducto"].str.contains("3\\d{2}ML|4\\d{2}ML|LATA|CAN|SLEEK", regex=True, na=False)) | df["Marca"].str.contains("BUDWEISER|CORONA|MIKES", case=False, na=False)

    if p_key == "BM": return df[cond_cerv | df["Marca"].str.contains("MIKES|MIKE´S|MIKE\'S", case=False, na=False)]
    elif p_key == "PREM": return df[cond_prem]
    elif p_key == "SS": return df[cond_ss]
    elif p_key == "NABS": return df[df["Marca"].str.contains("GUARANÁ|GUARANA|VIVA|CRISTALINA", regex=True, case=False)]
    elif p_key == "MKTP": return df[df["SubCategoria"].str.contains("MARKET PLACE", case=False, na=False)]
    else: return df[df["DescripcionProducto"].str.contains("FRESH|CORONA CERO|CERO TRIGO|FLYING|TRIGO CERO", case=False, na=False)]

  raw_26_full = pd.concat([raw_26, raw_act], ignore_index=True) if not raw_act.empty else raw_26

  f25_bm_ytd = filtrar_por_portafolio_raw(raw_25, "BM")
  f25_bm_ytd = f25_bm_ytd[(f25_bm_ytd["Mes"] <= max_mes_actual) & (f25_bm_ytd["bdr"].isin(zonas_hn01 + zonas_ab01))]["CajasConvertidas"].sum()
  f26_bm_ytd = filtrar_por_portafolio_raw(raw_26_full, "BM")
  f26_bm_ytd = f26_bm_ytd[(f26_bm_ytd["Mes"] <= max_mes_actual) & (f26_bm_ytd["bdr"].isin(zonas_hn01 + zonas_ab01))]["CajasConvertidas"].sum()
  crec_bm_ytd = (((f26_bm_ytd / f25_bm_ytd) - 1) * 100 if f25_bm_ytd > 0 else 0)

  st.markdown(f"""
        <div class="accumulated-card">
            <h4>📈 Crecimiento Acumulado YTD (Enero - Septiembre 2025 vs 2026)</h4>
            <p><b>Beer + Mike's:</b> 2025: {f25_bm_ytd:,.2f} cjs | 2026: {f26_bm_ytd:,.2f} cjs | <b>Crecimiento Acumulado: <span style="color: {'#4ade80' if crec_bm_ytd >= 0 else '#f87171'};">{crec_bm_ytd:+.2f}%</span></b></p>
        </div>
    """, unsafe_allow_html=True)

  col_sel1, col_sel2 = st.columns(2)
  with col_sel1: sel_port = st.selectbox("🎯 Portafolio / SKU para Curva Anual:", list(portafolios.keys()), format_func=lambda x: portafolios[x]["name"])
  with col_sel2: mes_seleccionado = st.selectbox("📅 Seleccionar Mes para Comparativa YoY:", list(meses_dict.keys()), format_func=lambda x: meses_dict[x], index=8)

  regla_cfg = portafolios[sel_port]
  c_val = regla_cfg["col"]
  f25_tot = filtrar_por_portafolio_raw(raw_25, sel_port)
  f26_tot = filtrar_por_portafolio_raw(raw_26_full, sel_port)
  curva_25_sku = f25_tot[f25_tot["bdr"].isin(zonas_hn01 + zonas_ab01)].groupby("Mes")[c_val].sum() if not f25_tot.empty else pd.Series(dtype=float)
  curva_26_sku = f26_tot[f26_tot["bdr"].isin(zonas_hn01 + zonas_ab01)].groupby("Mes")[c_val].sum() if not f26_tot.empty else pd.Series(dtype=float)

  fig = go.Figure()
  meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
  if not curva_25_sku.empty: fig.add_trace(go.Scatter(x=curva_25_sku.index, y=curva_25_sku.values, mode="lines+markers", name="2025", line=dict(color="#94a3b8", width=3, shape="spline")))
  if not curva_26_sku.empty: fig.add_trace(go.Scatter(x=curva_26_sku.index, y=curva_26_sku.values, mode="lines+markers", name="2026", line=dict(color="#3b82f6", width=4, shape="spline")))
  fig.update_layout(title=f"📈 Tendencia Anual YoY - {portafolios[sel_port]['name']}", xaxis_title="", yaxis_title=portafolios[sel_port]["lbl"], hovermode="x unified", height=300, margin=dict(t=30, b=10, l=10, r=10), paper_bgcolor="rgba(30,41,59,0.7)", plot_bgcolor="rgba(15,23,42,0.6)", font=dict(color="#f8fafc"))
  fig.update_xaxes(tickvals=list(range(1, 13)), ticktext=meses_nombres, gridcolor="rgba(255,255,255,0.1)")
  fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
  st.plotly_chart(fig, use_container_width=True)

  c1, c2 = st.columns(2)
  with c1:
    st.subheader(f"📦 Volumen / Facturación ({meses_dict[mes_seleccionado]} 2025 vs 2026)")
    d_vol = []
    for k, v in portafolios.items():
      f_p25 = filtrar_por_portafolio_raw(raw_25, k)
      f_p26 = filtrar_por_portafolio_raw(raw_26_full, k)
      val_25 = f_p25[(f_p25["Mes"] == mes_seleccionado) & (f_p25["bdr"].isin(zonas_hn01 + zonas_ab01))][v["col"]].sum() if not f_p25.empty else 0
      val_26 = f_p26[(f_p26["Mes"] == mes_seleccionado) & (f_p26["bdr"].isin(zonas_hn01 + zonas_ab01))][v["col"]].sum() if not f_p26.empty else 0
      crec_yoy = ((val_26 / val_25) - 1) * 100 if val_25 > 0 else 0
      d_vol.append({"Portafolio": v["name"], f"{meses_dict[mes_seleccionado]} 2025": val_25, f"{meses_dict[mes_seleccionado]} 2026": val_26, "Crec YoY (%)": crec_yoy, "Meta": dat_nob[f"Ct Vol {k}"], "% Avance": dat_nob[f"% Av Vol {k}"]})
    st.dataframe(
        pd.DataFrame(d_vol).style.apply(lambda r: [cls(x) if i in [3, 5] else ("color: #15803d; font-weight: bold;" if i == 3 and x > 0 else "color: #b91c1c; font-weight: bold;" if i == 3 else "") for i, x in enumerate(r)], axis=1).format({f"{meses_dict[mes_seleccionado]} 2025": "{:,.2f}", f"{meses_dict[mes_seleccionado]} 2026": "{:,.2f}", "Crec YoY (%)": "{:.2f}%", "Meta": "{:,.2f}", "% Avance": "{:.2f}%"}),
        use_container_width=True, hide_index=True,
    )

  with c2:
    st.subheader(f"🎯 BrandDistro ({meses_dict[mes_seleccionado]} 2025 vs 2026)")
    d_dis = []
    for k, v in portafolios.items():
      f_p25 = filtrar_por_portafolio_raw(raw_25, k)
      f_p26 = filtrar_por_portafolio_raw(raw_26_full, k)
      s25_m = f_p25[(f_p25["Mes"] == mes_seleccionado) & (f_p25["bdr"].isin(zonas_hn01 + zonas_ab01))] if not f_p25.empty else pd.DataFrame()
      s26_m = f_p26[(f_p26["Mes"] == mes_seleccionado) & (f_p26["bdr"].isin(zonas_hn01 + zonas_ab01))] if not f_p26.empty else pd.DataFrame()
      d25_val = s25_m[s25_m["Canal"].str.contains("TRADICIONAL", na=False)][["CodigoCliente", v["dis_col"]]].drop_duplicates().shape[0] if not s25_m.empty else 0
      d26_val = s26_m[s26_m["Canal"].str.contains("TRADICIONAL", na=False)][["CodigoCliente", v["dis_col"]]].drop_duplicates().shape[0] if not s26_m.empty else 0
      crec_dis = ((d26_val / d25_val) - 1) * 100 if d25_val > 0 else 0
      d_dis.append({"Portafolio": v["name"], f"Imp {meses_dict[mes_seleccionado]} 25": d25_val, f"Imp {meses_dict[mes_seleccionado]} 26": d26_val, "Crec YoY (%)": crec_dis, "Meta Imp": dat_nob[f"Mt Dis {k}"], "% Avance": dat_nob[f"% Av Dis {k}"]})
    st.dataframe(
        pd.DataFrame(d_dis).style.apply(lambda r: [cls(x) if i in [3, 5] else ("color: #15803d; font-weight: bold;" if i == 3 and x > 0 else "color: #b91c1c; font-weight: bold;" if i == 3 else "") for i, x in enumerate(r)], axis=1).format({f"Imp {meses_dict[mes_seleccionado]} 25": "{:,.0f}", f"Imp {meses_dict[mes_seleccionado]} 26": "{:,.0f}", "Crec YoY (%)": "{:.2f}%", "Meta Imp": "{:,.0f}", "% Avance": "{:.2f}%"}),
        use_container_width=True, hide_index=True,
    )

# --- TAB 1: FOCOS DEL DÍA ---
with tabs[1]:
  col_btn1, col_btn2 = st.columns([0.8, 0.2])
  with col_btn1: st.header("🎯 Focos del Día: Control Comercial Exacto")
  with col_btn2:
      st.write("") 
      if st.button("🔄 Actualizar Datos de Preventa", help="Recarga el archivo Excel Dinámica"):
          st.cache_data.clear()
          st.rerun()

  st.markdown("Selecciona **4 focos** de portafolio y ajusta las cuotas por cada vendedor.")

  focos_opciones = ["Vol. Beer + Mike's", "Premium", "Single Serve", "NABS", "MarketPlace", "Innovaciones", "SKU x POC (Impactos)"]
  short_names = {"Vol. Beer + Mike's": "B/M", "Premium": "Prem", "Single Serve": "SS", "NABS": "NABS", "MarketPlace": "MKTP", "Innovaciones": "Innov", "SKU x POC (Impactos)": "SKUxPOC"}

  focos_seleccionados = st.multiselect("🎯 Selecciona los 4 Focos Diarios:", focos_opciones, default=["Vol. Beer + Mike's", "Premium", "Single Serve", "MarketPlace"], max_selections=4)

  if len(focos_seleccionados) != 4:
    st.warning("⚠️ Por favor, selecciona exactamente **4 focos** para continuar.")
  else:
    c_ctrl1, c_ctrl2 = st.columns([0.3, 0.7])
    with c_ctrl1: 
        dia_consulta = st.selectbox("📅 Día a Consultar:", ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO"], index=2)
    with c_ctrl2: 
        st.markdown("<br>👉 **Configura las Zonas, Frecuencias y Cuotas en la tabla minimizada de abajo.**", unsafe_allow_html=True)

    # --- INICIALIZAR TABLA CON CHECKBOXES ---
    if 'metas_diarias' not in st.session_state or 'Activo' not in st.session_state.metas_diarias.columns or st.session_state.get('last_focos') != focos_seleccionados:
        df_m_d = pd.DataFrame({'BDR': bdrs_unicos})
        df_m_d['Activo'] = True
        df_m_d['Semanal'] = True
        df_m_d['Q1'] = False
        df_m_d['Q2'] = False
        for f in focos_seleccionados:
            if "Market" in f: df_m_d[f] = 500.0
            elif "Premium" in f: df_m_d[f] = 25.0
            elif "Single" in f: df_m_d[f] = 150.0
            else: df_m_d[f] = 300.0
        st.session_state.metas_diarias = df_m_d
        st.session_state.last_focos = focos_seleccionados

    with st.expander("⚙️ Configurar Cuotas Diarias por BDR (Minimizado)", expanded=False):
        st.markdown("🔒 **Solo los 2 Supervisores y el Jefe pueden modificar las cuotas de esta pestaña.**")
        
        col_pwd, _ = st.columns([1, 2])
        with col_pwd:
            pwd_foco = st.text_input("Contraseña de autorización:", type="password", key="pwd_focos")
        
        PASSWORDS_PERMITIDOS = [PASSWORD_JEFE, PASSWORD_SV1, PASSWORD_SV2] 
        
        config_cols = {
            "BDR": st.column_config.TextColumn("BDR", disabled=True),
        }
        
        if pwd_foco in PASSWORDS_PERMITIDOS:
            st.success("Acceso concedido. Marca/desmarca frecuencias y ajusta cuotas por BDR:")
            edited_df = st.data_editor(st.session_state.metas_diarias, hide_index=True, use_container_width=True, column_config=config_cols)
            st.session_state.metas_diarias = edited_df
        else:
            if pwd_foco:
                st.error("Contraseña incorrecta. Se muestra en modo de solo lectura.")
            else:
                st.info("Ingresa la contraseña para habilitar la edición de cuotas.")
            st.dataframe(st.session_state.metas_diarias, hide_index=True, use_container_width=True)

    dict_metas = st.session_state.metas_diarias.set_index('BDR').to_dict('index')

    col_maestro_dia = next((c for c in df_maestro.columns if "DIA" in c.upper() or "VISITA" in c.upper()), None)

    dias_map = {"LUNES": ["LUNES", "LU", "L"], "MARTES": ["MARTES", "MA", "M"], "MIERCOLES": ["MIERCOLES", "MI", "X", "MIÉRC", "MIE"], "JUEVES": ["JUEVES", "JU", "J"], "VIERNES": ["VIERNES", "VI", "V"], "SABADO": ["SABADO", "SA", "S"]}

    def limpiar_id(series):
        s = series.fillna("").astype(str).str.strip().str.upper()
        s = s.str.replace(r'\.0+$', '', regex=True)
        s = s.str.lstrip('0')
        return s.replace('', '0')

    def obtener_clientes_programados(lista_zonas):
      df_sub = df_maestro[df_maestro["Zona Vendedor"].isin(lista_zonas)].copy()
      if df_sub.empty: return set()
      
      # 1. Filtro estricto de clientes Activos
      col_estado = next((c for c in df_sub.columns if c.upper() in ["ESTADO", "ESTADO CLIENTE", "ESTADO DEL CLIENTE"]), None)
      if not col_estado:
          col_estado = next((c for c in df_sub.columns if "ESTADO" in c.upper()), None)
      if col_estado:
          df_sub = df_sub[df_sub[col_estado].astype(str).str.upper().str.startswith("A")]

      # 2. Filtro estricto del Día a consultar
      if col_maestro_dia:
        df_sub["_dia"] = df_sub[col_maestro_dia].fillna("").astype(str).str.upper()
        patron_dia = "|".join([rf"\b{d}\b" for d in dias_map.get(dia_consulta, [dia_consulta])])
        df_sub = df_sub[df_sub["_dia"].str.contains(patron_dia, na=False, regex=True)]
        if df_sub.empty: return set()
      
      # 3. CONCATENAMOS TODAS LAS COLUMNAS RELEVANTES DE RUTA PARA EVITAR QUE SE PIERDA LA FRECUENCIA
      cols_ruta = [c for c in df_sub.columns if any(x in c.upper() for x in ["FREQ", "FRECUENCIA", "RUTA", "QUINCEN", "SECUENCIA", "VISITA", "ZONA"])]
      if cols_ruta:
          df_sub["_info_ruta"] = df_sub[cols_ruta].fillna("").astype(str).agg(' '.join, axis=1).str.upper()
      else:
          df_sub["_info_ruta"] = df_sub.fillna("").astype(str).agg(' '.join, axis=1).str.upper()

      # 4. Clasificamos las rutas a nivel matemático en TODA la base
      mask_q1 = df_sub["_info_ruta"].str.contains(r"\bQ1\b|-Q1|QUINCENAL 1|\b1\b|\b3\b|S1|S3", na=False, regex=True)
      mask_q2 = df_sub["_info_ruta"].str.contains(r"\bQ2\b|-Q2|QUINCENAL 2|\b2\b|\b4\b|S2|S4", na=False, regex=True)
      # Un cliente es semanal puro si NO tiene etiqueta Q1 y NO tiene etiqueta Q2 (o si explícitamente dice SEMANAL)
      mask_sem = (~mask_q1 & ~mask_q2) | df_sub["_info_ruta"].str.contains("SEMANAL", na=False, regex=True)

      clientes_validos = []
      for z in lista_zonas:
          cfg_z = dict_metas.get(z, {})
          
          # Si la zona está apagada en la tabla, la saltamos por completo
          if not cfg_z.get('Activo', True):
              continue

          mask_z = (df_sub["Zona Vendedor"] == z)
          
          # Evaluamos qué checkboxes tiene encendidos este BDR en particular
          condiciones = []
          if cfg_z.get('Semanal', False): condiciones.append(mask_sem)
          if cfg_z.get('Q1', False): condiciones.append(mask_q1)
          if cfg_z.get('Q2', False): condiciones.append(mask_q2)

          if condiciones:
              # Une las condiciones marcadas (Ej: Semanal OR Q1) y cruza con la Zona
              mask_freq = np.logical_or.reduce(condiciones)
              clientes_validos.append(df_sub[mask_z & mask_freq])

      if clientes_validos:
          df_sub = pd.concat(clientes_validos)
      else:
          return set()
          
      return set(limpiar_id(df_sub["Cliente_ID"]).unique())

    def obtener_clientes_compraron(df_p_zona):
      if df_p_zona.empty: return set()
      return set(limpiar_id(df_p_zona["ClienteCod"]).unique())

    def filtrar_foco_preventa(df, foco_name):
      if df.empty: return df
      c_n4, prod = df["ClaseN4"].fillna("").str.upper(), df["Producto"].fillna("").str.upper()
      if foco_name == "Vol. Beer + Mike's": return df[c_n4.str.contains("CERVEZA", na=False) | prod.str.contains("MIKES|MIKE´S|MIKE\'S", case=False, na=False)]
      elif foco_name == "Premium": return df[prod.str.contains("CUSQUEÑA|CORONA|BUDWEISER|STELLA ARTOIS", case=False, na=False)]
      elif foco_name == "Single Serve": return df[(prod.str.contains("|".join(["PILSEN CALLAO", "CUSQUEÑA", "CRISTAL", "GOLDEN"]), case=False, na=False) & prod.str.contains("3\\d{2}ML|4\\d{2}ML|LATA|CAN|SLEEK", regex=True, na=False)) | prod.str.contains("BUDWEISER|CORONA|MIKES", case=False, na=False)]
      elif foco_name == "NABS": return df[prod.str.contains("GUARANÁ|GUARANA|VIVA|CRISTALINA", regex=True, case=False)]
      elif foco_name == "MarketPlace": return df[c_n4.str.contains("MARKET PLACE", case=False, na=False)]
      elif foco_name == "Innovaciones": return df[prod.str.contains("FRESH|CORONA CERO|CERO TRIGO|FLYING|TRIGO CERO", case=False, na=False)]
      return df

    def calcular_fila_foco(nombre_zona, lista_zonas, agrupa=False):
      zonas_validas = [z for z in lista_zonas if dict_metas.get(z, {}).get('Activo', True)]
      
      if not agrupa and not zonas_validas:
          return None
          
      clientes_prog_set = obtener_clientes_programados(zonas_validas)
      clientes_visita = len(clientes_prog_set)
      
      df_p_zona = df_preventa[df_preventa["bdr"].isin(zonas_validas)] if not df_preventa.empty else pd.DataFrame()
      clientes_comp_set = obtener_clientes_compraron(df_p_zona)
      
      clientes_compraron_total = len(clientes_comp_set)
      
      efectividad = (clientes_compraron_total / clientes_visita) * 100 if clientes_visita > 0 else 0.0

      row = {
          "Zona / BDR": nombre_zona,
          "Visita\nProg.": clientes_visita,
          "Comp.\nTotal": clientes_compraron_total,
          "% Efectividad": efectividad,
          "Es_Agrupacion": agrupa,
      }

      for foco in focos_seleccionados:
        s = short_names[foco] 
        if df_p_zona.empty: avance = 0.0
        else:
          if foco in ["Vol. Beer + Mike's", "Premium", "Single Serve", "NABS", "Innovaciones"]: avance = filtrar_foco_preventa(df_p_zona, foco)["Cantidad"].sum()
          elif foco == "MarketPlace": avance = filtrar_foco_preventa(df_p_zona, foco)["Total"].sum()
          elif foco == "SKU x POC (Impactos)": avance = df_p_zona[["ClienteCod", "Producto"]].drop_duplicates().shape[0] if not df_p_zona.empty else 0
          else: avance = 0.0

        meta_val = sum([dict_metas.get(z, {}).get(foco, 100.0) for z in zonas_validas])
        pct = (avance / meta_val) * 100 if meta_val > 0 else 0.0
        row[f"{s}\nCuota"] = f"{meta_val:,.0f}" if "MarketPlace" not in foco else f"S/{meta_val:,.0f}"
        row[f"{s}\nAvance"] = f"{avance:,.1f}" if "MarketPlace" not in foco else f"S/{avance:,.0f}"
        row[f"{s}\n% Meta"] = pct

      return row

    filas_focos = []
    
    fila_total = calcular_fila_foco("NOBLE (TOTAL)", zonas_hn01 + zonas_ab01, agrupa=True)
    if fila_total: filas_focos.append(fila_total)
    
    fila_hn01 = calcular_fila_foco("HN01", zonas_hn01, agrupa=True)
    if fila_hn01: filas_focos.append(fila_hn01)
    
    for z in zonas_hn01:
      if z in bdrs_unicos: 
          fila_z = calcular_fila_foco(z, [z], agrupa=False)
          if fila_z: filas_focos.append(fila_z)
          
    fila_ab01 = calcular_fila_foco("AB01", zonas_ab01, agrupa=True)
    if fila_ab01: filas_focos.append(fila_ab01)
    
    for z in zonas_ab01:
      if z in bdrs_unicos: 
          fila_z = calcular_fila_foco(z, [z], agrupa=False)
          if fila_z: filas_focos.append(fila_z)

    df_focos_rpt = pd.DataFrame(filas_focos).fillna(0)

    st.markdown("---")
    st.subheader(f"📋 Control Comercial para el día **{dia_consulta}** (Programación Activa)")

    colores_focos = ["rgba(54, 162, 235, 0.15)", "rgba(255, 99, 132, 0.15)", "rgba(255, 206, 86, 0.25)", "rgba(153, 102, 255, 0.15)"]

    def color_por_kpi(row):
      estilos = []
      is_group = row["Es_Agrupacion"] if "Es_Agrupacion" in row.index else False
      for col in row.index:
        cel = ""
        if is_group: cel = "background-color: #FFFF00; font-weight: bold; color: black;"
        
        if col == "% Efectividad" and not is_group:
            val_pct = row[col]
            color_txt = "#15803d" if val_pct >= 60 else ("#b91c1c" if val_pct < 40 else "#d97706")
            cel = f"background-color: #f8fafc; font-weight: bold; color: {color_txt}; text-align: center;"

        for idx, foco in enumerate(focos_seleccionados):
          s = short_names[foco]
          if col.startswith(s):
            bg_color = colores_focos[idx % len(colores_focos)]
            if "% Meta" in col:
              val_pct = row[col]
              color_txt = "#15803d" if val_pct >= 100 else ("#b91c1c" if val_pct < 85 else "#d97706")
              cel = f"background-color: {bg_color}; font-weight: bold; color: {color_txt}; text-align: center;"
            else: cel = f"background-color: {bg_color}; font-weight: bold; color: black; text-align: center;"
        estilos.append(cel)
      return estilos

    cols_mostrar = ["Zona / BDR", "Visita\nProg.", "Comp.\nTotal", "% Efectividad"]
    for foco in focos_seleccionados:
      s = short_names[foco]
      cols_mostrar.extend([f"{s}\nCuota", f"{s}\nAvance", f"{s}\n% Meta"])

    cols_para_estilo = cols_mostrar + ["Es_Agrupacion"]

    formatos_focos = {"Visita\nProg.": "{:,.0f}", "Comp.\nTotal": "{:,.0f}", "% Efectividad": "{:.1f}%"}
    for foco in focos_seleccionados:
      formatos_focos[f"{short_names[foco]}\n% Meta"] = "{:.1f}%"

    st.dataframe(
        df_focos_rpt[cols_para_estilo]
        .style.apply(color_por_kpi, axis=1)
        .format(formatos_focos)
        .hide(subset=["Es_Agrupacion"], axis="columns"),
        use_container_width=True, height=550,
    )

# --- TABS PORTAFOLIOS DETALLADOS ---
for i, (p_key, p_data) in enumerate(portafolios.items()):
  with tabs[i + 2]:
    st.subheader(f"Desempeño Operativo: {p_data['name']}")
    metrica = st.radio(f"Ver ({p_data['name']}):", [f"📦 Volumen", "🎯 BrandDistro"], horizontal=True, key=f"rad_{p_key}")
    m = "Vol" if "Volumen" in metrica else "Dis"
    av_col, me_col = f"Av {m} {p_key}", (f"Ct Vol {p_key}" if m == "Vol" else f"Mt Dis {p_key}")

    c_vis = ["bdr", me_col, av_col, f"% Av {m} {p_key}", f"Proy {m} {p_key}", f"% Proy {m} {p_key}", f"Falt {m} {p_key}", "Es_Agrupacion"]
    fmt = p_data["fmt"] if m == "Vol" else "{:,.0f}"
    formato = {c: fmt for c in c_vis if c not in ["bdr", f"% Av {m} {p_key}", f"% Proy {m} {p_key}", "Es_Agrupacion"]}
    formato.update({f"% Av {m} {p_key}": "{:.2f}%", f"% Proy {m} {p_key}": "{:.2f}%"})

    st.dataframe(
        rpt[c_vis].style.apply(lambda r: pintar_kpi(r, f"% Av {m} {p_key}", f"% Proy {m} {p_key}"), axis=1).format(formato).hide(subset=["Es_Agrupacion"], axis="columns").hide(axis="index"),
        use_container_width=True, height=580,
    )

# --- TAB PRODUCTIVIDAD NETA ---
with tabs[-2]:
  st.subheader("Productividad Real de Clientes (Cobertura por Zona)")
  cob_sel = st.radio("Categoría:", list(coberturas.keys()), format_func=lambda x: coberturas[x]["name"], horizontal=True)
  c_vis = ["bdr", "Universo_Cob", f"Activos Cob {cob_sel}", f"% Prod Cob {cob_sel}", f"Faltante Cob {cob_sel}", "Es_Agrupacion"]
  formato_c = {"Universo_Cob": "{:,.0f}", f"Activos Cob {cob_sel}": "{:,.0f}", f"Faltante Cob {cob_sel}": "{:,.0f}", f"% Prod Cob {cob_sel}": "{:.2f}%"}
  st.dataframe(
      rpt[c_vis].style.apply(lambda r: pintar_kpi(r, f"% Prod Cob {cob_sel}"), axis=1).format(formato_c).hide(subset=["Es_Agrupacion"], axis="columns").hide(axis="index"),
      use_container_width=True, height=580,
  )

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
      if "Dias_Transcurridos" in st.session_state.df_cuotas.columns: st.session_state.df_cuotas["Dias_Transcurridos"] = n_t
      if "Dias_Pendientes" in st.session_state.df_cuotas.columns: st.session_state.df_cuotas["Dias_Pendientes"] = n_p
      st.session_state.df_cuotas.to_csv(ARCHIVO_CUOTAS, index=False)
      st.cache_data.clear()
      st.success("¡Configuración guardada exitosamente! Presiona 'R' o recarga la página para refrescar.")
  elif password_ingresada != "":
    st.error("Contraseña incorrecta.")