import streamlit as st
import os
import tempfile
import json
import base64
from datetime import datetime
from fpdf import FPDF
from PIL import Image

# ==========================
# CONFIGURAÇÃO INICIAL
# ==========================
st.set_page_config(page_title="Trasus - Gestão de Orçamentos", page_icon="👕", layout="wide", initial_sidebar_state="expanded")

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

@st.dialog("📄 Pré-visualização do Orçamento", width="large")
def exibir_popup_pdf(pdf_bytes, numero_orcamento):
    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="650" type="application/pdf" style="border: none; border-radius: 8px; box-shadow: 0px 4px 12px rgba(0,0,0,0.5);"></iframe>'
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
if 'desconto_tipo' not in st.session_state:
    st.session_state.desconto_tipo = "Sem desconto"
if 'desconto_valor' not in st.session_state:
    st.session_state.desconto_valor = 0.0
if 'valor_manual_ativado' not in st.session_state:
    st.session_state.valor_manual_ativado = False
if 'valor_manual' not in st.session_state:
    st.session_state.valor_manual = 0.0
if 'confirmar_exclusao' not in st.session_state:
    st.session_state.confirmar_exclusao = None

def novo_pedido():
    st.session_state.carrinho = []
    st.session_state.cliente_atual = {"nome": "", "empresa": "", "telefone": "", "email": ""}
    st.session_state.orcamento_editando = None
    st.session_state.desconto_tipo = "Sem desconto"
    st.session_state.desconto_valor = 0.0
    st.session_state.valor_manual_ativado = False
    st.session_state.valor_manual = 0.0

def remover_item(index):
    st.session_state.carrinho.pop(index)

banco = carregar_banco()

# ==========================
# TABELAS DE PREÇOS
# ==========================
TABELA_MODELOS = {"Camiseta Básica": 35.00, "Camisa Polo": 55.00, "Camisa Social": 85.00, "Regata": 28.00, "Shorts": 25.00, "Calça Esportiva": 45.00}
TABELA_TECIDOS = {"Algodão 100%": 0.00, "Malha Fria (PV)": 2.50, "Dry-Fit": 5.00, "Piquet (Polo)": 8.00, "Cacharel": 3.00, "Helanca": 4.50}
TABELA_PERSONALIZACAO = {"Sem Personalização": 0.00, "Silk Screen (Estampa)": 4.50, "Bordado Peito": 8.00, "Bordado Costas": 15.00, "Sublimação Total": 12.00}

