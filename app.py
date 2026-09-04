"""
Projeto Sala de Som. Simulador financeiro.
Streamlit app para planeamento de uma sala de ensaios e gravação de música em Portugal.
"""
from __future__ import annotations

import io
from datetime import date

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
    div[data-testid="stAlert"] {
        border-radius: 12px;
    }
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
    "renda_mensal": 450.0,
    "meses_caucao": 2.0,
    "isolamento_esponjas": 800.0,
    "eletricidade_setup": 250.0,
    "mobiliario": 400.0,
    "sinaletica_marketing_inicial": 150.0,
    "registo_legal": 0.0,
    "extras_iniciais": 200.0,

    "renda_mensal_ongoing": 450.0,
    "agua": 25.0,
    "eletricidade": 90.0,
    "internet": 30.0,
    "seguros": 20.0,
    "limpeza": 40.0,
    "reparacoes_budget": 50.0,
    "contabilista": 0.0,
    "consumiveis": 20.0,
    "marketing_mensal": 30.0,
    "outros_mensais": 30.0,

    "preco_ensaio_hora": 10.0,
    "horas_ensaio_mes": 50.0,
    "preco_gravacao": 250.0,
    "gravacoes_mes": 3.0,
    "horas_por_gravacao": 2.0,

    "iva_aplicavel": False,
    "taxa_irs_estimada": 0.0,

    "meses_simulacao": 12,
    "crescimento_mensal_pct": 5.0,
    "cap_horas_ensaio": 200.0,
    "cap_gravacoes": 15.0,
    "mes_inicio": date.today().replace(day=1),

    "invest_externo_total": 0.0,
    "invest_externo_mes_entrada": 1,
}


def _init_state():
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)


_init_state()


