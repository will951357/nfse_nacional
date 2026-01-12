import base64
import os

from pdf.nfse.nfse import Nfse
from pdf.nfse.config import NfseConfig

def main():
    xml = open("pdf/assets/nfse.xml", "rb").read()
    # xml_base64 = base64.b64encode(xml_base64).decode('utf-8')
    
    # Configura o logo da NFSe nacional
    logo_path = os.path.join("pdf", "assets", "Logo-Nfse.png")
    config = NfseConfig(nfse_logo=logo_path)

    nfse = Nfse(xml, config=config)

if __name__ == "__main__":
    main()