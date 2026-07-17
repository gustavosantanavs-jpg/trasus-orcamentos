import streamlit as st
import os, json, base64, tempfile
from datetime import datetime
from fpdf import FPDF
from PIL import Image
import firebase_admin
from firebase_admin import credentials, firestore

# --- Configuração Firebase ---
if not firebase_admin._apps:
    firebase_secrets = json.loads(st.secrets["FIREBASE_JSON"])
    cred = credentials.Certificate(firebase_secrets)
    firebase_admin.initialize_app(cred)
db = firestore.client()

st.set_page_config(page_title="Trasus - Gestão Pro", layout="wide")

# --- Tabelas de Preço ---
TABELA_MODELOS = {"Camiseta Básica": 35.0, "Camisa Polo": 55.0, "Camisa Social": 85.0}
TABELA_TECIDOS = {"Algodão 100%": 0.0, "Dry-Fit": 5.0}
TABELA_PERSONALIZACAO = {"Sem": 0.0, "Sublimação": 12.0}

# --- Funções de Banco e Lógica ---
def carregar_banco():
    docs = db.collection('orcamentos').stream()
    return {doc.id: doc.to_dict() for doc in docs}

def salvar_orcamento(numero, dados):
    db.collection('orcamentos').document(numero).set(dados)

def excluir_orcamento(numero):
    db.collection('orcamentos').document(numero).delete()

@st.dialog("📄 Pré-visualização do Orçamento", width="large")
def exibir_popup_pdf(pdf_bytes, numero):
    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    st.markdown(f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600"></iframe>', unsafe_allow_html=True)
    st.download_button("📥 Baixar PDF", pdf_bytes, f"{numero}.pdf")

# --- Estado da Sessão ---
if 'carrinho' not in st.session_state: st.session_state.carrinho = []
if 'cliente' not in st.session_state: st.session_state.cliente = {"nome": "", "empresa": ""}
if 'desconto' not in st.session_state: st.session_state.desconto = 0.0
if 'ajuste' not in st.session_state: st.session_state.ajuste = 0.0

# --- Interface ---
aba1, aba2 = st.tabs(["📝 Criar Orçamento", "🔍 Histórico"])

with aba1:
    st.title("👕 Orçamento Trasus")
    
    with st.sidebar:
        st.session_state.cliente["nome"] = st.text_input("Nome", value=st.session_state.cliente["nome"])
        st.session_state.cliente["empresa"] = st.text_input("Empresa", value=st.session_state.cliente["empresa"])

    c1, c2 = st.columns(2)
    modelo = c1.selectbox("Produto", list(TABELA_MODELOS.keys()))
    tecido = c2.selectbox("Tecido", list(TABELA_TECIDOS.keys()))
    
    p1, p2, p3 = st.columns(3)
    qtd_p = p1.number_input("P", 0)
    qtd_m = p2.number_input("M", 0)
    qtd_g = p3.number_input("G", 0)

    if st.button("➕ Adicionar Item"):
        total_item = (qtd_p + qtd_m + qtd_g) * (TABELA_MODELOS[modelo] + TABELA_TECIDOS[tecido])
        st.session_state.carrinho.append({"desc": f"{modelo} ({tecido})", "qtd": qtd_p+qtd_m+qtd_g, "total": total_item})
        st.rerun()

    st.subheader("Itens")
    for i, item in enumerate(st.session_state.carrinho):
        c_i, c_b = st.columns([5, 1])
        c_i.write(f"{item['desc']} - {item['qtd']} unidades - R$ {item['total']:.2f}")
        if c_b.button("🗑️", key=f"del_{i}"): st.session_state.carrinho.pop(i); st.rerun()

    d1, d2 = st.columns(2)
    st.session_state.desconto = d1.number_input("Desconto (%)", 0.0, 100.0)
    st.session_state.ajuste = d2.number_input("Ajuste (R$)", value=0.0)
    
    subtotal = sum(item['total'] for item in st.session_state.carrinho)
    total_final = subtotal - (subtotal * (st.session_state.desconto/100)) + st.session_state.ajuste
    st.metric("Total Final", f"R$ {total_final:.2f}")

    if st.button("💾 Salvar e Gerar PDF"):
        num = f"TRC-{datetime.now().strftime('%y%m%d%H%M')}"
        dados = {"cliente": st.session_state.cliente, "carrinho": st.session_state.carrinho, "total": total_final}
        salvar_orcamento(num, dados)
        # Lógica de PDF simplificada para teste
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Orçamento: {num} - Total: R$ {total_final:.2f}", ln=True)
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        exibir_popup_pdf(pdf_bytes, num)

with aba2:
    for num, dados in carregar_banco().items():
        with st.expander(f"{num} - {dados['cliente']['nome']} - R$ {dados['total']:.2f}"):
            if st.button("🗑️ Excluir", key=f"del_h_{num}"): excluir_orcamento(num); st.rerun()