def _reset_defaults():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Sidebar. Parâmetros editáveis
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Parâmetros")
    st.caption("Todos os valores são editáveis. As mudanças propagam-se a todas as tabelas.")

    if st.button("Repor valores por defeito", use_container_width=True):
        _reset_defaults()
        st.rerun()

    with st.expander("Investimento inicial", expanded=False):
        st.number_input("Renda mensal do espaço (EUR)", key="renda_mensal", min_value=0.0, step=25.0)
        st.number_input("Meses de renda adiantados (caução mais 1 mês)", key="meses_caucao", min_value=0.0, step=0.5)
        st.number_input("Isolamento acústico e esponjas (EUR)", key="isolamento_esponjas", min_value=0.0, step=50.0)
        st.number_input("Ligações eléctricas e adaptações (EUR)", key="eletricidade_setup", min_value=0.0, step=25.0)
        st.number_input("Mobiliário básico (EUR)", key="mobiliario", min_value=0.0, step=25.0)
        st.number_input("Sinalética e marketing inicial (EUR)", key="sinaletica_marketing_inicial", min_value=0.0, step=25.0)
        st.number_input("Registo legal (associação ou empresa) (EUR)", key="registo_legal", min_value=0.0, step=25.0,
                        help="0 se ficarem só na atividade aberta do André.")
        st.number_input("Outros custos iniciais (EUR)", key="extras_iniciais", min_value=0.0, step=25.0)

    with st.expander("Custos mensais fixos", expanded=False):
        st.number_input("Renda mensal (EUR)", key="renda_mensal_ongoing", min_value=0.0, step=25.0)
        st.number_input("Água (EUR)", key="agua", min_value=0.0, step=5.0)
        st.number_input("Eletricidade (EUR)", key="eletricidade", min_value=0.0, step=5.0)
        st.number_input("Internet (EUR)", key="internet", min_value=0.0, step=5.0)
        st.number_input("Seguros (EUR)", key="seguros", min_value=0.0, step=5.0)
        st.number_input("Limpeza (EUR)", key="limpeza", min_value=0.0, step=5.0)
        st.number_input("Budget reparações (EUR)", key="reparacoes_budget", min_value=0.0, step=5.0)
        st.number_input("Contabilista (EUR)", key="contabilista", min_value=0.0, step=10.0,
                        help="Atividade aberta em regime simplificado pode dispensar; empresa ou associação normalmente não.")
        st.number_input("Consumíveis, cabos, cordas, pilhas (EUR)", key="consumiveis", min_value=0.0, step=5.0)
        st.number_input("Marketing mensal (EUR)", key="marketing_mensal", min_value=0.0, step=5.0)
        st.number_input("Outros custos mensais (EUR)", key="outros_mensais", min_value=0.0, step=5.0)

    with st.expander("Receita", expanded=True):
        st.number_input("Preço por hora de ensaio (EUR)", key="preco_ensaio_hora", min_value=0.0, step=1.0)
        st.number_input("Horas de ensaio no 1.º mês", key="horas_ensaio_mes", min_value=0.0, step=5.0)
        st.number_input("Preço por gravação (EUR por faixa)", key="preco_gravacao", min_value=0.0, step=10.0)
        st.number_input("Gravações no 1.º mês", key="gravacoes_mes", min_value=0.0, step=1.0)
        st.number_input("Horas por gravação", key="horas_por_gravacao", min_value=0.0, step=0.5)

    with st.expander("Simulação", expanded=False):
        st.number_input("Meses a simular", key="meses_simulacao", min_value=1, max_value=60, step=1)
        st.number_input("Crescimento de ocupação por mês (%)", key="crescimento_mensal_pct",
                        min_value=-50.0, max_value=100.0, step=1.0,
                        help="Aplicado a horas de ensaio e a gravações. Composto mês a mês.")
        st.number_input("Tecto de horas de ensaio por mês", key="cap_horas_ensaio", min_value=0.0, step=10.0,
                        help="Limite realista. 8h por dia vezes 25 dias dá cerca de 200h. As gravações ocupam o mesmo espaço.")
        st.number_input("Tecto de gravações por mês", key="cap_gravacoes", min_value=0.0, step=1.0)
        st.date_input("Mês de arranque", key="mes_inicio")

    with st.expander("Investimento externo", expanded=False):
        st.number_input("Total emprestado por amigos (EUR)", key="invest_externo_total", min_value=0.0, step=100.0)
        st.number_input("Mês em que entra o empréstimo (1 igual ao mês inicial)",
                        key="invest_externo_mes_entrada", min_value=1, max_value=60, step=1)

    with st.expander("Impostos (estimativa grosseira)", expanded=False):
        st.checkbox("Aplicar IVA às receitas (23%)", key="iva_aplicavel",
                    help="Atividade aberta abaixo de cerca de 15 mil euros por ano de faturação pode estar isenta "
                         "(art. 53.º do CIVA). Ativa se ultrapassarem esse limite ou se optarem por regime normal.")
        st.number_input("Taxa efetiva de IRS ou IRC estimada (%)", key="taxa_irs_estimada",
                        min_value=0.0, max_value=50.0, step=1.0,
                        help="Deixa em 0 para uma leitura conservadora do cashflow bruto.")


# ---------------------------------------------------------------------------
# Cálculos partilhados
# ---------------------------------------------------------------------------
def investimento_inicial_df() -> pd.DataFrame:
    s = st.session_state
    rows = [
        ("Renda adiantada e caução", s.renda_mensal * s.meses_caucao),
        ("Isolamento acústico e esponjas", s.isolamento_esponjas),
        ("Ligações eléctricas e adaptações", s.eletricidade_setup),
        ("Mobiliário básico", s.mobiliario),
        ("Sinalética e marketing inicial", s.sinaletica_marketing_inicial),
        ("Registo legal", s.registo_legal),
        ("Outros custos iniciais", s.extras_iniciais),
    ]
    df = pd.DataFrame(rows, columns=["Rubrica", "Valor (EUR)"])
    df.loc[len(df)] = ["TOTAL", df["Valor (EUR)"].sum()]
    return df


