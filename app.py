import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# --- Configuração da Página ---
st.set_page_config(page_title="🏭 Dashboard Científico de Produção", layout="wide")

# --- URLs dos CSVs (CORRETAS E ATUALIZADAS) ---
url_data = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/main/updated_dataframe.csv"
url_log = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/refs/heads/main/updated_dataframe_log.csv"
url_pcp = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/refs/heads/main/updated_pcp_kpiv1.csv"
url_pre = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/refs/heads/main/updated_PRE_kpiv1.csv"
url_mod = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/refs/heads/main/updated_MOD_kpiv1.csv"
url_almx = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/refs/heads/main/updated_ALMX_kpiv1.csv"

# --- Carregar dados principais: OS (updated_dataframe.csv) ---
try:
    df = pd.read_csv(url_data, sep=',', on_bad_lines='warn', encoding='utf-8', low_memory=False)
    df = df.rename(columns={
        'DATA DE ENTREGA': 'DATA_DE_ENTREGA',
        'ANO-MES entrega': 'MES_ANO',
        'MES ENTREGA': 'MES_ENTREGA',
        'ANO ENTREGA': 'ANO_ENTREGA',
        'CATEGORIA CONVERSOR': 'CATEGORIA_CONVERSOR',
        'FAMILIA1': 'FAMILIA',
        'QUANTIDADE PONDERADA': 'QTD_PONDERADA',
        'OS UNICA': 'OS_UNICA',
        'CODIGO/CLIENTE': 'CODIGO_CLIENTE',
        'PRODUTO': 'PRODUTO',
        'CANAL': 'CANAL',
        'STATUS': 'STATUS'
    })

    df['QTD'] = pd.to_numeric(df['QTD'], errors='coerce')
    df['QTD_PONDERADA'] = pd.to_numeric(df['QTD_PONDERADA'], errors='coerce')
    df['MES_ENTREGA'] = pd.to_numeric(df['MES_ENTREGA'], errors='coerce')
    df['ANO_ENTREGA'] = pd.to_numeric(df['ANO_ENTREGA'], errors='coerce')
    df['DATA_DE_ENTREGA'] = pd.to_datetime(df['DATA_DE_ENTREGA'], format='%d/%m/%Y', errors='coerce', dayfirst=True)

    df = df.dropna(subset=['QTD', 'ANO_ENTREGA', 'RESPONSAVEL', 'EQUIPE', 'DATA_DE_ENTREGA'])
    df = df[df['QTD'] > 0]
    df['MES_ANO'] = df['DATA_DE_ENTREGA'].dt.to_period('M').astype(str)
    df['FAMILIA'] = df['FAMILIA'].str.upper()
    df['CATEGORIA_CONVERSOR'] = df['CATEGORIA_CONVERSOR'].fillna('N/A').str.upper()

except Exception as e:
    st.error(f"❌ Erro ao carregar updated_dataframe.csv: {e}")
    st.stop()

# --- Carregar dados de capacidade: updated_dataframe_log (1).csv ---
try:
    log = pd.read_csv(url_log, sep=",", encoding="utf-8")
    log.columns = log.columns.str.strip()
    log = log.rename(columns={
        "MES": "MES_ANO",
        "DIAS_UTEIS_TRABALHADOS": "DIAS_UTEIS",
        "SABADOS_TRABALHADOS": "SABADOS",
        "HORAS EXTRAS TRABALHADAS": "HE_DIA",
        "FUNCIONARIOS_MESA": "FUNC_MESA",
        "PRODUCAO_BRUTA": "PROD",
        "PRODUTOS_HORA_FUNCIONARIO": "PROD_HORA"
    })
    log["MES_ANO"] = log["MES_ANO"].astype(str)
    log["PROD"] = pd.to_numeric(log["PROD"], errors="coerce")
    log["PROD_HORA"] = pd.to_numeric(log["PROD_HORA"], errors="coerce")
    log["FUNC_MESA"] = pd.to_numeric(log["FUNC_MESA"], errors="coerce")
    st.success("✅ Dados de capacidade (updated_dataframe_log.csv) carregados com sucesso.")
except Exception as e:
    st.error(f"❌ Erro ao carregar updated_dataframe_log.csv: {e}")
    st.stop()

# --- Carregar dados dos setores (PCP, PRE, MOD, ALMX) ---
def load_sector_data(url, name):
    try:
        df_sec = pd.read_csv(url, header=None, encoding='utf-8')
        df_sec = df_sec.set_index(0).T
        months = [f"{y}-{m:02d}" for y in range(2023, 2026) for m in range(1, 13)]
        df_sec.index = months[:len(df_sec)]
        df_sec.index.name = 'MES_ANO'
        return df_sec.apply(pd.to_numeric, errors="coerce")
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar {name}: {e}")
        return None

pcp = load_sector_data(url_pcp, "PCP")
pre = load_sector_data(url_pre, "Pré-Produção")
mod = load_sector_data(url_mod, "MOD")
almx = load_sector_data(url_almx, "Almoxarifado")

