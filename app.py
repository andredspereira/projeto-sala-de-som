"""
Projeto Sala de Som — Simulador financeiro
Streamlit app para planeamento de uma sala de ensaios + gravação em Portugal.
"""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
import streamlit as st

APP_PASSWORD = "projetosaladesom"

st.set_page_config(
    page_title="Projeto Sala de Som",
    page_icon="🎛️",
    layout="wide",
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
    # Investimento inicial
    "renda_mensal": 450.0,
    "meses_caucao": 2.0,
    "isolamento_esponjas": 800.0,
    "eletricidade_setup": 250.0,
    "mobiliario": 400.0,
    "sinaletica_marketing_inicial": 150.0,
    "registo_legal": 0.0,   # 0 se ficarem só na atividade aberta
    "extras_iniciais": 200.0,

    # Custos mensais fixos
    "renda_mensal_ongoing": 450.0,
    "agua": 25.0,
    "eletricidade": 90.0,
    "internet": 30.0,
    "seguros": 20.0,
    "limpeza": 40.0,
    "reparacoes_budget": 50.0,
    "contabilista": 0.0,    # atividade aberta simplificada pode dispensar
    "consumiveis": 20.0,
    "marketing_mensal": 30.0,
    "outros_mensais": 30.0,

    # Receita
    "preco_ensaio_hora": 10.0,
    "horas_ensaio_mes": 50.0,
    "preco_gravacao": 250.0,
    "gravacoes_mes": 3.0,
    "horas_por_gravacao": 2.0,

    # Impostos / retenção
    "iva_aplicavel": False,   # atividade aberta abaixo de 15k€/ano pode estar isenta (art.53)
    "taxa_irs_estimada": 0.0, # simplificado a 0 para conservador; utilizador ajusta

    # Simulação
    "meses_simulacao": 12,
    "crescimento_mensal_pct": 5.0,  # % de crescimento de ocupação por mês
    "cap_horas_ensaio": 200.0,      # tecto realista (8h/dia * ~25 dias)
    "cap_gravacoes": 15.0,
    "mes_inicio": date.today().replace(day=1),

    # Investimento externo (empréstimos de amigos)
    "invest_externo_total": 0.0,
    "invest_externo_mes_entrada": 1,  # em que mês entra
}


def _init_state():
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)


_init_state()


