import streamlit as st
import os
import tempfile
from datetime import datetime
from fpdf import FPDF
from PIL import Image

# Configuração inicial
st.set_page_config(page_title="Trasus - Orçamentos", layout="wide", initial_sidebar_state="expanded")

# ==========================
# INICIANDO A MEMÓRIA (CARRINHO)
# ==========================
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

# ==========================
# TABELAS DE PREÇOS (Atualizadas)
# ==========================
TABELA_MODELOS = {
    "Camiseta Básica": 35.00,
    "Camisa Polo": 55.00,
    "Camisa Social": 85.00,
    "Regata": 28.00,
    "Shorts": 25.00,         # NOVO ITEM
    "Calça Esportiva": 45.00 # NOVO ITEM
}

TABELA_TECIDOS = {
    "Algodão 100%": 0.00,
    "Malha Fria (PV)": 2.50,
    "Dry-Fit": 5.00,
    "Piquet (Polo)": 8.00,
    "Cacharel": 3.00,        # NOVO TECIDO
    "Helanca": 4.50          # NOVO TECIDO
}

TABELA_PERSONALIZACAO = {
    "Sem Personalização": 0.00,
    "Silk Screen (Estampa)": 4.50,
    "Bordado Peito": 8.00,
    "Bordado Costas": 15.00,
    "Sublimação Total": 12.00
}

# ==========================
# ESTILOS VISUAIS (CSS)
# ==========================
st.markdown("""
<style>
    .stApp { background-color: #1c1c1c; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #262626; padding-top: 20px; }
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input { background-color: #333333; color: #e0e0e0; border: 1px solid #444444; }
    .stTextInput>label, .stSelectbox>label, .stNumberInput>label, .stFileUploader>label { color: #aaaaaa; }
    .stButton>button { background-color: #ff4c4c; color: white; border: none; padding: 10px 24px; border-radius: 4px; font-weight: bold; }
    .stButton>button:hover { background-color: #ff3333; color: white; }
    .box-carrinho { background-color: #262626; padding: 15px; border-radius: 8px; border-left: 4px solid #4caf50; margin-bottom: 10px;}
    .resultado-box { background-color: #333333; padding: 20px; border-radius: 8px; border-left: 5px solid #ff4c4c; margin-top: 20px;}
</style>
""", unsafe_allow_html=True)

st.title("👕 Orçamentos Multi-Itens Trasus")
st.markdown("---")

