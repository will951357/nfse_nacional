

from fpdf.enums import StrokeCapStyle
from pdf.nfse.config import NfseConfig
from pdf.nfse.xpdf import xFPDF
from pdf.nfse.layout import Layout, TextElement
import xml.etree.ElementTree as ET


class Nfse(xFPDF):

    URL = "http://www.sped.fazenda.gov.br/nfse"
    URL_QRCODE = 'https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave='

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

                # Serviço
                serv = find_tag("serv", inf_dps)
                if serv is not None:
                    loc_prest = find_tag("locPrest", serv)
                    if loc_prest is not None:
                        self.serv_c_loc_prestacao = find_tag_text(
                            "cLocPrestacao", loc_prest)

                    c_serv = find_tag("cServ", serv)
                    if c_serv is not None:
                        self.serv_c_trib_nac = find_tag_text(
                            "cTribNac", c_serv)
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
            effective_page_width=self.epw
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

        self.output_pdf("nfse.pdf")

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
        # TODO: Implementar geração do QR Code
        # Por enquanto, apenas desenha o espaço reservado
        if qr_element.width and qr_element.height:
            self.rect(
                x=qr_element.x,
                y=qr_element.y,
                w=qr_element.width,
                h=qr_element.height
            )

        # Chave de Acesso
        self._draw_cell(self.layout.get_info_note_chave_label(), "Chave de Acesso da NFS-e")
        self._draw_cell(self.layout.get_info_note_chave_value(), "42054072205231453000142000000000005125122985836525")

        # Número
        self._draw_cell(self.layout.get_info_note_numero_label(), "Número da NFS-e")
        self._draw_cell(self.layout.get_info_note_numero_value(), "1234567890")

        self._draw_cell(self.layout.get_info_note_competencia_label(), "Competência da NFS-e")
        self._draw_cell(self.layout.get_info_note_competencia_value(), "2026-01-12")

        self._draw_cell(self.layout.get_info_note_data_label(), "Data e Hora da emissão da NFS-e")
        self._draw_cell(self.layout.get_info_note_data_value(), "2026-01-12 10:00:00")

        self._draw_cell(self.layout.get_info_note_number_dps_label(), "Número da DPS")
        self._draw_cell(self.layout.get_info_note_number_dps_value(), "1234567890")

        self._draw_cell(self.layout.get_info_note_serie_dps_label(), "Série da DPS")
        self._draw_cell(self.layout.get_info_note_serie_dps_value(), "1234567890")

        self._draw_cell(self.layout.get_info_note_date_dps_label(), "Data e Hora da emissão da DPS")
        self._draw_cell(self.layout.get_info_note_date_dps_value(), "2026-01-12 10:00:00")

        self._draw_multi_cell(self.layout.get_info_note_qr_label(), "A autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e")

    def _draw_emitente(self):
        """
        Desenha a seção Emitente com os dados do emitente.
        """
        self._draw_cell(self.layout.get_emitente_title(), "EMITENTE DA NFS-e")

        self._draw_cell(self.layout.get_emitente_subtitle(), "Prestador do Serviço")

        self._draw_cell(self.layout.get_emitente_cnpj_label(), "CNPJ / CPF / NIF")
        self._draw_cell(self.layout.get_emitente_cnpj_value(), "05.231.453/0001-42")

        self._draw_cell(self.layout.get_emitente_insc_municipal_label(), "Inscrição Municipal")
        self._draw_cell(self.layout.get_emitente_insc_municipal_value(), "1234567890")

        self._draw_cell(self.layout.get_emitente_telefone_label(), "Telefone")
        self._draw_cell(self.layout.get_emitente_telefone_value(), "(48) 9191-1777")

        self._draw_cell(self.layout.get_emitente_nome_label(), "Nome / Nome Empresarial")
        self._draw_cell(self.layout.get_emitente_nome_value(), "JEXPERTS TECNOLOGIA S.A.")

        self._draw_cell(self.layout.get_emitente_email_label(), "Email")
        self._draw_cell(self.layout.get_emitente_email_value(), "FERNANDA.NEVES@JEXPERTS.COM.BR")

        self._draw_cell(self.layout.get_emitente_endereco_label(), "Endereço")
        self._draw_cell(self.layout.get_emitente_endereco_value(), "Rua das Flores, 123, Centro")

        self._draw_cell(self.layout.get_emitente_municipio_label(), "Município")
        self._draw_cell(self.layout.get_emitente_municipio_value(), "Florianópolis - SC")

        self._draw_cell(self.layout.get_emitente_cep_label(), "CEP")
        self._draw_cell(self.layout.get_emitente_cep_value(), "88032-005")

        self._draw_cell(self.layout.get_emitente_sn_label(), "Simples Nacional na Data de Competência")
        self._draw_cell(self.layout.get_emitente_sn_value(), "Não optante")

        self._draw_cell(self.layout.get_emitente_sn_apuracao_label(), "Regime de Apuração Tributária pelo SN")
        self._draw_cell(self.layout.get_emitente_sn_apuracao_value(), "Não optante")

    def _draw_tomador(self):
        """
        Desenha a seção Tomador com os dados do tomador.
        """
        # Título
        self._draw_cell(self.layout.get_tomador_title(), "TOMADOR DO SERVIÇO")

        self._draw_cell(self.layout.get_tomador_cnpj_label(), "CNPJ / CPF / NIF")
        self._draw_cell(self.layout.get_tomador_cnpj_value(), "05.231.453/0001-42")

        self._draw_cell(self.layout.get_tomador_im_label(), "Inscrição Municipal")
        self._draw_cell(self.layout.get_tomador_im_value(), "1234567890")

        self._draw_cell(self.layout.get_tomador_telefone_label(), "Telefone")
        self._draw_cell(self.layout.get_tomador_telefone_value(), "(48) 9191-1777")

        self._draw_cell(self.layout.get_tomador_nome_label(), "Nome / Nome Empresarial")
        self._draw_multi_cell( self.layout.get_tomador_nome_value())

        self._draw_cell(self.layout.get_tomador_email_label(), "Email")
        self._draw_multi_cell(self.layout.get_tomador_email_value())

        self._draw_cell(self.layout.get_tomador_endereco_label(), "Endereço")
        self._draw_cell(self.layout.get_tomador_endereco_value(), "Rua das Flores, 123, Centro")

        self._draw_cell(self.layout.get_tomador_municipio_label(), "Município")
        self._draw_cell(self.layout.get_tomador_municipio_value(), "São Paulo - SP")

        self._draw_cell(self.layout.get_tomador_cep_label(), "CEP")
        self._draw_cell(self.layout.get_tomador_cep_value(), "88032-005")

    def _draw_intermediario(self):
        """
        Desenha a seção Intermediário com os dados do intermediário.
        """
        self._draw_cell(self.layout.get_intermediario_null_label())

    def _draw_servico(self):
        """
        Desenha a seção Serviço com os dados do serviço.
        """
        self._draw_cell(self.layout.get_servico_title())

        self._draw_cell(self.layout.get_servico_cod_trib_nac_label())
        self._draw_multi_cell(self.layout.get_servico_cod_trib_nac_value())

        self._draw_cell(self.layout.get_servico_cod_trib_mun_label())
        self._draw_multi_cell(self.layout.get_servico_cod_trib_mun_value())

        self._draw_cell(self.layout.get_servico_local_label())
        self._draw_cell(self.layout.get_servico_local_value(),"Florianópolis - SC")

        self._draw_cell(self.layout.get_servico_pais_label())
        self._draw_cell(self.layout.get_servico_pais_value(), "Brasil")

        self._draw_cell(self.layout.get_servico_desc_label())
        self._draw_cell(self.layout.get_servico_desc_value(),"Serviço de suporte técnico em informática")

    def _draw_trib_municipal(self):
        """
        Desenha a seção Tributação Municipal com os dados da tributação municipal.
        """
        self._draw_cell(self.layout.get_trib_mun_title())

        self._draw_cell(self.layout.get_trib_mun_issqn_label())
        self._draw_cell(self.layout.get_trib_mun_issqn_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_mun_pais_result_serv_label())
        self._draw_cell(self.layout.get_trib_mun_pais_result_serv_value(), "Brasil")

        self._draw_cell(self.layout.get_trib_mun_inc_issqn_label())
        self._draw_cell(self.layout.get_trib_mun_inc_issqn_value(), "Florianópolis - SC")

        self._draw_cell(self.layout.get_trib_regime_label())
        self._draw_cell(self.layout.get_trib_regime_value(), "Nenhum")

        self._draw_cell(self.layout.get_trib_tipo_imun_label())
        self._draw_cell(self.layout.get_trib_tipo_imun_value(), "Nenhum")

        self._draw_cell(self.layout.get_trib_susp_issqn_label())
        self._draw_cell(self.layout.get_trib_susp_issqn_value(), "Nenhum")

        self._draw_cell(self.layout.get_trib_num_proc_susp_issqn_label())
        self._draw_cell(self.layout.get_trib_num_proc_susp_issqn_value(), "Nenhum")

        self._draw_cell(self.layout.get_trib_benef_mun_label())
        self._draw_cell(self.layout.get_trib_benef_mun_value(), "Nenhum")

        self._draw_cell(self.layout.get_trib_valor_serv_label())
        self._draw_cell(self.layout.get_trib_valor_serv_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_desc_incond_label())
        self._draw_cell(self.layout.get_trib_desc_incond_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_total_deduc_label())
        self._draw_cell(self.layout.get_trib_total_deduc_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_total_bm_label())
        self._draw_cell(self.layout.get_trib_total_bm_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_bc_issqn_label())
        self._draw_cell(self.layout.get_trib_bc_issqn_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_aliq_label())
        self._draw_cell(self.layout.get_trib_aliq_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_ret_issqn_label())
        self._draw_cell(self.layout.get_trib_ret_issqn_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_valor_issqn_apurado_label())
        self._draw_cell(self.layout.get_trib_valor_issqn_apurado_value(), "R$ 22,67")


    def _draw_trib_federal(self):
        """
        Desenha a seção Tributação Federal com os dados da tributação federal.
        """
        self._draw_cell(self.layout.get_trib_federal_title())

        self._draw_cell(self.layout.get_trib_federal_irrf_label())
        self._draw_cell(self.layout.get_trib_federal_irrf_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_federal_cp_label())
        self._draw_cell(self.layout.get_trib_federal_cp_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_federal_csll_label())
        self._draw_cell(self.layout.get_trib_federal_csll_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_federal_pis_label())
        self._draw_cell(self.layout.get_trib_federal_pis_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_federal_cofins_label())
        self._draw_cell(self.layout.get_trib_federal_cofins_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_federal_ret_pis_cofins_label())
        self._draw_cell(self.layout.get_trib_federal_ret_pis_cofins_value(), "R$ 22,67")

        self._draw_cell(self.layout.get_trib_federal_total_label())
        self._draw_cell(self.layout.get_trib_federal_total_value(), "R$ 22,67")

    def _draw_valor_nfse(self):
        """
        Desenha a seção Valor da NFS-e com os dados do valor da NFS-e.
        """
        self._draw_cell(self.layout.get_total_nfse_title())

        self._draw_cell(self.layout.get_total_nfse_vl_servico_label())
        self._draw_cell(self.layout.get_total_nfse_vl_servico_value())

        self._draw_cell(self.layout.get_total_nfse_desc_cond_label())
        self._draw_cell(self.layout.get_total_nfse_desc_cond_value())

        self._draw_cell(self.layout.get_total_nfse_desc_incond_label())
        self._draw_cell(self.layout.get_total_nfse_desc_incond_value())

        self._draw_cell(self.layout.get_total_nfse_issqn_label())
        self._draw_cell(self.layout.get_total_nfse_issqn_value())

        self._draw_cell(self.layout.get_total_nfse_irrf_label())
        self._draw_cell(self.layout.get_total_nfse_irrf_value())

        self._draw_cell(self.layout.get_total_nfse_pis_label())
        self._draw_cell(self.layout.get_total_nfse_pis_value())

        self._draw_cell(self.layout.get_total_nfse_liquido_label())
        self._draw_cell(self.layout.get_total_nfse_liquido_value())

    def _draw_cell(self, element: TextElement, value: str = None):
        self.set_font(self.default_font, element.font_style, element.font_size)
        self.set_xy(element.x, element.y)
        self.cell(w=element.width or 30, h=element.height,
                  txt=element.value, border=0, align="L")
        return self

    def _draw_multi_cell(self, element: TextElement, value: str = None):
        self.set_font(self.default_font, element.font_style, element.font_size)
        self.set_xy(element.x, element.y)
        self.multi_cell(w=element.width, h=element.height,
                        txt=element.value, border=0, align="L")
        return self

    def output_pdf(self, output_path):
        self.output(output_path)