def _reset_defaults():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Sidebar — parâmetros editáveis
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Parâmetros")
    st.caption("Todos os valores são editáveis. As mudanças propagam-se a todas as tabelas.")

    if st.button("↺ Repor valores por defeito", use_container_width=True):
        _reset_defaults()
        st.rerun()

    with st.expander("💰 Investimento inicial", expanded=False):
        st.number_input("Renda mensal do espaço (€)", key="renda_mensal", min_value=0.0, step=25.0)
        st.number_input("Meses de renda adiantados (caução + 1º mês)", key="meses_caucao", min_value=0.0, step=0.5)
        st.number_input("Isolamento acústico / esponjas (€)", key="isolamento_esponjas", min_value=0.0, step=50.0)
        st.number_input("Ligações eléctricas / adaptações (€)", key="eletricidade_setup", min_value=0.0, step=25.0)
        st.number_input("Mobiliário básico (€)", key="mobiliario", min_value=0.0, step=25.0)
        st.number_input("Sinalética + marketing inicial (€)", key="sinaletica_marketing_inicial", min_value=0.0, step=25.0)
        st.number_input("Registo legal (associação/empresa) (€)", key="registo_legal", min_value=0.0, step=25.0,
                        help="0 se ficarem só na atividade aberta do André.")
        st.number_input("Outros custos iniciais (€)", key="extras_iniciais", min_value=0.0, step=25.0)

    with st.expander("🧾 Custos mensais fixos", expanded=False):
        st.number_input("Renda mensal (€)", key="renda_mensal_ongoing", min_value=0.0, step=25.0)
        st.number_input("Água (€)", key="agua", min_value=0.0, step=5.0)
        st.number_input("Eletricidade (€)", key="eletricidade", min_value=0.0, step=5.0)
        st.number_input("Internet (€)", key="internet", min_value=0.0, step=5.0)
        st.number_input("Seguros (€)", key="seguros", min_value=0.0, step=5.0)
        st.number_input("Limpeza (€)", key="limpeza", min_value=0.0, step=5.0)
        st.number_input("Budget reparações (€)", key="reparacoes_budget", min_value=0.0, step=5.0)
        st.number_input("Contabilista (€)", key="contabilista", min_value=0.0, step=10.0,
                        help="Atividade aberta em regime simplificado pode dispensar; empresa/associação normalmente não.")
        st.number_input("Consumíveis (cabos, cordas, pilhas…) (€)", key="consumiveis", min_value=0.0, step=5.0)
        st.number_input("Marketing mensal (€)", key="marketing_mensal", min_value=0.0, step=5.0)
        st.number_input("Outros custos mensais (€)", key="outros_mensais", min_value=0.0, step=5.0)

    with st.expander("🎤 Receita", expanded=True):
        st.number_input("Preço por hora de ensaio (€)", key="preco_ensaio_hora", min_value=0.0, step=1.0)
        st.number_input("Horas de ensaio no 1º mês", key="horas_ensaio_mes", min_value=0.0, step=5.0)
        st.number_input("Preço por gravação (€/faixa)", key="preco_gravacao", min_value=0.0, step=10.0)
        st.number_input("Gravações no 1º mês", key="gravacoes_mes", min_value=0.0, step=1.0)
        st.number_input("Horas por gravação", key="horas_por_gravacao", min_value=0.0, step=0.5)

    with st.expander("📈 Simulação", expanded=False):
        st.number_input("Meses a simular", key="meses_simulacao", min_value=1, max_value=60, step=1)
        st.number_input("Crescimento de ocupação por mês (%)", key="crescimento_mensal_pct", min_value=-50.0, max_value=100.0, step=1.0,
                        help="Aplicado a horas de ensaio e a gravações. Composto mês a mês.")
        st.number_input("Tecto de horas de ensaio/mês", key="cap_horas_ensaio", min_value=0.0, step=10.0,
                        help="Limite realista. 8h/dia * 25 dias ≈ 200h. As gravações ocupam o mesmo espaço.")
        st.number_input("Tecto de gravações/mês", key="cap_gravacoes", min_value=0.0, step=1.0)
        st.date_input("Mês de arranque", key="mes_inicio")

    with st.expander("🤝 Investimento externo", expanded=False):
        st.number_input("Total emprestado por amigos (€)", key="invest_externo_total", min_value=0.0, step=100.0)
        st.number_input("Mês em que entra o empréstimo (1 = mês inicial)", key="invest_externo_mes_entrada",
                        min_value=1, max_value=60, step=1)

    with st.expander("🧮 Impostos (estimativa grosseira)", expanded=False):
        st.checkbox("Aplicar IVA às receitas (23%)", key="iva_aplicavel",
                    help="Atividade aberta abaixo de ~15k€/ano de faturação pode estar isenta (art. 53º CIVA). "
                         "Ativa se ultrapassarem esse limite ou se optarem por regime normal.")
        st.number_input("Taxa efetiva de IRS/IRC estimada (%)", key="taxa_irs_estimada", min_value=0.0, max_value=50.0, step=1.0,
                        help="Deixa em 0 para uma leitura conservadora do cashflow bruto.")


# ---------------------------------------------------------------------------
# Cálculos partilhados
# ---------------------------------------------------------------------------
def investimento_inicial_df() -> pd.DataFrame:
    s = st.session_state
    rows = [
        ("Renda adiantada + caução", s.renda_mensal * s.meses_caucao),
        ("Isolamento acústico / esponjas", s.isolamento_esponjas),
        ("Ligações eléctricas / adaptações", s.eletricidade_setup),
        ("Mobiliário básico", s.mobiliario),
        ("Sinalética + marketing inicial", s.sinaletica_marketing_inicial),
        ("Registo legal", s.registo_legal),
        ("Outros custos iniciais", s.extras_iniciais),
    ]
    df = pd.DataFrame(rows, columns=["Rubrica", "Valor (€)"])
    df.loc[len(df)] = ["TOTAL", df["Valor (€)"].sum()]
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
    df = pd.DataFrame(rows, columns=["Rubrica", "Valor (€)"])
    df.loc[len(df)] = ["TOTAL / mês", df["Valor (€)"].sum()]
    return df