def custos_mensais_df() -> pd.DataFrame:
    s = st.session_state
    rows = [
        ("Renda", s.renda_mensal_ongoing),
        ("Água", s.agua),
        ("Eletricidade", s.eletricidade),
        ("Internet", s.internet),
        ("Seguros", s.seguros),
        ("Limpeza", s.limpeza),
        ("Reparações (budget)", s.reparacoes_budget),
        ("Contabilista", s.contabilista),
        ("Consumíveis", s.consumiveis),
        ("Marketing", s.marketing_mensal),
        ("Outros", s.outros_mensais),
    ]
    df = pd.DataFrame(rows, columns=["Rubrica", "Valor (EUR)"])
    df.loc[len(df)] = ["TOTAL por mês", df["Valor (EUR)"].sum()]
    return df


def receita_base_mes() -> dict:
    s = st.session_state
    receita_ensaios = s.preco_ensaio_hora * s.horas_ensaio_mes
    receita_gravacoes = s.preco_gravacao * s.gravacoes_mes
    horas_ocupadas = s.horas_ensaio_mes + s.gravacoes_mes * s.horas_por_gravacao
    return {
        "Horas de ensaio": s.horas_ensaio_mes,
        "Receita ensaios (EUR)": receita_ensaios,
        "Gravações": s.gravacoes_mes,
        "Receita gravações (EUR)": receita_gravacoes,
        "Horas totais de ocupação": horas_ocupadas,
        "Receita bruta por mês (EUR)": receita_ensaios + receita_gravacoes,
    }


def simular_meses() -> pd.DataFrame:
    s = st.session_state
    n = int(s.meses_simulacao)
    crescimento = 1 + s.crescimento_mensal_pct / 100.0
    custo_fixo = custos_mensais_df().iloc[-1]["Valor (EUR)"]

    horas_ensaio = s.horas_ensaio_mes
    gravacoes = s.gravacoes_mes

    invest_inicial_total = investimento_inicial_df().iloc[-1]["Valor (EUR)"]

    linhas = []
    caixa_acumulada = -invest_inicial_total
    mes0 = s.mes_inicio

    for i in range(n):
        m_horas = min(horas_ensaio, s.cap_horas_ensaio)
        m_grav = min(gravacoes, s.cap_gravacoes)

        receita_ensaios = m_horas * s.preco_ensaio_hora
        receita_gravacoes = m_grav * s.preco_gravacao
        receita_bruta = receita_ensaios + receita_gravacoes

        iva = receita_bruta * 0.23 / 1.23 if s.iva_aplicavel else 0.0
        receita_liq_iva = receita_bruta - iva

        margem_pre_imposto = receita_liq_iva - custo_fixo
        irs = max(margem_pre_imposto, 0) * (s.taxa_irs_estimada / 100.0)
        margem_liq = margem_pre_imposto - irs

        invest_externo_mes = s.invest_externo_total if (i + 1) == int(s.invest_externo_mes_entrada) else 0.0
        caixa_acumulada += margem_liq + invest_externo_mes

        year = mes0.year + (mes0.month - 1 + i) // 12
        month = (mes0.month - 1 + i) % 12 + 1
        mes_label = f"{year}-{month:02d}"

        linhas.append({
            "Mês": mes_label,
            "Horas ensaio": round(m_horas, 1),
            "Gravações": round(m_grav, 2),
            "Receita ensaios (EUR)": round(receita_ensaios, 2),
            "Receita gravações (EUR)": round(receita_gravacoes, 2),
            "Receita bruta (EUR)": round(receita_bruta, 2),
            "IVA a entregar (EUR)": round(iva, 2),
            "Custos fixos (EUR)": round(custo_fixo, 2),
            "Margem pré-imposto (EUR)": round(margem_pre_imposto, 2),
            "IRS ou IRC estimado (EUR)": round(irs, 2),
            "Margem líquida (EUR)": round(margem_liq, 2),
            "Investimento externo (EUR)": round(invest_externo_mes, 2),
            "Caixa acumulada (EUR)": round(caixa_acumulada, 2),
        })

        horas_ensaio *= crescimento
        gravacoes *= crescimento

    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Exportação Excel