# --- Métrica: QTD vs QTD_PONDERADA ---
st.sidebar.markdown("### 📊 Métrica de Produção")
use_ponderada = st.sidebar.checkbox("Usar Quantidade Ponderada", value=False)
valor_coluna = 'QTD_PONDERADA' if use_ponderada else 'QTD'
label_metrica = 'Quantidade Ponderada' if use_ponderada else 'Quantidade Bruta (QTD)'

# --- Filtros Dinâmicos ---
st.sidebar.header("🔍 Filtros")

if st.sidebar.button("🔄 Resetar Filtros"):
    st.session_state.clear()
    st.rerun()

# Anos disponíveis
anos_disponiveis = sorted(df['ANO_ENTREGA'].dropna().unique().astype(int))
ano_filtro_ativo = st.sidebar.checkbox("Filtrar por Ano", value=False)
anos_selecionados = anos_disponiveis if not ano_filtro_ativo else st.sidebar.multiselect("Ano", anos_disponiveis, default=anos_disponiveis, key="anos")

# Meses disponíveis (dinâmico por ano)
meses_disponiveis = sorted(df['MES_ENTREGA'].dropna().unique())
mes_filtro_ativo = st.sidebar.checkbox("Filtrar por Mês", value=False)
if mes_filtro_ativo:
    # Filtrar meses apenas para anos selecionados
    df_temp = df[df['ANO_ENTREGA'].isin(anos_selecionados)]
    meses_disponiveis_filtrados = sorted(df_temp['MES_ENTREGA'].dropna().unique())
    meses_selecionados = st.sidebar.multiselect("Mês", meses_disponiveis_filtrados, default=meses_disponiveis_filtrados, key="mes")
else:
    meses_selecionados = meses_disponiveis

# Filtro por Família
familia_disponiveis = sorted(df['FAMILIA'].dropna().unique())
familia_filtro_ativo = st.sidebar.checkbox("Filtrar por Família", value=False)
familias_selecionadas = familia_disponiveis if not familia_filtro_ativo else st.sidebar.multiselect("Família", familia_disponiveis, default=familia_disponiveis, key="familia")

# Filtro por Categoria
categoria_disponiveis = sorted(df['CATEGORIA_CONVERSOR'].dropna().unique())
categoria_filtro_ativo = st.sidebar.checkbox("Filtrar por Categoria", value=False)
categorias_selecionadas = categoria_disponiveis if not categoria_filtro_ativo else st.sidebar.multiselect("Categoria", categoria_disponiveis, default=categoria_disponiveis, key="categoria")

# Responsável
responsavel_disponiveis = sorted(df['RESPONSAVEL'].dropna().unique())
responsavel_filtro_ativo = st.sidebar.checkbox("Filtrar por Responsável", value=False)
responsavel_selecionados = responsavel_disponiveis if not responsavel_filtro_ativo else st.sidebar.multiselect("Responsável", responsavel_disponiveis, default=responsavel_disponiveis, key="responsavel")

# Equipe
equipes_disponiveis = sorted(df['EQUIPE'].dropna().unique())
equipe_filtro_ativo = st.sidebar.checkbox("Filtrar por Equipe", value=False)
equipes_selecionados = equipes_disponiveis if not equipe_filtro_ativo else st.sidebar.multiselect("Equipe", equipes_disponiveis, default=equipes_disponiveis, key="equipe")

# Canal
canal_disponiveis = sorted(df['CANAL'].dropna().unique())
canal_filtro_ativo = st.sidebar.checkbox("Filtrar por Canal", value=False)
canais_selecionados = canal_disponiveis if not canal_filtro_ativo else st.sidebar.multiselect("Canal", canal_disponiveis, default=canal_disponiveis, key="canal")

# --- Filtragem ---
mask = (
    df['ANO_ENTREGA'].isin(anos_selecionados) &
    df['MES_ENTREGA'].isin(meses_selecionados) &
    df['RESPONSAVEL'].isin(responsavel_selecionados) &
    df['EQUIPE'].isin(equipes_selecionados) &
    df['CANAL'].isin(canais_selecionados) &
    df['FAMILIA'].isin(familias_selecionadas) &
    df['CATEGORIA_CONVERSOR'].isin(categorias_selecionadas)
)
df_filtrado = df[mask].copy()

# --- Função auxiliar: Info Tooltip ---
def info_tooltip(label, text):
    with st.container():
        col_i, col_c = st.columns([1, 20])
        with col_i:
            st.markdown(f"<h4 style='text-align: center; margin: 0;'>ℹ️</h4>", unsafe_allow_html=True)
        with col_c:
            st.markdown(label)
        with st.expander("📘 Como ler este gráfico"):
            st.markdown(text)

# --- Métrica Ativa ---
st.markdown(f"### 📌 Métrica Ativa: **{label_metrica}**")
st.markdown("---")

# --- Título ---
st.title("🏭 Dashboard Científico de Produção")
st.markdown("Análise avançada da linha de produção com métricas de desempenho, tendências e eficiência.")
st.markdown("---")

# --- Métricas Gerais ---
st.subheader("📈 Métricas Gerais")
if not df_filtrado.empty:
    total = df_filtrado[valor_coluna].sum()
    media = df_filtrado[valor_coluna].mean()
    num_os = len(df_filtrado)
    categoria_top = df_filtrado['CATEGORIA_CONVERSOR'].mode().iloc[0] if not df_filtrado['CATEGORIA_CONVERSOR'].mode().empty else "N/A"