# ==========================
# BARRA LATERAL: Dados do Cliente
# ==========================
with st.sidebar:
    if os.path.exists('logo_trasus.png'):
        st.image('logo_trasus.png', use_column_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: white;'>TRASUS</h1>", unsafe_allow_html=True)

    st.header("👤 Dados do Cliente")
    cliente_nome = st.text_input("Nome / Contato", value="Marcelo")
    cliente_empresa = st.text_input("Empresa", value="MG propagapa")
    cliente_telefone = st.text_input("WhatsApp (apenas números)", value="75981040304")
    cliente_email = st.text_input("E-mail")

# ==========================
# ÁREA 1: ADICIONAR NOVO ITEM
# ==========================
st.header("1. Configurar Novo Item")
col1, col2 = st.columns(2)

with col1:
    modelo_selecionado = st.selectbox("Produto", list(TABELA_MODELOS.keys()))
    tecido_selecionado = st.selectbox("Tecido", list(TABELA_TECIDOS.keys()))

with col2:
    personalizacao_selecionada = st.multiselect("Personalizações", list(TABELA_PERSONALIZACAO.keys()), default=["Sublimação Total"])
    cor_principal = st.color_picker("Cor Predominante", "#000000")

st.markdown("**Grade de Tamanhos:**")
col_p, col_m, col_g, col_gg, col_xg = st.columns(5)
with col_p: qtd_p = st.number_input("P", min_value=0, step=1, value=0)
with col_m: qtd_m = st.number_input("M", min_value=0, step=1, value=0)
with col_g: qtd_g = st.number_input("G", min_value=0, step=1, value=0)
with col_gg: qtd_gg = st.number_input("GG", min_value=0, step=1, value=0)
with col_xg: qtd_xg = st.number_input("XG", min_value=0, step=1, value=0)

qtd_item_total = qtd_p + qtd_m + qtd_g + qtd_gg + qtd_xg

# Botão para salvar o item na memória (Carrinho)
if st.button("➕ Adicionar Item ao Pedido"):
    if qtd_item_total == 0:
        st.warning("⚠️ Adicione quantidades na grade antes de salvar o item.")
    else:
        # Calcula os valores deste item específico
        v_modelo = TABELA_MODELOS[modelo_selecionado]
        v_tecido = TABELA_TECIDOS[tecido_selecionado]
        v_pers = sum([TABELA_PERSONALIZACAO[p] for p in personalizacao_selecionada])
        
        preco_unit = v_modelo + v_tecido + v_pers
        preco_total = preco_unit * qtd_item_total
        
        # Cria um dicionário com os dados do item
        novo_item = {
            "descricao": f"{modelo_selecionado} ({tecido_selecionado})",
            "quantidade": qtd_item_total,
            "unitario": preco_unit,
            "total": preco_total,
            "grade": f"P({qtd_p}) M({qtd_m}) G({qtd_g}) GG({qtd_gg}) XG({qtd_xg})",
            "personalizacao": ", ".join(personalizacao_selecionada)
        }
        
        # Salva na memória
        st.session_state.carrinho.append(novo_item)
        st.success(f"✅ {modelo_selecionado} adicionado com sucesso!")
        st.rerun() # Atualiza a tela

st.markdown("---")

# ==========================
# ÁREA 2: RESUMO DO PEDIDO (CARRINHO)
# ==========================
st.header(f"2. Resumo do Pedido ({len(st.session_state.carrinho)} itens)")

valor_geral_pedido = 0.0

if len(st.session_state.carrinho) == 0:
    st.info("Nenhum item adicionado ao pedido ainda.")
else:
    for i, item in enumerate(st.session_state.carrinho):
        valor_geral_pedido += item["total"]
        st.markdown(f"""
        <div class="box-carrinho">
            <strong>Item {i+1}: {item['descricao']}</strong><br>
            <span style="color:#aaaaaa; font-size:14px;">
            Quantidade: {item['quantidade']} peças | V. Unitário: R$ {item['unitario']:.2f} | <strong>Subtotal: R$ {item['total']:.2f}</strong><br>
            Grade: {item['grade']} | Extras: {item['personalizacao']}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🗑️ Limpar Pedido"):
        st.session_state.carrinho = []
        st.rerun()

st.markdown("---")

# ==========================
# ÁREA 3: ANEXOS E GERAÇÃO DO PDF
# ==========================
st.header("3. Anexos e Finalização")
imagem_upload = st.file_uploader("Anexe o Layout Geral (Opcional)", type=["jpg", "jpeg", "png"])

if st.button("Gerar Orçamento Final em PDF", type="primary", use_container_width=True):
    if len(st.session_state.carrinho) == 0:
        st.error("⚠️ O pedido está vazio. Adicione itens antes de gerar o PDF.")
    else:
        # Formatação WhatsApp
        telefone_limpo = ''.join(filter(str.isdigit, cliente_telefone))
        telefone_formatado = f"{telefone_limpo[:2]}.{telefone_limpo[2:7]}-{telefone_limpo[7:]}" if len(telefone_limpo) == 11 else cliente_telefone
        
        numero_orcamento = f"TRC-{datetime.now().strftime('%y%m%d-%H%M%S')}"

        st.markdown(f"""
        <div class="resultado-box">
            <h2 style="color: #ff4c4c; margin-bottom: 0;">Valor Total do Pedido: R$ {valor_geral_pedido:.2f}</h2>
            <p style="color: #aaaaaa;">Orçamento {numero_orcamento} gerado com sucesso! Baixe o PDF abaixo.</p>
        </div>
        """, unsafe_allow_html=True)

        # ==========================
        # CONSTRUÇÃO DO PDF
        # ==========================
        pdf = FPDF()
        pdf.add_page()
        
        if os.path.exists("background.jpg"):
            pdf.image("background.jpg", x=0, y=0, w=210, h=297)
        
        pdf.set_y(30) 
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 10, f"Orçamento: {numero_orcamento}", ln=True, align="R") 
        
        pdf.set_y(80) 
        
        # Dados do Cliente
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "PROPOSTA COMERCIAL", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 7, f"Cliente: {cliente_nome} | Empresa: {cliente_empresa}", ln=True)
        pdf.cell(0, 7, f"WhatsApp: {telefone_formatado} | E-mail: {cliente_email}", ln=True)
        pdf.ln(10)

        # Imagem Anexada
        if imagem_upload is not None:
            img = Image.open(imagem_upload).convert('RGB')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                img.save(tmp_file.name, format="JPEG")
                tmp_path = tmp_file.name
            pdf.image(tmp_path, x=55, y=pdf.get_y(), w=100)
            pdf.set_y(pdf.get_y() + 110) 
        
        # Construção da Tabela com Vários Itens
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(80, 10, " Descrição do Produto", border=1, align="L")
        pdf.cell(30, 10, " Qtd", border=1, align="C")
        pdf.cell(40, 10, " Valor Unitário", border=1, align="C")
        pdf.cell(40, 10, " Total", border=1, align="C")
        pdf.ln()
        
        # Laço de repetição: desenha uma linha para cada item no carrinho
        for item in st.session_state.carrinho:
            pdf.set_font("Arial", '', 10)
            pdf.cell(80, 8, f" {item['descricao'][:38]}", border="LTR", align="L")
            pdf.cell(30, 8, f" {item['quantidade']} pçs", border="LTR", align="C")
            pdf.cell(40, 8, f" R$ {item['unitario']:.2f}", border="LTR", align="C")
            pdf.cell(40, 8, f" R$ {item['total']:.2f}", border="LTR", align="C")
            pdf.ln()
            
            # Linha de baixo (Mesclada) com a grade e personalização em itálico
            pdf.set_font("Arial", 'I', 8)
            detalhes = f"   Grade: {item['grade']} | Extras: {item['personalizacao']}"
            pdf.cell(190, 6, detalhes, border="LBR", align="L")
            pdf.ln()

        # Resumo Financeiro Final no PDF
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(150, 10, "VALOR TOTAL DO PEDIDO:", align="R")
        pdf.cell(40, 10, f"R$ {valor_geral_pedido:.2f}", align="C")

        # Gera o Download
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📄 Fazer Download do Orçamento Completo",
            data=pdf_bytes,
            file_name=f"{numero_orcamento}_{cliente_empresa.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
