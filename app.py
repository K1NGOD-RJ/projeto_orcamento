import streamlit as st
import pandas as pd
import re

# ================== URLs dos CSVs no GitHub ==================
URL_COMPRAS = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/compradepapel.csv"
URL_USO_PAPEL_MIOLO = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapelmiolos.csv"
URL_USO_PAPEL_BOLSA = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapelbolsa.csv"
URL_USO_PAPEL_DIVISORIA = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapeldivisoria.csv"
URL_USO_PAPEL_ADESIVO = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/usodepapeladesivo.csv"
URL_COMPRA_DIRETA = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/compradireta.csv"
URL_TABELA_WIREO = "https://raw.githubusercontent.com/K1NGOD-RJ/projeto_orcamento/main/tabelawireo.csv"

# ================== CONFIGURAÇÃO DA PÁGINA ==================
st.set_page_config(page_title="📦 Cálculo de Custo de Produto", layout="centered")
st.title("📐 Análise de Custo: Miolo + Bolsa + Divisória + Adesivo + Compras Diretas")

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

        # Converter valor unitário
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
        papeis_unicos = sorted(df_compras['PapelLimpo'].dropna().unique())

        # --- 2. Carregar uso de papel por miolo, bolsa, divisória, adesivo ---
        def carregar_componente(url, colunas):
            df = pd.read_csv(url, encoding='utf-8')
            df.columns = colunas
            df['QuantidadePapel'] = pd.to_numeric(df['QuantidadePapel'], errors='coerce')
            df['ValorImpressao'] = pd.to_numeric(df['ValorImpressao'], errors='coerce')
            df['UnitImpressao'] = pd.to_numeric(df['UnitImpressao'], errors='coerce')
            df['QuantidadeAprovada'] = pd.to_numeric(df['QuantidadeAprovada'], errors='coerce')
            df['Papel'] = df['Papel'].apply(limpar_papel)
            return df

        df_miolos = carregar_componente(URL_USO_PAPEL_MIOLO, ['Miolo', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_bolsas = carregar_componente(URL_USO_PAPEL_BOLSA, ['Bolsa', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_divisorias = carregar_componente(URL_USO_PAPEL_DIVISORIA, ['Divisoria', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])
        df_adesivos = carregar_componente(URL_USO_PAPEL_ADESIVO, ['Adesivo', 'Papel', 'QuantidadePapel', 'ValorImpressao', 'UnitImpressao', 'QuantidadeAprovada'])

        # --- 3. Carregar compras diretas ---
        df_cd = pd.read_csv(URL_COMPRA_DIRETA, encoding='utf-8')
        if 'CATEGORIA_MATERIAL_PCP' not in df_cd.columns:
            st.error("❌ Coluna 'CATEGORIA_MATERIAL_PCP' não encontrada.")
            return None

        df_cd = df_cd.dropna(subset=['CATEGORIA_MATERIAL_PCP', 'VALOR_UNITARIO'])
        df_cd['VALOR_UNITARIO'] = pd.to_numeric(df_cd['VALOR_UNITARIO'], errors='coerce')
        df_cd = df_cd.dropna(subset=['VALOR_UNITARIO'])

        # Extrair nome limpo
        df_cd['NomeLimpo'] = df_cd['DEMANDA'].apply(lambda x: re.sub(r'^MP\d{3}\s*', '', str(x)))
        df_cd['NomeLimpo'] = df_cd['NomeLimpo'].apply(lambda x: re.sub(r'\s*UNICA-[A-Z0-9\-]+', '', str(x)))
        df_cd['NomeLimpo'] = df_cd['NomeLimpo'].str.strip()

        # Agrupar por categoria
        categorias_cd = {}
        for cat in df_cd['CATEGORIA_MATERIAL_PCP'].dropna().unique():
            itens = df_cd[df_cd['CATEGORIA_MATERIAL_PCP'] == cat]
            categorias_cd[cat] = itens[['NomeLimpo', 'VALOR_UNITARIO']].drop_duplicates().to_dict('records')

        # --- 4. Carregar tabela de WIRE-O ---
        try:
            df_wireo = pd.read_csv(URL_TABELA_WIREO, encoding='utf-8')
            df_wireo.columns = ['WIREO', 'QUANTIDADE_POR_CAIXA']
            df_wireo['WIREO'] = df_wireo['WIREO'].astype(str).str.strip()
            mapeamento_wireo = dict(zip(df_wireo['WIREO'], df_wireo['QUANTIDADE_POR_CAIXA']))
        except Exception:
            st.warning("⚠️ Não foi possível carregar a tabela de WIRE-O. Assumindo 6000 anéis por caixa.")
            mapeamento_wireo = {}

        return (df_compras, papeis_unicos, df_miolos, df_bolsas, df_divisorias, 
                df_adesivos, categorias_cd, mapeamento_wireo)

    except Exception as e:
        st.error(f"❌ Erro ao carregar os dados: {e}")
        return None

# ================== CARREGAR DADOS ==================
dados = carregar_dados()
if dados is None:
    st.stop()

(df_compras, papeis_unicos, df_miolos, df_bolsas, df_divisorias, 
 df_adesivos, categorias_cd, mapeamento_wireo) = dados

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

# ================== FUNÇÃO PARA CALCULAR CUSTO UNITÁRIO (papel + serviço) ==================
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
        st.warning(f"⚠️ Papel não encontrado: **{papel_necessario}**")
        return None, None, None, None

    preco_unitario_papel = df_papel.iloc[0]['ValorUnitario']
    custo_papel_por_unidade = preco_unitario_papel * folhas_por_unidade
    custo_servico_por_unidade = valor_impressao / quantidade_orcamento
    custo_total_unitario = custo_papel_por_unidade + custo_servico_por_unidade

    return custo_total_unitario, custo_papel_por_unidade, custo_servico_por_unidade, papel_necessario

# ================== FUNÇÃO: CÁLCULO PERSONALIZADO (papel) ==================
def calcular_personalizado(papel_selecionado, aproveitamento, valor_servico, quantidade_orcamento):
    if aproveitamento <= 0:
        aproveitamento = 1

    df_papel = df_compras[df_compras['PapelLimpo'] == papel_selecionado]
    if df_papel.empty:
        st.error(f"❌ Papel não encontrado: **{papel_selecionado}**")
        return None, None, None, None, None

    preco_unitario_papel = df_papel.iloc[0]['ValorUnitario']
    custo_papel_por_unidade = preco_unitario_papel / aproveitamento
    custo_servico_por_unidade = valor_servico / quantidade_orcamento
    custo_total = custo_papel_por_unidade + custo_servico_por_unidade

    return custo_total, custo_papel_por_unidade, custo_servico_por_unidade, papel_selecionado, ""

# ================== COMPONENTES: MIÓLO, BOLSA, DIVISÓRIA, ADESIVO ==================
st.markdown("### 📄 Componentes com Papel e Impressão")

# === Miolo ===
miolos = sorted(df_miolos['Miolo'].dropna().unique())
miolo_opcoes = ["Personalizado"] + list(miolos)
inclui_miolo = st.checkbox("📘 Incluir Miolo?", value=False)
if inclui_miolo:
    miolo_selecionado = st.selectbox("Miolo:", options=miolo_opcoes, index=0, key="miolo")
    if miolo_selecionado == "Personalizado":
        col1, col2, col3 = st.columns(3)
        papel_miolo = col1.selectbox("Papel utilizado (miolo)", options=papeis_unicos, index=0, key="papel_miolo")
        aproveitamento_miolo = col2.number_input("Aproveitamento (unidades por folha)", min_value=0.1, value=5.0, step=0.1, key="aprov_miolo")
        valor_servico_miolo = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=13050.0, key="serv_miolo")
    else:
        papel_miolo = None
else:
    miolo_selecionado = None

# === Bolsa ===
bolsas = sorted(df_bolsas['Bolsa'].dropna().unique())
bolsa_opcoes = ["Personalizado"] + list(bolsas)
inclui_bolsa = st.checkbox("👜 Incluir Bolsa?", value=False)
if inclui_bolsa:
    bolsa_selecionada = st.selectbox("Bolsa:", options=bolsa_opcoes, index=0, key="bolsa")
    if bolsa_selecionada == "Personalizado":
        col1, col2, col3 = st.columns(3)
        papel_bolsa = col1.selectbox("Papel utilizado (bolsa)", options=papeis_unicos, index=0, key="papel_bolsa")
        aproveitamento_bolsa = col2.number_input("Aproveitamento (unidades por folha)", min_value=0.1, value=4.0, step=0.1, key="aprov_bolsa")
        valor_servico_bolsa = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=2425.0, key="serv_bolsa")
    else:
        papel_bolsa = None
else:
    bolsa_selecionada = None

# === Divisória ===
divisorias = sorted(df_divisorias['Divisoria'].dropna().unique())
divisoria_opcoes = ["Personalizado"] + list(divisorias)
inclui_divisoria = st.checkbox("🔖 Incluir Divisória?", value=False)
if inclui_divisoria:
    divisoria_selecionada = st.selectbox("Divisória:", options=divisoria_opcoes, index=0, key="divisoria")
    if divisoria_selecionada == "Personalizado":
        col1, col2, col3 = st.columns(3)
        papel_divisoria = col1.selectbox("Papel utilizado (divisória)", options=papeis_unicos, index=0, key="papel_divisoria")
        aproveitamento_divisoria = col2.number_input("Aproveitamento (unidades por folha)", min_value=0.1, value=3.0, step=0.1, key="aprov_div")
        valor_servico_divisoria = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=22986.0, key="serv_div")
    else:
        papel_divisoria = None
else:
    divisoria_selecionada = None

# === Adesivo ===
adesivos = sorted(df_adesivos['Adesivo'].dropna().unique())
adesivo_opcoes = ["Personalizado"] + list(adesivos)
inclui_adesivo = st.checkbox("🏷️ Incluir Adesivo?", value=False)
if inclui_adesivo:
    adesivo_selecionado = st.selectbox("Adesivo:", options=adesivo_opcoes, index=0, key="adesivo")
    if adesivo_selecionado == "Personalizado":
        col1, col2, col3 = st.columns(3)
        papel_adesivo = col1.selectbox("Papel utilizado (adesivo)", options=papeis_unicos, index=0, key="papel_adesivo")
        aproveitamento_adesivo = col2.number_input("Aproveitamento (unidades por folha)", min_value=0.1, value=10.0, step=0.1, key="aprov_adesivo")
        valor_servico_adesivo = col3.number_input("Valor total do serviço (impressão)", min_value=0.0, value=4840.0, key="serv_adesivo")
    else:
        papel_adesivo = None
else:
    adesivo_selecionado = None

# ================== COMPRAS DIRETAS ==================
st.divider()
st.markdown("### 🔧 Compras Diretas (Aviamentos, Embalagens, etc.)")

custos_cd = {}

for categoria in sorted(categorias_cd.keys()):
    itens = categorias_cd[categoria]
    nomes_itens = [item['NomeLimpo'] for item in itens]
    opcoes = ["Personalizado"] + nomes_itens

    # Checkbox para incluir
    inclui = st.checkbox(f"🔧 Incluir {categoria}?", value=False, key=f"check_{categoria}")
    if not inclui:
        continue

    selecionado = st.selectbox(f"{categoria}:", options=opcoes, key=f"cd_{categoria}")

    if selecionado == "Personalizado":
        valor_unitario = st.number_input(f"Valor unitário do {categoria} personalizado", min_value=0.0, value=1.0, key=f"vu_{categoria}")
        aproveitamento = st.number_input(f"Aproveitamento (ex: 0.3 para 30cm de 1m)", min_value=0.0, value=1.0, step=0.01, key=f"aprov_{categoria}")
        custos_cd[categoria] = valor_unitario * aproveitamento
    else:
        item = next((i for i in itens if i['NomeLimpo'] == selecionado), None)
        if item:
            preco_unitario = item['VALOR_UNITARIO']
            if categoria == "WIRE-O":
                # WIRE-O: preço por caixa → anéis por caixa → anéis por produto
                quantidade_por_caixa = mapeamento_wireo.get(selecionado, 6000)
                aneis_por_unidade = st.number_input(f"Número de anéis por unidade ({selecionado})", min_value=1, value=1, step=1, key=f"aneis_{selecionado}")
                preco_por_anel = preco_unitario / quantidade_por_caixa
                custos_cd[categoria] = preco_por_anel * aneis_por_unidade
            else:
                aproveitamento = st.number_input(f"Aproveitamento ({selecionado})", min_value=0.0, value=1.0, step=0.01, key=f"aprov_{selecionado}")
                custos_cd[categoria] = preco_unitario * aproveitamento

# ================== CALCULAR CUSTOS ==================
custo_miolo = None
custo_bolsa = None
custo_divisoria = None
custo_adesivo = None

# Miolo
if inclui_miolo and miolo_selecionado and miolo_selecionado != "Personalizado":
    custo_miolo = calcular_custo(miolo_selecionado, df_miolos, "Miolo")
elif inclui_miolo and miolo_selecionado == "Personalizado":
    custo_miolo = calcular_personalizado(papel_miolo, aproveitamento_miolo, valor_servico_miolo, quantidade_orcamento)

# Bolsa
if inclui_bolsa and bolsa_selecionada and bolsa_selecionada != "Personalizado":
    custo_bolsa = calcular_custo(bolsa_selecionada, df_bolsas, "Bolsa")
elif inclui_bolsa and bolsa_selecionada == "Personalizado":
    custo_bolsa = calcular_personalizado(papel_bolsa, aproveitamento_bolsa, valor_servico_bolsa, quantidade_orcamento)

# Divisória
if inclui_divisoria and divisoria_selecionada and divisoria_selecionada != "Personalizado":
    custo_divisoria = calcular_custo(divisoria_selecionada, df_divisorias, "Divisoria")
elif inclui_divisoria and divisoria_selecionada == "Personalizado":
    custo_divisoria = calcular_personalizado(papel_divisoria, aproveitamento_divisoria, valor_servico_divisoria, quantidade_orcamento)

# Adesivo
if inclui_adesivo and adesivo_selecionado and adesivo_selecionado != "Personalizado":
    custo_adesivo = calcular_custo(adesivo_selecionado, df_adesivos, "Adesivo")
elif inclui_adesivo and adesivo_selecionado == "Personalizado":
    custo_adesivo = calcular_personalizado(papel_adesivo, aproveitamento_adesivo, valor_servico_adesivo, quantidade_orcamento)

# ================== EXIBIR RESULTADOS ==================
st.divider()
st.subheader("📊 Resultados por Componente")

cols = st.columns(4)

# Exibir Miolo
if inclui_miolo and miolo_selecionado != "Personalizado" and custo_miolo:
    with cols[0]:
        st.markdown(f"**{miolo_selecionado}**")
        st.metric("Custo Unit.", f"R$ {custo_miolo[0]:,.2f}".replace('.', ','))
elif inclui_miolo and miolo_selecionado == "Personalizado" and custo_miolo:
    with cols[0]:
        st.markdown("**Miolo Personalizado**")
        st.metric("Custo Unit.", f"R$ {custo_miolo[0]:,.2f}".replace('.', ','))

# Exibir Bolsa
if inclui_bolsa and bolsa_selecionada != "Personalizado" and custo_bolsa:
    with cols[1]:
        st.markdown(f"**{bolsa_selecionada}**")
        st.metric("Custo Unit.", f"R$ {custo_bolsa[0]:,.2f}".replace('.', ','))
elif inclui_bolsa and bolsa_selecionada == "Personalizado" and custo_bolsa:
    with cols[1]:
        st.markdown("**Bolsa Personalizada**")
        st.metric("Custo Unit.", f"R$ {custo_bolsa[0]:,.2f}".replace('.', ','))

# Exibir Divisória
if inclui_divisoria and divisoria_selecionada != "Personalizado" and custo_divisoria:
    with cols[2]:
        st.markdown(f"**{divisoria_selecionada}**")
        st.metric("Custo Unit.", f"R$ {custo_divisoria[0]:,.2f}".replace('.', ','))
elif inclui_divisoria and divisoria_selecionada == "Personalizado" and custo_divisoria:
    with cols[2]:
        st.markdown("**Divisória Personalizada**")
        st.metric("Custo Unit.", f"R$ {custo_divisoria[0]:,.2f}".replace('.', ','))

# Exibir Adesivo
if inclui_adesivo and adesivo_selecionado != "Personalizado" and custo_adesivo:
    with cols[3]:
        st.markdown(f"**{adesivo_selecionado}**")
        st.metric("Custo Unit.", f"R$ {custo_adesivo[0]:,.2f}".replace('.', ','))
elif inclui_adesivo and adesivo_selecionado == "Personalizado" and custo_adesivo:
    with cols[3]:
        st.markdown("**Adesivo Personalizado**")
        st.metric("Custo Unit.", f"R$ {custo_adesivo[0]:,.2f}".replace('.', ','))

# Exibir Compras Diretas
if custos_cd:
    st.markdown("#### 🔧 Compras Diretas")
    cols_cd = st.columns(3)
    i = 0
    for cat, valor in custos_cd.items():
        if valor > 0:
            col = cols_cd[i % 3]
            with col:
                st.markdown(f"**{cat}**")
                st.metric("Unitário", f"R$ {valor:,.2f}".replace('.', ','))
            i += 1

# ================== CUSTO TOTAL DO PRODUTO ==================
st.divider()
st.subheader("💰 Custo Total Unitário do Produto")

custo_total = 0.0
itens = []

if inclui_miolo and miolo_selecionado != "Personalizado" and custo_miolo:
    custo_total += custo_miolo[0]
    itens.append("Miolo")
elif inclui_miolo and miolo_selecionado == "Personalizado" and custo_miolo:
    custo_total += custo_miolo[0]
    itens.append("Miolo (Pers.)")

if inclui_bolsa and bolsa_selecionada != "Personalizado" and custo_bolsa:
    custo_total += custo_bolsa[0]
    itens.append("Bolsa")
elif inclui_bolsa and bolsa_selecionada == "Personalizado" and custo_bolsa:
    custo_total += custo_bolsa[0]
    itens.append("Bolsa (Pers.)")

if inclui_divisoria and divisoria_selecionada != "Personalizado" and custo_divisoria:
    custo_total += custo_divisoria[0]
    itens.append("Divisória")
elif inclui_divisoria and divisoria_selecionada == "Personalizado" and custo_divisoria:
    custo_total += custo_divisoria[0]
    itens.append("Divisória (Pers.)")

if inclui_adesivo and adesivo_selecionado != "Personalizado" and custo_adesivo:
    custo_total += custo_adesivo[0]
    itens.append("Adesivo")
elif inclui_adesivo and adesivo_selecionado == "Personalizado" and custo_adesivo:
    custo_total += custo_adesivo[0]
    itens.append("Adesivo (Pers.)")

# Compras diretas
for cat, valor in custos_cd.items():
    if valor > 0:
        custo_total += valor
        itens.append(cat)

if itens:
    st.success(f"**Custo Total Unitário ({' + '.join(itens)}):** R$ {custo_total:,.2f}".replace('.', ','))
else:
    st.warning("Nenhum item selecionado.")

# ================== RODAPÉ ==================
st.markdown("---")
st.caption("✅ Cálculo: `(Preço do Papel / Aproveitamento) + (Valor do Serviço / Quantidade)` + Compras Diretas (com aproveitamento)")