import base64
import os

from pdf.nfse.nfse import Nfse
from pdf.nfse.config import NfseConfig
from pdf.nfse.nfse_evento import NfseEvento

def main():
    xml = open("pdf/assets/nfse.xml", "rb").read()
    # xml_base64 = base64.b64encode(xml_base64).decode('utf-8')
    
    # Configura o logo da NFSe nacional
    logo_path = os.path.join("pdf", "assets", "Logo-Nfse.png")
    config = NfseConfig(nfse_logo=logo_path)

    nfse = Nfse(xml, config=config)

    xml_evento = open("pdf/assets/nfse_ev.xml", "rb").read()
    nfse_evento = NfseEvento(xml_evento)
    evento = nfse_evento.find_event()

    marca_dagua = ['Cancelada', 'Substituida', 'Bloqueada']
    
    if evento and evento in marca_dagua:
        nfse.draw_watermark(evento.upper())
    
    print(evento)
    
    # Salva o PDF
    nfse.output_pdf("nfse.pdf")

if __name__ == "__main__":
    main()