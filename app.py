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

    # Custos mensais fixos (sem contribuicao para ressarcimento)
    "custos_espaco_extra": 75.0,   # condominio, taxas de manutencao, etc.
    "pct_imi_anual": 0.20,         # % anual sobre preco de compra (VPT tipicamente e mais baixo)
    "agua": 30.0,
    "eletricidade": 75.0,
    "internet": 15.0,
    "seguros": 40.0,
    "consumiveis_gerais": 50.0,
    "consumiveis_estudio": 25.0,
    "armazenamento_online": 30.0,
    "marketing_mensal": 5.0,

    # Contribuição mensal para ressarcimento do imóvel (definido na tab final)
    "contribuicao_mensal": 1000.0,

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
    "meses_simulacao": 360,
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
        st.caption(
            "Custos mensais fixos, sem a contribuição para ressarcimento do imóvel. "
            "Essa contribuição é decidida na tab Sustentabilidade e é adicionada aos custos aí."
        )
        st.number_input("Custos mensais relacionados com o espaço (EUR)",
                        key="custos_espaco_extra", min_value=0.0, step=5.0,
                        help="Condomínio, taxas de manutenção do prédio, fundo de reserva, etc.")
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
        ("Custos mensais relacionados com o espaço", s.custos_espaco_extra),
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


