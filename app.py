import streamlit as st
import os
import tempfile
import json
import base64
from datetime import datetime
from fpdf import FPDF
from PIL import Image
import firebase_admin
from firebase_admin import credentials, firestore

# Configuração e Conexão Firebase
if not firebase_admin._apps:
    firebase_secrets = json.loads(st.secrets["FIREBASE_JSON"])
    cred = credentials.Certificate(firebase_secrets)
    firebase_admin.initialize_app(cred)
db = firestore.client()

st.set_page_config(page_title="Trasus - Gestão Pro", layout="wide")

# --- Funções de Banco ---
def carregar_banco():
    docs = db.collection('orcamentos').stream()
    return {doc.id: doc.to_dict() for doc in docs}

def salvar_orcamento(numero, dados):
    db.collection('orcamentos').document(numero).set(dados)

def excluir_orcamento(numero):
    db.collection('orcamentos').document(numero).delete()

# --- Funções de Sessão ---
if 'carrinho' not in st.session_state: st.session_state.carrinho = []
if 'desconto' not in st.session_state: st.session_state.desconto = 0.0
if 'ajuste_manual' not in st.session_state: st.session_state.ajuste_manual = 0.0

def novo_pedido():
    st.session_state.carrinho = []
    st.session_state.cliente_atual = {"nome": "", "empresa": "", "telefone": "", "email": ""}
    st.session_state.orcamento_editando = None
    st.session_state.desconto = 0.0
    st.session_state.ajuste_manual = 0.0

# --- Estilos ---
st.markdown("""<style>
    .stApp { background-color: #1c1c1c; color: #e0e0e0; }
    .stButton>button { background-color: #4a4a4a !important; color: white !important; }
</style>""", unsafe_allow_html=True)

aba1, aba2 = st.tabs(["📝 Orçamento", "🔍 Histórico"])

with aba1:
    col1, col2 = st.columns([3, 1])
    with col1: st.title("👕 Orçamento Trasus")
    with col2: st.button("🔄 Novo", on_click=novo_pedido)
    
    # [Logica de adicionar item mantida...]
    # ... (Seu código de adicionar itens aqui) ...
    
    # --- NOVOS CAMPOS: Desconto e Ajuste ---
    st.subheader("📊 Negociação Final")
    col_a, col_b = st.columns(2)
    with col_a:
        st.session_state.desconto = st.number_input("Desconto (%)", min_value=0.0, max_value=100.0, step=1.0)
    with col_b:
        st.session_state.ajuste_manual = st.number_input("Ajuste Manual (R$)", step=1.0)
    
    # Cálculo final
    subtotal = sum(item['total'] for item in st.session_state.carrinho)
    total_final = subtotal - (subtotal * (st.session_state.desconto/100)) + st.session_state.ajuste_manual
    st.metric("Total Final", f"R$ {total_final:.2f}")

with aba2:
    st.title("🔍 Histórico")
    banco = carregar_banco()
    for num, dados in reversed(banco.items()):
        with st.expander(f"📄 {num} - {dados['cliente']['nome']} - R$ {dados.get('total_final', dados['total']):.2f}"):
            col_x, col_y = st.columns(2)
            with col_x:
                if st.button("✏️ Editar", key=f"edit_{num}"):
                    # Carregar dados para edição
                    st.session_state.carrinho = dados['carrinho']
                    st.session_state.orcamento_editando = num
                    st.rerun()
            with col_y:
                # FUNCIONALIDADE EXCLUIR
                if st.button("🗑️ Excluir", key=f"del_{num}"):
                    excluir_orcamento(num)
                    st.rerun()
