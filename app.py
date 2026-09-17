"""
Projeto Sala de Som. Simulador financeiro.
Streamlit app para planeamento de duas salas de ensaios e gravacao em Portugal,
com compra do imovel a pronto.
"""
from __future__ import annotations

import io

import altair as alt
import pandas as pd
import streamlit as st

APP_PASSWORD = "gangdaapanhadefranca"

st.set_page_config(
    page_title="Projeto Sala de Som",
    page_icon="🎛️",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Estilo pastel
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --pastel-teal: #7fb8b3;
        --pastel-teal-soft: #cfe6e3;
        --pastel-violet: #b39ddb;
        --pastel-violet-soft: #e5dbf3;
        --pastel-yellow: #f6d78a;
        --pastel-yellow-soft: #fbecc4;
        --off-white: #faf7f0;
        --ink: #2d2a26;
    }
    .stApp { background-color: var(--off-white); }
    .block-container { padding-top: 2rem; }
    h1, h2, h3, h4 { color: var(--ink); }
    div[data-testid="stMetric"] {
        background-color: var(--pastel-teal-soft);
        border-radius: 12px;
        padding: 12px 16px;
        border: 1px solid rgba(127, 184, 179, 0.4);
    }
    div[data-testid="stMetricValue"] { color: var(--ink); }
    section[data-testid="stSidebar"] { background-color: #f2ecdd; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: var(--pastel-yellow-soft);
        padding: 6px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        padding: 8px 16px;
        color: var(--ink);
    }
    .stButton > button, .stDownloadButton > button {
        background-color: var(--pastel-violet-soft);
        color: var(--ink);
        border: 1px solid var(--pastel-violet);
        border-radius: 10px;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: var(--pastel-violet);
        color: var(--ink);
    }
    div[data-testid="stAlert"] { border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Password gate
# ---------------------------------------------------------------------------
def _check_password() -> bool:
    if st.session_state.get("auth_ok"):
        return True

    st.markdown("## 🎛️ Projeto Sala de Som")
    st.caption("Introduz a palavra-passe para acederes ao simulador.")
    with st.form("login", clear_on_submit=False):
        pw = st.text_input("Palavra-passe", type="password")
        submitted = st.form_submit_button("Entrar")
    if submitted:
        if pw.strip() == APP_PASSWORD:
            st.session_state["auth_ok"] = True
            st.rerun()
        else:
            st.error("Palavra-passe incorreta.")
    st.stop()
    return False


_check_password()


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULTS = {
    # Investimento inicial (compra do imovel a pronto)
    "preco_imovel": 300000.0,
    "pct_imposto_selo": 0.8,       # % sobre preco de compra
    "obras_iniciais": 15000.0,
    "mobiliario_material": 1000.0,

    # Custos mensais fixos
    "pagamento_espaco": 1000.0,
    "pct_imi_anual": 0.20,         # % anual sobre preco de compra (VPT tipicamente e mais baixo)
    "agua": 30.0,
    "eletricidade": 75.0,
    "internet": 15.0,
    "seguros": 40.0,
    "consumiveis_gerais": 50.0,
    "consumiveis_estudio": 25.0,
    "armazenamento_online": 30.0,
    "marketing_mensal": 5.0,

    # Receita Sala 1 - Ensaios
    "s1_preco_hora_ensaio": 9.0,
    "s1_horas_ensaio_mes": 100.0,
    "s1_preco_acordo": 120.0,
    "s1_horas_por_acordo": 24.0,
    "s1_num_acordos": 3.0,

    # Receita Sala 2 - Ensaios
    "s2_preco_hora_ensaio": 15.0,
    "s2_horas_ensaio_mes": 50.0,
    "s2_preco_extra_gravado": 5.0,
    "s2_horas_ensaio_gravado": 25.0,
    "s2_preco_acordo": 180.0,
    "s2_horas_por_acordo": 24.0,
    "s2_num_acordos": 1.0,

    # Receita Sala 2 - Gravacao
    "s2_horas_gravacao_mes": 5.0,
    "s2_preco_hora_gravacao": 30.0,
    "s2_faixas_mistura_mes": 2.0,
    "s2_preco_faixa_mistura": 100.0,

    # Simulacao
    "meses_simulacao": 240,
    "crescimento_mensal_pct": 2.0,
    "cap_horas_ensaio": 200.0,
    "cap_horas_gravacao": 50.0,
    "cap_faixas_mistura": 10.0,
}

ARTISTAS_INICIAIS = [
    {"Artista": "Inês Rebelo (Salacia)", "Estilo": "", "Notas": ""},
    {"Artista": "Giblets and Gravy", "Estilo": "", "Notas": ""},
    {"Artista": "Samuel Dias", "Estilo": "", "Notas": ""},
    {"Artista": "Razy", "Estilo": "", "Notas": ""},
    {"Artista": "Diogo Verdelindo", "Estilo": "", "Notas": ""},
    {"Artista": "SubRosa", "Estilo": "", "Notas": ""},
]


def _init_state():
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)
    st.session_state.setdefault("catalogo_artistas", pd.DataFrame(ARTISTAS_INICIAIS))