def custo_ressarcir_imovel() -> float:
    """Custo do imóvel a ressarcir: imóvel + selo + obras."""
    s = st.session_state
    return s.preco_imovel + s.preco_imovel * s.pct_imposto_selo / 100.0 + s.obras_iniciais


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
def simular(contribuicao: float) -> pd.DataFrame:
    """Simula mês a mês. A `contribuicao` é paga até o imóvel estar totalmente ressarcido."""
    s = st.session_state
    n = int(s.meses_simulacao)
    g = 1.0 + s.crescimento_mensal_pct / 100.0
    custo_fixo_base = custos_mensais_total()
    a_ressarcir = custo_ressarcir_imovel()

    # Valores iniciais
    h1 = float(s.s1_horas_ensaio_mes)
    a1 = float(s.s1_num_acordos)
    h2 = float(s.s2_horas_ensaio_mes)
    hg = float(s.s2_horas_ensaio_gravado)
    a2 = float(s.s2_num_acordos)
    hgrav = float(s.s2_horas_gravacao_mes)
    faixas = float(s.s2_faixas_mistura_mes)

    caixa_empresa = 0.0
    pago_acumulado = 0.0
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

        # Contribuição este mês (só até o imóvel estar totalmente ressarcido)
        restante = max(a_ressarcir - pago_acumulado, 0.0)
        contrib_mes = min(contribuicao, restante)
        pago_acumulado += contrib_mes

        margem = receita - custo_fixo_base - contrib_mes
        caixa_empresa += margem

        linhas.append({
            "Mês": i,
            "Ano": (i - 1) // 12 + 1,
            "Receita Sala 1 Ensaios (EUR)": round(r_s1, 2),
            "Receita Sala 2 Ensaios (EUR)": round(r_s2e, 2),
            "Receita Sala 2 Gravação (EUR)": round(r_s2g, 2),
            "Receita total (EUR)": round(receita, 2),
            "Custos fixos (EUR)": round(custo_fixo_base, 2),
            "Contribuição de ressarcimento (EUR)": round(contrib_mes, 2),
            "Margem mensal (EUR)": round(margem, 2),
            "Caixa da empresa (EUR)": round(caixa_empresa, 2),
            "Total ressarcido (EUR)": round(pago_acumulado, 2),
            "Falta ressarcir (EUR)": round(max(a_ressarcir - pago_acumulado, 0.0), 2),
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


def meses_para_ressarcir(contribuicao: float) -> int | None:
    a_ressarcir = custo_ressarcir_imovel()
    if contribuicao <= 0:
        return None
    import math
    return int(math.ceil(a_ressarcir / contribuicao))


def estimativa_maxima_lucro(contribuicao: float) -> dict:
    """Cenário teórico: Sala 1 cheia com ensaios hora-a-hora, Sala 2 cheia com gravações
    ao máximo + faixas de mistura no máximo."""
    s = st.session_state
    max_r_s1 = s.cap_horas_ensaio * s.s1_preco_hora_ensaio
    max_r_s2 = (s.cap_horas_gravacao * s.s2_preco_hora_gravacao
                + s.cap_faixas_mistura * s.s2_preco_faixa_mistura)
    max_receita = max_r_s1 + max_r_s2
    custos = custos_mensais_total()
    margem_com_contrib = max_receita - custos - contribuicao
    margem_sem_contrib = max_receita - custos
    return {
        "receita_max_s1": max_r_s1,
        "receita_max_s2": max_r_s2,
        "receita_max_total": max_receita,
        "margem_max_com_contrib": margem_com_contrib,
        "margem_max_sem_contrib": margem_sem_contrib,
    }


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
        simular(float(st.session_state["contribuicao_mensal"])).to_excel(
            writer, sheet_name="Simulacao mensal", index=False
        )

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

    ressarcir = custo_ressarcir_imovel()
    st.info(
        f"**Custo a ressarcir**: o imóvel + imposto de selo + obras somam "
        f"**EUR {ressarcir:,.2f}**, e este valor é ressarcido pela empresa através "
        f"da contribuição mensal definida na tab Sustentabilidade. "
        f"O mobiliário e material (**EUR {st.session_state.mobiliario_material:,.2f}**) "
        f"fica a cargo dos fundadores no arranque."
    )
    st.caption("Compra do imóvel a pronto, sem empréstimo bancário. Todos os valores são editáveis na barra lateral.")

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

    def _smart_round(v: float) -> float:
        """Arredonda a 3 algarismos significativos para leitura fácil."""
        if v is None:
            return v
        av = abs(v)
        if av < 1000:
            step = 1
        elif av < 10000:
            step = 100
        elif av < 100000:
            step = 1000
        elif av < 1000000:
            step = 10000
        else:
            step = 100000
        return round(v / step) * step

    def _euro_fmt(v: float) -> str:
        return f"€ {_smart_round(v):,.0f}".replace(",", " ")

    a_ressarcir = custo_ressarcir_imovel()
    custos_fixos_mes = custos_mensais_total()

    st.markdown(
        f"O **preço do imóvel + imposto de selo + obras** somam "
        f"**{_euro_fmt(a_ressarcir)}**. Este valor é totalmente ressarcido através de uma "
        f"contribuição mensal fixa da empresa. Ajusta abaixo para ver o impacto no prazo "
        f"e no lucro."
    )

    st.number_input(
        "Contribuição mensal para ressarcimento do imóvel (EUR)",
        key="contribuicao_mensal",
        min_value=0.0,
        step=50.0,
        help="Adiciona-se aos custos mensais e é pago todos os meses até o imóvel estar "
             "totalmente ressarcido.",
    )
    contribuicao = float(st.session_state["contribuicao_mensal"])

    sim = simular(contribuicao)
    anos_sim = int(st.session_state["meses_simulacao"]) / 12.0
    caixa_final_empresa = float(sim.iloc[-1]["Caixa da empresa (EUR)"])
    pay = meses_para_ressarcir(contribuicao)

    if pay is not None:
        pay_str = f"{pay/12:,.1f} anos"
        pay_sub = f"{pay} meses"
        # Caixa da empresa no mês em que o imóvel está totalmente ressarcido
        if pay <= len(sim):
            caixa_no_ressarcimento = float(sim.iloc[pay - 1]["Caixa da empresa (EUR)"])
        else:
            caixa_no_ressarcimento = None
    else:
        pay_str = "sem contribuição"
        pay_sub = "aumenta a contribuição"
        caixa_no_ressarcimento = None

    # Cartões de KPI
    caixa_ressarc_str = _euro_fmt(caixa_no_ressarcimento) if caixa_no_ressarcimento is not None else "estica a sim."
    st.markdown(
        f"""
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin-bottom:1rem;">
          <div style="background:#cfe6e3; padding:14px 16px; border-radius:12px; border:1px solid rgba(127,184,179,0.5);">
            <div style="font-size:0.78rem; color:#2d2a26; opacity:0.75;">Total a ressarcir</div>
            <div style="font-size:1.35rem; font-weight:700; color:#2d2a26; line-height:1.15; margin-top:4px; white-space:nowrap;">{_euro_fmt(a_ressarcir)}</div>
            <div style="font-size:0.72rem; color:#2d2a26; opacity:0.6; margin-top:2px;">imóvel + selo + obras</div>
          </div>
          <div style="background:#e5dbf3; padding:14px 16px; border-radius:12px; border:1px solid rgba(179,157,219,0.5);">
            <div style="font-size:0.78rem; color:#2d2a26; opacity:0.75;">Imóvel totalmente ressarcido em</div>
            <div style="font-size:1.35rem; font-weight:700; color:#2d2a26; line-height:1.15; margin-top:4px; white-space:nowrap;">{pay_str}</div>
            <div style="font-size:0.72rem; color:#2d2a26; opacity:0.6; margin-top:2px;">{pay_sub}</div>
          </div>
          <div style="background:#fbecc4; padding:14px 16px; border-radius:12px; border:1px solid rgba(246,215,138,0.6);">
            <div style="font-size:0.78rem; color:#2d2a26; opacity:0.75;">Caixa quando ressarcido</div>
            <div style="font-size:1.35rem; font-weight:700; color:#2d2a26; line-height:1.15; margin-top:4px; white-space:nowrap;">{caixa_ressarc_str}</div>
            <div style="font-size:0.72rem; color:#2d2a26; opacity:0.6; margin-top:2px;">na empresa</div>
          </div>
          <div style="background:#cfe6e3; padding:14px 16px; border-radius:12px; border:1px solid rgba(127,184,179,0.5);">
            <div style="font-size:0.78rem; color:#2d2a26; opacity:0.75;">Caixa aos {anos_sim:,.0f} anos</div>
            <div style="font-size:1.35rem; font-weight:700; color:#2d2a26; line-height:1.15; margin-top:4px; white-space:nowrap;">{_euro_fmt(caixa_final_empresa)}</div>
            <div style="font-size:0.72rem; color:#2d2a26; opacity:0.6; margin-top:2px;">acumulada na empresa</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Aviso conforme viabilidade
    receita_mes_1 = float(sim.iloc[0]["Receita total (EUR)"])
    margem_mes_1 = receita_mes_1 - custos_fixos_mes - contribuicao
    if pay is None:
        st.warning(
            "Sem contribuição mensal não há ressarcimento do imóvel. Aumenta o valor para começar a ressarcir."
        )
    elif margem_mes_1 < 0:
        st.warning(
            f"Com esta contribuição, no arranque a empresa perde **{_euro_fmt(-margem_mes_1)}** por mês. "
            "O crescimento pode recuperar isto, mas os fundadores podem ter de suportar a diferença "
            "nos primeiros meses. Considera baixar a contribuição ou esticar o prazo de ressarcimento."
        )
    else:
        st.success(
            f"Com uma contribuição de **{_euro_fmt(contribuicao)} por mês**, o imóvel fica totalmente "
            f"ressarcido em **{pay/12:,.1f} anos**. Nesse momento a empresa terá "
            f"**{caixa_ressarc_str}** em caixa e, depois disso, deixa de pagar a contribuição, "
            f"pelo que a margem passa a ser lucro dos fundadores. Ao fim de {anos_sim:,.0f} anos, "
            f"caixa acumulada de **{_euro_fmt(caixa_final_empresa)}**."
        )

    # Gráfico 1: Ressarcimento do imóvel
    st.markdown("#### Ressarcimento do imóvel")
    chart_df = sim[["Mês", "Total ressarcido (EUR)"]].copy()
    chart_df["Ano"] = chart_df["Mês"] / 12.0

    ressarc_area = alt.Chart(chart_df).mark_area(
        line={"color": "#7fb8b3", "strokeWidth": 3},
        color=alt.Gradient(
            gradient="linear",
            stops=[alt.GradientStop(color="#cfe6e3", offset=0),
                   alt.GradientStop(color="#7fb8b3", offset=1)],
            x1=1, x2=1, y1=1, y2=0,
        ),
    ).encode(
        x=alt.X("Ano:Q", title="Anos desde o arranque"),
        y=alt.Y("Total ressarcido (EUR):Q", title="Total ressarcido (EUR)"),
        tooltip=[alt.Tooltip("Ano:Q", format=".1f"),
                 alt.Tooltip("Total ressarcido (EUR):Q", format=",.0f")],
    )
    ressarc_target = alt.Chart(pd.DataFrame({"y": [a_ressarcir]})).mark_rule(
        color="#f6a55c", strokeDash=[6, 4], size=2,
    ).encode(y="y:Q")
    ressarc_target_text = alt.Chart(pd.DataFrame({"y": [a_ressarcir], "label": [f"Alvo: {_euro_fmt(a_ressarcir)}"]})).mark_text(
        align="left", dx=8, dy=-8, color="#2d2a26", fontSize=12,
    ).encode(y="y:Q", text="label:N")

    layers1 = [ressarc_area, ressarc_target, ressarc_target_text]
    if pay is not None and pay <= len(sim):
        pay_rule = alt.Chart(pd.DataFrame({"Ano": [pay / 12.0]})).mark_rule(
            color="#b39ddb", strokeDash=[2, 2], size=2,
        ).encode(x="Ano:Q")
        layers1.append(pay_rule)

    chart1 = alt.layer(*layers1).properties(height=280).configure_axis(
        labelColor="#2d2a26", titleColor="#2d2a26",
    ).configure_view(strokeWidth=0)
    st.altair_chart(chart1, use_container_width=True)
    st.caption(
        "A linha laranja marca o valor total a ressarcir. "
        + (f"A linha violeta tracejada marca o ano {pay/12:.1f}, quando o imóvel fica totalmente ressarcido." if pay is not None else "")
    )

    # Gráfico 2: Caixa da empresa
    st.markdown("#### Caixa acumulada da empresa")
    chart_df2 = sim[["Mês", "Caixa da empresa (EUR)"]].copy()
    chart_df2["Ano"] = chart_df2["Mês"] / 12.0
    y_min = min(chart_df2["Caixa da empresa (EUR)"].min(), 0.0)
    y_max = max(chart_df2["Caixa da empresa (EUR)"].max(), 0.0)

    caixa_line = alt.Chart(chart_df2).mark_area(
        line={"color": "#b39ddb", "strokeWidth": 3},
        color=alt.Gradient(
            gradient="linear",
            stops=[alt.GradientStop(color="#e5dbf3", offset=0),
                   alt.GradientStop(color="#b39ddb", offset=1)],
            x1=1, x2=1, y1=1, y2=0,
        ),
    ).encode(
        x=alt.X("Ano:Q", title="Anos desde o arranque"),
        y=alt.Y("Caixa da empresa (EUR):Q", title="Caixa da empresa (EUR)",
                scale=alt.Scale(domain=[y_min * 1.1 if y_min < 0 else 0, y_max * 1.05])),
        tooltip=[alt.Tooltip("Ano:Q", format=".1f"),
                 alt.Tooltip("Caixa da empresa (EUR):Q", format=",.0f")],
    )
    zero_line = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        color="#2d2a26", strokeDash=[4, 4], size=1,
    ).encode(y="y:Q")
    layers2 = [caixa_line, zero_line]
    if pay is not None and pay <= len(sim):
        pay_rule2 = alt.Chart(pd.DataFrame({"Ano": [pay / 12.0]})).mark_rule(
            color="#f6a55c", strokeDash=[2, 2], size=2,
        ).encode(x="Ano:Q")
        layers2.append(pay_rule2)
    chart2 = alt.layer(*layers2).properties(height=280).configure_axis(
        labelColor="#2d2a26", titleColor="#2d2a26",
    ).configure_view(strokeWidth=0)
    st.altair_chart(chart2, use_container_width=True)
    st.caption(
        "Enquanto o imóvel não estiver totalmente ressarcido, a empresa retira todos os meses a contribuição. "
        "Depois disso a margem fica toda em caixa. "
        + (f"A linha laranja tracejada marca o fim do ressarcimento (ano {pay/12:.1f})." if pay is not None else "")
    )

    # Milestones
    st.markdown("#### Marcos ao longo do tempo")
    marcos_meses = [12, 60, 120, 240, 360]
    marcos = []
    for m in marcos_meses:
        if m <= len(sim):
            row = sim.iloc[m - 1]
            receita_anual = sim.iloc[max(0, m-12):m]["Receita total (EUR)"].sum()
            margem_anual = sim.iloc[max(0, m-12):m]["Margem mensal (EUR)"].sum()
            marcos.append({
                "Fim do ano": m // 12,
                "Receita bruta anual (EUR)": _smart_round(receita_anual),
                "Margem anual (EUR)": _smart_round(margem_anual),
                "Total ressarcido (EUR)": _smart_round(row["Total ressarcido (EUR)"]),
                "Caixa da empresa no fim (EUR)": _smart_round(row["Caixa da empresa (EUR)"]),
            })
    if marcos:
        st.dataframe(pd.DataFrame(marcos), use_container_width=True, hide_index=True)

    # Estimativa máxima de lucro
    st.markdown("---")
    st.markdown("#### Estimativa máxima de lucro")
    st.caption(
        "Cenário teórico se as salas estivessem sempre no máximo de ocupação: "
        "Sala 1 cheia com ensaios hora-a-hora ao preço definido, Sala 2 cheia com gravação "
        "profissional ao preço definido e mistura ao máximo de faixas por mês."
    )
    max_est = estimativa_maxima_lucro(contribuicao)

    st.markdown(
        f"""
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin-bottom:0.5rem;">
          <div style="background:#fbecc4; padding:14px 16px; border-radius:12px; border:1px solid rgba(246,215,138,0.6);">
            <div style="font-size:0.78rem; color:#2d2a26; opacity:0.75;">Receita máxima Sala 1</div>
            <div style="font-size:1.3rem; font-weight:700; color:#2d2a26; margin-top:4px; white-space:nowrap;">{_euro_fmt(max_est['receita_max_s1'])}</div>
            <div style="font-size:0.72rem; color:#2d2a26; opacity:0.6;">{st.session_state.cap_horas_ensaio:,.0f} h × {st.session_state.s1_preco_hora_ensaio:,.0f} €</div>
          </div>
          <div style="background:#fbecc4; padding:14px 16px; border-radius:12px; border:1px solid rgba(246,215,138,0.6);">
            <div style="font-size:0.78rem; color:#2d2a26; opacity:0.75;">Receita máxima Sala 2</div>
            <div style="font-size:1.3rem; font-weight:700; color:#2d2a26; margin-top:4px; white-space:nowrap;">{_euro_fmt(max_est['receita_max_s2'])}</div>
            <div style="font-size:0.72rem; color:#2d2a26; opacity:0.6;">gravação + mistura no máximo</div>
          </div>
          <div style="background:#cfe6e3; padding:14px 16px; border-radius:12px; border:1px solid rgba(127,184,179,0.5);">
            <div style="font-size:0.78rem; color:#2d2a26; opacity:0.75;">Lucro máximo por mês</div>
            <div style="font-size:1.3rem; font-weight:700; color:#2d2a26; margin-top:4px; white-space:nowrap;">{_euro_fmt(max_est['margem_max_com_contrib'])}</div>
            <div style="font-size:0.72rem; color:#2d2a26; opacity:0.6;">com contribuição atual</div>
          </div>
          <div style="background:#e5dbf3; padding:14px 16px; border-radius:12px; border:1px solid rgba(179,157,219,0.5);">
            <div style="font-size:0.78rem; color:#2d2a26; opacity:0.75;">Lucro máximo por mês</div>
            <div style="font-size:1.3rem; font-weight:700; color:#2d2a26; margin-top:4px; white-space:nowrap;">{_euro_fmt(max_est['margem_max_sem_contrib'])}</div>
            <div style="font-size:0.72rem; color:#2d2a26; opacity:0.6;">após imóvel ressarcido</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        f"Receita máxima total: **{_euro_fmt(max_est['receita_max_total'])}/mês**. "
        f"Lucro anual máximo com contribuição: **{_euro_fmt(max_est['margem_max_com_contrib']*12)}**. "
        f"Lucro anual máximo depois do ressarcimento: **{_euro_fmt(max_est['margem_max_sem_contrib']*12)}**."
    )

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
