import streamlit as st

# Configuração inicial da página para um layout mais amplo
st.set_page_config(page_title="Trasus - Orçamentos", layout="wide")

st.title("👕 Trasus - Gerador de Orçamentos")
st.markdown("---")

# ==========================
# BARRA LATERAL: Dados do Cliente
# ==========================
with st.sidebar:
    st.header("👤 Dados do Cliente")
    cliente_nome = st.text_input("Nome / Contato")
    cliente_empresa = st.text_input("Empresa")
    cliente_telefone = st.text_input("WhatsApp")
    cliente_email = st.text_input("E-mail")

# ==========================
# ÁREA PRINCIPAL: Configuração do Pedido
# ==========================
st.header("1. Detalhes do Pedido")

# Dividindo em duas colunas para um design mais equilibrado
col1, col2 = st.columns(2)

with col1:
    modelo_camisa = st.selectbox(
        "Modelo da Camisa",
        ["Camiseta Básica", "Camisa Polo", "Camisa Social", "Regata"]
    )
    
    tipo_tecido = st.selectbox(
        "Tipo de Tecido",
        ["Algodão 100%", "Malha Fria (PV)", "Dry-Fit", "Piquet (Polo)"]
    )

with col2:
    tipo_personalizacao = st.multiselect(
        "Personalização (Selecione uma ou mais)",
        ["Silk Screen (Estampa)", "Bordado Peito", "Bordado Costas", "Sublimação Total"]
    )
    
    cor_principal = st.color_picker("Cor Predominante da Peça", "#FFFFFF")

st.markdown("---")

# ==========================
# ÁREA PRINCIPAL: Grade de Tamanhos
# ==========================
st.header("2. Grade de Tamanhos e Quantidades")

# Criando 5 colunas alinhadas para os inputs de tamanho ficarem lado a lado
col_p, col_m, col_g, col_gg, col_xg = st.columns(5)

with col_p:
    qtd_p = st.number_input("Tamanho P", min_value=0, step=1)
with col_m:
    qtd_m = st.number_input("Tamanho M", min_value=0, step=1)
with col_g:
    qtd_g = st.number_input("Tamanho G", min_value=0, step=1)
with col_gg:
    qtd_gg = st.number_input("Tamanho GG", min_value=0, step=1)
with col_xg:
    qtd_xg = st.number_input("Tamanho XG", min_value=0, step=1)

st.markdown("---")

# ==========================
# BOTÃO DE AÇÃO
# ==========================
# Botão em destaque ocupando toda a largura do container
if st.button("Calcular Orçamento", type="primary", use_container_width=True):
    # Por enquanto, apenas exibe uma mensagem de sucesso para validar o visual
    st.success("Interface visual carregada com sucesso! O próximo passo é integrar a lógica de cálculo.")