# ---------------------------------------------------------------------------
def build_excel() -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        investimento_inicial_df().to_excel(writer, sheet_name="Investimento inicial", index=False)
        custos_mensais_df().to_excel(writer, sheet_name="Custos mensais", index=False)

        rec = receita_base_mes()
        pd.DataFrame(list(rec.items()), columns=["Métrica", "Valor"]).to_excel(
            writer, sheet_name="Receita mes base", index=False
        )

        simular_meses().to_excel(writer, sheet_name="Simulacao mensal", index=False)

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
    "Simulação mensal",
    "Download",
])

# --- Investimento inicial ---
with tabs[0]:
    st.subheader("Investimento inicial")
    df = investimento_inicial_df()
    st.dataframe(df, use_container_width=True, hide_index=True)
    total = df.iloc[-1]["Valor (EUR)"]
    st.metric("Total de investimento inicial", f"EUR {total:,.2f}")
    st.caption("Edita qualquer valor na barra lateral em Investimento inicial.")

# --- Custos mensais ---
with tabs[1]:
    st.subheader("Custos mensais fixos")
    df = custos_mensais_df()
    st.dataframe(df, use_container_width=True, hide_index=True)
    total = df.iloc[-1]["Valor (EUR)"]
    st.metric("Total de custos mensais", f"EUR {total:,.2f}")

# --- Receita ---
with tabs[2]:
    st.subheader("Receita no mês base (o 1.º mês da simulação)")
    rec = receita_base_mes()
    df = pd.DataFrame(list(rec.items()), columns=["Métrica", "Valor"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    custo_fix = custos_mensais_df().iloc[-1]["Valor (EUR)"]
    receita_bruta = rec["Receita bruta por mês (EUR)"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Receita bruta por mês", f"EUR {receita_bruta:,.2f}")
    col2.metric("Custos fixos por mês", f"EUR {custo_fix:,.2f}")
    col3.metric("Margem bruta por mês", f"EUR {receita_bruta - custo_fix:,.2f}",
                delta=f"{(receita_bruta - custo_fix):.0f} EUR")

    horas_ocupacao_max = 8 * 25
    st.caption(
        f"Ocupação atual: {rec['Horas totais de ocupação']:.1f} h por mês "
        f"contra cerca de {horas_ocupacao_max} h por mês teóricas (8h por dia vezes 25 dias)."
    )

# --- Simulação mensal ---
with tabs[3]:
    st.subheader("Simulação mês a mês")
    st.caption(
        "A ocupação cresce à taxa que definires na barra lateral, com tetos realistas. "
        "O investimento inicial é lançado como caixa negativa no arranque."
    )
    sim = simular_meses()
    st.dataframe(sim, use_container_width=True, hide_index=True)

    st.markdown("#### Caixa acumulada")
    st.line_chart(sim.set_index("Mês")[["Caixa acumulada (EUR)"]])

    st.markdown("#### Receita vs custos")
    st.bar_chart(sim.set_index("Mês")[["Receita bruta (EUR)", "Custos fixos (EUR)"]])

    breakeven_row = sim[sim["Caixa acumulada (EUR)"] >= 0].head(1)
    if breakeven_row.empty:
        st.warning(
            "Nos meses simulados a caixa acumulada nunca chega a positivo. "
            "Ajusta preço, ocupação, crescimento, ou entra investimento externo."
        )
    else:
        mes_be = breakeven_row.iloc[0]["Mês"]
        st.success(f"Ponto de equilíbrio de caixa atingido em {mes_be}.")

# --- Download ---
with tabs[4]:
    st.subheader("Download da spreadsheet")
    st.caption(
        "Descarrega uma versão Excel com todas as tabelas e os parâmetros atuais. "
        "Cada vez que carregas no botão, o ficheiro é gerado com os valores que estão a ver no ecrã."
    )
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
        "Nota: os valores só existem enquanto a sessão do browser estiver aberta. "
        "Para guardares uma versão, faz download do Excel. Cada download é uma versão datada."
    )