else:
    total = media = num_os = 0
    categoria_top = "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Produção Total", f"{total:,.0f}")
col2.metric("Média por OS", f"{media:,.0f}")
col3.metric("Total de OS", f"{num_os:,}")
col4.metric("Categoria Dominante", categoria_top)
st.markdown("---")

# --- Abas ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Produção Diária",
    "👥 Líderes & Equipes",
    "📦 Produtos & Categorias",
    "📈 Análise Avançada",
    "💰 Digital Twin & Custos",
    "📅 Comparativo Anual (2024 vs 2025)",
    "📉 Comparativo Detalhado por Categoria"
])

# ====================
# ABAS DO DASHBOARD
# ====================

# --- Aba 1: Produção Diária ---
with tab1:
    info_tooltip(f"### 1. Produção Diária com Média Móvel (7 dias) - {label_metrica}", "Mostra a produção diária com uma linha de tendência (média móvel de 7 dias).")
    if not df_filtrado.empty:
        daily = df_filtrado.groupby('DATA_DE_ENTREGA')[valor_coluna].sum().reset_index().sort_values('DATA_DE_ENTREGA')
        daily['Média Móvel'] = daily[valor_coluna].rolling(window=7).mean()
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=daily['DATA_DE_ENTREGA'], y=daily[valor_coluna], mode='lines+markers', name=label_metrica, line=dict(color='blue')))
        fig1.add_trace(go.Scatter(x=daily['DATA_DE_ENTREGA'], y=daily['Média Móvel'], mode='lines', name='Média Móvel (7 dias)', line=dict(color='red', width=3)))
        fig1.update_layout(title="Produção Diária", xaxis_title="Data", yaxis_title="Quantidade", title_x=0.1, hovermode='x unified')
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir a produção diária.")

    info_tooltip(f"### 4. Distribuição do Tamanho dos Lotes ({label_metrica})", "Histograma que mostra como os tamanhos dos lotes estão distribuídos. Boxplot acima mostra outliers.")
    if not df_filtrado.empty:
        fig4 = px.histogram(df_filtrado, x=valor_coluna, nbins=30, marginal="box", title=f"Distribuição do Tamanho dos Lotes de Produção ({label_metrica})")
        fig4.update_layout(template="plotly_white")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir a distribuição de lotes.")

# --- Aba 2: Líderes & Equipes ---
with tab2:
    info_tooltip(f"### 3. Top 5 Líderes por Volume - {label_metrica}", "Os 5 líderes com maior volume de produção. Use para reconhecimento e análise de desempenho.")
    if not df_filtrado.empty:
        top_resp = df_filtrado.groupby('RESPONSAVEL')[valor_coluna].sum().nlargest(5).reset_index().sort_values(valor_coluna, ascending=True)
        fig3 = px.bar(top_resp, x=valor_coluna, y='RESPONSAVEL', orientation='h', title="Top 5 Líderes por Volume", text=valor_coluna)
        fig3.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir os líderes.")

    info_tooltip(f"### 9. Frequência de OS por Líder ({label_metrica})", "Número total de OS por líder (não volume). Mostra engajamento e distribuição de carga.")
    if not df_filtrado.empty:
        os_count = df_filtrado.groupby('RESPONSAVEL').size().reset_index(name='OS Count').sort_values('OS Count', ascending=True)
        fig9 = px.bar(os_count, x='OS Count', y='RESPONSAVEL', orientation='h', title="Número de OS por Líder (Frequência)", text='OS Count')
        fig9.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig9, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir frequência por líder.")

    info_tooltip("### 🏆 7. Leaderboard Mensal por Produção", "Mostra os 3 principais líderes por mês. Barras empilhadas mostram evolução do desempenho.")
    if not df_filtrado.empty:
        leaderboard = df_filtrado.groupby(['MES_ANO', 'RESPONSAVEL'])[valor_coluna].sum().reset_index().sort_values(['MES_ANO', valor_coluna], ascending=[True, False])
        top3 = leaderboard.groupby('MES_ANO').head(3)
        fig_lb = px.bar(top3, x=valor_coluna, y='MES_ANO', color='RESPONSAVEL', orientation='h', title="Top 3 Líderes por Mês")
        fig_lb.update_layout(barmode='stack')
        st.plotly_chart(fig_lb, use_container_width=True)
    else:
        st.info("Nenhum dado para leaderboard.")