_init_state()


def _reset_defaults():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.session_state["catalogo_artistas"] = pd.DataFrame(ARTISTAS_INICIAIS)


# ---------------------------------------------------------------------------
# Sidebar. Parametros editaveis
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Parâmetros")
    st.caption("Todos os valores são editáveis. As mudanças propagam-se a todas as tabelas.")

    if st.button("Repor valores por defeito", use_container_width=True):
        _reset_defaults()
        st.rerun()

    with st.expander("Investimento inicial", expanded=False):
        st.number_input("Preço do imóvel (EUR)", key="preco_imovel", min_value=0.0, step=1000.0,
                        help="Compra a pronto, sem empréstimo bancário.")
        st.number_input("Imposto de selo na compra (% sobre preço)",
                        key="pct_imposto_selo", min_value=0.0, max_value=10.0, step=0.1,
                        help="Em Portugal, imposto de selo em transmissões onerosas de imóveis é 0,8%.")
        st.number_input("Obras (inclui tratamento acústico) (EUR)",
                        key="obras_iniciais", min_value=0.0, step=500.0)
        st.number_input("Mobiliário e material (EUR)",
                        key="mobiliario_material", min_value=0.0, step=100.0)

    with st.expander("Custos mensais fixos", expanded=False):
        st.number_input("Pagamento do espaço (EUR)", key="pagamento_espaco", min_value=0.0, step=25.0,
                        help="Condomínio, fundo de manutenção reservado, ou pagamento aos vossos pais. "
                             "Não é renda porque o imóvel é comprado a pronto.")
        st.number_input("IMI anual (% sobre preço do imóvel)",
                        key="pct_imi_anual", min_value=0.0, max_value=2.0, step=0.05,
                        help="IMI incide sobre o VPT, tipicamente inferior ao preço de compra. "
                             "0,20% do preço de compra é uma aproximação conservadora.")
        st.number_input("Água (EUR)", key="agua", min_value=0.0, step=5.0)
        st.number_input("Eletricidade (EUR)", key="eletricidade", min_value=0.0, step=5.0)
        st.number_input("Internet (EUR)", key="internet", min_value=0.0, step=5.0)
        st.number_input("Seguros (EUR)", key="seguros", min_value=0.0, step=5.0)
        st.number_input("Consumíveis gerais (limpeza, café, chá) (EUR)",
                        key="consumiveis_gerais", min_value=0.0, step=5.0)
        st.number_input("Consumíveis estúdio (cabos, cordas, pilhas) (EUR)",
                        key="consumiveis_estudio", min_value=0.0, step=5.0)
        st.number_input("Armazenamento online (EUR)", key="armazenamento_online", min_value=0.0, step=5.0)
        st.number_input("Marketing mensal (EUR)", key="marketing_mensal", min_value=0.0, step=5.0)

    with st.expander("Receita. Sala 1. Ensaios", expanded=True):
        st.number_input("Preço por hora de ensaio (EUR)", key="s1_preco_hora_ensaio", min_value=0.0, step=1.0)
        st.number_input("Horas de ensaio hora-a-hora por mês", key="s1_horas_ensaio_mes",
                        min_value=0.0, step=5.0)
        st.markdown("**Acordo Mensal**")
        st.number_input("Preço do acordo mensal (EUR)", key="s1_preco_acordo", min_value=0.0, step=5.0)
        st.number_input("Horas incluídas por acordo", key="s1_horas_por_acordo", min_value=0.0, step=1.0)
        st.number_input("Número de acordos mensais", key="s1_num_acordos", min_value=0.0, step=1.0)

    with st.expander("Receita. Sala 2. Ensaios", expanded=True):
        st.number_input("Preço por hora de ensaio (EUR)", key="s2_preco_hora_ensaio", min_value=0.0, step=1.0)
        st.number_input("Horas de ensaio hora-a-hora por mês", key="s2_horas_ensaio_mes",
                        min_value=0.0, step=5.0)
        st.markdown("**Ensaio gravado (add-on, sem mistura)**")
        st.number_input("Preço extra por hora de ensaio gravado (EUR)",
                        key="s2_preco_extra_gravado", min_value=0.0, step=1.0,
                        help="Adicional cobrado por cima do preço-hora quando o ensaio é gravado.")
        st.number_input("Horas de ensaio gravado por mês", key="s2_horas_ensaio_gravado",
                        min_value=0.0, step=1.0,
                        help="Subconjunto das horas de ensaio Sala 2 que são gravadas.")
        st.markdown("**Acordo Mensal**")
        st.number_input("Preço do acordo mensal (EUR)", key="s2_preco_acordo", min_value=0.0, step=5.0)
        st.number_input("Horas incluídas por acordo", key="s2_horas_por_acordo", min_value=0.0, step=1.0)
        st.number_input("Número de acordos mensais", key="s2_num_acordos", min_value=0.0, step=1.0)

    with st.expander("Receita. Sala 2. Gravação", expanded=True):
        st.number_input("Horas de gravação profissional por mês",
                        key="s2_horas_gravacao_mes", min_value=0.0, step=1.0)
        st.number_input("Preço por hora de gravação (EUR)",
                        key="s2_preco_hora_gravacao", min_value=0.0, step=5.0)
        st.number_input("Faixas para mistura por mês", key="s2_faixas_mistura_mes",
                        min_value=0.0, step=1.0)
        st.number_input("Preço por faixa de mistura (EUR)", key="s2_preco_faixa_mistura",
                        min_value=0.0, step=10.0)

    with st.expander("Simulação", expanded=False):
        st.number_input("Meses a simular", key="meses_simulacao",
                        min_value=1, max_value=600, step=12,
                        help="240 meses = 20 anos.")
        st.number_input("Crescimento de ocupação por mês (%)", key="crescimento_mensal_pct",
                        min_value=-10.0, max_value=20.0, step=0.5,
                        help="Aplicado a horas, acordos, gravações e faixas. Composto mês a mês.")
        st.number_input("Tecto de horas de ensaio por mês, por sala",
                        key="cap_horas_ensaio", min_value=0.0, step=10.0,
                        help="Cap combinado. Inclui horas hora-a-hora mais horas dos acordos mensais.")
        st.number_input("Tecto de horas de gravação por mês", key="cap_horas_gravacao",
                        min_value=0.0, step=5.0)
        st.number_input("Tecto de faixas de mistura por mês", key="cap_faixas_mistura",
                        min_value=0.0, step=1.0)


