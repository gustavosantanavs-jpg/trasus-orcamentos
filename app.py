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

st.set_page_config(page_title="Trasus - Gestão", layout="wide")

# --- Funções ---
def carregar_banco():
    docs = db.collection('orcamentos').stream()
    return {doc.id: doc.to_dict() for doc in docs}

def salvar_orcamento(numero, dados):
    db.collection('orcamentos').document(numero).set(dados)

def excluir_orcamento(numero):
    db.collection('orcamentos').document(numero).delete()

def novo_pedido():
    st.session_state.carrinho = []
    st.session_state.cliente_atual = {"nome": "", "empresa": "", "telefone": "", "email": ""}
    st.session_state.orcamento_editando = None
    st.session_state.desconto = 0.0
    st.session_state.ajuste_manual = 0.0

def remover_item(index):
    st.session_state.carrinho.pop(index)

# --- Estado ---
if 'carrinho' not in st.session_state: novo_pedido()

# --- Interface ---
aba1, aba2 = st.tabs(["📝 Orçamento", "🔍 Histórico"])

with aba1:
    col1, col2 = st.columns([3, 1])
    with col1: st.title("👕 Orçamento Trasus")
    with col2: st.button("🔄 Novo Pedido", on_click=novo_pedido)

    with st.sidebar:
        st.header("👤 Dados do Cliente")
        st.session_state.cliente_atual["nome"] = st.text_input("Nome", value=st.session_state.cliente_atual["nome"])
        st.session_state.cliente_atual["empresa"] = st.text_input("Empresa", value=st.session_state.cliente_atual["empresa"])

    st.subheader("1. Adicionar Item")
    # Tabelas de apoio
    produtos = {"Camiseta": 35.0, "Polo": 55.0}
    
    prod = st.selectbox("Produto", list(produtos.keys()))
    qtd = st.number_input("Quantidade", min_value=1, value=1)
    
    if st.button("➕ Adicionar ao Carrinho"):
        st.session_state.carrinho.append({"desc": prod, "qtd": qtd, "total": produtos[prod] * qtd})
        st.rerun()

    st.subheader("2. Itens do Pedido")
    for i, item in enumerate(st.session_state.carrinho):
        c1, c2 = st.columns([4, 1])
        c1.write(f"{item['desc']} - Qtd: {item['qtd']} - R$ {item['total']:.2f}")
        c2.button("🗑️", key=f"del_{i}", on_click=remover_item, args=(i,))

    st.subheader("3. Negociação")
    col_d, col_a = st.columns(2)
    st.session_state.desconto = col_d.number_input("Desconto (%)", 0.0, 100.0)
    st.session_state.ajuste_manual = col_a.number_input("Ajuste (R$)", value=0.0)

    subtotal = sum(item['total'] for item in st.session_state.carrinho)
    total_final = subtotal - (subtotal * (st.session_state.desconto/100)) + st.session_state.ajuste_manual
    st.metric("Total Final", f"R$ {total_final:.2f}")

    if st.button("💾 Salvar Orçamento"):
        num = f"TRC-{datetime.now().strftime('%y%m%d%H%M')}"
        salvar_orcamento(num, {"cliente": st.session_state.cliente_atual, "carrinho": st.session_state.carrinho, "total": total_final})
        st.success("Salvo!")

with aba2:
    st.title("🔍 Histórico")
    for num, dados in carregar_banco().items():
        with st.expander(f"Orçamento {num} - R$ {dados['total']:.2f}"):
            if st.button("🗑️ Excluir", key=f"del_hist_{num}"):
                excluir_orcamento(num); st.rerun()
