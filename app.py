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

def salvar_precos(modelos, tecidos, personalizacao, percentual_gg_xg=None, golas=None):
    doc_atual = db.collection("configuracoes").document("precos").get()
    dados_atuais = doc_atual.to_dict() if doc_atual.exists else {}
    if percentual_gg_xg is None:
        percentual_gg_xg = dados_atuais.get("percentual_gg_xg", 25.0)
    if golas is None:
        golas = dados_atuais.get("golas", {"Gola Careca": 0.00, "Gola V": 1.50, "Gola Polo": 3.00})
    db.collection("configuracoes").document("precos").set({
        "modelos": modelos,
        "tecidos": tecidos,
        "personalizacao": personalizacao,
        "percentual_gg_xg": percentual_gg_xg,
        "golas": golas
    })

def carregar_precos():
    doc = db.collection("configuracoes").document("precos").get()
    if doc.exists:
        dados = doc.to_dict()
        return (
            dados.get("modelos", {}),
            dados.get("tecidos", {}),
            dados.get("personalizacao", {}),
            dados.get("percentual_gg_xg", 25.0),
            dados.get("golas", {"Gola Careca": 0.00, "Gola V": 1.50, "Gola Polo": 3.00})
        )
    else:
        modelos_padrao = {"Camiseta Básica": 35.00, "Camisa Polo": 55.00, "Camisa Social": 85.00, "Regata": 28.00, "Shorts": 25.00, "Calça Esportiva": 45.00, "Baby Look Feminina": 35.00}
        tecidos_padrao = {"Algodão 100%": 0.00, "Malha Fria (PV)": 2.50, "Dry-Fit": 5.00, "Piquet (Polo)": 8.00, "Cacharel": 3.00, "Helanca": 4.50}
        personalizacao_padrao = {"Sem Personalização": 0.00, "Silk Screen (Estampa)": 4.50, "Bordado Peito": 8.00, "Bordado Costas": 15.00, "Sublimação Total": 12.00}
        percentual_padrao = 25.0
        golas_padrao = {"Gola Careca": 0.00, "Gola V": 1.50, "Gola Polo": 3.00}
        salvar_precos(modelos_padrao, tecidos_padrao, personalizacao_padrao, percentual_padrao, golas_padrao)
        return modelos_padrao, tecidos_padrao, personalizacao_padrao, percentual_padrao, golas_padrao

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
TABELA_MODELOS, TABELA_TECIDOS, TABELA_PERSONALIZACAO, PERCENTUAL_GG_XG, TABELA_GOLAS = carregar_precos()

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
</di