# ---------------------------------------------------------------------------
# Calculos: Investimento inicial
# ---------------------------------------------------------------------------
def investimento_inicial_df() -> pd.DataFrame:
    s = st.session_state
    imposto_selo = s.preco_imovel * s.pct_imposto_selo / 100.0
    rows = [
        ("Preço de aquisição do imóvel", s.preco_imovel),
        (f"Imposto de selo ({s.pct_imposto_selo:.2f}%)", imposto_selo),
        ("Obras (inclui tratamento acústico)", s.obras_iniciais),
        ("Mobiliário e material", s.mobiliario_material),
    ]
    df = pd.DataFrame(rows, columns=["Rubrica", "Valor (EUR)"])
    df.loc[len(df)] = ["TOTAL", df["Valor (EUR)"].sum()]
    return df


def investimento_inicial_total() -> float:
    return float(investimento_inicial_df().iloc[-1]["Valor (EUR)"])


# ---------------------------------------------------------------------------
# Calculos: Custos mensais
# ---------------------------------------------------------------------------
def imi_mensal() -> float:
    s = st.session_state
    return s.preco_imovel * s.pct_imi_anual / 100.0 / 12.0


def custos_mensais_df() -> pd.DataFrame:
    s = st.session_state
    rows = [
        ("Pagamento do espaço", s.pagamento_espaco),
        (f"IMI mensalizado ({s.pct_imi_anual:.2f}% ao ano)", imi_mensal()),
        ("Água", s.agua),
        ("Eletricidade", s.eletricidade),
        ("Internet", s.internet),
        ("Seguros", s.seguros),
        ("Consumíveis gerais", s.consumiveis_gerais),
        ("Consumíveis estúdio", s.consumiveis_estudio),
        ("Armazenamento online", s.armazenamento_online),
        ("Marketing mensal", s.marketing_mensal),
    ]
    df = pd.DataFrame(rows, columns=["Rubrica", "Valor (EUR)"])
    df.loc[len(df)] = ["TOTAL por mês", df["Valor (EUR)"].sum()]
    return df


