

from datetime import datetime
from fpdf.enums import StrokeCapStyle
try:
    from pdf.nfse.config import NfseConfig
except ImportError:
    from config import NfseConfig

try:
    from pdf.nfse.xpdf import xFPDF
except ImportError:
    from xpdf import xFPDF


try:
    from pdf.nfse.layout import Layout, TextElement
except ImportError:
    from layout import Layout, TextElement

try:
    from pdf.nfse.qrcode_ import Qrcode
except ImportError:
    from qrcode_ import Qrcode

try:
    from pdf.nfse.de_para import PAISES_ISO, de_para_codigo_trib_nac, de_para_reg_esp_trib, de_para_susp_issqn, de_para_tipo_imun_issqn, de_para_tp_ret_pis_cofins, de_para_trib_issqn
except ImportError:
    from de_para import PAISES_ISO, de_para_codigo_trib_nac, de_para_reg_esp_trib, de_para_susp_issqn, de_para_tipo_imun_issqn, de_para_tp_ret_pis_cofins, de_para_trib_issqn

import xml.etree.ElementTree as ET
import re

def formatar_cnpj_cpf_nif(value):
    """
    Formata o CNPJ, CPF ou NIF brasileiro. Exemplo:
    '1234567890' -> '12.345.678-90'
    '12345678901234' -> '12.345.678/9000-1234'
    Aceita uma string ou int, retorna a string formatada ou original se formato inválido.
    """
    if value is None:
        return "-"
    if isinstance(value, int):
        value = str(value)
    value = re.sub(r'\D', '', str(value))
    if len(value) == 14:
        return f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}"

    elif len(value) == 11:
        return f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}"

    return value

def formatar_cep(value):
    """
    Formata o CEP brasileiro. Exemplo:
    '88032005' -> '88032-005'
    '12345678' -> '12345-678'
    Aceita uma string ou int, retorna a string formatada ou original se formato inválido.
    """
    if value is None:
        return "-"
    if isinstance(value, int):
        value = str(value)
    value = re.sub(r'\D', '', str(value))
    if len(value) == 8:
        return f"{value[:5]}-{value[5:]}"
    return value

def formatar_telefone(value):
    """
    Formata o telefone brasileiro. Exemplo:
    '(11) 91234-5678' -> '11912345678'
    '(11) 91234-5678' -> '11912345678'
    Aceita uma string ou int, retorna a string formatada ou original se formato inválido.
    """
    if value is None:
        return "-"

    try:

        if isinstance(value, int):
            value = str(value)
        value = re.sub(r'\D', '', str(value))
        if len(value) == 11:
            return f"({value[:2]}) {value[2:7]}-{value[7:]}"
    
    except Exception as e:
        return value
    finally:
        return value

def formatar_moeda(value):
    """
    Formata o valor monetário brasileiro. Exemplo:
    '1133.33' -> 'R$ 1.133,33'
    '1234567.89' -> 'R$ 1.234.567,89'
    Aceita uma string ou número, retorna a string formatada ou "-" se valor vazio/inválido.
    """
    if value is None or value == "":
        return "-"
    
    try:
        # Converte para float (aceita tanto . quanto , como separador decimal)
        if isinstance(value, str):
            # Remove espaços e substitui vírgula por ponto para conversão
            value_float = float(value.strip().replace(',', '.'))
        else:
            value_float = float(value)
        
        # Formata no padrão brasileiro: R$ 1.234.567,89
        # Usa locale ou formatação manual
        parte_inteira = int(abs(value_float))
        parte_decimal = abs(value_float) - parte_inteira
        
        # Formata parte inteira com pontos como separador de milhares
        parte_inteira_str = f"{parte_inteira:,}".replace(',', '.')
        
        # Formata parte decimal com 2 casas e vírgula
        parte_decimal_int = int(round(parte_decimal * 100))
        parte_decimal_str = f"{parte_decimal_int:02d}"
        
        # Adiciona sinal negativo se necessário
        sinal = "-" if value_float < 0 else ""
        
        return f"R$ {sinal}{parte_inteira_str},{parte_decimal_str}"
    except (ValueError, AttributeError, TypeError):
        return value

def de_para_op_simp_nac(value): 
    if value == '1':
        return 'Não optante'
    
    elif value == '2':
        return 'Optante - Microempreendor Individual (MEI)'
    
    elif value == '3':
        return 'Optante - Micro Empresa de Pequeno Porte (ME/EPP)'

    else:
        '-'