# --- Aba 3: Produtos & Categorias ---
with tab3:
    info_tooltip(f"### 🔥 Representatividade por Família ({label_metrica})", "Mostra a participação de cada família de produtos na produção total.")
    if not df_filtrado.empty:
        fam = df_filtrado.groupby('FAMILIA')[valor_coluna].sum().reset_index().sort_values(valor_coluna, ascending=False)
        fig_fam_pie = px.pie(fam, names='FAMILIA', values=valor_coluna, title="Distribuição por Família", hole=0.4)
        fig_fam_pie.update_traces(textinfo='percent+label', textposition='inside')
        st.plotly_chart(fig_fam_pie, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir por família.")

    # --- Nova: Representatividade por Categoria ---
    info_tooltip(f"### 🔥 Representatividade por Categoria ({label_metrica})", "Mostra a participação de cada categoria de produtos na produção total.")
    if not df_filtrado.empty:
        cat = df_filtrado.groupby('CATEGORIA_CONVERSOR')[valor_coluna].sum().reset_index().sort_values(valor_coluna, ascending=False)
        fig_cat_pie = px.pie(cat, names='CATEGORIA_CONVERSOR', values=valor_coluna, title="Distribuição por Categoria", hole=0.4)
        fig_cat_pie.update_traces(textinfo='percent+label', textposition='inside')
        st.plotly_chart(fig_cat_pie, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir por categoria.")

    info_tooltip(f"### 6. Produção por Canal de Venda ({label_metrica})", "Gráfico de pizza mostrando a participação de cada canal.")
    if not df_filtrado.empty:
        canal = df_filtrado.groupby('CANAL')[valor_coluna].sum().reset_index()
        fig6 = px.pie(canal, names='CANAL', values=valor_coluna, title="Distribuição da Produção por Canal de Venda", hole=0.4)
        fig6.update_traces(textinfo='percent+label')
        st.plotly_chart(fig6, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir por canal.")

    info_tooltip(f"### 8. Tamanho Médio do Lote por Categoria ({label_metrica})", "Mostra o tamanho médio dos lotes por categoria.")
    if not df_filtrado.empty:
        avg_qtd = df_filtrado.groupby('CATEGORIA_CONVERSOR')[valor_coluna].mean().reset_index().sort_values(valor_coluna, ascending=True)
        fig8 = px.bar(avg_qtd, x=valor_coluna, y='CATEGORIA_CONVERSOR', orientation='h', title="Tamanho Médio do Lote por Categoria", text=valor_coluna)
        fig8.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig8, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir o tamanho médio por categoria.")

    info_tooltip(f"### 12. Distribuição da {label_metrica} por Categoria (Boxplot)", "Boxplot mostra mediana, quartis e outliers por categoria.")
    if not df_filtrado.empty:
        fig12 = px.box(df_filtrado, x='CATEGORIA_CONVERSOR', y=valor_coluna, color='CATEGORIA_CONVERSOR', title="Distribuição da Quantidade por Categoria")
        fig12.update_layout(showlegend=False)
        st.plotly_chart(fig12, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir o boxplot.")

# --- Aba 4: Análise Avançada ---
with tab4:
    info_tooltip("### 📈 1. Fluxo Cumulativo de Produção", "Mostra a produção total acumulada ao longo do tempo. A inclinação indica velocidade.")
    if not df_filtrado.empty:
        cfd = df_filtrado.groupby('DATA_DE_ENTREGA')[valor_coluna].sum().reset_index().sort_values('DATA_DE_ENTREGA')
        cfd['Acumulado'] = cfd[valor_coluna].cumsum()
        fig_cfd = px.area(cfd, x='DATA_DE_ENTREGA', y='Acumulado', title="Fluxo Cumulativo de Produção ao Longo do Tempo")
        fig_cfd.update_layout(hovermode='x unified')
        st.plotly_chart(fig_cfd, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir o CFD.")

    info_tooltip("### 🎯 2. Análise de Pareto: 80/20 dos Líderes", "Os líderes são ordenados do maior para o menor produtor. A linha vermelha em 80% mostra onde os principais 20% terminam.")
    if not df_filtrado.empty:
        pareto = df_filtrado.groupby('RESPONSAVEL')[valor_coluna].sum().sort_values(ascending=False).reset_index()
        pareto['cumsum'] = pareto[valor_coluna].cumsum() / pareto[valor_coluna].sum() * 100
        fig_pareto = px.line(pareto, x='RESPONSAVEL', y='cumsum', markers=True, title="Acumulado de Produção por Líder (Regra 80/20)")
        fig_pareto.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="80%")
        st.plotly_chart(fig_pareto, use_container_width=True)
    else:
        st.info("Nenhum dado para análise de Pareto.")

    info_tooltip("### 🌡️ 4. Sazonalidade: Produção por Mês e Ano", "Mapa de calor que mostra a produção em cada mês de cada ano.")
    if not df_filtrado.empty:
        season = df_filtrado.groupby(['ANO_ENTREGA', 'MES_ENTREGA'])[valor_coluna].sum().reset_index()
        season_pivot = season.pivot(index='ANO_ENTREGA', columns='MES_ENTREGA', values=valor_coluna).fillna(0)
        fig_season = px.imshow(season_pivot, color_continuous_scale="Reds", title="Calor da Produção por Mês e Ano")
        st.plotly_chart(fig_season, use_container_width=True)
    else:
        st.info("Nenhum dado para mapa de sazonalidade.")


# --- Aba 5: Digital Twin & Custos (com fator de dificuldade dinâmico) ---
with tab5:
    st.markdown("### 💡 Digital Twin: Projeção com Custo Detalhado e Dificuldade Ajustada")

    # --- URLs ---
    DATA_URL = "https://raw.githubusercontent.com/K1NGOD-RJ/Analise-da-Controle/refs/heads/main/updated_dataframe_log.csv    "

    if mod is None or df_filtrado.empty:
        st.info("Dados insuficientes para executar o Digital Twin.")
    else:
        # --- 1. Carregar produtividade horária ---
        try:
            df_cap = pd.read_csv(DATA_URL)
            df_cap = df_cap.rename(columns={"MES": "MES_ANO", "PRODUTOS_HORA_FUNCIONARIO": "PROD_HORA"})
            df_cap["MES_ANO"] = df_cap["MES_ANO"].astype(str)
            prod_base_hora = df_cap["PROD_HORA"].tail(3).mean()
            st.markdown(f"**🔧 Produtividade Base (hora):** {prod_base_hora:.2f} unidades/hora")
        except Exception as e:
            st.error(f"❌ Erro ao carregar updated_dataframe_log.csv: {e}")
            st.stop()

        # --- 2. Calcular Dificuldade Média (últimos 3 meses) ---
        try:
            # Calcular dificuldade: QTD_PONDERADA / QTD
            df_hist = df_filtrado.groupby('MES_ANO')[['QTD', 'QTD_PONDERADA']].sum().reset_index()
            df_hist = df_hist[df_hist['QTD'] > 0]
            df_hist['Dificuldade'] = df_hist['QTD_PONDERADA'] / df_hist['QTD']
            dificuldade_media = df_hist['Dificuldade'].tail(3).mean()
            st.markdown(f"**📊 Dificuldade Média (últimos 3 meses):** {dificuldade_media:.3f}")
        except Exception as e:
            st.warning(f"⚠️ Não foi possível calcular dificuldade: {e}")
            dificuldade_media = 1.0

        st.markdown("---")

        # --- 3. Extrair custos reais do MOD (histórico mensal) ---
        def safe_numeric(series):
            return pd.to_numeric(series, errors='coerce').fillna(0)

        if 'Total geral:' not in mod.columns:
            st.error("❌ Coluna 'Total geral:' não encontrada em MOD.")
            st.stop()

        mod_total = safe_numeric(mod['Total geral:'])
        mod_months = mod_total.index.tolist()

        # Último mês para custos voláteis
        last_month = mod.columns[-1]
        valores = {}
        for col_name in ['Plano de Saúde', 'Vale Alimentação', 'Gratificação', 'Hora Extra', 'PJ', 'Bruto c/ Férias', '1/3 Férias + 13º', 'FGTS', 'FGTS + Rescisão', 'VT', 'Desconto VT']:
            if col_name in mod.index:
                valor = safe_numeric(mod.loc[col_name, last_month])
                valores[col_name] = valor if pd.notna(valor) else 0
            else:
                valores[col_name] = 0

        # --- 4. Custos setoriais (média dos últimos 3 meses) ---
        def avg_last_3(series):
            return series.dropna().tail(3).mean() if len(series.dropna()) >= 3 else 0

        pcp_avg = avg_last_3(safe_numeric(pcp['Total geral:'])) if pcp is not None and 'Total geral:' in pcp.columns else 0
        pre_avg = avg_last_3(safe_numeric(pre['Total geral:'])) if pre is not None and 'Total geral:' in pre.columns else 0
        almx_avg = avg_last_3(safe_numeric(almx['Total geral:'])) if almx is not None and 'Total geral:' in almx.columns else 0

        # --- 5. Parâmetros de Custo ---
        custo_freelancer_diario = 90.0
        horas_mensais_base = 144

        # Salários corretos
        salario_clt_mesa = 1679.60
        salario_clt_final = 1679.60
        salario_clt_maquina = 2479.86

        custo_hora_mesa = salario_clt_mesa / horas_mensais_base
        custo_hora_maquina = salario_clt_maquina / horas_mensais_base
        custo_hora_extra_mesa = custo_hora_mesa * 1.5
        custo_hora_extra_maquina = custo_hora_maquina * 1.5
        custo_hora_extra_final = custo_hora_mesa * 1.5

        # --- 6. Equipe Fixa ---
        try:
            ultima_linha = df_cap.iloc[-1]
            func_final_fixo = int(ultima_linha['FUNCIONARIOS_FINALIZACAO'])
            op_maquina_fixo = int(ultima_linha['OPERADORES_MAQUINA'])
            st.markdown(f"**👥 Equipe Fixa:** {func_final_fixo} Finalização + {op_maquina_fixo} Operadores de Máquina")
        except Exception as e:
            st.warning(f"⚠️ Não foi possível carregar equipe fixa: {e}")
            func_final_fixo = 5
            op_maquina_fixo = 9

        # --- 7. Projeção ---
        last_date = df_filtrado['DATA_DE_ENTREGA'].max()
        next_months = pd.date_range(last_date, periods=4, freq='MS')[1:4]
        month_names = [date.strftime('%b/%Y') for date in next_months]
        proj_data = []

        col1, col2, col3 = st.columns(3)
        for i, col in enumerate([col1, col2, col3]):
            with col:
                st.markdown(f"**📅 {month_names[i]}**")

                func_mesa_total = st.number_input("Total Funcionários (Mesa)", min_value=1, value=50, key=f"mesa_{i}")
                clts_mesa = st.number_input("CLTs na Mesa", min_value=0, max_value=func_mesa_total, value=int(0.8 * func_mesa_total), key=f"clts_mesa_{i}")
                freelancers_mesa = func_mesa_total - clts_mesa

                dias_uteis = st.number_input("Dias Úteis", min_value=1, value=22, key=f"dias_uteis_{i}")
                he_dia = st.number_input("HE por dia útil (h)", min_value=0.0, max_value=8.0, step=0.5, value=2.0, key=f"he_{i}")
                sabados = st.number_input("Sábados Trabalhados", min_value=0, max_value=5, value=2, key=f"sabados_{i}")
                he_maquina = st.number_input("HE Operadores de Máquina (h/dia)", min_value=0.0, max_value=8.0, step=0.5, value=0.0, key=f"he_maquina_{i}")
                trabalham_sabado = st.checkbox("Freelancers trabalham aos sábados?", value=False, key=f"freela_sab_{i}")

                # --- Dificuldade Projetada ---
                dificuldade_proj = st.slider(
                    "Fator de Dificuldade Projetado",
                    min_value=0.5,
                    max_value=2.0,
                    value=round(dificuldade_media, 3),
                    step=0.01,
                    key=f"dificuldade_{i}"
                )

                # --- Ajuste de Produtividade por Dificuldade ---
                if dificuldade_proj > dificuldade_media:
                    # Maior dificuldade → menor produtividade
                    ajuste_prod = dificuldade_media / dificuldade_proj
                else:
                    # Menor dificuldade → maior produtividade (até 1.0)
                    ajuste_prod = 1.0

                prod_efetiva_hora = prod_base_hora * ajuste_prod

                # --- Carga de Trabalho ---
                carga_clt_mesa = clts_mesa * dias_uteis * (9 + he_dia)
                carga_freela_mesa = freelancers_mesa * dias_uteis * 9
                carga_sabados = clts_mesa * sabados * 8
                carga_total = carga_clt_mesa + carga_freela_mesa + carga_sabados

                # --- Produção ---
                prod_bruta_mesa = carga_clt_mesa * prod_efetiva_hora
                prod_bruta_freela = carga_freela_mesa * prod_efetiva_hora * 0.95  # -5%
                prod_bruta_sabado = carga_sabados * prod_efetiva_hora
                prod_bruta = int(prod_bruta_mesa + prod_bruta_freela + prod_bruta_sabado)
                prod_ponderada = int(prod_bruta * dificuldade_proj)

                # --- Custo MOD ---
                custo_clt_mesa = clts_mesa * salario_clt_mesa
                custo_va_mesa = clts_mesa * 21 * dias_uteis
                custo_he_mesa = clts_mesa * he_dia * dias_uteis * custo_hora_extra_mesa
                custo_he_sabados = clts_mesa * sabados * 8 * custo_hora_extra_mesa
                custo_freelancer_mesa = freelancers_mesa * custo_freelancer_diario * dias_uteis
                if trabalham_sabado:
                    custo_freelancer_mesa += freelancers_mesa * custo_freelancer_diario * sabados

                custo_finalizacao = func_final_fixo * salario_clt_final
                custo_va_final = func_final_fixo * 21 * dias_uteis
                custo_he_final = func_final_fixo * he_dia * dias_uteis * custo_hora_extra_final

                custo_maquina = op_maquina_fixo * salario_clt_maquina
                custo_va_maquina = op_maquina_fixo * 21 * dias_uteis
                custo_he_maquina = op_maquina_fixo * he_maquina * dias_uteis * custo_hora_extra_maquina

                custo_plano_saude = valores['Plano de Saúde']
                custo_gratificacao = valores['Gratificação']
                custo_fgts = (
                    clts_mesa * (salario_clt_mesa * 0.08) +
                    func_final_fixo * (salario_clt_final * 0.08) +
                    op_maquina_fixo * (salario_clt_maquina * 0.08) +
                    valores['FGTS']
                )
                custo_ferias_13 = valores['1/3 Férias + 13º'] / 12
                custo_rescisao = valores['FGTS + Rescisão'] / 12
                custo_vt = valores['VT']
                desconto_vt = valores['Desconto VT']
                custo_pj = valores['PJ']

                custo_mod = (
                    custo_clt_mesa + custo_va_mesa + custo_he_mesa + custo_he_sabados +
                    custo_freelancer_mesa + custo_finalizacao + custo_va_final + custo_he_final +
                    custo_maquina + custo_va_maquina + custo_he_maquina +
                    custo_plano_saude + custo_gratificacao + custo_fgts +
                    custo_ferias_13 + custo_rescisao + custo_vt + custo_pj - desconto_vt
                )

                custo_total_industria = custo_mod + pcp_avg + pre_avg + almx_avg

                proj_data.append({
                    "Mês": month_names[i],
                    "Tipo": "Projeção",
                    "Produção Bruta": prod_bruta,
                    "QTD": prod_bruta,
                    "QTD_PONDERADA": prod_ponderada,
                    "Custo MOD (R$)": custo_mod,
                    "Custo Total (R$)": custo_total_industria
                })

        # --- Histórico ---
        df_hist_prod = df_filtrado.groupby('MES_ANO')[['QTD', 'QTD_PONDERADA']].sum().reset_index()
        df_hist_prod['MES_ANO'] = df_hist_prod['MES_ANO'].astype(str)
        hist_df = pd.DataFrame({'Mês': mod_months})
        hist_df = hist_df.merge(df_hist_prod, left_on='Mês', right_on='MES_ANO', how='left')
        hist_df['QTD'] = hist_df['QTD'].fillna(0)
        hist_df['QTD_PONDERADA'] = hist_df['QTD_PONDERADA'].fillna(0)
        hist_df['Custo MOD (R$)'] = mod_total.values
        hist_df['Custo Total (R$)'] = hist_df['Custo MOD (R$)'] + pcp_avg + pre_avg + almx_avg
        hist_df['Tipo'] = 'Real'

        # --- Projeção ---
        proj_df = pd.DataFrame(proj_data)
        proj_df['Mês'] = pd.to_datetime(proj_df['Mês'], format='%b/%Y').dt.strftime('%Y-%m')

        # --- Combinar ---
        combined = pd.concat([hist_df, proj_df], ignore_index=True)
        combined['Mês'] = pd.to_datetime(combined['Mês'], format='%Y-%m')

        # --- Custo por Produto ---
        use_ponderada = st.checkbox("Usar Quantidade Ponderada", value=False, key="custo_ponderada")
        use_total = st.checkbox("Usar Custo Total da Indústria", value=True, key="custo_total")

        valor_coluna = 'QTD_PONDERADA' if use_ponderada else 'QTD'
        custo_coluna = 'Custo Total (R$)' if use_total else 'Custo MOD (R$)'

        combined[valor_coluna] = pd.to_numeric(combined[valor_coluna], errors='coerce').fillna(0)
        combined[custo_coluna] = pd.to_numeric(combined[custo_coluna], errors='coerce').fillna(0)

        combined['Custo por Produto (R$)'] = np.where(
            combined[valor_coluna] > 0,
            combined[custo_coluna] / combined[valor_coluna],
            0
        )

        # --- Exibir Tabela ---
        st.markdown("### 📊 Evolução do Custo por Produto")
        display = combined[['Mês', 'Tipo', valor_coluna, custo_coluna, 'Custo por Produto (R$)']].copy()
        display['Mês'] = display['Mês'].dt.strftime('%Y-%m')
        display[valor_coluna] = display[valor_coluna].round(0).astype(int)
        display[custo_coluna] = display[custo_coluna].apply(lambda x: f"R$ {x:,.2f}")
        display['Custo por Produto (R$)'] = display['Custo por Produto (R$)'].apply(lambda x: f"R$ {x:.2f}" if x > 0 else "R$ 0.00")

        st.dataframe(display, use_container_width=True)

        # --- Gráfico ---
        fig = px.line(
            combined,
            x='Mês',
            y='Custo por Produto (R$)',
            color='Tipo',
            markers=True,
            title=f"Custo por Produto: {'Total Indústria' if use_total else 'MOD'} / {'QTD Ponderada' if use_ponderada else 'QTD Bruta'}",
            line_shape='spline'
        )
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

        st.info("💡 **Dificuldade ajusta produtividade. HE em finalização = HE da mesa. Freelancers: -5%. Fadiga removido.**")

# --- Aba 6: Comparativo Anual ---
with tab6:
    st.markdown("### 📅 Comparativo Anual: 2024 vs 2025 (dados até Julho)")

    # Filtrar por ano e até julho
    df_2024_full = df_filtrado[df_filtrado['ANO_ENTREGA'] == 2024]
    df_2025_full = df_filtrado[df_filtrado['ANO_ENTREGA'] == 2025]

    # Dados reais: Jan–Jul
    df_2024 = df_2024_full[df_2024_full['MES_ENTREGA'] <= 7]
    df_2025 = df_2025_full[df_2025_full['MES_ENTREGA'] <= 7]

    total_2024_real = df_2024[valor_coluna].sum() if not df_2024.empty else 0
    total_2025_real = df_2025[valor_coluna].sum() if not df_2025.empty else 0

    # Projeção para 2025 (extrapolação linear)
    if not df_2025.empty and df_2025[valor_coluna].sum() > 0:
        meses_reais = len(df_2025['MES_ENTREGA'].unique())
        projecao_anual_2025 = (total_2025_real / meses_reais) * 12
    else:
        projecao_anual_2025 = 0

    # Total real de 2024 (completo)
    total_2024_completo = df_2024_full[valor_coluna].sum() if not df_2024_full.empty else 0

    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("2024 Real (Jan–Dez)", f"{total_2024_completo:,.0f}")
    col2.metric("2025 Real (Jan–Jul)", f"{total_2025_real:,.0f}")
    col3.metric("2025 Projetado (Full Year)", f"{projecao_anual_2025:,.0f}")
    crescimento_vs_2024 = f"{((projecao_anual_2025 - total_2024_completo) / total_2024_completo) * 100:+.1f}%" if total_2024_completo > 0 else "N/A"
    col4.metric("Crescimento Estimado", crescimento_vs_2024)

    st.info(f"💡 Projeção 2025 = Média mensal (Jan–Jul) × 12 meses")

    # --- Gráfico: Produção Mensal com Projeção ---
    mensal_2024 = df_2024.groupby('MES_ENTREGA')[valor_coluna].sum().reset_index()
    mensal_2024['ANO'] = 2024

    mensal_2025_real = df_2025.groupby('MES_ENTREGA')[valor_coluna].sum().reset_index()
    mensal_2025_real['ANO'] = "2025 (Real)"

    # Criar projeção para 2025 (agosto a dezembro)
    if not df_2025.empty:
        media_mensal_2025 = total_2025_real / len(mensal_2025_real)
        projecao = []
        for mes in range(8, 13):
            projecao.append({'MES_ENTREGA': mes, valor_coluna: media_mensal_2025, 'ANO': '2025 (Projetado)'})
        df_projecao = pd.DataFrame(projecao)
        mensal_2025 = pd.concat([mensal_2025_real, df_projecao], ignore_index=True)
    else:
        mensal_2025 = mensal_2025_real
        mensal_2025['ANO'] = "2025 (Real)"

    # Combinar dados
    combined = pd.concat([mensal_2024, mensal_2025], ignore_index=True)

    fig_yoy = px.bar(
        combined,
        x='MES_ENTREGA',
        y=valor_coluna,
        color='ANO',
        barmode='group',
        title="Produção Mensal: 2024 vs 2025 (com Projeção)",
        labels={valor_coluna: "Quantidade", "MES_ENTREGA": "Mês"}
    )
    fig_yoy.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1))
    st.plotly_chart(fig_yoy, use_container_width=True)

    # --- Top 5 Produtos (Jan–Jul) ---
    st.markdown("#### Top 5 Produtos (Jan–Jul)")
    col1, col2 = st.columns(2)
    with col1:
        if not df_2024.empty:
            top2024 = df_2024.groupby('PRODUTO')[valor_coluna].sum().nlargest(5).reset_index()
            st.markdown("**2024**")
            st.dataframe(top2024)
    with col2:
        if not df_2025.empty:
            top2025 = df_2025.groupby('PRODUTO')[valor_coluna].sum().nlargest(5).reset_index()
            st.markdown("**2025**")
            st.dataframe(top2025)

# --- Aba 7: Comparativo Detalhado por Categoria ---
with tab7:
    st.markdown("### 📊 Comparativo Detalhado: 2024 vs 2025 por Categoria")

    df_2024 = df_filtrado[df_filtrado['ANO_ENTREGA'] == 2024]
    df_2025 = df_filtrado[df_filtrado['ANO_ENTREGA'] == 2025]

    # --- Representatividade por Categoria ---
    col1, col2 = st.columns(2)
    with col1:
        if not df_2024.empty:
            cat_2024 = df_2024.groupby('CATEGORIA_CONVERSOR')[valor_coluna].sum().reset_index()
            fig_cat_2024 = px.pie(cat_2024, names='CATEGORIA_CONVERSOR', values=valor_coluna, title="2024: Distribuição por Categoria", hole=0.4)
            fig_cat_2024.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_cat_2024, use_container_width=True)
    with col2:
        if not df_2025.empty:
            cat_2025 = df_2025.groupby('CATEGORIA_CONVERSOR')[valor_coluna].sum().reset_index()
            fig_cat_2025 = px.pie(cat_2025, names='CATEGORIA_CONVERSOR', values=valor_coluna, title="2025: Distribuição por Categoria", hole=0.4)
            fig_cat_2025.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_cat_2025, use_container_width=True)

    # --- Tamanho Médio do Lote por Categoria ---
    col1, col2 = st.columns(2)
    with col1:
        if not df_2024.empty:
            avg_2024 = df_2024.groupby('CATEGORIA_CONVERSOR')[valor_coluna].mean().reset_index()
            fig_avg_2024 = px.bar(avg_2024, x=valor_coluna, y='CATEGORIA_CONVERSOR', orientation='h', title="2024: Tamanho Médio do Lote por Categoria")
            st.plotly_chart(fig_avg_2024, use_container_width=True)
    with col2:
        if not df_2025.empty:
            avg_2025 = df_2025.groupby('CATEGORIA_CONVERSOR')[valor_coluna].mean().reset_index()
            fig_avg_2025 = px.bar(avg_2025, x=valor_coluna, y='CATEGORIA_CONVERSOR', orientation='h', title="2025: Tamanho Médio do Lote por Categoria")
            st.plotly_chart(fig_avg_2025, use_container_width=True)

    # --- Boxplot por Categoria ---
    col1, col2 = st.columns(2)
    with col1:
        if not df_2024.empty:
            fig_box_2024 = px.box(df_2024, x='CATEGORIA_CONVERSOR', y=valor_coluna, title="2024: Distribuição por Categoria")
            st.plotly_chart(fig_box_2024, use_container_width=True)
    with col2:
        if not df_2025.empty:
            fig_box_2025 = px.box(df_2025, x='CATEGORIA_CONVERSOR', y=valor_coluna, title="2025: Distribuição por Categoria")
            st.plotly_chart(fig_box_2025, use_container_width=True)

# --- Diagnóstico Final ---
st.markdown("---")
st.write("### 🔍 Diagnóstico do DataFrame")
st.write(f"**Número de linhas:** {len(df)}")
st.write(f"**Número de colunas:** {len(df.columns)}")
st.write(f"**Colunas:** {list(df.columns)}")
st.caption("📊 Dashboard científico de produção. Atualizado com base nos dados mais recentes.")