def custos_mensais_total() -> float:
    return float(custos_mensais_df().iloc[-1]["Valor (EUR)"])


# ---------------------------------------------------------------------------
# Calculos: Receita
# ---------------------------------------------------------------------------
def _cap_ensaios(horas: float, acordos: float, horas_por_acordo: float, cap: float):
    """Cap combinado horas + 24 h por acordo <= cap. Corta acordos primeiro, depois horas."""
    total = horas + horas_por_acordo * acordos
    if total <= cap or cap <= 0:
        return horas, acordos
    max_acordos = cap / horas_por_acordo if horas_por_acordo > 0 else 0.0
    acordos_c = min(acordos, max_acordos)
    horas_c = max(0.0, min(horas, cap - horas_por_acordo * acordos_c))
    return horas_c, acordos_c


def receita_sala1_ensaios(horas: float, acordos: float) -> dict:
    s = st.session_state
    r_horas = horas * s.s1_preco_hora_ensaio
    r_acordos = acordos * s.s1_preco_acordo
    return {
        "Horas hora-a-hora": horas,
        "Receita horas (EUR)": r_horas,
        "Acordos mensais": acordos,
        "Receita acordos (EUR)": r_acordos,
        "Total Sala 1 Ensaios (EUR)": r_horas + r_acordos,
    }


def receita_sala2_ensaios(horas: float, horas_gravado: float, acordos: float) -> dict:
    s = st.session_state
    r_horas = horas * s.s2_preco_hora_ensaio
    r_extra = horas_gravado * s.s2_preco_extra_gravado
    r_acordos = acordos * s.s2_preco_acordo
    return {
        "Horas hora-a-hora": horas,
        "Receita horas (EUR)": r_horas,
        "Horas de ensaio gravado": horas_gravado,
        "Receita extra ensaio gravado (EUR)": r_extra,
        "Acordos mensais": acordos,
        "Receita acordos (EUR)": r_acordos,
        "Total Sala 2 Ensaios (EUR)": r_horas + r_extra + r_acordos,
    }


def receita_sala2_gravacao(horas_grav: float, faixas: float) -> dict:
    s = st.session_state
    r_grav = horas_grav * s.s2_preco_hora_gravacao
    r_mist = faixas * s.s2_preco_faixa_mistura
    return {
        "Horas de gravação profissional": horas_grav,
        "Receita gravação (EUR)": r_grav,
        "Faixas para mistura": faixas,
        "Receita mistura (EUR)": r_mist,
        "Total Sala 2 Gravação (EUR)": r_grav + r_mist,
    }