# ==========================
# ESTILOS VISUAIS (CSS) - Otimizado e com Animações
# ==========================
st.markdown("""
<style>
    /* Fundo e cores gerais */
    header[data-testid="stHeader"] { background-color: #1c1c1c !important; }
    .stApp { background-color: #1c1c1c; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #242424; padding-top: 20px; border-right: 1px solid #333333; }
    
    /* Inputs amigáveis ao mobile e com hover */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input { 
        background-color: #2b2b2b; 
        color: #f0f0f0; 
        border: 1px solid #444444; 
        border-radius: 6px;
        transition: all 0.3s ease; 
    }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus, .stNumberInput>div>div>input:focus { 
        border: 1px solid #888888; 
        box-shadow: 0 0 5px rgba(255, 255, 255, 0.1);
    }
    .stTextInput>label, .stSelectbox>label, .stNumberInput>label, .stFileUploader>label { 
        color: #ffffff !important; 
        font-weight: 600; 
        letter-spacing: 0.5px;
    }
    
    /* Botões Dinâmicos e Modernos */
    .stButton>button { 
        background-color: #383838 !important; 
        color: #ffffff !important; 
        border: 1px solid #555555 !important; 
        font-weight: bold !important; 
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover { 
        background-color: #505050 !important; 
        border-color: #777777 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }
    .stButton>button:active {
        transform: translateY(0);
        box-shadow: none;
    }

    /* Caixas de destaque (Sem cores alaranjadas, apenas paleta chumbo/prata) */
    .box-carrinho { 
        background-color: #262626; 
        padding: 18px; 
        border-radius: 8px; 
        border-left: 4px solid #6c757d; 
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .box-carrinho:hover {
        background-color: #2a2a2a;
    }
    .box-desconto { 
        background-color: #262626; 
        padding: 18px; 
        border-radius: 8px; 
        border-left: 4px solid #aaaaaa; 
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Expansores estéticos */
    [data-testid="stExpander"] {
        border: 1px solid #444;
        border-radius: 8px;
        background-color: #222222;
    }
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
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.button("🔄 Novo Pedido (Limpar)", on_click=novo_pedido, use_container_width=True)

    st.markdown("---")

    # ==========================
    # BARRA LATERAL: Dados do Cliente
    # ==========================
    with st.sidebar:
        if os.path.exists('logo_trasus.png'):
            st.image('logo_trasus.png', use_container_width=True)
        else:
            st.markdown("<h2 style='text-align: center; color: white;'>TRASUS</h2>", unsafe_allow_html=True)

        st.markdown("---")
        
        # Coloquei dentro de um container com visual agradável
        st.markdown("### 👤 Dados do Cliente")
        c_nome = st.text_input("Nome / Contato", value=st.session_state.cliente_atual["nome"])
        c_empresa = st.text_input("Empresa", value=st.session_state.cliente_atual["empresa"])
        c_telefone = st.text_input("WhatsApp (apenas números)", value=st.session_state.cliente_atual["telefone"])
        c_email = st.text_input("E-mail", value=st.session_state.cliente_atual["email"])
        
        st.session_state.cliente_atual = {"nome": c_nome, "empresa": c_empresa, "telefone": c_telefone, "email": c_email}

    # ==========================
    # ÁREA 1: ADICIONAR ITEM
    # ==========================
    st.subheader("1️⃣ Configurar Novo Item")
    col1, col2 = st.columns(2)
    with col1:
        modelo_selecionado = st.selectbox("Produto", list(TABELA_MODELOS.keys()))
        tecido_selecionado = st.selectbox("Tecido", list(TABELA_TECIDOS.keys()))
    with col2:
        personalizacao_selecionada = st.multiselect("Personalizações", list(TABELA_PERSONALIZACAO.keys()), default=["Sublimação Total"])

    st.markdown("**Grade de Tamanhos:**")
    col_p, col_m, col_g, col_gg, col_xg = st.columns(5)
    with col_p: qtd_p = st.number_input("P", min_value=0, step=1, value=0)
    with col_m: qtd_m = st.number_input("M", min_value=0, step=1, value=0)
    with col_g: qtd_g = st.number_input("G", min_value=0, step=1, value=0)
    with col_gg: qtd_gg = st.number_input("GG", min_value=0, step=1, value=0)
    with col_xg: qtd_xg = st.number_input("XG", min_value=0, step=1, value=0)

    qtd_item_total = qtd_p + qtd_m + qtd_g + qtd_gg + qtd_xg

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Adicionar Item ao Pedido"):
        if qtd_item_total == 0:
            st.warning("⚠️ Adicione quantidades na grade antes de prosseguir.")
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
    # ÁREA 2: RESUMO (COM BOTÃO REMOVER)
    # ==========================
    st.subheader(f"2️⃣ Resumo do Pedido ({len(st.session_state.carrinho)} itens)")
    subtotal_pedido = 0.0

    if len(st.session_state.carrinho) == 0:
        st.info("Nenhum item adicionado ao pedido ainda.")
    else:
        for i, item in enumerate(st.session_state.carrinho):
            subtotal_pedido += item["total"]
            
            col_info, col_btn = st.columns([4, 1])
            
            with col_info:
                st.markdown(f"""
                <div class="box-carrinho">
                    <strong style="font-size: 1.1em; color: #ffffff;">Item {i+1}: {item['descricao']}</strong><br>
                    <span style="color: #cccccc;">Qtd: {item['quantidade']} | V. Unitário: R$ {item['unitario']:.2f}</span> | <strong>Subtotal: R$ {item['total']:.2f}</strong><br>
                    <span style="font-size: 0.9em; color: #999999;">Grade: {item['grade']}</span>
                </div>
                """, unsafe_allow_html=True)
                
            with col_btn:
                st.markdown("<div style='margin-top: 35px;'></div>", unsafe_allow_html=True)
                st.button("🗑️", key=f"btn_remover_{i}", help="Remover item", on_click=remover_item, args=(i,), use_container_width=True)
    
    st.markdown("---")

    # ==========================
    # ÁREA 2.1: DESCONTO E AJUSTE MANUAL DE VALOR
    # ==========================
    st.subheader("⚙️ Desconto e Ajuste de Valor")
    st.markdown('<div class="box-desconto">', unsafe_allow_html=True)

    col_desc1, col_desc2 = st.columns(2)
    with col_desc1:
        opcoes_desconto = ["Sem desconto", "Desconto (%)", "Desconto (R$)"]
        desconto_tipo = st.selectbox(
            "Tipo de Desconto",
            opcoes_desconto,
            index=opcoes_desconto.index(st.session_state.desconto_tipo) if st.session_state.desconto_tipo in opcoes_desconto else 0
        )
    with col_desc2:
        if desconto_tipo == "Desconto (%)":
            desconto_valor = st.number_input("Percentual de Desconto (%)", min_value=0.0, max_value=100.0, step=1.0, value=float(st.session_state.desconto_valor))
        elif desconto_tipo == "Desconto (R$)":
            desconto_valor = st.number_input("Valor do Desconto (R$)", min_value=0.0, step=1.0, value=float(st.session_state.desconto_valor))
        else:
            desconto_valor = 0.0
            st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
            st.caption("Nenhum desconto aplicado.")

    # Calcula valor do desconto
    if desconto_tipo == "Desconto (%)":
        valor_desconto_calculado = subtotal_pedido * (desconto_valor / 100)
    elif desconto_tipo == "Desconto (R$)":
        valor_desconto_calculado = desconto_valor
    else:
        valor_desconto_calculado = 0.0

    valor_com_desconto = max(subtotal_pedido - valor_desconto_calculado, 0.0)

    st.markdown("<br>", unsafe_allow_html=True)

    ajustar_manual = st.checkbox("✏️ Ajustar valor final manualmente", value=st.session_state.valor_manual_ativado, help="Sobrepõe os descontos acima.")

    valor_manual_input = st.session_state.valor_manual
    if ajustar_manual:
        valor_padrao_manual = st.session_state.valor_manual if st.session_state.valor_manual_ativado and st.session_state.valor_manual > 0 else valor_com_desconto
        valor_manual_input = st.number_input("Valor Final do Pedido (R$)", min_value=0.0, step=1.0, value=float(valor_padrao_manual))
        valor_final_pedido = valor_manual_input
    else:
        valor_final_pedido = valor_com_desconto

    # Persiste na sessão
    st.session_state.desconto_tipo = desconto_tipo
    st.session_state.desconto_valor = desconto_valor
    st.session_state.valor_manual_ativado = ajustar_manual
    st.session_state.valor_manual = valor_manual_input

    st.markdown("<br>", unsafe_allow_html=True)
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Subtotal", f"R$ {subtotal_pedido:.2f}")
    if ajustar_manual:
        col_m2.metric("Ajuste Manual", "Ativo")
    else:
        col_m2.metric("Desconto Aplicado", f"R$ {valor_desconto_calculado:.2f}")
    col_m3.metric("Total Final", f"R$ {valor_final_pedido:.2f}")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # ==========================
    # ÁREA 3: ANEXOS MÚLTIPLOS E PDF
    # ==========================
    st.subheader("3️⃣ Anexos e Finalização")
    imagens_upload = st.file_uploader("📸 Anexe imagens do projeto (Até 2 recomendadas)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Gerar Orçamento / Atualizar", type="primary", use_container_width=True):
        if len(st.session_state.carrinho) == 0:
            st.error("⚠️ O pedido está vazio. Adicione itens antes de gerar o orçamento.")
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
                "subtotal": subtotal_pedido,
                "desconto_tipo": desconto_tipo,
                "desconto_valor": desconto_valor,
                "valor_desconto_calculado": valor_desconto_calculado,
                "valor_manual_ativado": ajustar_manual,
                "valor_manual": valor_manual_input,
                "total": valor_final_pedido,
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

            pdf.ln(3)

            # Linha de Subtotal
            pdf.set_font("Arial", '', 10)
            pdf.cell(145, 7, "Subtotal:", align="R")
            pdf.cell(45, 7, f"R$ {subtotal_pedido:.2f}", align="C")
            pdf.ln()

            # Linha de Desconto
            if not ajustar_manual and valor_desconto_calculado > 0:
                if desconto_tipo == "Desconto (%)":
                    label_desconto = f"Desconto ({desconto_valor:.0f}%):"
                else:
                    label_desconto = "Desconto:"
                pdf.cell(145, 7, label_desconto, align="R")
                pdf.cell(45, 7, f"- R$ {valor_desconto_calculado:.2f}", align="C")
                pdf.ln()

            pdf.ln(2)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(145, 10, "TOTAL DO PEDIDO:", align="R")
            pdf.cell(45, 10, f"R$ {valor_final_pedido:.2f}", align="C")

            pdf_bytes = pdf.output(dest='S').encode('latin1')
            
            st.success("✅ Orçamento processado e salvo!")
            exibir_popup_pdf(pdf_bytes, numero_orcamento)

# ==========================
# ABA 2: BUSCAR, EDITAR E EXCLUIR HISTÓRICO
# ==========================
with aba_buscar:
    st.title("🔍 Histórico de Orçamentos")
    termo_busca = st.text_input("Buscar por Nome do Cliente, Empresa ou Número do Orçamento:")
    
    if len(banco) == 0:
        st.info("Nenhum orçamento salvo ainda.")
    else:
        for num, dados in reversed(list(banco.items())):
            texto_busca = f"{num} {dados['cliente']['nome']} {dados['cliente']['empresa']}".lower()
            if termo_busca.lower() in texto_busca:
                with st.expander(f"📄 {num} - {dados['cliente']['nome']} ({dados['cliente']['empresa']}) - R$ {dados['total']:.2f}"):
                    st.write(f"**Data:** {dados['data']}")
                    st.write(f"**Itens:** {len(dados['carrinho'])}")
                    if dados.get('desconto_tipo', 'Sem desconto') != 'Sem desconto' and not dados.get('valor_manual_ativado', False):
                        st.write(f"**Subtotal:** R$ {dados.get('subtotal', dados['total']):.2f} | **Desconto:** R$ {dados.get('valor_desconto_calculado', 0):.2f}")
                    if dados.get('valor_manual_ativado', False):
                        st.write("**Valor ajustado manualmente.**")

                    col_edit, col_del = st.columns(2)

                    with col_edit:
                        if st.button("✏️ Editar", key=f"edit_{num}", use_container_width=True):
                            st.session_state.cliente_atual = dados['cliente']
                            st.session_state.carrinho = dados['carrinho']
                            st.session_state.orcamento_editando = num
                            st.session_state.desconto_tipo = dados.get('desconto_tipo', 'Sem desconto')
                            st.session_state.desconto_valor = dados.get('desconto_valor', 0.0)
                            st.session_state.valor_manual_ativado = dados.get('valor_manual_ativado', False)
                            st.session_state.valor_manual = dados.get('valor_manual', 0.0)
                            st.success("✅ Orçamento carregado! Volte para a aba 'Criar / Editar'.")

                    with col_del:
                        if st.session_state.confirmar_exclusao == num:
                            st.warning("⚠️ Deseja excluir? Essa ação não pode ser desfeita.")
                            col_sim, col_nao = st.columns(2)
                            with col_sim:
                                if st.button("✅ Sim", key=f"confirma_del_{num}", use_container_width=True):
                                    del banco[num]
                                    salvar_banco(banco)
                                    st.session_state.confirmar_exclusao = None
                                    if st.session_state.orcamento_editando == num:
                                        novo_pedido()
                                    st.rerun()
                            with col_nao:
                                if st.button("❌ Não", key=f"cancela_del_{num}", use_container_width=True):
                                    st.session_state.confirmar_exclusao = None
                                    st.rerun()
                        else:
                            if st.button("🗑️ Excluir", key=f"del_{num}", use_container_width=True):
                                st.session_state.confirmar_exclusao = num
                                st.rerun()
