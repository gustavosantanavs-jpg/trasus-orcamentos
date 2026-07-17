import streamlit as st
import os
import tempfile
import json
import base64
from datetime import datetime
from fpdf import FPDF
from PIL import Image

# Configuração inicial
st.set_page_config(page_title="Trasus - Gestão de Orçamentos", layout="wide", initial_sidebar_state="expanded")

ARQUIVO_BD = "banco_orcamentos.json"

# ==========================
# FUNÇÕES DE BANCO DE DADOS (JSON) E POP-UP
# ==========================
def carregar_banco():
    if os.path.exists(ARQUIVO_BD):
        with open(ARQUIVO_BD, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_banco(dados):
    with open(ARQUIVO_BD, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# 🚀 NOVA FUNÇÃO: Cria a janela flutuante (Pop-up) para exibir o PDF
@st.dialog("📄 Pré-visualização do Orçamento", width="large")
def exibir_popup_pdf(pdf_bytes, numero_orcamento):
    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="650" type="application/pdf" style="border: none; border-radius: 8px;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(label="📥 Baixar Arquivo PDF", data=pdf_bytes, file_name=f"{numero_orcamento}.pdf", mime="application/pdf", use_container_width=True)

# ==========================
# INICIANDO A MEMÓRIA DA SESSÃO
# ==========================
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'cliente_atual' not in st.session_state:
    st.session_state.cliente_atual = {"nome": "", "empresa": "", "telefone": "", "email": ""}
if 'orcamento_editando' not in st.session_state:
    st.session_state.orcamento_editando = None

def novo_pedido():
    st.session_state.carrinho = []
    st.session_state.cliente_atual = {"nome": "", "empresa": "", "telefone": "", "email": ""}
    st.session_state.orcamento_editando = None

banco = carregar_banco()

# ==========================
# TABELAS DE PREÇOS
# ==========================
TABELA_MODELOS = {"Camiseta Básica": 35.00, "Camisa Polo": 55.00, "Camisa Social": 85.00, "Regata": 28.00, "Shorts": 25.00, "Calça Esportiva": 45.00}
TABELA_TECIDOS = {"Algodão 100%": 0.00, "Malha Fria (PV)": 2.50, "Dry-Fit": 5.00, "Piquet (Polo)": 8.00, "Cacharel": 3.00, "Helanca": 4.50}
TABELA_PERSONALIZACAO = {"Sem Personalização": 0.00, "Silk Screen (Estampa)": 4.50, "Bordado Peito": 8.00, "Bordado Costas": 15.00, "Sublimação Total": 12.00}

# ==========================
# ESTILOS VISUAIS (CSS)
# ==========================
st.markdown("""
<style>
    header[data-testid="stHeader"] { background-color: #1c1c1c !important; }
    .stApp { background-color: #1c1c1c; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #262626; padding-top: 20px; }
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input { background-color: #333333; color: #e0e0e0; border: 1px solid #444444; }
    .stTextInput>label, .stSelectbox>label, .stNumberInput>label, .stFileUploader>label { color: #ffffff !important; font-weight: 500; }
    .stButton>button { background-color: #4a4a4a !important; color: white !important; border: none !important; font-weight: bold !important; }
    .stButton>button:hover { background-color: #5c5c5c !important; color: white !important; }
    .box-carrinho { background-color: #262626; padding: 15px; border-radius: 8px; border-left: 4px solid #4a4a4a; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# ==========================
# NAVEGAÇÃO EM ABAS
# ==========================
aba_criar, aba_buscar = st.tabs(["📝 Criar / Editar Orçamento", "🔍 Buscar Histórico"])

with aba_criar:
    col_titulo, col_btn_novo = st.columns([3, 1])
    with col_titulo:
        if st.session_state.orcamento_editando:
            st.title(f"✏️ Editando: {st.session_state.orcamento_editando}")
        else:
            st.title("👕 Novo Orçamento Trasus")
    
    with col_btn_novo:
        st.button("🔄 Novo Pedido (Limpar)", on_click=novo_pedido, use_container_width=True)

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
        c_nome = st.text_input("Nome / Contato", value=st.session_state.cliente_atual["nome"])
        c_empresa = st.text_input("Empresa", value=st.session_state.cliente_atual["empresa"])
        c_telefone = st.text_input("WhatsApp (números)", value=st.session_state.cliente_atual["telefone"])
        c_email = st.text_input("E-mail", value=st.session_state.cliente_atual["email"])
        
        st.session_state.cliente_atual = {"nome": c_nome, "empresa": c_empresa, "telefone": c_telefone, "email": c_email}

    # ==========================
    # ÁREA 1: ADICIONAR ITEM
    # ==========================
    st.header("1. Configurar Novo Item")
    col1, col2 = st.columns(2)
    with col1:
        modelo_selecionado = st.selectbox("Produto", list(TABELA_MODELOS.keys()))
        tecido_selecionado = st.selectbox("Tecido", list(TABELA_TECIDOS.keys()))
    with col2:
        personalizacao_selecionada = st.multiselect("Personalizações", list(TABELA_PERSONALIZACAO.keys()), default=["Sublimação Total"])

    col_p, col_m, col_g, col_gg, col_xg = st.columns(5)
    with col_p: qtd_p = st.number_input("P", min_value=0, step=1, value=0)
    with col_m: qtd_m = st.number_input("M", min_value=0, step=1, value=0)
    with col_g: qtd_g = st.number_input("G", min_value=0, step=1, value=0)
    with col_gg: qtd_gg = st.number_input("GG", min_value=0, step=1, value=0)
    with col_xg: qtd_xg = st.number_input("XG", min_value=0, step=1, value=0)

    qtd_item_total = qtd_p + qtd_m + qtd_g + qtd_gg + qtd_xg

    if st.button("➕ Adicionar Item"):
        if qtd_item_total == 0:
            st.warning("Adicione quantidades na grade.")
        else:
            preco_unit = TABELA_MODELOS[modelo_selecionado] + TABELA_TECIDOS[tecido_selecionado] + sum([TABELA_PERSONALIZACAO[p] for p in personalizacao_selecionada])
            st.session_state.carrinho.append({
                "descricao": f"{modelo_selecionado} ({tecido_selecionado})",
                "quantidade": qtd_item_total,
                "unitario": preco_unit,
                "total": preco_unit * qtd_item_total,
                "grade": f"P({qtd_p}) M({qtd_m}) G({qtd_g}) GG({qtd_gg}) XG({qtd_xg})",
                "personalizacao": ", ".join(personalizacao_selecionada)
            })
            st.rerun()

    st.markdown("---")

    # ==========================
    # ÁREA 2: RESUMO
    # ==========================
    st.header(f"2. Resumo do Pedido ({len(st.session_state.carrinho)} itens)")
    valor_geral_pedido = 0.0

    for i, item in enumerate(st.session_state.carrinho):
        valor_geral_pedido += item["total"]
        st.markdown(f"""
        <div class="box-carrinho">
            <strong>Item {i+1}: {item['descricao']}</strong><br>
            Qtd: {item['quantidade']} | V. Unitário: R$ {item['unitario']:.2f} | <strong>Subtotal: R$ {item['total']:.2f}</strong><br>
            Grade: {item['grade']}
        </div>
        """, unsafe_allow_html=True)
    
    # ==========================
    # ÁREA 3: ANEXOS MÚLTIPLOS E PDF
    # ==========================
    st.header("3. Anexos e Finalização")
    imagens_upload = st.file_uploader("Anexe as imagens (Até 2 recomendadas)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if st.button("Gerar Orçamento / Atualizar", type="primary", use_container_width=True):
        if len(st.session_state.carrinho) == 0:
            st.error("⚠️ O pedido está vazio.")
        else:
            telefone_limpo = ''.join(filter(str.isdigit, c_telefone))
            telefone_formatado = f"{telefone_limpo[:2]}.{telefone_limpo[2:7]}-{telefone_limpo[7:]}" if len(telefone_limpo) == 11 else c_telefone
            
            if st.session_state.orcamento_editando:
                numero_orcamento = st.session_state.orcamento_editando
            else:
                numero_orcamento = f"TRC-{datetime.now().strftime('%y%m%d-%H%M%S')}"
                st.session_state.orcamento_editando = numero_orcamento

            banco[numero_orcamento] = {
                "cliente": st.session_state.cliente_atual,
                "carrinho": st.session_state.carrinho,
                "total": valor_geral_pedido,
                "data": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            salvar_banco(banco)

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
            
            pdf.set_y(85) 
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "PROPOSTA COMERCIAL", ln=True, align="C")
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 6, f"Cliente: {c_nome} | Empresa: {c_empresa}", ln=True)
            pdf.cell(0, 6, f"WhatsApp: {telefone_formatado} | E-mail: {c_email}", ln=True)
            pdf.ln(5)

            if imagens_upload:
                x_pos = 30
                for img_file in imagens_upload[:2]: 
                    img = Image.open(img_file).convert('RGB')
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                        img.save(tmp_file.name, format="JPEG")
                        tmp_path = tmp_file.name
                    pdf.image(tmp_path, x=x_pos, y=pdf.get_y(), w=70)
                    x_pos += 80 
                pdf.set_y(pdf.get_y() + 85) 
            
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(80, 8, " Descricao", border=1)
            pdf.cell(20, 8, " Qtd", border=1, align="C")
            pdf.cell(45, 8, " V. Unitario", border=1, align="C")
            pdf.cell(45, 8, " Total", border=1, align="C")
            pdf.ln()
            
            for item in st.session_state.carrinho:
                pdf.set_font("Arial", '', 9)
                pdf.cell(80, 6, f" {item['descricao'][:35]}", border="LTR")
                pdf.cell(20, 6, f" {item['quantidade']}", border="LTR", align="C")
                pdf.cell(45, 6, f" R$ {item['unitario']:.2f}", border="LTR", align="C")
                pdf.cell(45, 6, f" R$ {item['total']:.2f}", border="LTR", align="C")
                pdf.ln()
                pdf.set_font("Arial", 'I', 7)
                pdf.cell(190, 5, f"   Grade: {item['grade']} | Extras: {item['personalizacao']}", border="LBR")
                pdf.ln()

            pdf.ln(5)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(145, 10, "TOTAL DO PEDIDO:", align="R")
            pdf.cell(45, 10, f"R$ {valor_geral_pedido:.2f}", align="C")

            pdf_bytes = pdf.output(dest='S').encode('latin1')
            
            st.success("✅ Orçamento processado e salvo!")
            
            # Chama o Pop-up com o PDF na tela centralizada
            exibir_popup_pdf(pdf_bytes, numero_orcamento)

# ==========================
# ABA 2: BUSCAR E EDITAR HISTÓRICO
# ==========================
with aba_buscar:
    st.title("🔍 Histórico de Orçamentos")
    termo_busca = st.text_input("Buscar por Nome do Cliente, Empresa ou Número do Orçamento:")
    
    if len(banco) == 0:
        st.info("Nenhum orçamento salvo ainda.")
    else:
        for num, dados in reversed(banco.items()):
            texto_busca = f"{num} {dados['cliente']['nome']} {dados['cliente']['empresa']}".lower()
            if termo_busca.lower() in texto_busca:
                with st.expander(f"📄 {num} - {dados['cliente']['nome']} ({dados['cliente']['empresa']}) - R$ {dados['total']:.2f}"):
                    st.write(f"**Data:** {dados['data']}")
                    st.write(f"**Itens:** {len(dados['carrinho'])}")
                    
                    if st.button(f"✏️ Editar este orçamento", key=f"edit_{num}"):
                        st.session_state.cliente_atual = dados['cliente']
                        st.session_state.carrinho = dados['carrinho']
                        st.session_state.orcamento_editando = num
                        st.success("Orçamento carregado! Volte para a aba 'Criar / Editar' no topo da tela para alterar os dados.")