def receita_base_mes() -> dict:
    s = st.session_state
    # Sala 1
    h1, a1 = _cap_ensaios(s.s1_horas_ensaio_mes, s.s1_num_acordos,
                          s.s1_horas_por_acordo, s.cap_horas_ensaio)
    # Sala 2 ensaios
    h2, a2 = _cap_ensaios(s.s2_horas_ensaio_mes, s.s2_num_acordos,
                          s.s2_horas_por_acordo, s.cap_horas_ensaio)
    hg = min(s.s2_horas_ensaio_gravado, h2)  # ensaio gravado é subconjunto
    # Gravação
    hgrav = min(s.s2_horas_gravacao_mes, s.cap_horas_gravacao)
    faixas = min(s.s2_faixas_mistura_mes, s.cap_faixas_mistura)

    r_s1 = receita_sala1_ensaios(h1, a1)
    r_s2e = receita_sala2_ensaios(h2, hg, a2)
    r_s2g = receita_sala2_gravacao(hgrav, faixas)

    total = (r_s1["Total Sala 1 Ensaios (EUR)"] +
             r_s2e["Total Sala 2 Ensaios (EUR)"] +
             r_s2g["Total Sala 2 Gravação (EUR)"])

    return {
        "Sala 1 Ensaios": r_s1,
        "Sala 2 Ensaios": r_s2e,
        "Sala 2 Gravação": r_s2g,
        "Total geral (EUR)": total,
    }


# ---------------------------------------------------------------------------
# Simulação mensal
# ---------------------------------------------------------------------------
def simular() -> pd.DataFrame:
    s = st.session_state
    n = int(s.meses_simulacao)
    g = 1.0 + s.crescimento_mensal_pct / 100.0
    custo_fixo = custos_mensais_total()
    invest_ini = investimento_inicial_total()

    # Valores iniciais
    h1 = float(s.s1_horas_ensaio_mes)
    a1 = float(s.s1_num_acordos)
    h2 = float(s.s2_horas_ensaio_mes)
    hg = float(s.s2_horas_ensaio_gravado)
    a2 = float(s.s2_num_acordos)
    hgrav = float(s.s2_horas_gravacao_mes)
    faixas = float(s.s2_faixas_mistura_mes)

    caixa = -invest_ini
    linhas = []

    for i in range(1, n + 1):
        h1_c, a1_c = _cap_ensaios(h1, a1, s.s1_horas_por_acordo, s.cap_horas_ensaio)
        h2_c, a2_c = _cap_ensaios(h2, a2, s.s2_horas_por_acordo, s.cap_horas_ensaio)
        hg_c = min(hg, h2_c)
        hgrav_c = min(hgrav, s.cap_horas_gravacao)
        faixas_c = min(faixas, s.cap_faixas_mistura)

        r_s1 = h1_c * s.s1_preco_hora_ensaio + a1_c * s.s1_preco_acordo
        r_s2e = (h2_c * s.s2_preco_hora_ensaio
                 + hg_c * s.s2_preco_extra_gravado
                 + a2_c * s.s2_preco_acordo)
        r_s2g = hgrav_c * s.s2_preco_hora_gravacao + faixas_c * s.s2_preco_faixa_mistura
        receita = r_s1 + r_s2e + r_s2g
        margem = receita - custo_fixo
        caixa += margem

        linhas.append({
            "Mês": i,
            "Ano": (i - 1) // 12 + 1,
            "Receita Sala 1 Ensaios (EUR)": round(r_s1, 2),
            "Receita Sala 2 Ensaios (EUR)": round(r_s2e, 2),
            "Receita Sala 2 Gravação (EUR)": round(r_s2g, 2),
            "Receita total (EUR)": round(receita, 2),
            "Custos fixos (EUR)": round(custo_fixo, 2),
            "Margem mensal (EUR)": round(margem, 2),
            "Caixa acumulada (EUR)": round(caixa, 2),
        })

        # Crescimento composto
        h1 *= g
        a1 *= g
        h2 *= g
        hg *= g
        a2 *= g
        hgrav *= g
        faixas *= g

    return pd.DataFrame(linhas)


