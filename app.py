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

# --- Tabelas e Funções de Dados ---
TABELA_MODELOS = {"Camiseta Básica": 35.0, "Camisa Polo": 55.0, "Camisa Social": 85.0}
TABELA_TECIDOS = {"Algodão 100%": 0.0, "Dry-Fit": 5.0}
TABELA_PERSONALIZACAO = {"Sem": 0.0, "Sublimação": 12.0}

def carregar_banco():
    docs = db.collection('orcamentos').stream()
    return {doc.id: doc.to_dict() for doc in docs}

def salvar_orcamento(numero, dados):
    db.collection('orcamentos').document(numero).set(dados)

def excluir_orcamento(numero):
    db.collection('orcamentos').document(numero).delete()

# --- Estado da Sessão ---
if 'carrinho' not in st.session_state: st.session_state.carrinho = []
if 'desconto' not in st.session_state: st.session_state.desconto = 0.0
if 'ajuste' not in st.session_state: st.session_state.ajuste = 0.0
if 'cliente' not in st.session_state: st.session_state.cliente = {"nome": "", "empresa": ""}

def remover_item(index): st.session_state.carrinho.pop(index)

# --- Interface ---
aba1, aba2 = st.tabs(["📝 Criar Orçamento", "🔍 Histórico"])

with aba1:
    st.title("👕 Orçamento Trasus")
    
    # Sidebar Cliente
    with st.sidebar:
        st.session_state.cliente["nome"] = st.text_input("Nome", value=st.session_state.cliente["nome"])
        st.session_state.cliente["empresa"] = st.text_input("Empresa", value=st.session_state.cliente["empresa"])

    # Adicionar Item
    col1, col2 = st.columns(2)
    modelo = col1.selectbox("Produto", list(TABELA_MODELOS.keys()))
    tecido = col2.selectbox("Tecido", list(TABELA_TECIDOS.keys()))
    p, m, g = st.columns(3)
    qtd_p = p.number_input("P", 0)
    qtd_m = m.number_input("M", 0)
    qtd_g = g.number_input("G", 0)
    
    if st.button("➕ Adicionar ao Carrinho"):
        preco = TABELA_MODELOS[modelo] + TABELA_TECIDOS[tecido]
        total_item = (qtd_p + qtd_m + qtd_g) * preco
        st.session_state.carrinho.append({"desc": f"{modelo} ({tecido})", "qtd": qtd_p+qtd_m+qtd_g, "total": total_item})
        st.rerun()

    # Resumo
    st.subheader("Itens no Carrinho")
    for i, item in enumerate(st.session_state.carrinho):
        c1, c2 = st.columns([5, 1])
        c1.write(f"{item['desc']} - {item['qtd']} unid - R$ {item['total']:.2f}")
        c2.button("🗑️", key=f"del_{i}", on_click=remover_item, args=(i,))

    # Negociação
    col_d, col_a = st.columns(2)
    st.session_state.desconto = col_d.number_input("Desconto (%)", 0.0, 100.0)
    st.session_state.ajuste = col_a.number_input("Ajuste Manual (R$)", value=0.0)
    
    subtotal = sum(item['total'] for item in st.session_state.carrinho)
    total_final = subtotal - (subtotal * (st.session_state.desconto/100)) + st.session_state.ajuste
    st.metric("Total Final", f"R$ {total_final:.2f}")

    if st.button("💾 Salvar na Nuvem"):
        num = f"TRC-{datetime.now().strftime('%y%m%d%H%M')}"
        salvar_orcamento(num, {"cliente": st.session_state.cliente, "carrinho": st.session_state.carrinho, "total": total_final})
        st.success("Orçamento salvo com sucesso!")

with aba2:
    st.title("🔍 Histórico")
    for num, dados in carregar_banco().items():
        with st.expander(f"Orçamento {num} - Cliente: {dados['cliente']['nome']} - R$ {dados['total']:.2f}"):
            if st.button("🗑️ Excluir Orçamento", key=f"del_h_{num}"):
                excluir_orcamento(num); st.rerun()
