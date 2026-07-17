import streamlit as st
import os
import tempfile
from fpdf import FPDF

st.set_page_config(page_title="Trasus - Orçamentos", layout="wide", initial_sidebar_state="expanded")

# ==========================
# TABELAS DE PREÇOS
# ==========================
TABELA_MODELOS = {
    "Camiseta Básica": 35.00,
    "Camisa Polo": 55.00,
    "Camisa Social": 85.00,
    "Regata": 28.00
}

TABELA_TECIDOS = {
    "Algodão 100%": 0.00,
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
    .stTextInput>label, .stSelectbox>label, .stNumberInput>label, .stFileUploader>label { color: #aaaaaa; }
    .stButton>button { background-color: #ff4c4c; color: white; border: none; padding: 10px 24px; border-radius: 4px; font-weight: bold; }
    .stButton>button:hover { background-color: #ff3333; color: white; }
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
    tipo_tecido = st.selectbox("Tipo de Tecido", list(TABELA_TECIDOS.keys()), index=2)

with col2:
    tipo_personalizacao = st.multiselect("Personalização", list(TABELA_PERSONALIZACAO.keys()), default=["Sublimação Total"])
    cor_principal = st.color_picker("Cor Predominante da Peça", "#000000")

st.markdown("---")

# ==========================
# ÁREA PRINCIPAL: Grade
# ==========================
st.header("2. Grade de Tamanhos e Quantidades")
col_p, col_m, col_g, col_gg, col_xg = st.columns(5)
with col_p: qtd_p = st.number_input("P", min_value=0, step=1, value=1)
with col_m: qtd_m = st.number_input("M", min_value=0, step=1, value=5)
with col_g: qtd_g = st.number_input("G", min_value=0, step=1, value=10)
with col_gg: qtd_gg = st.number_input("GG", min_value=0, step=1, value=1)
with col_xg: qtd_xg = st.number_input("XG", min_value=0, step=1, value=1)

st.markdown("---")

# ==========================
# ÁREA PRINCIPAL: Anexos
# ==========================
st.header("3. Layout e Anexos")
imagem_upload = st.file_uploader("Anexe a imagem com o layout/mockup da camisa (JPG ou PNG)", type=["jpg", "jpeg", "png"])

st.markdown("---")

# ==========================
# LÓGICA DE CÁLCULO E PDF
# ==========================
quantidade_total = qtd_p + qtd_m + qtd_g + qtd_gg + qtd_xg

if st.button("Calcular e Gerar Orçamento", type="primary", use_container_width=True):
    if quantidade_total == 0:
        st.error("⚠️ Por favor, adicione pelo menos uma peça na grade de tamanhos.")
    else:
        # Cálculos Matemáticos
        valor_modelo = TABELA_MODELOS[modelo_camisa]
        valor_tecido = TABELA_TECIDOS[tipo_tecido]
        valor_personalizacao = sum([TABELA_PERSONALIZACAO[item] for item in tipo_personalizacao])
        preco_unitario = valor_modelo + valor_tecido + valor_personalizacao
        valor_final = preco_unitario * quantidade_total
        
        # Exibição na Tela
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

        # ==========================
        # GERAÇÃO DO PDF
        # ==========================
        pdf = FPDF()
        pdf.add_page()
        
        # 1. Background / Papel Timbrado (Se o arquivo timbrado.jpg existir na pasta)
        if os.path.exists("timbrado.jpg"):
            pdf.image("timbrado.jpg", x=0, y=0, w=210, h=297) # Preenche folha A4
        
        # 2. Margem inicial (ajuste dependendo do cabeçalho do seu timbrado)
        pdf.set_y(60) 
        
        # 3. Dados do Cliente
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "PROPOSTA COMERCIAL", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 7, f"Cliente: {cliente_nome} | Empresa: {cliente_empresa}", ln=True)
        pdf.cell(0, 7, f"WhatsApp: {cliente_telefone} | E-mail: {cliente_email}", ln=True)
        pdf.ln(10)

        # 4. Inserir a Imagem do Mockup (se foi feito o upload)
        if imagem_upload is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(imagem_upload.getvalue())
                tmp_path = tmp_file.name
            
            # Centraliza a imagem no PDF (largura de 100mm)
            pdf.image(tmp_path, x=55, y=pdf.get_y(), w=100)
            pdf.set_y(pdf.get_y() + 110) # Pula o espaço da imagem para desenhar a tabela
        
        # 5. Construção da Tabela (Colunas)
        pdf.set_font("Arial", 'B', 10)
        # Cabeçalho da Tabela
        pdf.cell(80, 10, " Descrição do Produto", border=1, align="L")
        pdf.cell(35, 10, " Quantidades", border=1, align="C")
        pdf.cell(35, 10, " Valor Unitário", border=1, align="C")
        pdf.cell(40, 10, " Total", border=1, align="C")
        pdf.ln()
        
        # Linha da Tabela
        pdf.set_font("Arial", '', 10)
        desc_produto = f"{modelo_camisa} ({tipo_tecido})"
        # Tenta criar as linhas da tabela
        pdf.cell(80, 10, f" {desc_produto[:40]}", border=1, align="L")
        pdf.cell(35, 10, f" {quantidade_total} peças", border=1, align="C")
        pdf.cell(35, 10, f" R$ {preco_unitario:.2f}", border=1, align="C")
        pdf.cell(40, 10, f" R$ {valor_final:.2f}", border=1, align="C")
        pdf.ln(15)

        # Detalhamento da Grade
        pdf.set_font("Arial", 'I', 9)
        grade_texto = f"Detalhamento da Grade: P({qtd_p}), M({qtd_m}), G({qtd_g}), GG({qtd_gg}), XG({qtd_xg})"
        personalizacoes = ", ".join(tipo_personalizacao)
        pdf.cell(0, 5, grade_texto, ln=True)
        pdf.cell(0, 5, f"Personalizações inclusas: {personalizacoes}", ln=True)

        # Processar bytes do PDF
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📄 Fazer Download do Orçamento em PDF",
            data=pdf_bytes,
            file_name=f"Orcamento_Trasus_{cliente_empresa.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
