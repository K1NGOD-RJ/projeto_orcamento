import streamlit as st
import pandas as pd
import re
from datetime import datetime

# ================== URLs dos CSVs no GitHub ==================
URL_COMPRAS = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/compradepapel.csv"
URL_USO_PAPEL_MIOLO = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapelmiolos.csv"
URL_USO_PAPEL_BOLSA = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapelbolsa.csv"
URL_USO_PAPEL_DIVISORIA = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapeldivisoria.csv"
URL_USO_PAPEL_ADESIVO = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapeladesivo.csv"

# ================== CONFIGURAÇÃO DA PÁGINA ==================
st.set_page_config(page_title="📦 Cálculo de Custo de Produto", layout="centered")
st.title("📐 Análise de Custo: Miolo + Bolsa + Divisória + Adesivo")

# ================== FUNÇÕES AUXILIARES ==================
@st.cache_data
def carregar_dados():
    try:
        # --- 1. Carregar compras de papel ---
        df_compras = pd.read_csv(URL_COMPRAS, encoding='utf-8')
        df_compras.columns = [
            'Demanda', 'Quantidade', 'DataSolicitacao', 'PrazoDesejado', 'DataAprovacao',
            'DataEmissaoNF', 'PrevisaoEntrega', 'NumeroNF', 'Fornecedor', 'ValorTotal',
            'ValorFrete', 'CreditoICMS', 'CNPJ', 'FormaPagamento', 'Parcelas', 'ValorUnitarioStr'
        ]

        # Converter datas
        date_cols = ['DataSolicitacao', 'PrazoDesejado', 'DataAprovacao', 'DataEmissaoNF', 'PrevisaoEntrega']
        for col in date_cols:
            df_compras[col] = pd.to_datetime(df_compras[col], format='%d/%m/%Y', errors='coerce')

        # Converter valor unitário (R$ 0,40 → 0.40)
        df_compras['ValorUnitario'] = (df_compras['ValorUnitarioStr']
                                       .astype(str)
                                       .str.replace('R\\$', '', regex=True)
                                       .str.replace(',', '.')
                                       .str.strip())
        df_compras['ValorUnitario'] = pd.to_numeric(df_compras['ValorUnitario'], errors='coerce')

        # Limpar nome do papel
        def limpar_papel(nome):
            if pd.isna(nome):
                return ""
            nome = re.sub(r'^(MP\d{3}|COUCHE|CARTAO|PAPEL|20\d{3}|COLOR|SCRITURA|Papel|Cartão)\s*', '', str(nome), flags=re.IGNORECASE)
            nome = re.sub(r'\s*UNICA-\w+', '', nome)
            nome = re.sub(r'\s*-\s*SEM\s*LINER', '', nome, flags=re.IGNORECASE)
            nome = re.sub(r'\s*-\s*CHAMBRIL', '', nome, flags=re.IGNORECASE)
            nome = re.sub(r'\s+', ' ', nome).strip()
            return nome.title()

        df_compras['PapelLimpo'] = df_compras['Demanda'].apply(limpar_papel)
        df_compras = df_compras.dropna(subset=['ValorUnitario', 'PapelLimpo'])
        df_compras = df_compras[df_compras['PapelLimpo'] != ""]
        df_compras = df_compras.sort_values('DataEmissaoNF', ascending=False)

        # Lista única de papéis para dropdown
        papeis_unicos = sorted(df_compras['PapelLimpo'].dropna().unique())

        # --- 2. Carregar uso de papel por miolo ---
        df_miolos = pd.read_csv(URL_USO_PAPEL_MIOLO, encoding='utf-8')
        df_miolos.columns = [
            'Miolo', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'
        ]
        df_miolos['QuantidadePapel'] = pd.to_numeric(df_miolos['QuantidadePapel'], errors='coerce')
        df_miolos['UnitImpressao'] = pd.to_numeric(df_miolos['UnitImpressao'], errors='coerce')
        df_miolos['QuantidadeAprovada'] = pd.to_numeric(df_miolos['QuantidadeAprovada'], errors='coerce')
        df_miolos['Papel'] = df_miolos['Papel'].apply(limpar_papel)

        # --- 3. Carregar uso de papel por bolsa ---
        df_bolsas = pd.read_csv(URL_USO_PAPEL_BOLSA, encoding='utf-8')
        df_bolsas.columns = [
            'Bolsa', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'
        ]
        df_bolsas['QuantidadePapel'] = pd.to_numeric(df_bolsas['QuantidadePapel'], errors='coerce')
        df_bolsas['UnitImpressao'] = pd.to_numeric(df_bolsas['UnitImpressao'], errors='coerce')
        df_bolsas['QuantidadeAprovada'] = pd.to_numeric(df_bolsas['QuantidadeAprovada'], errors='coerce')
        df_bolsas['Papel'] = df_bolsas['Papel'].apply(limpar_papel)

        # --- 4. Carregar uso de papel por divisória ---
        df_divisorias = pd.read_csv(URL_USO_PAPEL_DIVISORIA, encoding='utf-8')
        df_divisorias.columns = [
            'Divisoria', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'
        ]
        df_divisorias['QuantidadePapel'] = pd.to_numeric(df_divisorias['QuantidadePapel'], errors='coerce')
        df_divisorias['UnitImpressao'] = pd.to_numeric(df_divisorias['UnitImpressao'], errors='coerce')
        df_divisorias['QuantidadeAprovada'] = pd.to_numeric(df_divisorias['QuantidadeAprovada'], errors='coerce')
        df_divisorias['Papel'] = df_divisorias['Papel'].apply(limpar_papel)

        # --- 5. Carregar uso de papel por adesivo ---
        df_adesivos = pd.read_csv(URL_USO_PAPEL_ADESIVO, encoding='utf-8')
        df_adesivos.columns = [
            'Adesivo', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'
        ]
        df_adesivos['QuantidadePapel'] = pd.to_numeric(df_adesivos['QuantidadePapel'], errors='coerce')
        df_adesivos['UnitImpressao'] = pd.to_numeric(df_adesivos['UnitImpressao'], errors='coerce')
        df_adesivos['QuantidadeAprovada'] = pd.to_numeric(df_adesivos['QuantidadeAprovada'], errors='coerce')
        df_adesivos['Papel'] = df_adesivos['Papel'].apply(limpar_papel)

        return df_compras, df_miolos, df_bolsas, df_divisorias, df_adesivos, papeis_unicos

    except Exception as e:
        st.error(f"❌ Erro ao carregar os dados: {e}")
        return None, None, None, None, None, None