class Nfse(xFPDF):

    URL = "http://www.sped.fazenda.gov.br/nfse"
    URL_QRCODE = 'https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave='
    
    @staticmethod
    def parse_datetime(date_string):
        """
        Faz parse de uma string de data no formato ISO 8601 ou outros formatos comuns.
        
        Args:
            date_string: String com a data (ex: '2025-12-09T10:46:04-03:00' ou '2025-12-09')
        
        Returns:
            datetime object ou None se não conseguir fazer parse
        """
        if not date_string:
            return None
        
        # Remove espaços em branco
        date_string = date_string.strip()
        
        # Tenta diferentes formatos
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 com timezone: 2025-12-09T10:46:04-03:00
            "%Y-%m-%dT%H:%M:%S",     # ISO 8601 sem timezone: 2025-12-09T10:46:04
            "%Y-%m-%d %H:%M:%S",     # Formato padrão: 2025-12-09 10:46:04
            "%Y-%m-%d",              # Apenas data: 2025-12-09
        ]
        
        for fmt in formats:
            try:
                # Se o formato tem timezone (%z), precisa tratar o sinal
                if '%z' in fmt:
                    # Remove o ':' do timezone se existir (2025-12-09T10:46:04-03:00 -> 2025-12-09T10:46:04-0300)
                    date_string_fixed = re.sub(r'([+-])(\d{2}):(\d{2})$', r'\1\2\3', date_string)
                    return datetime.strptime(date_string_fixed, fmt)
                else:
                    return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        return None

    def __init__(self, xml, config: NfseConfig = None):
        super().__init__(unit="mm", format="A4")

        config = config if config is not None else NfseConfig()

        self.set_margins(
            left=config.margins.left, top=config.margins.top, right=config.margins.right
        )

        # Salva margem inferior para uso posterior
        self.bottom_margin = config.margins.bottom

        # TODO: Verificar se isso influencia na quebra e divisão de paginas
        self.set_auto_page_break(auto=False, margin=config.margins.bottom)
        self.set_title("NFSE")

        self.logo_image = config.nfse_logo
        self.pref_logo = config.pref_logo

        self.receipt_pos = config.receipt_pos

        self.default_font = config.font_type.value
        self.price_precision = config.decimal_config.price_precision
        self.quantity_precision = config.decimal_config.quantity_precision

        self.orientation = 'P'

        root = ET.fromstring(xml)

        self.inf_nfse = root.find(f".//{{{self.URL}}}infNFSe")
        
        # Extrai a chave de acesso do atributo Id da tag infNFSe
        self.chave_acesso = self.inf_nfse.get("Id") if self.inf_nfse is not None else None
        
        # Cria a URL completa do QR code
        if self.chave_acesso:
            self.qr_code_url = self.URL_QRCODE + self.chave_acesso.split('S')[1]
        else:
            self.qr_code_url = None

        # Método auxiliar para buscar tags com namespace
        def find_tag(tag_name, parent=None):
            if parent is None:
                parent = self.inf_nfse
            if parent is None:
                return None
            # Busca recursiva dentro do parent fornecido
            return parent.find(f".//{{{self.URL}}}{tag_name}")

        def find_tag_text(tag_name, parent=None):
            elem = find_tag(tag_name, parent)
            return elem.text if elem is not None and elem.text else None

        # Captura das tags principais de infNFSe
        self.x_loc_emi = find_tag_text("xLocEmi")
        self.x_loc_prestacao = find_tag_text("xLocPrestacao")
        self.n_nfse = find_tag_text("nNFSe")
        self.c_loc_incid = find_tag_text("cLocIncid")
        self.x_loc_incid = find_tag_text("xLocIncid")
        self.x_trib_nac = find_tag_text("xTribNac")
        self.ver_aplic = find_tag_text("verAplic")
        self.amb_ger = find_tag_text("ambGer")
        self.tp_emis = find_tag_text("tpEmis")
        self.proc_emi = find_tag_text("procEmi")
        self.c_stat = find_tag_text("cStat")
        self.dh_proc = find_tag_text("dhProc")
        self.n_dfse = find_tag_text("nDFSe")

        # Captura dos dados do emitente
        emit = find_tag("emit")
        if emit is not None:
            self.emit_cnpj = find_tag_text("CNPJ", emit)
            self.emit_x_nome = find_tag_text("xNome", emit)
            self.emit_fone = find_tag_text("fone", emit)
            self.emit_email = find_tag_text("email", emit)
            self.emit_im = find_tag_text("IM", emit)

            # Endereço do emitente
            ender_nac = find_tag("enderNac", emit)
            if ender_nac is not None:
                self.emit_x_lgr = find_tag_text("xLgr", ender_nac)
                self.emit_nro = find_tag_text("nro", ender_nac)
                self.emit_x_bairro = find_tag_text("xBairro", ender_nac)
                self.emit_c_mun = find_tag_text("cMun", ender_nac)
                self.emit_uf = find_tag_text("UF", ender_nac)
                self.emit_cep = find_tag_text("CEP", ender_nac)

        # Captura dos valores
        valores = find_tag("valores")
        if valores is not None:
            self.v_bc = find_tag_text("vBC", valores)
            self.p_aliq_aplic = find_tag_text("pAliqAplic", valores)
            self.v_issqn = find_tag_text("vISSQN", valores)
            self.v_total_ret = find_tag_text("vTotalRet", valores)
            self.v_liq = find_tag_text("vLiq", valores)
            self.v_calc_dr= find_tag_text("vCalcDR", valores)
            self.v_bm = find_tag_text("vCalcBM", valores)


        # Captura dos dados do DPS
        dps = root.find(f".//{{{self.URL}}}DPS")
        if dps is not None:
            inf_dps = dps.find(f".//{{{self.URL}}}infDPS")

            if inf_dps is not None:
                self.dps_tp_amb = find_tag_text("tpAmb", inf_dps)
                self.dps_dh_emi = find_tag_text("dhEmi", inf_dps)
                self.dps_ver_aplic = find_tag_text("verAplic", inf_dps)
                self.dps_serie = find_tag_text("serie", inf_dps)
                self.dps_n_dps = find_tag_text("nDPS", inf_dps)
                self.dps_d_compet = find_tag_text("dCompet", inf_dps)
                self.dps_tp_emit = find_tag_text("tpEmit", inf_dps)
                self.dps_c_loc_emi = find_tag_text("cLocEmi", inf_dps)

                # Prestador
                prest = find_tag("prest", inf_dps)
                if prest is not None:
                    self.prest_cnpj = find_tag_text("CNPJ", prest)
                    self.prest_fone = find_tag_text("fone", prest)
                    self.prest_email = find_tag_text("email", prest)

                    reg_trib = find_tag("regTrib", prest)
                    if reg_trib is not None:
                        self.prest_op_simp_nac = find_tag_text(
                            "opSimpNac", reg_trib)
                        self.prest_reg_esp_trib = find_tag_text(
                            "regEspTrib", reg_trib)

                # Tomador
                toma = find_tag("toma", inf_dps)
                if toma is not None:
                    self.toma_cnpj = find_tag_text("CNPJ", toma)
                    self.toma_x_nome = find_tag_text("xNome", toma)
                    self.toma_email = find_tag_text("email", toma)
                    self.toma_fone = find_tag_text("fone", toma)
                    self.toma_im = find_tag_text("IM", toma)

                    end = find_tag("end", toma)
                    if end is not None:
                        end_nac = find_tag("endNac", end)
                        if end_nac is not None:
                            self.toma_c_mun = find_tag_text("cMun", end_nac)
                            self.toma_cep = find_tag_text("CEP", end_nac)
                        self.toma_x_lgr = find_tag_text("xLgr", end)
                        self.toma_nro = find_tag_text("nro", end)
                        self.toma_x_cpl = find_tag_text("xCpl", end)
                        self.toma_x_bairro = find_tag_text("xBairro", end)

                # Intermediario
                interm = find_tag("interm", inf_dps)
                if interm is not None:
                    self.interm_cnpj = find_tag_text("CNPJ", interm)
                    self.interm_cpf = find_tag_text("CPF", interm)
                    self.interm_nif = find_tag_text("NIF", interm)
                    self.interm_x_n_nif = find_tag_text("cNaoNIF", interm)
                    self.interm_caep = find_tag_text("CAEPF", interm)
                    self.interm_im = find_tag_text("IM", interm)
                    self.interm_nome = find_tag_text("xNome", interm)

                    end = find_tag("end", interm)

                    if end is not None:
                        end_nac = find_tag("endNac", end)

                        if end_nac is not None:
                            self.interm_c_mun = find_tag_text("cMun", end_nac)
                            self.interm_cep = find_tag_text("CEP", end_nac)
                        
                        end_ext = find_tag("endExt", end)
                        if end_ext is not None:
                            self.interm_c_pais = find_tag_text("cPais", end_ext)
                            self.interm__end_post = find_tag_text("cEndPost", end_ext)
                            self.interm_x_cidade = find_tag_text("xCidade", end_ext)
                            self.interm_est_prov = find_tag_text("xEstProvReg", end_ext)

                        self.interm_x_lgr = find_tag_text("xLgr", end)
                        self.interm_nro = find_tag_text("nro", end)
                        self.interm_x_cpl = find_tag_text("xCpl", end)
                        self.interm_x_bairro = find_tag_text("xBairro", end)

                        self.interm_fone = find_tag_text("fone", end)
                        self.interm_email = find_tag_text("email", end)

                    end = find_tag("end", interm)
                    if end is not None:
                        end_nac = find_tag("endNac", end)

                # Serviço
                serv = find_tag("serv", inf_dps)
                if serv is not None:
                    loc_prest = find_tag("locPrest", serv)
                    if loc_prest is not None:
                        self.serv_c_loc_prestacao = find_tag_text(
                            "cLocPrestacao", loc_prest)

                        self.serv_c_pais_prestacao = find_tag_text(
                            "cPaisPrestacao", loc_prest)

                    c_serv = find_tag("cServ", serv)
                    if c_serv is not None:
                        self.serv_c_trib_nac = find_tag_text(
                            "cTribNac", c_serv)

                        self.serv_c_trib_mun = find_tag_text(
                            "cTribMun", c_serv)

                        self.serv_x_desc_serv = find_tag_text(
                            "xDescServ", c_serv)

                    info_compl = find_tag("infoCompl", serv)
                    if info_compl is not None:
                        self.serv_x_inf_comp = find_tag_text(
                            "xInfComp", info_compl)

                # Valores do DPS
                valores_dps = find_tag("valores", inf_dps)
                if valores_dps is not None:
                    v_serv_prest = find_tag("vServPrest", valores_dps)
                    if v_serv_prest is not None:
                        self.dps_v_serv = find_tag_text("vServ", v_serv_prest)

                    v_desc_inc = find_tag('vDescCondIncond', valores_dps)
                    if v_desc_inc is not None:
                        self.trib_v_desc_incond = find_tag_text("vDescIcond", v_desc_inc)
                        self.trib_v_desc_cond = find_tag_text("vDescCond", v_desc_inc)

                    # Tributos
                    trib = find_tag("trib", valores_dps)
                    if trib is not None:
                        # Tributos Municipais
                        trib_mun = find_tag("tribMun", trib)
                        if trib_mun is not None:
                            self.trib_trib_issqn = find_tag_text(
                                "tribISSQN", trib_mun)
                            self.trib_tp_ret_issqn = find_tag_text(
                                "tpRetISSQN", trib_mun)

                            self.trib_pais_result = find_tag_text(
                                "cPaisResult", trib_mun)

                            self.trib_tp_imun = find_tag_text(
                                "tpImunidade", trib_mun)

                            self.trib_p_aliq = find_tag_text("pAliq", trib_mun)

                            bm = find_tag("BM", trib_mun)
                            if bm is not None:
                                self.trib_v_bc_bm = find_tag_text(
                                    "nBM", bm)
                                self.trib_red_bc_bm = find_tag_text("vRedBCBM", bm)

                            susp = find_tag("exigSusp", trib_mun)
                            if susp is not None:
                                self.trib_tp_susp = find_tag_text("tpSusp", susp)
                                self.trib_num_proc_susp = find_tag_text("nProcesso", susp)

                        # Tributos Federais
                        trib_fed = find_tag("tribFed", trib)
                        if trib_fed is not None:
                            piscofins = find_tag("piscofins", trib_fed)
                            if piscofins is not None:
                                self.trib_cst = find_tag_text("CST", piscofins)
                                self.trib_v_bc_pis_cofins = find_tag_text(
                                    "vBCPisCofins", piscofins)
                                self.trib_p_aliq_pis = find_tag_text(
                                    "pAliqPis", piscofins)
                                self.trib_p_aliq_cofins = find_tag_text(
                                    "pAliqCofins", piscofins)
                                self.trib_v_pis = find_tag_text(
                                    "vPis", piscofins)
                                self.trib_v_cofins = find_tag_text(
                                    "vCofins", piscofins)
                                self.trib_tp_ret_pis_cofins = find_tag_text(
                                    "tpRetPisCofins", piscofins)

                            self.trib_v_ret_irrf = find_tag_text(
                                "vRetIRRF", trib_fed)

                            self.trib_v_ret_cp = find_tag_text(
                                "vRetCP", trib_fed)
                            self.trib_v_ret_csll = find_tag_text(
                                "vRetCSLL", trib_fed)

                        # Total de Tributos
                        tot_trib = find_tag("totTrib", trib)
                        if tot_trib is not None:
                            v_tot_trib = find_tag("vTotTrib", tot_trib)
                            if v_tot_trib is not None:
                                self.trib_v_tot_trib_fed = find_tag_text(
                                    "vTotTribFed", v_tot_trib)
                                self.trib_v_tot_trib_est = find_tag_text(
                                    "vTotTribEst", v_tot_trib)
                                self.trib_v_tot_trib_mun = find_tag_text(
                                    "vTotTribMun", v_tot_trib)

        self.add_page(orientation=self.orientation)

        # Inicializa o layout com as dimensões da página

        self.layout = Layout(
            left_margin=self.l_margin,
            top_margin=self.t_margin,
            effective_page_width=self.epw,
            exclude_sections=self._exclude_sections()
        )

        self._draw_borders()

        self._draw_header()

        self._draw_horizontal_line("info_nota")

        self._draw_info_note()

        self._draw_horizontal_line("emitente")

        self._draw_emitente()

        self._draw_horizontal_line("tomador")

        self._draw_tomador()

        self._draw_horizontal_line("intermediario")

        self._draw_intermediario()

        self._draw_horizontal_line("servico")

        self._draw_servico()

        self._draw_horizontal_line("tb_municipal")

        self._draw_trib_municipal()

        self._draw_horizontal_line('trib_federal')

        self._draw_trib_federal()

        self._draw_horizontal_line("valor_nfse")

        self._draw_valor_nfse()

        self._draw_horizontal_line("totais")

        self._draw_totais()

        self._draw_horizontal_line("info_complementar")

        self._draw_info_complementar()

        # Não salva automaticamente - deve ser chamado explicitamente via output_pdf()
        # self.output_pdf("nfse.pdf")


    def _exclude_sections(self):
        '''
        Verifica entre as seções de Tomador e Intermediário se existe seção opcional.
        '''
        list = []
        if getattr(self, 'interm_cnpj', None) is None:
            list.append("intermediario")

        if getattr(self, 'toma_cnpj', None) is None:
            list.append("tomador")
        
        return list

        
    def _draw_borders(self):
        """
        Desenha a borda principal do documento (Borda-Pagina) baseado no SVG.
        Usa as dimensões efetivas do PDF para garantir que a borda caiba na página.
        """
        x_margin = self.l_margin
        y_start = self.t_margin

        # BORDA PRINCIPAL DA PÁGINA (Borda-Pagina do SVG)
        # Usa a largura efetiva do PDF (já considera as margens)
        border_width = self.epw

        # Calcula altura efetiva: altura da página menos margens superior e inferior
        # self.h = altura total da página em mm (A4 = 297mm)
        # self.t_margin = margem superior
        # self.bottom_margin = margem inferior (salva no __init__)
        border_height = self.h - self.t_margin - self.bottom_margin

        # Define a espessura da linha da borda (0.3mm para deixar mais visível)
        self.set_line_width(0.3)

        # Desenha retângulo da borda principal (começa na margem)
        self.rect(
            x=x_margin,
            y=y_start,
            w=border_width,
            h=border_height
        )

        # Restaura a espessura padrão da linha (0.2mm)
        self.set_line_width(0.2)

    def _draw_header(self):
        """
        Desenha o módulo do header baseado no SVG (id="header").
        Adiciona o logo da NFSe nacional e os textos centralizados.
        As bordas serão adicionadas em outra função.
        """
        # Obtém o elemento do logo do layout
        logo_element = self.layout.get_header_logo()

        # Adiciona o logo da NFSe se disponível
        # Tenta usar o logo do config, senão tenta o caminho padrão
        logo_path = self.logo_image
        if not logo_path:
            # Tenta usar o logo padrão se não estiver configurado
            import os
            default_logo = os.path.join("pdf", "assets", "Logo-Nfse.png")
            if os.path.exists(default_logo):
                logo_path = default_logo

        if logo_path and logo_element.width and logo_element.height:
            try:
                self.image(
                    name=logo_path,
                    x=logo_element.x,
                    y=logo_element.y,
                    w=logo_element.width,
                    h=logo_element.height
                )
            except Exception as e:
                # Se não conseguir carregar a imagem, apenas deixa o espaço
                # Em produção, pode ser útil logar o erro
                print(f"Erro ao carregar logo: {e}")
                pass

        # Obtém os elementos de texto do layout
        text1_element = self.layout.get_header_text1()
        text2_element = self.layout.get_header_text2()

        # Desenha o primeiro texto ("DANFSe v1.0")
        self.set_font(self.default_font, text1_element.font_style,
                      text1_element.font_size)
        self.set_xy(text1_element.x, text1_element.y)
        self.cell(
            w=text1_element.width,
            h=text1_element.height,
            txt=text1_element.value,
            border=0,
            align="C"
        )

        # Desenha o segundo texto ("Documento Auxiliar da NFS-e")
        self.set_font(self.default_font, text2_element.font_style,
                      text2_element.font_size)
        self.set_xy(text2_element.x, text2_element.y)
        self.cell(
            w=text2_element.width,
            h=text2_element.height,
            txt=text2_element.value,
            border=0,
            align="C"
        )
        
        # Desenha o texto da prefeitura (lado direito)
        if self.x_loc_emi:
            prefeitura_element = self.layout.get_header_prefeitura(self.x_loc_emi)
            self.set_font(self.default_font, prefeitura_element.font_style,
                          prefeitura_element.font_size)
            
            # Calcula a largura máxima disponível (da posição X até a margem direita)
            # Margem direita = margem esquerda + largura efetiva
            margin_right = 5.0  # Margem da borda direita em mm
            max_width = (self.l_margin + self.epw) - prefeitura_element.x - margin_right
            
            # Garante que a largura seja positiva
            if max_width > 0:
                # Usa multi_cell para permitir quebra de linha automática
                # O texto será quebrado automaticamente se exceder a largura máxima
                self.set_xy(prefeitura_element.x, prefeitura_element.y)
                self.multi_cell(
                    w=max_width,
                    h=prefeitura_element.height,
                    txt=prefeitura_element.value,
                    border=0,
                    align="R"  # Alinhado à direita
                )

    def _draw_horizontal_line(self, line_name: str):
        """
        Desenha uma linha horizontal baseada no nome da linha.

        Args:
            line_name: Nome da linha (ex: "totais", "valor_nfse", "info_nota", etc.)
        """
        try:
            # Obtém o elemento de linha do layout
            line_element = self.layout.get_horizontal_line(line_name)

            # Desenha a linha horizontal
            # FPDF usa: line(x1, y1, x2, y2)
            self.line(line_element.x, line_element.y,
                      line_element.x2, line_element.y2)
        except ValueError as e:
            print(f"Aviso: {e}")

    def _draw_info_note(self):
        """
        Desenha a seção Info-Nota com QR Code e informações da nota.
        """
        # QR Code
        qr_element = self.layout.get_info_note_qr_code()
        if qr_element.width and qr_element.height and self.qr_code_url:
            try:
                target_size_px = int(qr_element.width * 3.779527559)
                box_size = max(3, int(target_size_px / 25))
                x_offset = qr_element.x - self.l_margin
                y_offset = qr_element.y - self.t_margin
                
                qr_code_instance = Qrcode(
                    qr_code_data=self.qr_code_url,
                    y_margin_ret=self.l_margin,
                    x_offset=x_offset,
                    y_offset=y_offset,
                    box_size=box_size,
                    border=1
                )
                
                import qrcode
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=qr_code_instance.box_size,
                    border=qr_code_instance.border,
                )
                qr.add_data(qr_code_instance.qr_code_data)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                from PIL import Image
                target_width_px = int(qr_element.width * 3.779527559)
                target_height_px = int(qr_element.height * 3.779527559)
                qr_img_resized = qr_img.resize((target_width_px, target_height_px), Image.Resampling.LANCZOS)
                
                num_x = qr_code_instance.y_margin_ret + qr_code_instance.x_offset
                num_y = self.t_margin + qr_code_instance.y_offset
                
                self.image(
                    name=qr_img_resized,
                    x=num_x,
                    y=num_y,
                    w=qr_element.width,
                    h=qr_element.height
                )
                
            except Exception as e:
                print(f"Erro ao gerar QR code: {e}")
                import traceback
                traceback.print_exc()

    
        self._draw_cell(self.layout.get_info_note_chave_label(), "Chave de Acesso da NFS-e")
        self._draw_cell(self.layout.get_info_note_chave_value(value=self.chave_acesso))

        self._draw_cell(self.layout.get_info_note_numero_label(), "Número da NFS-e")
        self._draw_cell(self.layout.get_info_note_numero_value(value=self.n_nfse))

        comp_data = self.parse_datetime(self.dps_d_compet)
        comp_format = comp_data.strftime("%d/%m/%Y") if comp_data else "-"
        self._draw_cell(self.layout.get_info_note_competencia_label(), "Competência da NFS-e")
        self._draw_cell(self.layout.get_info_note_competencia_value(value=comp_format))

        data_emiss = self.parse_datetime(self.dh_proc)
        data_emiss_format = data_emiss.strftime("%d/%m/%Y %H:%M:%S") if data_emiss else ""
        self._draw_cell(self.layout.get_info_note_data_label(), "Data e Hora da emissão da NFS-e")
        self._draw_cell(self.layout.get_info_note_data_value(value=data_emiss_format))


        self._draw_cell(self.layout.get_info_note_number_dps_label(), "Número da DPS")
        self._draw_cell(self.layout.get_info_note_number_dps_value(value=self.dps_n_dps))

        self._draw_cell(self.layout.get_info_note_serie_dps_label(), "Série da DPS")
        self._draw_cell(self.layout.get_info_note_serie_dps_value(value=self.dps_serie))

        data_dps = self.parse_datetime(self.dps_dh_emi)
        data_dps_format = data_dps.strftime("%d/%m/%Y %H:%M:%S") if data_dps else "-"
        self._draw_cell(self.layout.get_info_note_date_dps_label(), "Data e Hora da emissão da DPS")
        self._draw_cell(self.layout.get_info_note_date_dps_value(value=data_dps_format))

        # Texto de autenticidade do QR code
        qr_label_element = self.layout.get_info_note_qr_label()
        # O elemento já tem o texto definido, mas podemos sobrescrever se necessário
        self._draw_multi_cell(qr_label_element)

    def _draw_emitente(self):
        """
        Desenha a seção Emitente com os dados do emitente.
        """
        self._draw_cell(self.layout.get_emitente_title(), "EMITENTE DA NFS-e")

        self._draw_cell(self.layout.get_emitente_subtitle(), "Prestador do Serviço")

        self._draw_cell(self.layout.get_emitente_cnpj_label(), "CNPJ / CPF / NIF")
        self._draw_cell(self.layout.get_emitente_cnpj_value(value=formatar_cnpj_cpf_nif(self.emit_cnpj) if self.emit_cnpj else "-"))

        self._draw_cell(self.layout.get_emitente_insc_municipal_label(), "Inscrição Municipal")
        self._draw_cell(self.layout.get_emitente_insc_municipal_value(value=self.emit_im if self.emit_im else ""))

        self._draw_cell(self.layout.get_emitente_telefone_label(), "Telefone")
        self._draw_cell(self.layout.get_emitente_telefone_value(value=formatar_telefone(self.emit_fone) if self.emit_fone else ""))

        self._draw_cell(self.layout.get_emitente_nome_label(), "Nome / Nome Empresarial")
        self._draw_cell(self.layout.get_emitente_nome_value(value=self.emit_x_nome if self.emit_x_nome else ""))

        self._draw_cell(self.layout.get_emitente_email_label(), "Email")
        self._draw_cell(self.layout.get_emitente_email_value(value=self.emit_email if self.emit_email else ""))

        endereco = f"{self.emit_x_lgr}, {self.emit_nro} {self.emit_x_bairro}"
        self._draw_cell(self.layout.get_emitente_endereco_label(), "Endereço")
        self._draw_cell(self.layout.get_emitente_endereco_value(value=endereco if endereco else ""))

        import requests
        cod_mun = self.emit_c_mun if self.emit_c_mun else ""
        response = requests.get(f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{cod_mun}")
        
        if response.status_code == 200:
            data = response.json()
            municipio = data["nome"]
        else:
            municipio = ""

        municipio_uf = f"{municipio} - {self.emit_uf}"
        self._draw_cell(self.layout.get_emitente_municipio_label(), "Município")
        self._draw_cell(self.layout.get_emitente_municipio_value(municipio_uf), "Florianópolis - SC")


        self._draw_cell(self.layout.get_emitente_cep_label(), "CEP")
        self._draw_cell(self.layout.get_emitente_cep_value(value=formatar_cep(self.emit_cep) if self.emit_cep else ""))


        op_simp_nac = self.prest_op_simp_nac if self.prest_op_simp_nac else ""
        op_simp_nac_desc = de_para_op_simp_nac(op_simp_nac)
        self._draw_cell(self.layout.get_emitente_sn_label(), "Simples Nacional na Data de Competência")
        self._draw_cell(self.layout.get_emitente_sn_value(value=op_simp_nac_desc))

        regime = self.prest_reg_esp_trib if self.prest_reg_esp_trib else ""
        regime_desc = de_para_reg_esp_trib(regime)
        self._draw_cell(self.layout.get_emitente_sn_apuracao_label(), "Regime de Apuração Tributária pelo SN")
        self._draw_cell(self.layout.get_emitente_sn_apuracao_value(value=regime_desc))

    def _draw_tomador(self):
        """
        Desenha a seção Tomador com os dados do tomador.
        """

        if 'tomador' in self._exclude_sections():
            self._draw_cell(self.layout.dados_tomador_null(), "TOMADOR DO SERVIÇO NÃO IDENTIFICADO NA NFS-e")
            return

        self._draw_cell(self.layout.get_tomador_title(), "TOMADOR DO SERVIÇO")

        self._draw_cell(self.layout.get_tomador_cnpj_label(), "CNPJ / CPF / NIF")
        self._draw_cell(self.layout.get_tomador_cnpj_value(value=formatar_cnpj_cpf_nif(self.toma_cnpj) if self.toma_cnpj else "-"))

        self._draw_cell(self.layout.get_tomador_im_label(), "Inscrição Municipal")
        self._draw_cell(self.layout.get_tomador_im_value(self.toma_im if self.toma_im else ""), "1234567890")

        self._draw_cell(self.layout.get_tomador_telefone_label(), "Telefone")
        self._draw_cell(self.layout.get_tomador_telefone_value(value=formatar_telefone(self.toma_fone) if self.toma_fone else ""))

        self._draw_cell(self.layout.get_tomador_nome_label(), "Nome / Nome Empresarial")
        self._draw_multi_cell( self.layout.get_tomador_nome_value(value=self.toma_x_nome if self.toma_x_nome else ""))

        self._draw_cell(self.layout.get_tomador_email_label(), "Email")
        self._draw_multi_cell(self.layout.get_tomador_email_value(value=self.toma_email if self.toma_email else ""))

        try:
            endereco = f"{self.toma_x_lgr}, {self.toma_nro} {self.toma_x_bairro}"
        except Exception as e:
            endereco = ""
        
        import textwrap
        endereco_linhas = textwrap.wrap(endereco, width=75, break_long_words=False) if endereco and len(endereco) > 75 else ([endereco] if endereco else [])
        len_endereco_linhas = len(endereco_linhas)
        
        endereco_element = self.layout.get_tomador_endereco_value()
        line_height = endereco_element.line_height if endereco_element.line_height is not None else endereco_element.height

        if len_endereco_linhas > 1:
            add_height = (len_endereco_linhas - 1) * line_height
        else:
            add_height = 0

        self.layout.position_manager._recalculate_positions({
            "tomador": add_height
        })

        endereco_formatado = "\n".join(endereco_linhas) if endereco_linhas else ""
        self._draw_cell(self.layout.get_tomador_endereco_label(), "Endereço")
        self._draw_multi_cell(self.layout.get_tomador_endereco_value(value=endereco_formatado))

        import requests
        cod_mun = self.toma_c_mun if self.toma_c_mun else ""
        response = requests.get(f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{cod_mun}")
        
        if response.status_code == 200:
            data = response.json()
            municipio = data["nome"]
            uf = data['microrregiao']['mesorregiao']['UF']['sigla']
        else:
            municipio = ""
            uf = ""

        municipio_uf = f"{municipio} - {uf}"
        self._draw_cell(self.layout.get_tomador_municipio_label(), "Município")
        self._draw_cell(self.layout.get_tomador_municipio_value(value=municipio_uf if municipio_uf else ""))

        self._draw_cell(self.layout.get_tomador_cep_label(), "CEP")
        self._draw_cell(self.layout.get_tomador_cep_value(value=formatar_cep(self.toma_cep) if self.toma_cep else ""))

    def _draw_intermediario(self):
        """
        Desenha a seção Intermediário com os dados do intermediário.
        """

        if 'intermediario' in self._exclude_sections():
            self._draw_cell(self.layout.get_intermediario_null_label())
            return

        self._draw_cell(self.layout.get_intermediario_title())

        doc = '-'

        cnpj = getattr(self, 'interm_cnpj', None)
        cpf = getattr(self, 'interm_cpf', None)
        nif = getattr(self, 'interm_nif', None)

        # Verificar o primeiro campo não nulo
        list = [cnpj, cpf, nif]
        for item in list:
            if item is not None:
                doc = item
                break

        doc = formatar_cnpj_cpf_nif(doc)

        self._draw_cell(self.layout.get_intermediario_cnpj_label())
        self._draw_cell(self.layout.get_intermediario_cnpj_value(value=doc))

        im = getattr(self, 'interm_im', '-')
        self._draw_cell(self.layout.get_intermediario_insc_mun_label())
        self._draw_cell(self.layout.get_intermediario_insc_mun_value(value=im))

        fone = getattr(self, 'interm_fone', '-')
        self._draw_cell(self.layout.get_intermediario_telefone_label())
        self._draw_cell(self.layout.get_intermediario_telefone_value(value=formatar_telefone(fone)))

        nome = getattr(self, 'interm_nome', '-')
        self._draw_cell(self.layout.get_intermediario_nome_label())
        self._draw_cell(self.layout.get_intermediario_nome_value(value=nome))

        email = getattr(self, 'interm_email', '-')
        self._draw_cell(self.layout.get_intermediario_email_label())
        self._draw_cell(self.layout.get_intermediario_email_value(value=email))

        endereco = getattr(self, 'interm_x_lgr', '-')
        log = getattr(self, 'interm_x_lgr', '-')
        nro = getattr(self, 'interm_nro', '-')
        comp = getattr(self, 'interm_x_cpl', '-')
        bairro = getattr(self, 'interm_x_bairro', '-')

        endereco = f"{log}, {nro}, {comp}, {bairro}"
        
        import textwrap
        endereco_linhas = textwrap.wrap(endereco, width=75, break_long_words=True) if len(endereco) > 75 else [endereco]
        len_endereco_linhas = len(endereco_linhas)
        
        endereco_element = self.layout.get_intermediario_endereco_value()
        line_height = endereco_element.line_height if endereco_element.line_height is not None else endereco_element.height
        
        if len_endereco_linhas > 1:
            add_height = (len_endereco_linhas - 1) * line_height
        else:
            add_height = 0

        self.layout.position_manager._recalculate_positions({
            "intermediario": add_height
        })

        endereco_formatado = "\n".join(endereco_linhas)
        self._draw_cell(self.layout.get_intermediario_endereco_label())
        self._draw_multi_cell(self.layout.get_intermediario_endereco_value(value=endereco_formatado))

        cod_mun = getattr(self, 'interm_c_mun', '-')
        municipio = ""
        uf = ""

        if cod_mun != '-':
            import requests

            response = requests.get(f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{cod_mun}")
            if response.status_code == 200:
                data = response.json()
                municipio = data["nome"]
                uf = data['microrregiao']['mesorregiao']['UF']['sigla']
            else:
                municipio = ""
                uf = ""

        municipio_uf = f"{municipio} - {uf}"
        self._draw_cell(self.layout.get_intermediario_municipio_label())
        self._draw_cell(self.layout.get_intermediario_municipio_value(value=municipio_uf))

        cep = getattr(self, 'interm_cep', '-')
        self._draw_cell(self.layout.get_intermediario_cep_label())
        self._draw_cell(self.layout.get_intermediario_cep_value(value=formatar_cep(cep)))

    def _draw_servico(self):
        """
        Desenha a seção Serviço com os dados do serviço.
        """
        self._draw_cell(self.layout.get_servico_title())

        cod_serv = self.serv_c_trib_nac if self.serv_c_trib_nac else ""
        cod_serv_desc = de_para_codigo_trib_nac(cod_serv, formatar=True, max_chars=72) if cod_serv else ""

        self._draw_cell(self.layout.get_servico_cod_trib_nac_label())
        self._draw_multi_cell(self.layout.get_servico_cod_trib_nac_value(value=cod_serv_desc))

        self._draw_cell(self.layout.get_servico_cod_trib_mun_label())
        self._draw_multi_cell(self.layout.get_servico_cod_trib_mun_value('-'))

        local_prest = self.serv_c_loc_prestacao if self.serv_c_loc_prestacao else ""

        import requests
        response = requests.get(f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{local_prest}")
        
        if response.status_code == 200:
            data = response.json()
            municipio = data["nome"]
            uf = data['microrregiao']['mesorregiao']['UF']['sigla']
        else:
            municipio = ""
            uf = ""

        municipio_uf = f"{municipio} - {uf}"
        self._draw_cell(self.layout.get_servico_local_label())
        self._draw_cell(self.layout.get_servico_local_value(value=municipio_uf if municipio_uf else ""))

        pais_prest = self.serv_c_pais_prestacao if self.serv_c_pais_prestacao else ""
        pais_prest = PAISES_ISO.get(pais_prest, '')
        self._draw_cell(self.layout.get_servico_pais_label())
        self._draw_cell(self.layout.get_servico_pais_value(pais_prest), value=pais_prest)

        desc_list = self.serv_x_desc_serv.split('\n')[:6]
        len_desc_list = len(desc_list)

        # Obtém o elemento para pegar o line_height correto
        desc_element = self.layout.get_servico_desc_value()
        # line_height padrão é 4mm (do height do elemento)
        line_height = desc_element.line_height if desc_element.line_height is not None else desc_element.height
        
        # Calcula altura adicional: considera apenas linhas além da primeira
        # (a primeira linha já está no espaço base da seção)
        if len_desc_list > 1:
            # Altura adicional = (número de linhas - 1) * line_height
            primeiro_elemento = desc_list[0].strip()
            resto_dos_elementos = [desc.strip() for desc in desc_list[1:] if desc]
            
            # juntar o resto dos elementos
            texto_resto = " ".join(resto_dos_elementos)

            import textwrap

            lista_linhas = textwrap.wrap(texto_resto, width=160 , break_long_words=False) if texto_resto and len(texto_resto) > 160 else ([texto_resto] if texto_resto else [])
            
            lista_final = [primeiro_elemento] + lista_linhas

            add_height = (len(lista_final) - 1) * line_height


        else:
            lista_final = desc_list
            add_height = 0

        self.layout.position_manager._recalculate_positions({
            "servico": add_height
        })

        desc_serv = "\n".join([desc.strip() for desc in lista_final if desc])
        self._draw_cell(self.layout.get_servico_desc_label())
        self._draw_multi_cell(self.layout.get_servico_desc_value(value=desc_serv if desc_serv else ""))

    def _draw_trib_municipal(self):
        """
        Desenha a seção Tributação Municipal com os dados da tributação municipal.
        """
        self._draw_cell(self.layout.get_trib_mun_title())

        trib_issqn = de_para_trib_issqn(getattr(self, 'trib_trib_issqn', ''))
        self._draw_cell(self.layout.get_trib_mun_issqn_label())
        self._draw_cell(self.layout.get_trib_mun_issqn_value(de_para_trib_issqn(trib_issqn)))

        pais_result = PAISES_ISO.get(self.trib_pais_result, '') if self.trib_pais_result else "-"
        self._draw_cell(self.layout.get_trib_mun_pais_result_serv_label())
        self._draw_cell(self.layout.get_trib_mun_pais_result_serv_value(pais_result))


        inc_issqn = getattr(self, 'trib_v_bc_bm', None) or ""
        municipio = ""
        uf = ""

        if inc_issqn != "": 
            try:

                import requests
                response = requests.get(f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{inc_issqn}")
                
                if response.status_code == 200:
                    data = response.json()
                    municipio = data["nome"]
                    uf = data['microrregiao']['mesorregiao']['UF']['sigla']
                else:
                    municipio = ""
                    uf = ""
            except Exception as e:
                municipio = ""
                uf = ""

        municipio_uf = f"{municipio} - {uf}"
        self._draw_cell(self.layout.get_trib_mun_inc_issqn_label())
        self._draw_cell(self.layout.get_trib_mun_inc_issqn_value(value=municipio_uf if municipio_uf else "-"))


        regime = de_para_reg_esp_trib(getattr(self, 'prest_reg_esp_trib', '-'))
        self._draw_cell(self.layout.get_trib_regime_label())
        self._draw_cell(self.layout.get_trib_regime_value(value=regime))

        tipo_imun = de_para_tipo_imun_issqn(getattr(self, 'trib_tp_imun', '-'))
        self._draw_cell(self.layout.get_trib_tipo_imun_label())
        self._draw_cell(self.layout.get_trib_tipo_imun_value('-'))

        susp = de_para_susp_issqn(getattr(self, 'trib_tp_susp', 'Não'))
        self._draw_cell(self.layout.get_trib_susp_issqn_label())
        self._draw_cell(self.layout.get_trib_susp_issqn_value(value=susp))

        num_proc = getattr(self, 'trib_num_proc_susp', '-')
        self._draw_cell(self.layout.get_trib_num_proc_susp_issqn_label())
        self._draw_cell(self.layout.get_trib_num_proc_susp_issqn_value(num_proc))

        benef_mun =  formatar_moeda(getattr(self, 'trib_benef_mun', '-'))
        self._draw_cell(self.layout.get_trib_benef_mun_label())
        self._draw_cell(self.layout.get_trib_benef_mun_value(value=benef_mun))

        vl_serv = formatar_moeda(getattr(self, 'dps_v_serv', '-'))
        self._draw_cell(self.layout.get_trib_valor_serv_label())
        self._draw_cell(self.layout.get_trib_valor_serv_value(value=vl_serv))

        desc_incond = formatar_moeda(getattr(self, 'trib_v_desc_incond', '-'))
        self._draw_cell(self.layout.get_trib_desc_incond_label())
        self._draw_cell(self.layout.get_trib_desc_incond_value(value=desc_incond))

        red_deduc = formatar_moeda(getattr(self, 'v_calc_dr', '-'))
        self._draw_cell(self.layout.get_trib_total_deduc_label())
        self._draw_cell(self.layout.get_trib_total_deduc_value(red_deduc))

        bm = formatar_moeda(getattr(self, 'v_bm', '-'))
        self._draw_cell(self.layout.get_trib_total_bm_label())
        self._draw_cell(self.layout.get_trib_total_bm_value(value=bm))

        bc_issqn = formatar_moeda(getattr(self, 'v_bc', '-'))
        self._draw_cell(self.layout.get_trib_bc_issqn_label())
        self._draw_cell(self.layout.get_trib_bc_issqn_value(value=bc_issqn))

        aliq = getattr(self, 'p_aliq_aplic', '0.00') + '%'
        self._draw_cell(self.layout.get_trib_aliq_label())
        self._draw_cell(self.layout.get_trib_aliq_value(value=aliq))

        ret = formatar_moeda(getattr(self, 'v_total_ret', 'Não Retido'))
        self._draw_cell(self.layout.get_trib_ret_issqn_label())
        self._draw_cell(self.layout.get_trib_ret_issqn_value(value=ret))

        aliq_num = float(aliq.replace('%', '')) if aliq else 0
        bc_issqn_num = float(getattr(self, 'v_bc', 0))
        vl_apr = (aliq_num * bc_issqn_num) / 100
        vl_apr = round(vl_apr, 2)
        vl_apr = formatar_moeda(vl_apr)
        self._draw_cell(self.layout.get_trib_valor_issqn_apurado_label())
        self._draw_cell(self.layout.get_trib_valor_issqn_apurado_value(value=vl_apr))


    def _draw_trib_federal(self):
        """
        Desenha a seção Tributação Federal com os dados da tributação federal.
        """
        self._draw_cell(self.layout.get_trib_federal_title())

        irrf = formatar_moeda(getattr(self, 'trib_v_ret_irrf', '-'))
        self._draw_cell(self.layout.get_trib_federal_irrf_label())
        self._draw_cell(self.layout.get_trib_federal_irrf_value(value=irrf))

        cp = formatar_moeda(getattr(self, 'trib_v_ret_cp', '-'))
        self._draw_cell(self.layout.get_trib_federal_cp_label())
        self._draw_cell(self.layout.get_trib_federal_cp_value(value=cp))

        csll = formatar_moeda(getattr(self, 'trib_v_ret_csll', '-'))
        self._draw_cell(self.layout.get_trib_federal_csll_label())
        self._draw_cell(self.layout.get_trib_federal_csll_value(value=csll))

        pis = formatar_moeda(getattr(self, 'trib_v_pis', '-'))
        self._draw_cell(self.layout.get_trib_federal_pis_label())
        self._draw_cell(self.layout.get_trib_federal_pis_value(value=pis))

        cofins = formatar_moeda(getattr(self, 'trib_v_cofins', '-'))
        self._draw_cell(self.layout.get_trib_federal_cofins_label())
        self._draw_cell(self.layout.get_trib_federal_cofins_value(value=cofins))

        ret_pis_cofins = de_para_tp_ret_pis_cofins(getattr(self, 'trib_tp_ret_pis_cofins', '-'))
        self._draw_cell(self.layout.get_trib_federal_ret_pis_cofins_label())
        self._draw_cell(self.layout.get_trib_federal_ret_pis_cofins_value(value=ret_pis_cofins))

        total = formatar_moeda(getattr(self, 'trib_v_tot_trib_fed', '-'))
        self._draw_cell(self.layout.get_trib_federal_total_label())
        self._draw_cell(self.layout.get_trib_federal_total_value(value=total))

    def _draw_valor_nfse(self):
        """
        Desenha a seção Valor da NFS-e com os dados do valor da NFS-e.
        """
        self._draw_cell(self.layout.get_total_nfse_title())

        vl_serv = formatar_moeda(getattr(self, 'dps_v_serv', '-'))
        self._draw_cell(self.layout.get_total_nfse_vl_servico_label())
        self._draw_cell(self.layout.get_total_nfse_vl_servico_value(value=vl_serv))

        desc_cond = formatar_moeda(getattr(self, 'trib_v_desc_cond', '-'))
        self._draw_cell(self.layout.get_total_nfse_desc_cond_label())
        self._draw_cell(self.layout.get_total_nfse_desc_cond_value(value=desc_cond))

        desc_incond = formatar_moeda(getattr(self, 'trib_v_desc_incond', '-'))
        self._draw_cell(self.layout.get_total_nfse_desc_incond_label())
        self._draw_cell(self.layout.get_total_nfse_desc_incond_value(value=desc_incond))

        issqn_ret = formatar_moeda(getattr(self, 'v_total_ret', '-'))
        self._draw_cell(self.layout.get_total_nfse_issqn_label())
        self._draw_cell(self.layout.get_total_nfse_issqn_value(value=issqn_ret))

        v_ret_cp = float(getattr(self, 'trib_v_ret_cp', 0) if getattr(self, 'trib_v_ret_cp', 0) else 0)
        v_ret_irrf = float(getattr(self, 'trib_v_ret_irrf', 0) if getattr(self, 'trib_v_ret_irrf', 0) else 0)
        v_ret_csll = float(getattr(self, 'trib_v_ret_csll', 0) if getattr(self, 'trib_v_ret_csll', 0) else 0)
        v_ret_total = v_ret_cp + v_ret_irrf + v_ret_csll
        v_ret_total = formatar_moeda(v_ret_total)

        self._draw_cell(self.layout.get_total_nfse_irrf_label())
        self._draw_cell(self.layout.get_total_nfse_irrf_value(value=v_ret_total))

        v_pis = float(getattr(self, 'trib_v_pis', 0) if getattr(self, 'trib_v_pis', 0) else 0)
        v_cofins = float(getattr(self, 'trib_v_cofins', 0) if getattr(self, 'trib_v_cofins', 0) else 0)
        v_pis_cofins_total = v_pis + v_cofins
        v_pis_cofins_total = formatar_moeda(v_pis_cofins_total)
        self._draw_cell(self.layout.get_total_nfse_pis_label())
        self._draw_cell(self.layout.get_total_nfse_pis_value(value=v_pis_cofins_total))

        v_liq = formatar_moeda(getattr(self, 'v_liq', '-'))
        self._draw_cell(self.layout.get_total_nfse_liquido_label())
        self._draw_cell(self.layout.get_total_nfse_liquido_value(value=v_liq))

    def _draw_totais(self):
        """
        Desenha a seção Totais com os dados dos totais.
        """
        self._draw_cell(self.layout.get_totais_title())
        
        v_tot_trib_fed = formatar_moeda(getattr(self, 'trib_v_tot_trib_fed', '-'))
        self._draw_cell(self.layout.get_totais_federais_label())
        self._draw_cell(self.layout.get_totais_federais_value(value=v_tot_trib_fed))
        
        v_tot_trib_est = formatar_moeda(getattr(self, 'trib_v_tot_trib_est', '-'))
        self._draw_cell(self.layout.get_totais_estaduais_label())
        self._draw_cell(self.layout.get_totais_estaduais_value(value=v_tot_trib_est))
        
        v_tot_trib_mun = formatar_moeda(getattr(self, 'trib_v_tot_trib_mun', '-'))
        self._draw_cell(self.layout.get_totais_municipais_label())
        self._draw_cell(self.layout.get_totais_municipais_value(value=v_tot_trib_mun))

    def _draw_info_complementar(self):
        """
        Desenha a seção Informações Complementares com os dados das informações complementares.
        """
        info_compl = getattr(self, 'serv_x_inf_comp', '-')

        info_compl = info_compl.split('\n')
        info_compl = [info.strip() for info in info_compl if info]

        info_compl = " ".join(info_compl)

        import textwrap

        lista_linhas = textwrap.wrap(info_compl, width=160, break_long_words=False) if info_compl and len(info_compl) > 160 else ([info_compl] if info_compl else [])
        
        texto_final = "\n".join([info.strip() for info in lista_linhas if info])
        self._draw_cell(self.layout.get_info_complementar_title())
        self._draw_multi_cell(self.layout.get_info_complementar_value(value=texto_final))
    

    def _draw_cell(self, element: TextElement, value: str = None):
        self.set_font(self.default_font, element.font_style, element.font_size)
        self.set_xy(element.x, element.y)
        self.cell(w=element.width or 30, h=element.height,
                  txt=element.value, border=0, align="L")
        return self

    def _draw_multi_cell(self, element: TextElement, value: str = None):
        self.set_font(self.default_font, element.font_style, element.font_size)
        self.set_xy(element.x, element.y)
        
        # Usa line_height se disponível, senão usa height
        # No FPDF, o parâmetro 'h' do multi_cell controla o espaçamento entre linhas
        line_height = element.line_height if element.line_height is not None else element.height
        
        # Se value foi fornecido, usa ele em vez do value do element
        text = value if value is not None else element.value
        
        # Garante que há texto para desenhar
        if not text:
            return self
        
        # Garante que width está definido
        width = element.width if element.width is not None else self.epw - (element.x - self.l_margin)
        
        self.multi_cell(
            w=width, 
            h=line_height,  # Altura da linha (espaçamento entre linhas)
            txt=text, 
            border=0, 
            align="L"
        )
        return self

    def draw_watermark(self, text: str):
        """
        Desenha uma marca d'água diagonal grande no PDF.
        A marca vai da esquerda inferior para a direita superior.
        
        Args:
            text: Texto da marca d'água (ex: "CANCELADA", "SUBSTITUÍDA", "BLOQUEADA")
        """
        with self.local_context(
            fill_opacity=0.5,
            text_color=(230, 230, 230),
            font_family=self.default_font,
            font_size=40,
            ):
            
            page_width = self.w
            page_height = self.h
            center_x = page_width / 2
            center_y = page_height / 2
            
            
            text_width = self.get_string_width(text)
            
            x = center_x - (text_width / 2)
            y = center_y
            
            # Define cor cinza muito claro para a marca d'água (mais transparente)
            # Usa RGB: 230, 230, 230 (cinza muito claro, quase transparente)
            self.set_text_color(230, 230, 230)
            
            # Desenha o texto rotacionado usando o context manager rotation
            with self.rotation(45, x=center_x, y=center_y):
                self.text(x, y, text)
            
            # Restaura a cor preta para o resto do documento
            self.set_text_color(0, 0, 0)

    def output_pdf(self, output_path):
        self.output(output_path)
