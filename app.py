import streamlit as st
import os
import tempfile
import json
import base64
import urllib.parse
import urllib.request
import io
from datetime import datetime
from fpdf import FPDF
from PIL import Image
import firebase_admin
from firebase_admin import credentials, firestore, storage

# Configuração inicial
st.set_page_config(page_title="Trasus - Gestão de Orçamentos", layout="wide", initial_sidebar_state="expanded")

# ==========================
# CONEXÃO COM O FIREBASE (Firestore + Storage)
# ==========================
@st.cache_resource
def iniciar_firebase():
    if not firebase_admin._apps:
        cred_dict = dict(st.secrets["firebase"])
        storage_bucket = cred_dict.pop("storage_bucket")
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {'storageBucket': storage_bucket})
    return firestore.client(), storage.bucket()

db, bucket = iniciar_firebase()

COLECAO_ORCAMENTOS = "orcamentos"
COLECAO_OS = "ordens_servico"

# ==========================
# FUNÇÕES DE BANCO DE DADOS (FIRESTORE) E POP-UP
# ==========================
def carregar_banco():
    docs = db.collection(COLECAO_ORCAMENTOS).stream()
    return {doc.id: doc.to_dict() for doc in docs}

def salvar_banco(dados):
    colecao = db.collection(COLECAO_ORCAMENTOS)
    existentes = {doc.id for doc in colecao.stream()}
    for numero, conteudo in dados.items():
        colecao.document(numero).set(conteudo)
    for numero in existentes - set(dados.keys()):
        colecao.document(numero).delete()

def carregar_banco_os():
    docs = db.collection(COLECAO_OS).stream()
    return {doc.id: doc.to_dict() for doc in docs}

def salvar_banco_os(dados):
    colecao = db.collection(COLECAO_OS)
    existentes = {doc.id for doc in colecao.stream()}
    for numero, conteudo in dados.items():
        colecao.document(numero).set(conteudo)
    for numero in existentes - set(dados.keys()):
        colecao.document(numero).delete()

def upload_foto_os(numero_os, indice, arquivo):
    """Envia uma foto para o Firebase Storage e retorna o caminho (blob path) salvo."""
    ext = arquivo.name.split(".")[-1]
    caminho_blob = f"fotos_os/{numero_os}_{indice}.{ext}"
    blob = bucket.blob(caminho_blob)
    blob.upload_from_string(arquivo.getbuffer().tobytes(), content_type=arquivo.type)
    blob.make_public()
    return caminho_blob

def url_foto_os(caminho_blob):
    """Retorna a URL pública de uma foto a partir do seu caminho no Storage."""
    return bucket.blob(caminho_blob).public_url

def excluir_foto_os(caminho_blob):
    try:
        bucket.blob(caminho_blob).delete()
    except Exception:
        pass

def salvar_precos(modelos, tecidos, personalizacao):
    db.collection("configuracoes").document("precos").set({
        "modelos": modelos,
        "tecidos": tecidos,
        "personalizacao": personalizacao
    })

def carregar_precos():
    doc = db.collection("configuracoes").document("precos").get()
    if doc.exists:
        dados = doc.to_dict()
        return dados.get("modelos", {}), dados.get("tecidos", {}), dados.get("personalizacao", {})
    else:
        modelos_padrao = {"Camiseta Básica": 35.00, "Camisa Polo": 55.00, "Camisa Social": 85.00, "Regata": 28.00, "Shorts": 25.00, "Calça Esportiva": 45.00, "Baby Look Feminina": 35.00}
        tecidos_padrao = {"Algodão 100%": 0.00, "Malha Fria (PV)": 2.50, "Dry-Fit": 5.00, "Piquet (Polo)": 8.00, "Cacharel": 3.00, "Helanca": 4.50}
        personalizacao_padrao = {"Sem Personalização": 0.00, "Silk Screen (Estampa)": 4.50, "Bordado Peito": 8.00, "Bordado Costas": 15.00, "Sublimação Total": 12.00}
        salvar_precos(modelos_padrao, tecidos_padrao, personalizacao_padrao)
        return modelos_padrao, tecidos_padrao, personalizacao_padrao