# ================== CARREGAR DADOS ==================
df_compras, df_miolos, df_bolsas, df_divisorias, df_adesivos, papeis_unicos = carregar_dados()

if df_compras is None or df_miolos is None or df_bolsas is None or df_divisorias is None or df_adesivos is None:
    st.stop()

# ================== SELETOR DE QUANTIDADE (TOP) ==================
st.markdown("### 📦 Quantidade do Orçamento")
quantidade_orcamento = st.number_input(
    "Digite a quantidade total do orçamento:",
    min_value=1,
    value=15000,
    step=1,
    help="Essa quantidade será usada para dividir o valor do serviço no cálculo unitário"
)
st.divider()

# ================== FUNÇÃO PARA CALCULAR CUSTO UNITÁRIO ==================
def calcular_custo(nome_item, df_item, tipo="Item"):
    linha = df_item[df_item[tipo] == nome_item].iloc[0]
    papel_necessario = linha['Papel']
    qtd_papel_total = linha['QuantidadePapel']
    qtd_aprovada = linha['QuantidadeAprovada']
    valor_impressao = linha['ValorImpressao']

    if qtd_aprovada <= 0:
        qtd_aprovada = 1

    folhas_por_unidade = qtd_papel_total / qtd_aprovada
    df_papel = df_compras[df_compras['PapelLimpo'] == papel_necessario]
    if df_papel.empty:
        st.warning(f"⚠️ Nenhuma compra encontrada para o papel usado no(a) {tipo.lower()}: **{papel_necessario}**")
        return None, None, None, None

    preco_unitario_papel = df_papel.iloc[0]['ValorUnitario']
    custo_papel_por_unidade = preco_unitario_papel * folhas_por_unidade
    custo_servico_por_unidade = valor_impressao / quantidade_orcamento
    custo_total_unitario = custo_papel_por_unidade + custo_servico_por_unidade

    return custo_total_unitario, custo_papel_por_unidade, custo_servico_por_unidade, papel_necessario