def receita_base_mes() -> dict:
    s = st.session_state
    receita_ensaios = s.preco_ensaio_hora * s.horas_ensaio_mes
    receita_gravacoes = s.preco_gravacao * s.gravacoes_mes
    horas_ocupadas = s.horas_ensaio_mes + s.gravacoes_mes * s.horas_por_gravacao
    return {
        "Horas de ensaio": s.horas_ensaio_mes,
        "Receita ensaios (€)": receita_ensaios,
        "Gravações": s.gravacoes_mes,
        "Receita gravações (€)": receita_gravacoes,
        "Horas totais de ocupação": horas_ocupadas,
        "Receita bruta / mês (€)": receita_ensaios + receita_gravacoes,
    }


def simular_meses() -> pd.DataFrame:
    s = st.session_state
    n = int(s.meses_simulacao)
    crescimento = 1 + s.crescimento_mensal_pct / 100.0
    custo_fixo = custos_mensais_df().iloc[-1]["Valor (€)"]

    horas_ensaio = s.horas_ensaio_mes
    gravacoes = s.gravacoes_mes

    invest_inicial_total = investimento_inicial_df().iloc[-1]["Valor (€)"]

    linhas = []
    caixa_acumulada = -invest_inicial_total  # arranca no vermelho pelo investimento
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

        # Data do mês
        year = mes0.year + (mes0.month - 1 + i) // 12
        month = (mes0.month - 1 + i) % 12 + 1
        mes_label = f"{year}-{month:02d}"

        linhas.append({
            "Mês": mes_label,
            "Horas ensaio": round(m_horas, 1),
            "Gravações": round(m_grav, 2),
            "Receita ensaios (€)": round(receita_ensaios, 2),
            "Receita gravações (€)": round(receita_gravacoes, 2),
            "Receita bruta (€)": round(receita_bruta, 2),
            "IVA a entregar (€)": round(iva, 2),
            "Custos fixos (€)": round(custo_fixo, 2),
            "Margem pré-imposto (€)": round(margem_pre_imposto, 2),
            "IRS/IRC estimado (€)": round(irs, 2),
            "Margem líquida (€)": round(margem_liq, 2),
            "Investimento externo (€)": round(invest_externo_mes, 2),
            "Caixa acumulada (€)": round(caixa_acumulada, 2),
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
            writer, sheet_name="Receita mês base", index=False
        )

        simular_meses().to_excel(writer, sheet_name="Simulação mensal", index=False)

        # Sheet de parâmetros para transparência
        params = {k: st.session_state.get(k) for k in DEFAULTS.keys()}
        pd.DataFrame(list(params.items()), columns=["Parâmetro", "Valor"]).to_excel(
            writer, sheet_name="Parâmetros", index=False
        )
    return buf.getvalue()


# ---------------------------------------------------------------------------
# UI principal
# ---------------------------------------------------------------------------
st.title("🎛️ Projeto Sala de Som — Simulador")
st.caption("Simulação financeira editável para apresentação. Todas as células da barra lateral são customizáveis.")

tabs = st.tabs([
    "📌 Estrutura legal",
    "💰 Investimento inicial",
    "🧾 Custos mensais",
    "🎤 Receita",
    "📈 Simulação mensal",
    "⬇️ Download",
])

# --- Tab 1: Estrutura legal ---
with tabs[0]:
    st.subheader("Que forma legal usar?")
    st.markdown(
        """
**Recomendação prática para arrancar**: **usarem a atividade aberta que o André já tem** como pessoa singular.
É a via mais barata (0 € de setup), a mais rápida, e não obriga ninguém a receber salário.
Depois, se o projeto crescer ou se a Câmara / IEFP começar a exigir enquadramento próprio, migram para associação ou empresa.

---

### Opção A — Atividade aberta (pessoa singular, o que o André já tem)
- **Custos de setup**: 0 €.
- **Contabilidade**: regime simplificado até 200 000 € de faturação/ano — dispensa contabilista certificado.
- **IVA**: se a faturação anual ficar abaixo de ~15 000 € podem estar isentos pelo art. 53º do CIVA. Acima disso passam a cobrar 23%.
- **Segurança social**: contribuições trimestrais como trabalhador independente (calculadas sobre 70% do rendimento; primeiros 12 meses isentos se for a 1ª abertura, no vosso caso já não).
- **IRS**: rendimentos entram na categoria B do André; 75% do rendimento é considerado tributável no simplificado.
- **Como acomodar sócios/gerentes sem salário**: eles simplesmente colaboram sem vínculo. Ninguém precisa de estar declarado. Se receberem algo pontual, faz-se um recibo verde individual.
- **Grande limitação**: **responsabilidade ilimitada** (o património pessoal do André responde por dívidas do negócio) e **toda a faturação é do André** — o que também significa que toda a carga fiscal cai sobre ele.

### Opção B — Associação Cultural sem fins lucrativos
- **Custos de setup**: ~150–250 € (Ato Constitutivo Online no Espaço Empresa ou notário) + publicação obrigatória. Precisam de **mínimo 3 sócios fundadores**.
- **Sem salários obrigatórios**: os órgãos sociais (direção, mesa da assembleia, conselho fiscal) **são obrigatoriamente não remunerados por defeito** — encaixa exatamente no vosso caso.
- **Fiscalidade**: podem estar isentos de IRC nas atividades culturais sem fins lucrativos; obrigadas a IES anual mesmo assim.
- **Vantagens**: acesso a **candidaturas culturais** (DGArtes, Câmara Municipal, Fundação Calouste Gulbenkian, GDA), imagem pública alinhada com o projeto (sala de ensaios comunitária), e o património separa-se das pessoas.
- **Desvantagens**: **não podem distribuir lucros** — tudo o que sobrar tem de ser reinvestido no objeto social. Se o objetivo final for tirarem dinheiro para vocês, não serve.
- **Burocracia**: assembleias gerais anuais, atas, IES, contabilidade organizada normalmente exigida se ultrapassarem certos limiares.

### Opção C — Sociedade por Quotas (Lda.) via *Empresa na Hora*
- **Custos de setup**: ~360 € + capital social (mínimo legal 1 €, na prática 1 000–5 000 €).
- **Contabilista certificado obrigatório**: ~100–200 €/mês. Isto sozinho já mata a viabilidade nos primeiros meses do vosso plano.
- **Gerência sem remuneração**: **é possível** — o gerente pode estar dispensado de descontos para a Segurança Social se declarar que não é remunerado *e* tiver enquadramento noutra atividade (ex.: a atividade aberta do André). Sem esse enquadramento, há risco de a SS presumir remuneração e cobrar contribuições sobre o IAS.
- **Vantagem principal**: responsabilidade limitada ao capital social.
- **Recomendação**: **evitar para já**. Só faz sentido quando a faturação justificar os ~1 500–2 500 €/ano só em contabilidade + fiscalidade.

---

### Comparação rápida
"""
    )
    comp = pd.DataFrame(
        [
            ["Setup (€)", "0", "~200", "~360 + capital"],
            ["Contabilista obrigatório", "Não (simplificado)", "Depende (geralmente sim)", "Sim"],
            ["Sócios/gerentes podem não ter salário", "Sim (só o titular)", "Sim (por regra)", "Sim, mas com riscos SS"],
            ["Podem distribuir lucros", "Sim (é rendimento do titular)", "Não", "Sim (após IRC)"],
            ["Responsabilidade pessoal", "Ilimitada", "Limitada à associação", "Limitada ao capital"],
            ["Acesso a apoios culturais", "Muito limitado", "Alto", "Baixo"],
            ["Melhor para arrancar já", "✅", "⚠️ 2ª fase", "❌ prematuro"],
        ],
        columns=["Critério", "Atividade aberta", "Associação Cultural", "Lda."],
    )
    st.dataframe(comp, use_container_width=True, hide_index=True)

    st.info(
        "**Sugestão de caminho**: arrancam em nome do André (0 € de setup, 0 € de contabilista). "
        "Passados 6–12 meses, se a ocupação se consolidar e quiserem candidatar-se a apoios culturais, "
        "abrem uma Associação Cultural em paralelo e passam parte da operação para lá. "
        "A Lda. só se justifica se a faturação anual passar largamente os 30 000 €.",
        icon="💡",
    )

# --- Tab 2: Investimento inicial ---
with tabs[1]:
    st.subheader("Investimento inicial")
    df = investimento_inicial_df()
    st.dataframe(df, use_container_width=True, hide_index=True)
    total = df.iloc[-1]["Valor (€)"]
    st.metric("Total de investimento inicial", f"€ {total:,.2f}")
    st.caption("Edita qualquer valor na barra lateral → **Investimento inicial**.")

# --- Tab 3: Custos mensais ---
with tabs[2]:
    st.subheader("Custos mensais fixos")
    df = custos_mensais_df()
    st.dataframe(df, use_container_width=True, hide_index=True)
    total = df.iloc[-1]["Valor (€)"]
    st.metric("Total de custos mensais", f"€ {total:,.2f}")

# --- Tab 4: Receita ---
with tabs[3]:
    st.subheader("Receita — mês base (o 1º mês da simulação)")
    rec = receita_base_mes()
    df = pd.DataFrame(list(rec.items()), columns=["Métrica", "Valor"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    custo_fix = custos_mensais_df().iloc[-1]["Valor (€)"]
    receita_bruta = rec["Receita bruta / mês (€)"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Receita bruta / mês", f"€ {receita_bruta:,.2f}")
    col2.metric("Custos fixos / mês", f"€ {custo_fix:,.2f}")
    col3.metric("Margem bruta / mês", f"€ {receita_bruta - custo_fix:,.2f}",
                delta=f"{(receita_bruta - custo_fix):.0f} €")

    horas_ocupacao_max = 8 * 25  # 8h/dia, 25 dias/mês
    st.caption(
        f"Ocupação atual: **{rec['Horas totais de ocupação']:.1f} h/mês** "
        f"contra ~{horas_ocupacao_max} h/mês teóricas (8h/dia × 25 dias)."
    )

# --- Tab 5: Simulação mensal ---
with tabs[4]:
    st.subheader("Simulação mês a mês")
    st.caption(
        "A ocupação cresce à taxa que definires na barra lateral, com tetos realistas. "
        "O investimento inicial é lançado como caixa negativa no arranque."
    )
    sim = simular_meses()
    st.dataframe(sim, use_container_width=True, hide_index=True)

    st.markdown("#### Caixa acumulada")
    st.line_chart(sim.set_index("Mês")[["Caixa acumulada (€)"]])

    st.markdown("#### Receita vs custos")
    st.bar_chart(sim.set_index("Mês")[["Receita bruta (€)", "Custos fixos (€)"]])

    # Breakeven
    breakeven_row = sim[sim["Caixa acumulada (€)"] >= 0].head(1)
    if breakeven_row.empty:
        st.warning(
            "Nos meses simulados a caixa acumulada nunca chega a positivo. "
            "Ajusta preço, ocupação, crescimento, ou entra investimento externo.",
            icon="⚠️",
        )
    else:
        mes_be = breakeven_row.iloc[0]["Mês"]
        st.success(f"Ponto de equilíbrio de caixa atingido em **{mes_be}**.", icon="✅")

# --- Tab 6: Download ---
with tabs[5]:
    st.subheader("Download da spreadsheet")
    st.caption(
        "Descarrega uma versão Excel com todas as tabelas e os parâmetros atuais. "
        "Cada vez que carregas no botão, o ficheiro é gerado com os valores que estão a ver no ecrã."
    )
    data = build_excel()
    fname = f"projeto_sala_de_som_{date.today().isoformat()}.xlsx"
    st.download_button(
        label="⬇️ Descarregar Excel",
        data=data,
        file_name=fname,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.markdown("---")
    st.caption(
        "Nota: os valores só existem enquanto a sessão do browser estiver aberta. "
        "Para guardares uma 'versão', faz download do Excel — cada download é uma versão datada."
    )