def payback_meses(sim: pd.DataFrame) -> int | None:
    linha = sim[sim["Caixa acumulada (EUR)"] >= 0].head(1)
    if linha.empty:
        return None
    return int(linha.iloc[0]["Mês"])


# ---------------------------------------------------------------------------
# Exportação Excel
# ---------------------------------------------------------------------------
def build_excel() -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        investimento_inicial_df().to_excel(writer, sheet_name="Investimento inicial", index=False)
        custos_mensais_df().to_excel(writer, sheet_name="Custos mensais", index=False)

        rec = receita_base_mes()
        rows = []
        for bloco in ["Sala 1 Ensaios", "Sala 2 Ensaios", "Sala 2 Gravação"]:
            for k, v in rec[bloco].items():
                rows.append({"Bloco": bloco, "Métrica": k, "Valor": v})
        rows.append({"Bloco": "TOTAL", "Métrica": "Receita bruta por mês (EUR)", "Valor": rec["Total geral (EUR)"]})
        pd.DataFrame(rows).to_excel(writer, sheet_name="Receita mensal", index=False)

        st.session_state["catalogo_artistas"].to_excel(writer, sheet_name="Catalogo artistas", index=False)
        simular().to_excel(writer, sheet_name="Simulacao mensal", index=False)

        params = {k: st.session_state.get(k) for k in DEFAULTS.keys()}
        pd.DataFrame(list(params.items()), columns=["Parâmetro", "Valor"]).to_excel(
            writer, sheet_name="Parametros", index=False
        )
    return buf.getvalue()


# ---------------------------------------------------------------------------
# UI principal
# ---------------------------------------------------------------------------
st.title("🎛️ Projeto Sala de Som")
st.caption("Simulação financeira editável para apresentação. Todas as células da barra lateral são customizáveis.")

tabs = st.tabs([
    "Investimento inicial",
    "Custos mensais",
    "Receita",
    "Catálogo de Artistas",
    "Sustentabilidade",
    "Download",
])

# --- Investimento inicial ---
with tabs[0]:
    st.subheader("Investimento inicial")
    df = investimento_inicial_df()
    st.dataframe(df, use_container_width=True, hide_index=True)
    total = df.iloc[-1]["Valor (EUR)"]
    st.metric("Total de investimento inicial", f"EUR {total:,.2f}")
    st.caption(
        "Compra do imóvel a pronto, sem empréstimo bancário. "
        "Ajusta o preço, o imposto de selo, as obras e o mobiliário na barra lateral."
    )

# --- Custos mensais ---
with tabs[1]:
    st.subheader("Custos mensais fixos")
    df = custos_mensais_df()
    st.dataframe(df, use_container_width=True, hide_index=True)
    total = df.iloc[-1]["Valor (EUR)"]
    st.metric("Total de custos mensais", f"EUR {total:,.2f}")