# ================== FUNÇÃO: CÁLCULO PERSONALIZADO ==================
def calcular_personalizado(nome, papel_selecionado, aproveitamento, valor_servico, quantidade_orcamento):
    if aproveitamento <= 0:
        aproveitamento = 1

    # Buscar preço do papel selecionado
    df_papel = df_compras[df_compras['PapelLimpo'] == papel_selecionado]
    if df_papel.empty:
        st.error(f"❌ Papel não encontrado: **{papel_selecionado}**")
        return None, None, None, None, None

    preco_unitario_papel = df_papel.iloc[0]['ValorUnitario']
    ultima_data = df_papel.iloc[0]['DataEmissaoNF'].strftime('%d/%m/%Y')

    custo_papel_por_unidade = preco_unitario_papel / aproveitamento
    custo_servico_por_unidade = valor_servico / quantidade_orcamento
    custo_total = custo_papel_por_unidade + custo_servico_por_unidade

    return custo_total, custo_papel_por_unidade, custo_servico_por_unidade, papel_selecionado, ultima_data

# ================== INTERFACE DO USUÁRIO ==================
st.markdown("Selecione um **miolo**, uma **bolsa**, uma **divisória**, um **adesivo** ou use a opção personalizada.")

# === Miolo ===
miolos = sorted(df_miolos['Miolo'].dropna().unique())
miolo_opcoes = ["Personalizado"] + list(miolos)
miolo_selecionado = st.selectbox("📘 Miolo:", options=miolo_opcoes, index=0, key="miolo")

if miolo_selecionado == "Personalizado":
    col1, col2, col3 = st.columns(3)
    papel_miolo = col1.selectbox("Papel utilizado (miolo)", options=papeis_unicos, index=0, key="papel_miolo")
    aproveitamento_miolo = col2.number_input("Aproveitamento (unidades por folha)", min_value=1, value=5, key="aprov_miolo")
    valor_servico_miolo = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=13050.0, key="serv_miolo")
else:
    papel_miolo = None

# === Bolsa ===
bolsas = sorted(df_bolsas['Bolsa'].dropna().unique())
bolsa_opcoes = ["Personalizado"] + list(bolsas)
bolsa_selecionada = st.selectbox("👜 Bolsa:", options=bolsa_opcoes, index=0, key="bolsa")

if bolsa_selecionada == "Personalizado":
    col1, col2, col3 = st.columns(3)
    papel_bolsa = col1.selectbox("Papel utilizado (bolsa)", options=papeis_unicos, index=0, key="papel_bolsa")
    aproveitamento_bolsa = col2.number_input("Aproveitamento (unidades por folha)", min_value=1, value=4, key="aprov_bolsa")
    valor_servico_bolsa = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=2425.0, key="serv_bolsa")
else:
    papel_bolsa = None

# === Divisória ===
divisorias = sorted(df_divisorias['Divisoria'].dropna().unique())
divisoria_opcoes = ["Personalizado"] + list(divisorias)
divisoria_selecionada = st.selectbox("🔖 Divisória:", options=divisoria_opcoes, index=0, key="divisoria")

if divisoria_selecionada == "Personalizado":
    col1, col2, col3 = st.columns(3)
    papel_divisoria = col1.selectbox("Papel utilizado (divisória)", options=papeis_unicos, index=0, key="papel_divisoria")
    aproveitamento_divisoria = col2.number_input("Aproveitamento (unidades por folha)", min_value=1, value=3, key="aprov_div")
    valor_servico_divisoria = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=22986.0, key="serv_div")
else:
    papel_divisoria = None

# === Adesivo ===
adesivos = sorted(df_adesivos['Adesivo'].dropna().unique())
adesivo_opcoes = ["Personalizado"] + list(adesivos)
adesivo_selecionado = st.selectbox("🏷️ Adesivo:", options=adesivo_opcoes, index=0, key="adesivo")

if adesivo_selecionado == "Personalizado":
    col1, col2, col3 = st.columns(3)
    papel_adesivo = col1.selectbox("Papel utilizado (adesivo)", options=papeis_unicos, index=0, key="papel_adesivo")
    aproveitamento_adesivo = col2.number_input("Aproveitamento (unidades por folha)", min_value=1, value=10, key="aprov_adesivo")
    valor_servico_adesivo = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=4840.0, key="serv_adesivo")
