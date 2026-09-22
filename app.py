from fpdf import FPDF
from PIL import Image
from PIL import Image, ImageOps
import firebase_admin



class PDFTrasus(FPDF):
    """Reserva a área da marca e do rodapé também nas páginas seguintes."""

    def __init__(self):
        super().__init__()
        self.set_margins(10, 85, 10)
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if os.path.exists("background.jpg"):
            self.image("background.jpg", x=0, y=0, w=self.w, h=self.h)
        self.set_y(85)

    def reservar_espaco(self, altura):
        if self.get_y() + altura > self.h - self.b_margin:
            self.add_page()


def inserir_imagens_pdf(pdf, fontes, largura_max=70, altura_max=75, espaco_apos=8):
    """Encaixa até duas imagens sem recorte e posiciona o próximo texto abaixo."""
    imagens = []
    for fonte in list(fontes)[:2]:
        if hasattr(fonte, "seek"):
            fonte.seek(0)
        with Image.open(fonte) as original:
            imagem = ImageOps.exif_transpose(original).convert("RGBA")
            fundo = Image.new("RGBA", imagem.size, "white")
            fundo.alpha_composite(imagem)
            imagem = fundo.convert("RGB")
        fator = min(largura_max / imagem.width, altura_max / imagem.height)
        imagens.append((imagem, imagem.width * fator, imagem.height * fator))
    if not imagens:
        return

    altura_linha = max(altura for _, _, altura in imagens)
    pdf.reservar_espaco(altura_linha + espaco_apos)
    y = pdf.get_y()
    intervalo = 10
    largura_grupo = len(imagens) * largura_max + (len(imagens) - 1) * intervalo
    inicio = (pdf.w - largura_grupo) / 2
    # Os arquivos existem até o FPDF terminar de ler cada imagem.
    with tempfile.TemporaryDirectory(prefix="trasus_pdf_") as pasta:
        for indice, (imagem, largura, altura) in enumerate(imagens):
            caminho = os.path.join(pasta, f"imagem_{indice}.jpg")
            imagem.save(caminho, format="JPEG", quality=95)
            x = inicio + indice * (largura_max + intervalo) + (largura_max - largura) / 2
            pdf.image(caminho, x=x, y=y, w=largura, h=altura)
    pdf.set_y(y + altura_linha + espaco_apos)


def bytes_pdf(pdf):
    """Aceita tanto o retorno do PyFPDF quanto o do fpdf2."""
    resultado = pdf.output(dest="S")
    return resultado.encode("latin1") if isinstance(resultado, str) else bytes(resultado)

# Configuração inicial

            # ==========================
            pdf = FPDF()
            pdf = PDFTrasus()
            pdf.add_page()
            
            if os.path.exists("background.jpg"):
                pdf.image("background.jpg", x=0, y=0, w=210, h=297)
            

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
                inserir_imagens_pdf(pdf, imagens_upload)

            pdf.reservar_espaco(19)
            

            for item in st.session_state.carrinho:
                if pdf.get_y() + 11 > pdf.h - pdf.b_margin:
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 9)
                    for largura, titulo in [(80, " Descricao"), (20, " Qtd"), (45, " V. Unitario"), (45, " Total")]:
                        pdf.cell(largura, 8, titulo, border=1, align="C")
                    pdf.ln()
                pdf.set_font("Arial", '', 9)


            pdf.reservar_espaco(29 if not ajustar_manual and valor_desconto_calculado > 0 else 22)
            pdf.ln(3)