# --- Receita ---
with tabs[2]:
    st.subheader("Receita mensal")
    rec = receita_base_mes()

    st.markdown("#### Sala 1. Ensaios")
    df1 = pd.DataFrame(list(rec["Sala 1 Ensaios"].items()), columns=["Métrica", "Valor"])
    st.dataframe(df1, use_container_width=True, hide_index=True)

    st.markdown("#### Sala 2. Ensaios")
    df2 = pd.DataFrame(list(rec["Sala 2 Ensaios"].items()), columns=["Métrica", "Valor"])
    st.dataframe(df2, use_container_width=True, hide_index=True)

    st.markdown("#### Sala 2. Gravação")
    df3 = pd.DataFrame(list(rec["Sala 2 Gravação"].items()), columns=["Métrica", "Valor"])
    st.dataframe(df3, use_container_width=True, hide_index=True)

    st.markdown("---")
    custo_fix = custos_mensais_total()
    receita_bruta = rec["Total geral (EUR)"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Receita bruta por mês", f"EUR {receita_bruta:,.2f}")
    col2.metric("Custos fixos por mês", f"EUR {custo_fix:,.2f}")
    col3.metric("Margem por mês", f"EUR {receita_bruta - custo_fix:,.2f}")

# --- Catálogo de Artistas ---
with tabs[3]:
    st.subheader("Catálogo de Artistas")
    st.caption(
        "Lista de artistas que esperamos que usem o espaço. Podes editar, "
        "adicionar linhas (última linha em branco) e apagar directamente na tabela."
    )
    edited = st.data_editor(
        st.session_state["catalogo_artistas"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Artista": st.column_config.TextColumn("Artista", required=True),
            "Estilo": st.column_config.TextColumn("Estilo"),
            "Notas": st.column_config.TextColumn("Notas"),
        },
        key="catalogo_editor",
    )
    st.session_state["catalogo_artistas"] = edited
    st.metric("Total de artistas no catálogo", len(edited))

# --- Sustentabilidade ---
with tabs[4]:
    st.subheader("Sustentabilidade do projeto")

    sim = simular()
    invest_ini = investimento_inicial_total()
    custo_fix = custos_mensais_total()
    receita_base = receita_base_mes()["Total geral (EUR)"]
    margem_base = receita_base - custo_fix

    pay = payback_meses(sim)
    anos_sim = int(st.session_state["meses_simulacao"]) / 12.0
    caixa_final = float(sim.iloc[-1]["Caixa acumulada (EUR)"])

    def _euro_fmt(v: float) -> str:
        return f"€ {v:,.0f}".replace(",", " ")

    if pay is not None:
        pay_str = f"{pay/12:,.1f} anos"
        pay_sub = f"{pay} meses"
    else:
        pay_str = "não atinge"
        pay_sub = "ajusta parâmetros"

    st.markdown(
        f"""
        <div style="display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; margin-bottom:1rem;">
          <div style="background:#cfe6e3; padding:16px 18px; border-radius:12px; border:1px solid rgba(127,184,179,0.5);">
            <div style="font-size:0.85rem; color:#2d2a26; opacity:0.75;">Investimento inicial</div>
            <div style="font-size:1.6rem; font-weight:700; color:#2d2a26; line-height:1.15; margin-top:6px;">{_euro_fmt(invest_ini)}</div>
          </div>
          <div style="background:#e5dbf3; padding:16px 18px; border-radius:12px; border:1px solid rgba(179,157,219,0.5);">
            <div style="font-size:0.85rem; color:#2d2a26; opacity:0.75;">Imóvel pago em</div>
            <div style="font-size:1.6rem; font-weight:700; color:#2d2a26; line-height:1.15; margin-top:6px;">{pay_str}</div>
            <div style="font-size:0.8rem; color:#2d2a26; opacity:0.6; margin-top:2px;">{pay_sub}</div>
          </div>
          <div style="background:#fbecc4; padding:16px 18px; border-radius:12px; border:1px solid rgba(246,215,138,0.6);">
            <div style="font-size:0.85rem; color:#2d2a26; opacity:0.75;">Caixa após {anos_sim:,.0f} anos</div>
            <div style="font-size:1.6rem; font-weight:700; color:#2d2a26; line-height:1.15; margin-top:6px;">{_euro_fmt(caixa_final)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Mensagem principal
    if pay is not None and caixa_final > 0:
        st.success(
            f"Com uma estimativa conservadora (crescimento {st.session_state['crescimento_mensal_pct']:.1f}% "
            f"por mês, tectos realistas), o projeto **paga o imóvel em cerca de "
            f"{pay/12:,.1f} anos** e, ao fim de {anos_sim:,.0f} anos, tem uma caixa "
            f"acumulada de **EUR {caixa_final:,.0f}** para reinvestir ou distribuir."
        )
    elif pay is None:
        st.warning(
            "Nesta configuração o projeto não paga o imóvel dentro do horizonte simulado. "
            "Ajusta preço-hora, ocupação ou crescimento na barra lateral."
        )
    else:
        st.info(
            f"O imóvel paga-se em {pay/12:,.1f} anos, mas a caixa final é baixa. "
            "Podes esticar a simulação ou aumentar a ocupação."
        )

    # Gráfico principal: caixa acumulada + linha do imóvel pago
    chart_df = sim[["Mês", "Caixa acumulada (EUR)"]].copy()
    chart_df["Ano"] = chart_df["Mês"] / 12.0

    y_min = min(chart_df["Caixa acumulada (EUR)"].min(), 0.0)
    y_max = max(chart_df["Caixa acumulada (EUR)"].max(), 0.0)

    base = alt.Chart(chart_df).encode(
        x=alt.X("Ano:Q", title="Anos desde o arranque"),
    )

    area = base.mark_area(
        line={"color": "#7fb8b3", "strokeWidth": 3},
        color=alt.Gradient(
            gradient="linear",
            stops=[alt.GradientStop(color="#cfe6e3", offset=0),
                   alt.GradientStop(color="#7fb8b3", offset=1)],
            x1=1, x2=1, y1=1, y2=0,
        ),
    ).encode(
        y=alt.Y("Caixa acumulada (EUR):Q",
                title="Caixa acumulada (EUR)",
                scale=alt.Scale(domain=[y_min * 1.05, y_max * 1.05])),
        tooltip=[alt.Tooltip("Ano:Q", format=".1f"),
                 alt.Tooltip("Caixa acumulada (EUR):Q", format=",.0f")],
    )

    zero_line = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        color="#b39ddb", strokeDash=[6, 4], size=2,
    ).encode(y="y:Q")

    payback_layer = None
    if pay is not None:
        pay_df = pd.DataFrame({"Ano": [pay / 12.0]})
        payback_layer = alt.Chart(pay_df).mark_rule(
            color="#f6a55c", strokeDash=[2, 2], size=2,
        ).encode(x="Ano:Q")

    layers = [area, zero_line]
    if payback_layer is not None:
        layers.append(payback_layer)
    chart = alt.layer(*layers).properties(height=380).configure_axis(
        labelColor="#2d2a26", titleColor="#2d2a26",
    ).configure_view(strokeWidth=0)

    st.altair_chart(chart, use_container_width=True)
    st.caption(
        "A linha violeta tracejada marca o momento em que os fundadores recuperam tudo o que "
        "foi investido no arranque (caixa acumulada = 0). "
        + (f"A linha laranja tracejada marca o ano {pay/12:.1f}, quando o imóvel está pago."
           if pay is not None else "")
    )

    # Milestones
    st.markdown("#### Marcos ao longo do tempo")
    marcos_meses = [12, 60, 120, 240]
    marcos = []
    for m in marcos_meses:
        if m <= len(sim):
            row = sim.iloc[m - 1]
            marcos.append({
                "Fim do ano": m // 12,
                "Receita bruta anual (EUR)": round(sim.iloc[max(0, m-12):m]["Receita total (EUR)"].sum(), 0),
                "Margem anual (EUR)": round(sim.iloc[max(0, m-12):m]["Margem mensal (EUR)"].sum(), 0),
                "Caixa acumulada no fim (EUR)": round(row["Caixa acumulada (EUR)"], 0),
            })
    if marcos:
        st.dataframe(pd.DataFrame(marcos), use_container_width=True, hide_index=True)

    # Detalhes técnicos (colapsado)
    with st.expander("Ver simulação mês-a-mês (detalhe técnico)"):
        st.dataframe(sim, use_container_width=True, hide_index=True)

# --- Download ---
with tabs[5]:
    st.subheader("Download da spreadsheet")
    st.caption(
        "Descarrega uma versão Excel com todas as tabelas e os parâmetros atuais. "
        "Inclui investimento inicial, custos mensais, receita mensal detalhada, "
        "catálogo de artistas e simulação mês-a-mês completa."
    )
    from datetime import date
    data = build_excel()
    fname = f"projeto_sala_de_som_{date.today().isoformat()}.xlsx"
    st.download_button(
        label="Descarregar Excel",
        data=data,
        file_name=fname,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.caption(
        "Os valores só existem enquanto a sessão do browser estiver aberta. "
        "Para guardares uma versão, faz download do Excel. Cada download é uma versão datada."
    )