else:
    papel_adesivo = None

# ================== CALCULAR CUSTOS ==================
custo_miolo = None
custo_bolsa = None
custo_divisoria = None
custo_adesivo = None

# Miolo
if miolo_selecionado and miolo_selecionado != "Personalizado":
    custo_miolo = calcular_custo(miolo_selecionado, df_miolos, "Miolo")
elif miolo_selecionado == "Personalizado":
    custo_miolo = calcular_personalizado(
        "Miolo Personalizado",
        papel_miolo,
        aproveitamento_miolo,
        valor_servico_miolo,
        quantidade_orcamento
    )

# Bolsa
if bolsa_selecionada and bolsa_selecionada != "Personalizado":
    custo_bolsa = calcular_custo(bolsa_selecionada, df_bolsas, "Bolsa")
elif bolsa_selecionada == "Personalizado":
    custo_bolsa = calcular_personalizado(
        "Bolsa Personalizada",
        papel_bolsa,
        aproveitamento_bolsa,
        valor_servico_bolsa,
        quantidade_orcamento
    )

# Divisória
if divisoria_selecionada and divisoria_selecionada != "Personalizado":
    custo_divisoria = calcular_custo(divisoria_selecionada, df_divisorias, "Divisoria")
elif divisoria_selecionada == "Personalizado":
    custo_divisoria = calcular_personalizado(
        "Divisória Personalizada",
        papel_divisoria,
        aproveitamento_divisoria,
        valor_servico_divisoria,
        quantidade_orcamento
    )

# Adesivo
if adesivo_selecionado and adesivo_selecionado != "Personalizado":
    custo_adesivo = calcular_custo(adesivo_selecionado, df_adesivos, "Adesivo")
elif adesivo_selecionado == "Personalizado":
    custo_adesivo = calcular_personalizado(
        "Adesivo Personalizado",
        papel_adesivo,
        aproveitamento_adesivo,
        valor_servico_adesivo,
        quantidade_orcamento
    )

# ================== EXIBIR RESULTADOS ==================
st.divider()
st.subheader("📊 Resultados por Componente")

cols = st.columns(4)

# Exibir Miolo
if miolo_selecionado != "Personalizado" and custo_miolo:
    with cols[0]:
        st.markdown(f"**{miolo_selecionado}**")
        st.metric("Custo Unit.", f"R$ {custo_miolo[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {custo_miolo[3]}")
            st.markdown(f"**Papel/unid:** R$ {custo_miolo[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Serviço/unid:** R$ {custo_miolo[2]:,.2f}".replace('.', ','))
elif miolo_selecionado == "Personalizado" and custo_miolo:
    with cols[0]:
        st.markdown("**Miolo Personalizado**")
        st.metric("Custo Unit.", f"R$ {custo_miolo[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {papel_miolo}")
            st.markdown(f"**Última NF:** {custo_miolo[4]}")
            st.markdown(f"**Aproveitamento:** {aproveitamento_miolo} unid/folha")
            st.markdown(f"**Custo papel/unid:** R$ {custo_miolo[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Custo serviço/unid:** R$ {custo_miolo[2]:,.2f}".replace('.', ','))

# Exibir Bolsa
if bolsa_selecionada != "Personalizado" and custo_bolsa:
    with cols[1]:
        st.markdown(f"**{bolsa_selecionada}**")
        st.metric("Custo Unit.", f"R$ {custo_bolsa[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {custo_bolsa[3]}")
            st.markdown(f"**Papel/unid:** R$ {custo_bolsa[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Serviço/unid:** R$ {custo_bolsa[2]:,.2f}".replace('.', ','))
elif bolsa_selecionada == "Personalizado" and custo_bolsa:
    with cols[1]:
        st.markdown("**Bolsa Personalizada**")
        st.metric("Custo Unit.", f"R$ {custo_bolsa[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {papel_bolsa}")
            st.markdown(f"**Última NF:** {custo_bolsa[4]}")
            st.markdown(f"**Aproveitamento:** {aproveitamento_bolsa} unid/folha")
            st.markdown(f"**Custo papel/unid:** R$ {custo_bolsa[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Custo serviço/unid:** R$ {custo_bolsa[2]:,.2f}".replace('.', ','))

