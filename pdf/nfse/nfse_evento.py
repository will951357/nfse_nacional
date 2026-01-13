import xml.etree.ElementTree as ET

try:
    from pdf.nfse.de_para import cod_eventos
except ImportError:
    from de_para import cod_eventos


class NfseEvento:

    URL = "http://www.sped.fazenda.gov.br/nfse"
    def __init__(self, xml):
        self.xml = xml

        self.root = ET.fromstring(xml)

        self.eventos = cod_eventos

    def find_event(self):
        infPedReg = self.root.find(f'.//{{{self.URL}}}infPedReg')

        if infPedReg is not None:
            for cod in self.eventos.keys():
                evento_encontrado = infPedReg.find(f'.//{{{self.URL}}}{cod}')
                
                if evento_encontrado is not None:
                    desc = evento_encontrado.find(f'.//{{{self.URL}}}xDesc')

                    return self.eventos[cod]
        return None
    