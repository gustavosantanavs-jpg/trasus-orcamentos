import streamlit as st
import os

st.set_page_config(page_title="Trasus - Orçamentos", layout="wide", initial_sidebar_state="expanded")

# ==========================
# TABELAS DE PREÇOS (Você pode alterar esses valores depois)
# ==========================
TABELA_MODELOS = {
    "Camiseta Básica": 35.00,
    "Camisa Polo": 55.00,
    "Camisa Social": 85.00,
    "Regata": 28.00
}

TABELA_TECIDOS = {
    "Algodão 100%": 0.00,       # Base sem custo extra
    "Malha Fria (PV)": 2.50,
    "Dry-Fit": 5.00,
    "Piquet (Polo)": 8.00
}

TABELA_PERSONALIZACAO = {
    "Silk Screen (Estampa)": 4.50,
    "Bordado Peito": 8.00,
    "Bordado Costas": 15.00,
    "Sublimação Total": 12.00
}

# ==========================
# ESTILOS VISUAIS
# ==========================
st.markdown("""
<style>
    .stApp { background-color: #1c1c1c; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #262626; padding-top: 20px; }
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input { background-color: #333333; color: #e0e0e0; border: 1px solid #444444; }
    .stTextInput>label, .stSelectbox>label, .stNumberInput>label { color: #aaaaaa; }
    .stButton>button { background-color: #ff4c4c; color: white; border: none; padding: 10px 24px; border-radius: 4px; font-weight: bold; }
    .stButton>button:hover { background-color: #ff3333; color: white; }
    
    /* Estilo para a caixa de resultado final */
    .resultado-box { background-color: #333333; padding: 20px; border-radius: 8px; border-left: 5px solid #ff4c4c; margin-top: 20px;}
</style>
""", unsafe_allow_html=True)

st.title("👕 Orçamentos de Camisaria Trasus")
st.markdown("---")

# ==========================
# BARRA LATERAL
# ==========================
with st.sidebar:
    if os.path.exists('logo_trasus.png'):
        st.image('logo_trasus.png', use_column_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: white;'>TRASUS</h1>", unsafe_allow_html=True)
        st.markdown("---")

    st.header("👤 Dados do Cliente")
    cliente_nome = st.text_input("Nome / Contato", value="Marcelo")
    cliente_empresa = st.text_input("Empresa", value="MG propagapa")
    cliente_telefone = st.text_input("WhatsApp", value="75981040304")
    cliente_email = st.text_input("E-mail")

# ==========================
# ÁREA PRINCIPAL: Configuração
# ==========================
st.header("1. Detalhes do Pedido")
col1, col2 = st.columns(2)

with col1:
    modelo_camisa = st.selectbox("Modelo da Camisa", list(TABELA_MODELOS.keys()))
    tipo_tecido = st.selectbox("Tipo de Tecido", list(TABELA_TECIDOS.keys()), index=2) # Index 2 = Dry-Fit

with col2:
    tipo_personalizacao = st.multiselect(
        "Personalização (Selecione uma ou mais)",
        list(TABELA_PERSONALIZACAO.keys()),
        default=["Sublimação Total"]
    )
    cor_principal = st.color_picker("Cor Predominante da Peça", "#000000")

st.markdown("---")

# ==========================
# ÁREA PRINCIPAL: Grade
# ==========================
st.header("2. Grade de Tamanhos e Quantidades")
col_p, col_m, col_g, col_gg, col_xg = st.columns(5)

with col_p: qtd_p = st.number_input("Tamanho P", min_value=0, step=1, value=1)
with col_m: qtd_m = st.number_input("Tamanho M", min_value=0, step=1, value=5)
with col_g: qtd_g = st.number_input("Tamanho G", min_value=0, step=1, value=10)
with col_gg: qtd_gg = st.number_input("Tamanho GG", min_value=0, step=1, value=1)
with col_xg: qtd_xg = st.number_input("Tamanho XG", min_value=0, step=1, value=1)

st.markdown("---")

# ==========================
# LÓGICA DE CÁLCULO
# ==========================
# 1. Calcular a quantidade total de peças
quantidade_total = qtd_p + qtd_m + qtd_g + qtd_gg + qtd_xg

if st.button("Calcular Orçamento", type="primary", use_container_width=True):
    if quantidade_total == 0:
        st.error("⚠️ Por favor, adicione pelo menos uma peça na grade de tamanhos.")
    else:
        # 2. Buscar os valores nos dicionários
        valor_modelo = TABELA_MODELOS[modelo_camisa]
        valor_tecido = TABELA_TECIDOS[tipo_tecido]
        
        # 3. Somar todas as personalizações escolhidas
        valor_personalizacao = sum([TABELA_PERSONALIZACAO[item] for item in tipo_personalizacao])
        
        # 4. Calcular o preço unitário e o total
        preco_unitario = valor_modelo + valor_tecido + valor_personalizacao
        valor_final = preco_unitario * quantidade_total
        
        # 5. Exibir o resultado formatado
        st.markdown(f"""
        <div class="resultado-box">
            <h3 style="color: #ffffff; margin-top: 0;">Resumo do Orçamento</h3>
            <p style="font-size: 16px; color: #aaaaaa;">
                <b>Cliente:</b> {cliente_nome} ({cliente_empresa})<br>
                <b>Produto:</b> {quantidade_total}x {modelo_camisa} em {tipo_tecido}<br>
                <b>Preço Unitário Calculado:</b> R$ {preco_unitario:.2f}
            </p>
            <h2 style="color: #ff4c4c; margin-bottom: 0;">Valor Total: R$ {valor_final:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