# Exibir Divisória
if divisoria_selecionada != "Personalizado" and custo_divisoria:
    with cols[2]:
        st.markdown(f"**{divisoria_selecionada}**")
        st.metric("Custo Unit.", f"R$ {custo_divisoria[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {custo_divisoria[3]}")
            st.markdown(f"**Papel/unid:** R$ {custo_divisoria[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Serviço/unid:** R$ {custo_divisoria[2]:,.2f}".replace('.', ','))
elif divisoria_selecionada == "Personalizado" and custo_divisoria:
    with cols[2]:
        st.markdown("**Divisória Personalizada**")
        st.metric("Custo Unit.", f"R$ {custo_divisoria[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {papel_divisoria}")
            st.markdown(f"**Última NF:** {custo_divisoria[4]}")
            st.markdown(f"**Aproveitamento:** {aproveitamento_divisoria} unid/folha")
            st.markdown(f"**Custo papel/unid:** R$ {custo_divisoria[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Custo serviço/unid:** R$ {custo_divisoria[2]:,.2f}".replace('.', ','))

# Exibir Adesivo
if adesivo_selecionado != "Personalizado" and custo_adesivo:
    with cols[3]:
        st.markdown(f"**{adesivo_selecionado}**")
        st.metric("Custo Unit.", f"R$ {custo_adesivo[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {custo_adesivo[3]}")
            st.markdown(f"**Papel/unid:** R$ {custo_adesivo[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Serviço/unid:** R$ {custo_adesivo[2]:,.2f}".replace('.', ','))
elif adesivo_selecionado == "Personalizado" and custo_adesivo:
    with cols[3]:
        st.markdown("**Adesivo Personalizado**")
        st.metric("Custo Unit.", f"R$ {custo_adesivo[0]:,.2f}".replace('.', ','))
        with st.expander("Detalhes"):
            st.markdown(f"**Papel:** {papel_adesivo}")
            st.markdown(f"**Última NF:** {custo_adesivo[4]}")
            st.markdown(f"**Aproveitamento:** {aproveitamento_adesivo} unid/folha")
            st.markdown(f"**Custo papel/unid:** R$ {custo_adesivo[1]:,.2f}".replace('.', ','))
            st.markdown(f"**Custo serviço/unid:** R$ {custo_adesivo[2]:,.2f}".replace('.', ','))

# ================== CUSTO TOTAL DO PRODUTO ==================
st.divider()
st.subheader("💰 Custo Total Unitário do Produto")

custo_total = 0.0
itens = []

if miolo_selecionado != "Personalizado" and custo_miolo:
    custo_total += custo_miolo[0]
    itens.append("Miolo")
elif miolo_selecionado == "Personalizado" and custo_miolo:
    custo_total += custo_miolo[0]
    itens.append("Miolo (Pers.)")

if bolsa_selecionada != "Personalizado" and custo_bolsa:
    custo_total += custo_bolsa[0]
    itens.append("Bolsa")
elif bolsa_selecionada == "Personalizado" and custo_bolsa:
    custo_total += custo_bolsa[0]
    itens.append("Bolsa (Pers.)")

if divisoria_selecionada != "Personalizado" and custo_divisoria:
    custo_total += custo_divisoria[0]
    itens.append("Divisória")
elif divisoria_selecionada == "Personalizado" and custo_divisoria:
    custo_total += custo_divisoria[0]
    itens.append("Divisória (Pers.)")

if adesivo_selecionado != "Personalizado" and custo_adesivo:
    custo_total += custo_adesivo[0]
    itens.append("Adesivo")
elif adesivo_selecionado == "Personalizado" and custo_adesivo:
    custo_total += custo_adesivo[0]
    itens.append("Adesivo (Pers.)")

if itens:
    st.success(f"**Custo Total Unitário ({' + '.join(itens)}):** R$ {custo_total:,.2f}".replace('.', ','))
else:
    st.warning("Nenhum item selecionado.")

# ================== RODAPÉ ==================
st.markdown("---")
st.caption("✅ Cálculo: `(Preço do Papel / Aproveitamento) + (Valor do Serviço / Quantidade do Orçamento)`")