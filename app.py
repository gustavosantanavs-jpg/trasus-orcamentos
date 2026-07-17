import streamlit as st
import os

# Configuração inicial da página e tema dark
st.set_page_config(
    page_title="Trasus - Orçamentos",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS para forçar cores e garantir consistência (tema dark/cinza)
st.markdown("""
<style>
    /* Cor de fundo e texto principal */
    .stApp {
        background-color: #1c1c1c;
        color: #e0e0e0;
    }
    
    /* Estilo para a barra lateral */
    [data-testid="stSidebar"] {
        background-color: #262626;
        padding-top: 20px;
    }
    
    /* Estilo para campos de entrada e seletores */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input {
        background-color: #333333;
        color: #e0e0e0;
        border: 1px solid #444444;
    }
    
    /* Estilo para rótulos de campo (labels) */
    .stTextInput>label, .stSelectbox>label, .stNumberInput>label {
        color: #aaaaaa;
    }
    
    /* Estilo para o botão principal (vermelho vibrante) */
    .stButton>button {
        background-color: #ff4c4c;
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 4px;
        font-weight: bold;
        use_container_width: True;
    }
    .stButton>button:hover {
        background-color: #ff3333;
        color: white;
    }

    /* Estilo para o banner de sucesso (verde-menta escuro) */
    .stAlert {
        background-color: #2e4d3f;
        color: #a3e6b5;
        border: 1px solid #416e59;
    }
</style>
""", unsafe_allow_html=True)

st.title("👕 Orçamentos de Camisaria Trasus")
st.markdown("---")

# ==========================
# BARRA LATERAL: Logo e Dados
# ==========================
with st.sidebar:
    # 2. Adicionando a logo acima dos dados
    # IMPORTANTE: Substitua 'logo_trasus.png' pelo arquivo real da sua logo
    if os.path.exists('logo_trasus.png'):
        st.image('logo_trasus.png', use_column_width=True)
    else:
        # Placeholder caso o arquivo de logo não exista
        st.warning("⚠️ Arquivo 'logo_trasus.png' não encontrado na pasta.")
        st.markdown("<h1 style='text-align: center; color: white;'>TRASUS</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #aaaaaa;'>Sua Logo Aqui</p>", unsafe_allow_html=True)
        st.markdown("---")

    st.header("👤 Dados do Cliente")
    # Campos de entrada escurecidos com rótulos cinza claro
    cliente_nome = st.text_input("Nome / Contato", key="nome")
    cliente_empresa = st.text_input("Empresa", key="empresa")
    cliente_telefone = st.text_input("WhatsApp", key="telefone")
    cliente_email = st.text_input("E-mail", key="email")

# ==========================
# ÁREA PRINCIPAL: Configuração
# ==========================
st.header("1. Detalhes do Pedido")

# Duas colunas para design equilibrado
col1, col2 = st.columns(2)

with col1:
    modelo_camisa = st.selectbox(
        "Modelo da Camisa",
        ["Camiseta Básica", "Camisa Polo", "Camisa Social", "Regata"],
        key="modelo"
    )
    
    tipo_tecido = st.selectbox(
        "Tipo de Tecido",
        ["Algodão 100%", "Malha Fria (PV)", "Dry-Fit", "Piquet (Polo)"],
        key="tecido"
    )

with col2:
    # Exemplo de chip vermelho (usando markdown simulado para chip)
    st.markdown('<div style="display: flex; align-items: center; gap: 8px;"><label style="color: #aaaaaa;">Personalização</label><div style="background-color: #ff4c4c; color: white; padding: 4px 8px; border-radius: 16px; font-size: 12px; font-weight: bold;">Sublimação Total <span style="cursor:pointer;">&times;</span></div></div>', unsafe_allow_html=True)
    
    tipo_personalizacao = st.multiselect(
        "(Selecione uma ou mais)",
        ["Silk Screen (Estampa)", "Bordado Peito", "Bordado Costas", "Sublimação Total"],
        default=["Sublimação Total"],
        key="personalizacao_hidden",
        label_visibility="collapsed" # Esconde o label real para usar o simulado acima
    )
    
    cor_principal = st.color_picker("Cor Predominante da Peça", "#000000", key="cor")

st.markdown("---")

# ==========================
# ÁREA PRINCIPAL: Grade
# ==========================
st.header("2. Grade de Tamanhos e Quantidades")

# Cinco colunas alinhadas
col_p, col_m, col_g, col_gg, col_xg = st.columns(5)

with col_p:
    qtd_p = st.number_input("Tamanho P", min_value=0, step=1, value=1, key="p")
with col_m:
    qtd_m = st.number_input("Tamanho M", min_value=0, step=1, value=5, key="m")
with col_g:
    qtd_g = st.number_input("Tamanho G", min_value=0, step=1, value=10, key="g")
with col_gg:
    qtd_gg = st.number_input("Tamanho GG", min_value=0, step=1, value=1, key="gg")
with col_xg:
    qtd_xg = st.number_input("Tamanho XG", min_value=0, step=1, value=1, key="xg")

st.markdown("---")

# ==========================
# BOTÃO E MENSAGEM
# ==========================
# Botão em destaque ocupando toda a largura
if st.button("Calcular Orçamento", type="primary", use_container_width=True, key="calcular"):
    # Mensagem de sucesso com estilo verde-menta escuro
    st.success("Interface visual carregada com sucesso! O próximo passo é integrar a lógica de cálculo.")