@st.dialog("📄 Pré-visualização do Orçamento", width="large")
def exibir_popup_pdf(pdf_bytes, numero_orcamento, telefone_cliente=None, nome_cliente=""):
    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="650" type="application/pdf" style="border: none; border-radius: 8px;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    st.download_button(label="📥 Baixar Arquivo PDF", data=pdf_bytes, file_name=f"{numero_orcamento}.pdf", mime="application/pdf", use_container_width=True)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    share_component = f"""
    <div style="width:100%;">
        <button id="btn_share_wa_{numero_orcamento}" style="
            width:100%; padding:0.7rem 1rem; border:none; border-radius:8px;
            background: linear-gradient(135deg, #25D366, #128C7E); color:#ffffff;
            font-weight:700; font-size:14px; letter-spacing:0.3px;
            cursor:pointer; box-shadow:0 0 14px rgba(37,211,102,0.35); font-family:sans-serif;">
            &#128241; Enviar para WhatsApp
        </button>
        <div id="share_status_{numero_orcamento}" style="font-size:12px; color:#9fd8ff; margin-top:6px; font-family:sans-serif;"></div>
    </div>
    <script>
    (function() {{
        const b64Data = "{b64_pdf}";
        const fileName = "{numero_orcamento}.pdf";
        const statusEl = document.getElementById("share_status_{numero_orcamento}");

        function b64toBlob(b64, contentType) {{
            const byteChars = atob(b64);
            const byteArrays = [];
            for (let offset = 0; offset < byteChars.length; offset += 512) {{
                const slice = byteChars.slice(offset, offset + 512);
                const byteNumbers = new Array(slice.length);
                for (let i = 0; i < slice.length; i++) {{
                    byteNumbers[i] = slice.charCodeAt(i);
                }}
                byteArrays.push(new Uint8Array(byteNumbers));
            }}
            return new Blob(byteArrays, {{type: contentType}});
        }}

        document.getElementById("btn_share_wa_{numero_orcamento}").addEventListener("click", async function() {{
            try {{
                const blob = b64toBlob(b64Data, "application/pdf");
                const file = new File([blob], fileName, {{type: "application/pdf"}});

                if (navigator.canShare && navigator.canShare({{files: [file]}})) {{
                    await navigator.share({{
                        files: [file],
                        title: "Orçamento {numero_orcamento}",
                        text: "Segue o orçamento {numero_orcamento}"
                    }});
                }} else {{
                    statusEl.innerText = "Este navegador não suporta envio direto de arquivo. Use o botão 'Baixar Arquivo PDF' acima e anexe manualmente no WhatsApp.";
                }}
            }} catch (err) {{
                if (err.name !== "AbortError") {{
                    statusEl.innerText = "Não foi possível abrir o compartilhamento. Use o botão 'Baixar Arquivo PDF' acima.";
                }}
            }}
        }});
    }})();
    </script>
    """
    st.components.v1.html(share_component, height=80)

    if telefone_cliente:
        telefone_limpo = ''.join(filter(str.isdigit, telefone_cliente))
        if telefone_limpo:
            if len(telefone_limpo) <= 11:
                telefone_limpo = "55" + telefone_limpo
            mensagem = f"Olá {nome_cliente}! Segue o orçamento {numero_orcamento} da Trasus."
            mensagem_codificada = urllib.parse.quote(mensagem)
            link_wa = f"https://wa.me/{telefone_limpo}?text={mensagem_codificada}"
            st.markdown(
                f'<a href="{link_wa}" target="_blank" style="display:block; text-align:center; margin-top:10px; color:#25D366; font-weight:600; text-decoration:none;">💬 Abrir conversa com {nome_cliente or "o cliente"} no WhatsApp</a>',
                unsafe_allow_html=True
            )
    st.caption("Dica: toque em 'Enviar para WhatsApp' para compartilhar o PDF direto pelo menu do seu celular, sem precisar baixar antes.")

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

if 'os_editando' not in st.session_state:
    st.session_state.os_editando = None
if 'confirmar_exclusao_os' not in st.session_state:
    st.session_state.confirmar_exclusao_os = None

def nova_os():
    st.session_state.os_editando = None

banco = carregar_banco()
banco_os = carregar_banco_os()

# ==========================
# TABELAS DE PREÇOS (editáveis via aba Configurações, salvas no Firestore)
# ==========================
TABELA_MODELOS, TABELA_TECIDOS, TABELA_PERSONALIZACAO = carregar_precos()

# ==========================
# ESTILOS VISUAIS (CSS) - TEMA TECNOLÓGICO
# ==========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');

    :root {
        --neon-cyan: #00e5ff;
        --neon-purple: #a855f7;
        --bg-dark: #0a0e17;
        --bg-panel: #121826;
        --bg-panel-2: #161d2e;
        --border-glow: rgba(0, 229, 255, 0.35);
    }

    header[data-testid="stHeader"] { background-color: var(--bg-dark) !important; }

    .stApp {
        background: radial-gradient(circle at 15% 0%, #0f1b2e 0%, #0a0e17 45%, #05070c 100%);
        color: #e6f1ff;
        font-family: 'Rajdhani', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 1px;
        color: #eaf6ff !important;
        text-shadow: 0 0 12px rgba(0, 229, 255, 0.25);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1220 0%, #10182b 100%);
        border-right: 1px solid var(--border-glow);
        padding-top: 10px;
    }

    .stTextInput>div>div>input, .stSelectbox>div>div>select,
    .stNumberInput>div>div>input, textarea {
        background-color: #0f1626 !important;
        color: #e6f1ff !important;
        border: 1px solid #263049 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border: 1px solid var(--neon-cyan) !important;
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.4) !important;
    }
    .stTextInput>label, .stSelectbox>label, .stNumberInput>label,
    .stFileUploader>label, .stMultiSelect>label {
        color: #9fd8ff !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px;
    }

    .stButton>button {
        background: linear-gradient(135deg, #0090b0, #00e5ff) !important;
        color: #04121a !important;
        border: none !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        border-radius: 8px !important;
        box-shadow: 0 0 14px rgba(0, 229, 255, 0.25);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        box-shadow: 0 0 22px rgba(0, 229, 255, 0.6);
        transform: translateY(-1px);
    }
    .stButton>button:active { transform: translateY(0px); }

    button[kind="primary"] {
        background: linear-gradient(135deg, #7b2ff7, #00e5ff) !important;
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.45) !important;
    }
    button[kind="primary"]:hover {
        box-shadow: 0 0 30px rgba(168, 85, 247, 0.75) !important;
    }

    .box-carrinho {
        background: var(--bg-panel);
        padding: 15px;
        border-radius: 10px;
        border-left: 3px solid var(--neon-cyan);
        box-shadow: 0 0 12px rgba(0, 229, 255, 0.08);
        margin-bottom: 10px;
    }
    .box-desconto {
        background: linear-gradient(135deg, #161d2e, #14101f);
        padding: 18px;
        border-radius: 10px;
        border: 1px solid rgba(168, 85, 247, 0.35);
        box-shadow: 0 0 14px rgba(168, 85, 247, 0.12);
        margin-bottom: 10px;
    }

    [data-testid="stMetric"] {
        background: var(--bg-panel-2);
        border: 1px solid var(--border-glow);
        border-radius: 10px;
        padding: 12px 10px;
    }
    [data-testid="stMetricLabel"] { color: #8fb8d9 !important; }
    [data-testid="stMetricValue"] {
        color: var(--neon-cyan) !important;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
    }

    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #10182b;
        border-radius: 8px 8px 0 0;
        color: #9fd8ff;
        font-family: 'Orbitron', sans-serif;
        font-size: 13px;
        padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0090b0, #00e5ff) !important;
        color: #04121a !important;
        font-weight: 700;
    }

    [data-testid="stExpander"] {
        background: var(--bg-panel);
        border: 1px solid #263049;
        border-radius: 10px;
    }

    hr { border-color: rgba(0, 229, 255, 0.15) !important; }

    .trasus-hero {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 16px 20px;
        border-radius: 14px;
        margin-bottom: 18px;
        background: linear-gradient(120deg, #0d1524, #131c30 60%, #10101c);
        border: 1px solid rgba(0, 229, 255, 0.3);
        box-shadow: 0 0 24px rgba(0, 229, 255, 0.12);
    }
    .trasus-hero img { max-height: 52px; border-radius: 6px; }
    .trasus-hero-text h1 {
        margin: 0;
        font-size: 26px !important;
        background: linear-gradient(90deg, #00e5ff, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: none !important;
    }
    .trasus-hero-text p {
        margin: 2px 0 0 0;
        color: #7fa8c9;
        font-size: 12.5px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    @media (max-width: 640px) {
        h1 { font-size: 20px !important; }
        h2 { font-size: 17px !important; }
        .trasus-hero { padding: 12px 14px; }
        .trasus-hero-text h1 { font-size: 20px !important; }
        .box-carrinho, .box-desconto { padding: 12px; }
        [data-testid="stMetricValue"] { font-size: 18px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# CABEÇALHO PRINCIPAL (visível mesmo com sidebar fechada no mobile)
# ==========================
_logo_path = 'logo_trasus.png'
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode('utf-8')
    _logo_html = f'<img src="data:image/png;base64,{_logo_b64}">'
else:
    _logo_html = '<div style="font-size:34px;">👕</div>'

st.markdown(f"""
<div class="trasus-hero">
    {_logo_html}
    <div class="trasus-hero-text">
        <h1>TRASUS</h1>
        <p>Sistema de Gestão de Orçamentos</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================
# NAVEGAÇÃO EM ABAS
# ==========================
aba_criar, aba_buscar, aba_os, aba_config = st.tabs(["📝 Criar / Editar Orçamento", "🔍 Buscar Histórico", "🛠️ Ordem de Serviço", "⚙️ Configurações"])

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

    with st.sidebar:
        if os.path.exists('logo_trasus.png'):
            st.image('logo_trasus.png', use_container_width=True)
        else:
            st.markdown("<h2 style='text-align: center; background: linear-gradient(90deg, #00e5ff, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>TRASUS</h2>", unsafe_allow_html=True)

        st.header("👤 Dados do Cliente")
        c_nome = st.text_input("Nome / Contato", value=st.session_state.cliente_atual["nome"])
        c_empresa = st.text_input("Empresa", value=st.session_state.cliente_atual["empresa"])
        c_telefone = st.text_input("WhatsApp (números)", value=st.session_state.cliente_atual["telefone"])
        c_email = st.text_input("E-mail", value=st.session_state.cliente_atual["email"])
        
        st.session_state.cliente_atual = {"nome": c_nome, "empresa": c_empresa, "telefone": c_telefone, "email": c_email}

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

    st.header(f"2. Resumo do Pedido ({len(st.session_state.carrinho)} itens)")
    subtotal_pedido = 0.0

    if len(st.session_state.carrinho) == 0:
        st.info("Nenhum item adicionado ao pedido ainda.")
    else:
        for i, item in enumerate(st.session_state.carrinho):
            subtotal_pedido += item["total"]
            
            col_info, col_btn = st.columns([5, 1])
            
            with col_info:
                st.markdown(f"""
                <div class="box-carrinho" style="margin-bottom: 0;">
                    <strong>Item {i+1}: {item['descricao']}</strong><br>
                    Qtd: {item['quantidade']} | V. Unitário: R$ {item['unitario']:.2f} | <strong>Subtotal: R$ {item['total']:.2f}</strong><br>
                    Grade: {item['grade']}
                </div>
                """, unsafe_allow_html=True)
                
            with col_btn:
                st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
                st.button("🗑️ Remover", key=f"btn_remover_{i}", on_click=remover_item, args=(i,), use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("---")

    st.header("2.1 Desconto e Ajuste de Valor")
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

    if desconto_tipo == "Desconto (%)":
        valor_desconto_calculado = subtotal_pedido * (desconto_valor / 100)
    elif desconto_tipo == "Desconto (R$)":
        valor_desconto_calculado = desconto_valor
    else:
        valor_desconto_calculado = 0.0

    valor_com_desconto = max(subtotal_pedido - valor_desconto_calculado, 0.0)

    st.markdown("<br>", unsafe_allow_html=True)

    ajustar_manual = st.checkbox("✏️ Ajustar valor final manualmente (sobrepõe o desconto acima)", value=st.session_state.valor_manual_ativado)

    valor_manual_input = st.session_state.valor_manual
    if ajustar_manual:
        valor_padrao_manual = st.session_state.valor_manual if st.session_state.valor_manual_ativado and st.session_state.valor_manual > 0 else valor_com_desconto
        valor_manual_input = st.number_input("Valor Final do Pedido (R$)", min_value=0.0, step=1.0, value=float(valor_padrao_manual))
        valor_final_pedido = valor_manual_input
    else:
        valor_final_pedido = valor_com_desconto

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
    
    st.header("3. Anexos e Finalização")
    imagens_upload = st.file_uploader("Anexe as imagens (Até 2 recomendadas)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if st.button("Gerar Orçamento / Atualizar", type="primary", use_container_width=True):
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

            pdf.set_font("Arial", '', 10)
            pdf.cell(145, 7, "Subtotal:", align="R")
            pdf.cell(45, 7, f"R$ {subtotal_pedido:.2f}", align="C")
            pdf.ln()

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
            
            exibir_popup_pdf(pdf_bytes, numero_orcamento, telefone_cliente=c_telefone, nome_cliente=c_nome)

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
                        if st.button("✏️ Editar este orçamento", key=f"edit_{num}", use_container_width=True):
                            st.session_state.cliente_atual = dados['cliente']
                            st.session_state.carrinho = dados['carrinho']
                            st.session_state.orcamento_editando = num
                            st.session_state.desconto_tipo = dados.get('desconto_tipo', 'Sem desconto')
                            st.session_state.desconto_valor = dados.get('desconto_valor', 0.0)
                            st.session_state.valor_manual_ativado = dados.get('valor_manual_ativado', False)
                            st.session_state.valor_manual = dados.get('valor_manual', 0.0)
                            st.success("Orçamento carregado! Volte para a aba 'Criar / Editar' no topo da tela para alterar os dados.")

                    with col_del:
                        if st.session_state.confirmar_exclusao == num:
                            st.warning("Tem certeza que deseja excluir este orçamento? Essa ação não pode ser desfeita.")
                            col_sim, col_nao = st.columns(2)
                            with col_sim:
                                if st.button("✅ Confirmar Exclusão", key=f"confirma_del_{num}", use_container_width=True):
                                    del banco[num]
                                    salvar_banco(banco)
                                    st.session_state.confirmar_exclusao = None
                                    if st.session_state.orcamento_editando == num:
                                        novo_pedido()
                                    st.success(f"Orçamento {num} excluído com sucesso!")
                                    st.rerun()
                            with col_nao:
                                if st.button("❌ Cancelar", key=f"cancela_del_{num}", use_container_width=True):
                                    st.session_state.confirmar_exclusao = None
                                    st.rerun()
                        else:
                            if st.button("🗑️ Excluir Orçamento", key=f"del_{num}", use_container_width=True):
                                st.session_state.confirmar_exclusao = num
                                st.rerun()

with aba_os:
    col_os_titulo, col_os_btn = st.columns([3, 1])
    with col_os_titulo:
        if st.session_state.os_editando:
            st.title(f"✏️ Editando OS: {st.session_state.os_editando}")
        else:
            st.title("🛠️ Nova Ordem de Serviço")
    with col_os_btn:
        st.button("🔄 Nova OS (Limpar)", on_click=nova_os, use_container_width=True, key="btn_nova_os")

    st.markdown("---")

    st.header("1. Vínculo do Pedido")
    tipo_os = st.radio(
        "Origem da OS",
        ["Vincular a Orçamento Existente", "OS Avulsa (sem orçamento)"],
        horizontal=True,
        key="tipo_os_radio"
    )

    cliente_os = {"nome": "", "empresa": "", "telefone": "", "email": ""}
    itens_os = []
    valor_total_os = 0.0
    orcamento_vinculado = None
    descricao_avulsa = ""

    if tipo_os == "Vincular a Orçamento Existente":
        if len(banco) == 0:
            st.warning("Nenhum orçamento salvo ainda. Crie um orçamento primeiro ou use a opção 'OS Avulsa'.")
        else:
            opcoes_orc = list(reversed(list(banco.keys())))
            orcamento_vinculado = st.selectbox(
                "Selecione o Orçamento",
                opcoes_orc,
                format_func=lambda n: f"{n} - {banco[n]['cliente']['nome']} ({banco[n]['cliente']['empresa']}) - R$ {banco[n]['total']:.2f}"
            )
            dados_orc = banco[orcamento_vinculado]
            cliente_os = dados_orc["cliente"]
            itens_os = dados_orc["carrinho"]
            valor_total_os = float(dados_orc["total"])

            st.markdown(f"""
            <div class="box-carrinho">
                <strong>Cliente:</strong> {cliente_os['nome']} | <strong>Empresa:</strong> {cliente_os['empresa']}<br>
                <strong>Itens:</strong> {len(itens_os)} | <strong>Valor Total:</strong> R$ {valor_total_os:.2f}
            </div>
            """, unsafe_allow_html=True)
    else:
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            os_nome = st.text_input("Nome / Contato do Cliente", key="os_avulsa_nome")
            os_telefone = st.text_input("WhatsApp (números)", key="os_avulsa_telefone")
        with col_a2:
            os_empresa = st.text_input("Empresa", key="os_avulsa_empresa")
            os_email = st.text_input("E-mail", key="os_avulsa_email")

        cliente_os = {"nome": os_nome, "empresa": os_empresa, "telefone": os_telefone, "email": os_email}
        descricao_avulsa = st.text_area("Descrição do Pedido (peças, tamanhos, tecidos, personalização)", key="os_avulsa_descricao", height=100)
        valor_total_os = st.number_input("Valor Total do Pedido (R$)", min_value=0.0, step=1.0, key="os_avulsa_valor_total")

    st.markdown("---")

    st.header("2. Pagamento")
    col_pag1, col_pag2 = st.columns(2)
    with col_pag1:
        valor_entrada_os = st.number_input("Valor de Entrada / Sinal (R$)", min_value=0.0, max_value=max(valor_total_os, 0.0) if valor_total_os > 0 else None, step=1.0, key="os_valor_entrada")
    with col_pag2:
        valor_restante_os = max(valor_total_os - valor_entrada_os, 0.0)
        st.number_input("Valor Restante (R$)", value=float(valor_restante_os), disabled=True, key="os_valor_restante_display")

    if valor_total_os <= 0:
        status_pagamento_os = "Pendente"
    elif valor_entrada_os <= 0:
        status_pagamento_os = "Pendente"
    elif valor_restante_os <= 0:
        status_pagamento_os = "Pago"
    else:
        status_pagamento_os = "Parcial"

    cor_status_pag = {"Pendente": "🔴", "Parcial": "🟡", "Pago": "🟢"}
    st.caption(f"Status do pagamento: {cor_status_pag[status_pagamento_os]} **{status_pagamento_os}**")

    st.markdown("---")

    st.header("3. Produção e Entrega")
    col_prod1, col_prod2 = st.columns(2)
    with col_prod1:
        prazo_entrega_os = st.date_input("Prazo de Entrega", key="os_prazo_entrega")
    with col_prod2:
        status_producao_os = st.selectbox("Status de Produção", ["Em Produção", "Pronto para Entrega", "Entregue"], key="os_status_producao")

    observacoes_producao_os = st.text_area("Observações de Produção (acabamento, urgência, detalhes)", key="os_observacoes")

    st.markdown("---")

    st.header("4. Fotos da Camisa")
    fotos_os_upload = st.file_uploader("Anexe fotos (mockup, arte final, referência do cliente)", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="os_fotos_upload")

    st.markdown("---")

    if st.button("💾 Salvar Ordem de Serviço", type="primary", use_container_width=True, key="btn_salvar_os"):
        if valor_total_os <= 0:
            st.error("⚠️ Informe um valor total válido para o pedido.")
        elif tipo_os == "OS Avulsa (sem orçamento)" and not cliente_os["nome"]:
            st.error("⚠️ Informe ao menos o nome do cliente.")
        else:
            if st.session_state.os_editando:
                numero_os = st.session_state.os_editando
            elif orcamento_vinculado:
                numero_os = f"OS-{orcamento_vinculado}"
            else:
                numero_os = f"OS-AV-{datetime.now().strftime('%y%m%d-%H%M%S')}"

            fotos_paths = banco_os.get(numero_os, {}).get("fotos", []) if numero_os in banco_os else []
            if fotos_os_upload:
                for idx, foto in enumerate(fotos_os_upload):
                    caminho_blob = upload_foto_os(numero_os, len(fotos_paths) + idx, foto)
                    fotos_paths.append(caminho_blob)

            banco_os[numero_os] = {
                "orcamento_vinculado": orcamento_vinculado,
                "cliente": cliente_os,
                "itens": itens_os,
                "descricao_avulsa": descricao_avulsa,
                "valor_total": valor_total_os,
                "valor_entrada": valor_entrada_os,
                "valor_restante": valor_restante_os,
                "status_pagamento": status_pagamento_os,
                "prazo_entrega": prazo_entrega_os.strftime("%d/%m/%Y"),
                "status_producao": status_producao_os,
                "observacoes": observacoes_producao_os,
                "fotos": fotos_paths,
                "data_criacao": banco_os.get(numero_os, {}).get("data_criacao", datetime.now().strftime("%d/%m/%Y %H:%M")),
                "data_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            salvar_banco_os(banco_os)
            st.session_state.os_editando = numero_os

            pdf_os = FPDF()
            pdf_os.add_page()

            if os.path.exists("background.jpg"):
                pdf_os.image("background.jpg", x=0, y=0, w=210, h=297)

            pdf_os.set_y(30)
            pdf_os.set_font("Arial", 'B', 10)
            pdf_os.cell(0, 10, f"Ordem de Serviço: {numero_os}", ln=True, align="R")

            pdf_os.set_y(85)
            pdf_os.set_font("Arial", 'B', 12)
            pdf_os.cell(0, 10, "ORDEM DE SERVIÇO", ln=True, align="C")
            pdf_os.set_font("Arial", '', 10)
            pdf_os.cell(0, 6, f"Cliente: {cliente_os['nome']} | Empresa: {cliente_os['empresa']}", ln=True)
            pdf_os.cell(0, 6, f"WhatsApp: {cliente_os['telefone']} | E-mail: {cliente_os['email']}", ln=True)
            pdf_os.ln(4)

            if itens_os:
                pdf_os.set_font("Arial", 'B', 9)
                pdf_os.cell(90, 8, " Descricao", border=1)
                pdf_os.cell(30, 8, " Qtd", border=1, align="C")
                pdf_os.cell(70, 8, " Grade", border=1, align="C")
                pdf_os.ln()
                for item in itens_os:
                    pdf_os.set_font("Arial", '', 9)
                    pdf_os.cell(90, 6, f" {item['descricao'][:40]}", border=1)
                    pdf_os.cell(30, 6, f" {item['quantidade']}", border=1, align="C")
                    pdf_os.cell(70, 6, f" {item['grade']}", border=1, align="C")
                    pdf_os.ln()
            elif descricao_avulsa:
                pdf_os.set_font("Arial", '', 10)
                pdf_os.multi_cell(0, 6, f"Descrição do pedido: {descricao_avulsa}")

            pdf_os.ln(4)
            pdf_os.set_font("Arial", '', 10)
            pdf_os.cell(0, 6, f"Valor Total: R$ {valor_total_os:.2f}", ln=True)
            pdf_os.cell(0, 6, f"Valor de Entrada: R$ {valor_entrada_os:.2f}", ln=True)
            pdf_os.cell(0, 6, f"Valor Restante: R$ {valor_restante_os:.2f}", ln=True)
            pdf_os.cell(0, 6, f"Status de Pagamento: {status_pagamento_os}", ln=True)
            pdf_os.ln(2)
            pdf_os.cell(0, 6, f"Prazo de Entrega: {prazo_entrega_os.strftime('%d/%m/%Y')}", ln=True)
            pdf_os.cell(0, 6, f"Status de Produção: {status_producao_os}", ln=True)
            if observacoes_producao_os:
                pdf_os.ln(2)
                pdf_os.multi_cell(0, 6, f"Observações: {observacoes_producao_os}")

            if fotos_paths:
                pdf_os.ln(4)
                x_pos = 20
                y_atual = pdf_os.get_y()
                for caminho_blob in fotos_paths[:2]:
                    try:
                        url_foto = url_foto_os(caminho_blob)
                        with urllib.request.urlopen(url_foto) as resp:
                            img_bytes = resp.read()
                        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                            img.save(tmp_file.name, format="JPEG")
                            pdf_os.image(tmp_file.name, x=x_pos, y=y_atual, w=70)
                        x_pos += 80
                    except Exception:
                        pass

            pdf_os_bytes = pdf_os.output(dest='S').encode('latin1')
            st.success(f"✅ Ordem de Serviço {numero_os} salva com sucesso!")
            exibir_popup_pdf(pdf_os_bytes, numero_os, telefone_cliente=cliente_os.get('telefone', ''), nome_cliente=cliente_os.get('nome', ''))

    st.markdown("---")

    st.header("📋 Histórico de Ordens de Serviço")
    termo_busca_os = st.text_input("Buscar por Cliente, Empresa ou Número da OS:", key="busca_os")

    if len(banco_os) == 0:
        st.info("Nenhuma Ordem de Serviço registrada ainda.")
    else:
        hoje = datetime.now().date()
        for num_os, dados_os in reversed(list(banco_os.items())):
            texto_busca_os = f"{num_os} {dados_os['cliente']['nome']} {dados_os['cliente']['empresa']}".lower()
            if termo_busca_os.lower() not in texto_busca_os:
                continue

            try:
                data_prazo = datetime.strptime(dados_os["prazo_entrega"], "%d/%m/%Y").date()
                dias_restantes = (data_prazo - hoje).days
            except Exception:
                dias_restantes = None

            if dados_os["status_producao"] == "Entregue":
                badge_prazo = "🟢"
            elif dias_restantes is not None and dias_restantes < 0:
                badge_prazo = "🔴 Atrasado"
            elif dias_restantes is not None and dias_restantes <= 2:
                badge_prazo = "🟡 Vence em breve"
            else:
                badge_prazo = "🔵"

            badge_pag = cor_status_pag.get(dados_os["status_pagamento"], "⚪")

            with st.expander(f"{badge_prazo} {num_os} - {dados_os['cliente']['nome']} ({dados_os['cliente']['empresa']}) | {badge_pag} {dados_os['status_pagamento']} | 📦 {dados_os['status_producao']}"):
                st.write(f"**Valor Total:** R$ {dados_os['valor_total']:.2f} | **Entrada:** R$ {dados_os['valor_entrada']:.2f} | **Restante:** R$ {dados_os['valor_restante']:.2f}")
                st.write(f"**Prazo de Entrega:** {dados_os['prazo_entrega']}")
                if dados_os.get("orcamento_vinculado"):
                    st.write(f"**Orçamento vinculado:** {dados_os['orcamento_vinculado']}")
                elif dados_os.get("descricao_avulsa"):
                    st.write(f"**Descrição:** {dados_os['descricao_avulsa']}")
                if dados_os.get("observacoes"):
                    st.write(f"**Observações:** {dados_os['observacoes']}")

                if dados_os.get("fotos"):
                    cols_fotos = st.columns(min(len(dados_os["fotos"]), 4))
                    for i, caminho_blob in enumerate(dados_os["fotos"][:4]):
                        try:
                            with cols_fotos[i % len(cols_fotos)]:
                                st.image(url_foto_os(caminho_blob), use_container_width=True)
                        except Exception:
                            pass

                col_edit_os, col_del_os = st.columns(2)
                with col_edit_os:
                    if st.button("✏️ Editar esta OS", key=f"edit_os_{num_os}", use_container_width=True):
                        st.session_state.os_editando = num_os
                        st.success("OS carregada para edição. Ajuste os campos acima e clique em 'Salvar Ordem de Serviço'.")

                with col_del_os:
                    if st.session_state.confirmar_exclusao_os == num_os:
                        st.warning("Confirma a exclusão desta OS? Essa ação não pode ser desfeita.")
                        col_sim_os, col_nao_os = st.columns(2)
                        with col_sim_os:
                            if st.button("✅ Confirmar", key=f"confirma_del_os_{num_os}", use_container_width=True):
                                for caminho_blob in dados_os.get("fotos", []):
                                    excluir_foto_os(caminho_blob)
                                del banco_os[num_os]
                                salvar_banco_os(banco_os)
                                st.session_state.confirmar_exclusao_os = None
                                if st.session_state.os_editando == num_os:
                                    nova_os()
                                st.success(f"OS {num_os} excluída com sucesso!")
                                st.rerun()
                        with col_nao_os:
                            if st.button("❌ Cancelar", key=f"cancela_del_os_{num_os}", use_container_width=True):
                                st.session_state.confirmar_exclusao_os = None
                                st.rerun()
                    else:
                        if st.button("🗑️ Excluir OS", key=f"del_os_{num_os}", use_container_width=True):
                            st.session_state.confirmar_exclusao_os = num_os
                            st.rerun()

with aba_config:
    st.title("⚙️ Configurações de Preços")
    st.caption("Edite os valores usados no cálculo dos orçamentos. As alterações ficam salvas permanentemente e valem para novos orçamentos.")

    def bloco_categoria(titulo, tabela_atual, chave_categoria, icone):
        st.markdown("---")
        st.header(f"{icone} {titulo}")

        if len(tabela_atual) == 0:
            st.info("Nenhum item cadastrado ainda.")

        novos_valores = {}
        itens_para_remover = []

        for nome, preco in tabela_atual.items():
            col_nome, col_preco, col_del = st.columns([3, 2, 1])
            with col_nome:
                st.markdown(f"<div style='padding-top:8px;'>{nome}</div>", unsafe_allow_html=True)
            with col_preco:
                novo_valor = st.number_input(
                    "Preço (R$)", min_value=0.0, step=0.5, value=float(preco),
                    key=f"preco_{chave_categoria}_{nome}", label_visibility="collapsed"
                )
                novos_valores[nome] = novo_valor
            with col_del:
                if st.button("🗑️", key=f"del_{chave_categoria}_{nome}", use_container_width=True):
                    itens_para_remover.append(nome)

        if itens_para_remover:
            for nome in itens_para_remover:
                tabela_atual.pop(nome, None)
            _modelos, _tecidos, _pers = carregar_precos()
            if chave_categoria == "modelo":
                salvar_precos(tabela_atual, _tecidos, _pers)
            elif chave_categoria == "tecido":
                salvar_precos(_modelos, tabela_atual, _pers)
            else:
                salvar_precos(_modelos, _tecidos, tabela_atual)
            st.success("Item removido!")
            st.rerun()

        if len(tabela_atual) > 0 and st.button(f"💾 Salvar Alterações em {titulo}", key=f"salvar_{chave_categoria}", use_container_width=True):
            _modelos, _tecidos, _pers = carregar_precos()
            if chave_categoria == "modelo":
                salvar_precos(novos_valores, _tecidos, _pers)
            elif chave_categoria == "tecido":
                salvar_precos(_modelos, novos_valores, _pers)
            else:
                salvar_precos(_modelos, _tecidos, novos_valores)
            st.success(f"Preços de {titulo} atualizados!")
            st.rerun()

        with st.expander(f"➕ Adicionar novo item em {titulo}"):
            col_novo_nome, col_novo_preco = st.columns([3, 2])
            with col_novo_nome:
                novo_nome = st.text_input("Nome do item", key=f"novo_nome_{chave_categoria}")
            with col_novo_preco:
                novo_preco_item = st.number_input("Preço (R$)", min_value=0.0, step=0.5, key=f"novo_preco_{chave_categoria}")
            if st.button(f"Adicionar a {titulo}", key=f"btn_add_{chave_categoria}", use_container_width=True):
                if not novo_nome.strip():
                    st.error("Informe um nome para o novo item.")
                elif novo_nome in tabela_atual:
                    st.error("Já existe um item com esse nome.")
                else:
                    _modelos, _tecidos, _pers = carregar_precos()
                    if chave_categoria == "modelo":
                        _modelos[novo_nome] = novo_preco_item
                        salvar_precos(_modelos, _tecidos, _pers)
                    elif chave_categoria == "tecido":
                        _tecidos[novo_nome] = novo_preco_item
                        salvar_precos(_modelos, _tecidos, _pers)
                    else:
                        _pers[novo_nome] = novo_preco_item
                        salvar_precos(_modelos, _tecidos, _pers)
                    st.success(f"'{novo_nome}' adicionado!")
                    st.rerun()

    bloco_categoria("Produtos (Modelos)", dict(TABELA_MODELOS), "modelo", "👕")
    bloco_categoria("Tecidos", dict(TABELA_TECIDOS), "tecido", "🧵")
    bloco_categoria("Personalizações", dict(TABELA_PERSONALIZACAO), "personalizacao", "✨")
