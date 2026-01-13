"""
Classe para gerenciar as dimensões e posicionamento dos elementos do PDF.
Centraliza todos os cálculos de conversão SVG -> PDF.
"""

from math import dist
import sys
import os
from typing import List
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from layout_refactored import PositionManager


class Element:
    """
    Classe base para representar um elemento do PDF.
    Todo elemento tem posição (x, y), valor (conteúdo) e opcionalmente dimensões (width, height).
    """
    
    def __init__(self, x: float, y: float, value, width: float = None, height: float = None):
        """
        Inicializa um elemento do PDF.
        
        Args:
            x: Posição X em mm (obrigatório)
            y: Posição Y em mm (obrigatório)
            value: Valor/conteúdo do elemento (obrigatório)
            width: Largura em mm (opcional)
            height: Altura em mm (opcional)
        """
        self.x = x
        self.y = y
        self.value = value
        self.width = width
        self.height = height
    
    def __repr__(self):
        return f"Element(x={self.x}, y={self.y}, value={self.value!r}, width={self.width}, height={self.height})"


class TextElement(Element):
    """
    Elemento de texto que herda de Element e adiciona propriedades de formatação de fonte.
    """
    
    def __init__(self, x: float, y: float, value: str, width: float = None, height: float = None,
                 font_size: int = 10, font_style: str = "", line_height: float = None):
        """
        Inicializa um elemento de texto.
        
        Args:
            x: Posição X em mm
            y: Posição Y em mm
            value: Texto a ser exibido
            width: Largura da célula em mm (opcional)
            height: Altura da célula em mm (opcional, usado como altura padrão se line_height não for fornecido)
            font_size: Tamanho da fonte (padrão: 10)
            font_style: Estilo da fonte ("B" para bold, "" para normal, "I" para itálico)
            line_height: Altura entre linhas em mm (opcional, padrão: usa height ou 4mm)
                        Usado no multi_cell para controlar o espaçamento entre linhas
        """
        super().__init__(x, y, value, width, height)
        self.font_size = font_size
        self.font_style = font_style
        # line_height controla o espaçamento entre linhas no multi_cell
        # Se não fornecido, usa height ou padrão de 4mm
        self.line_height = line_height if line_height is not None else (height if height is not None else 4.0)
    
    def __repr__(self):
        return (f"TextElement(x={self.x}, y={self.y}, value={self.value!r}, "
                f"width={self.width}, height={self.height}, "
                f"font_size={self.font_size}, font_style={self.font_style!r}, "
                f"line_height={self.line_height})")


class LineElement(Element):
    """
    Elemento de linha horizontal que herda de Element.
    Para uma linha horizontal: x é o início, y é a posição Y, width é o comprimento.
    """
    
    def __init__(self, x: float, y: float, width: float, value: str = None):
        """
        Inicializa um elemento de linha horizontal.
        
        Args:
            x: Posição X inicial em mm (geralmente a margem esquerda)
            y: Posição Y da linha em mm
            width: Comprimento da linha em mm (largura efetiva da página)
            value: Nome/identificador da linha (opcional, para referência)
        """
        super().__init__(x, y, value, width, height=None)
        # Para linha horizontal, x2 = x + width, y2 = y
        self.x2 = x + width
        self.y2 = y
    
    def __repr__(self):
        return f"LineElement(x={self.x}, y={self.y}, x2={self.x2}, y2={self.y2}, width={self.width}, value={self.value!r})"


class Layout:
    """
    Classe responsável por calcular e armazenar as dimensões dos elementos do PDF.
    Todas as conversões de coordenadas SVG para PDF são feitas aqui.
    """
    
    # Fator de conversão: SVG tem área útil ~595x842px, PDF A4 é 210x297mm
    PX_TO_MM = 210 / 595  # ≈ 0.3529
    
    # Offset do SVG (a borda do SVG começa em x=65, y=65)
    SVG_OFFSET_X = 65
    SVG_OFFSET_Y = 65
    
    def __init__(self, left_margin: float, top_margin: float, effective_page_width: float,
                 exclude_sections: List[str] = []):
        """
        Inicializa o layout com as margens e dimensões da página.
        
        Args:
            left_margin: Margem esquerda em mm
            top_margin: Margem superior em mm
            effective_page_width: Largura efetiva da página em mm (epw)
            tomador_exists: Se tomador existe no XML
            intermediario_exists: Se intermediário existe no XML
        """
        self.left_margin = left_margin
        self.internal_left_margin = left_margin + (left_margin/2)
        self.second_column_margin = self.internal_left_margin + 45
        self.third_column_margin = self.second_column_margin + 55
        self.fourth_column_margin = self.third_column_margin + 55
        self.top_margin = top_margin
        self.epw = effective_page_width
        self.title_font_size = 8
        self.value_font_size = 6.5
        self.label_font_size = 7
        
        
        # Inicializa o PositionManager e calcula as posições das seções
        self.position_manager = PositionManager(
            left_margin=left_margin,
            top_margin=top_margin,
            effective_page_width=effective_page_width
        )
        self.position_manager.calculate_positions(
            exclude_sections=exclude_sections
        )
    
    def get_section_y(self, section_name: str) -> float:
        """
        Retorna a posição Y de uma seção usando o PositionManager.
        
        Args:
            section_name: Nome da seção (ex: "info_nota", "emitente", "tomador", etc.)
        
        Returns:
            Posição Y em mm
        """
        if section_name in self.position_manager.positions:
            return self.position_manager.positions[section_name]['y']
        else:
            # Debug: mostra quais seções estão disponíveis
            available_sections = list(self.position_manager.positions.keys())
            raise ValueError(
                f"Seção '{section_name}' não encontrada no PositionManager. "
                f"Seções disponíveis: {available_sections}"
            )
    
    def _svg_to_pdf_x(self, svg_x: float) -> float:
        """Converte coordenada X do SVG para PDF em mm."""
        return self.left_margin + (svg_x - self.SVG_OFFSET_X) * self.PX_TO_MM
    
    def _svg_to_pdf_y(self, svg_y: float) -> float:
        """Converte coordenada Y do SVG para PDF em mm."""
        return self.top_margin + (svg_y - self.SVG_OFFSET_Y) * self.PX_TO_MM
    
    def _svg_to_pdf_size(self, svg_size: float) -> float:
        """Converte dimensão (largura/altura) do SVG para PDF em mm."""
        return svg_size * self.PX_TO_MM
    
    # ==================== HEADER ====================
    
    class Header:
        """Dimensões e posicionamento dos elementos do header."""
        
        # Coordenadas SVG do logo
        LOGO_SVG_X = 74.1732
        LOGO_SVG_Y = 72.4925
        LOGO_SVG_WIDTH = 113.386
        LOGO_SVG_HEIGHT = 22.6772
        
        # Coordenadas SVG dos textos
        TEXT1_SVG_Y = 76.395  # "DANFSe v1.0"
        TEXT2_SVG_Y = 85.5576  # "Documento Auxiliar da NFS-e"
        PREFEITURA_SVG_Y = 76.395  # "Prefeitura Municipal de {nome}" - mesma altura do TEXT1
        
        # Configurações dos textos
        TEXT1_FONT_SIZE = 10
        TEXT1_FONT_STYLE = "B"  # Bold
        TEXT1_CONTENT = "DANFSe v1.0"
        
        TEXT2_FONT_SIZE = 9
        TEXT2_FONT_STYLE = ""  # Normal
        TEXT2_CONTENT = "Documento Auxiliar da NFS-e"
        
        PREFEITURA_FONT_SIZE = 9
        PREFEITURA_FONT_STYLE = ""  # Normal
        
        TEXT_CELL_HEIGHT = 5
    
    def get_header_logo(self) -> Element:
        """
        Retorna o elemento do logo do header já convertido para PDF.
        
        Returns:
            Element com posição e dimensões do logo (value será o caminho da imagem)
        """
        return Element(
            x=self._svg_to_pdf_x(self.Header.LOGO_SVG_X),
            y=self._svg_to_pdf_y(self.Header.LOGO_SVG_Y + 2),  # Ajuste de +3px
            value=None,  # O caminho da imagem será definido no momento do desenho
            width=self._svg_to_pdf_size(self.Header.LOGO_SVG_WIDTH),
            height=self._svg_to_pdf_size(self.Header.LOGO_SVG_HEIGHT),
        )
    
    def get_header_text1(self) -> TextElement:
        """
        Retorna o elemento do primeiro texto do header.
        
        Returns:
            TextElement com posição, valor e formatação do texto
        """
        return TextElement(
            x=self.left_margin,
            y=self._svg_to_pdf_y(self.Header.TEXT1_SVG_Y),
            value=self.Header.TEXT1_CONTENT,
            width=self.epw,  # cell_width
            height=self.Header.TEXT_CELL_HEIGHT,  # cell_height
            font_size=self.Header.TEXT1_FONT_SIZE,
            font_style=self.Header.TEXT1_FONT_STYLE,
        )
    
    def get_header_text2(self) -> TextElement:
        """
        Retorna o elemento do segundo texto do header.
        
        Returns:
            TextElement com posição, valor e formatação do texto
        """
        return TextElement(
            x=self.left_margin,
            y=self._svg_to_pdf_y(self.Header.TEXT2_SVG_Y),
            value=self.Header.TEXT2_CONTENT,
            width=self.epw,  # cell_width
            height=self.Header.TEXT_CELL_HEIGHT,  # cell_height
            font_size=self.Header.TEXT2_FONT_SIZE,
            font_style=self.Header.TEXT2_FONT_STYLE,
        )
    
    def get_header_prefeitura(self, nome_municipio: str = None) -> TextElement:
        """
        Retorna o elemento do texto da prefeitura no header (lado direito).
        
        Args:
            nome_municipio: Nome do município (opcional, será formatado como "Prefeitura Municipal de {nome}")
        
        Returns:
            TextElement com posição, valor e formatação do texto
        """
        if nome_municipio:
            text = f"Prefeitura Municipal de {nome_municipio}"
        else:
            text = "Prefeitura Municipal"
        
        # Posiciona à direita: deixa uma margem de 5mm da borda direita
        # A largura será calculada dinamicamente no método de desenho
        # para permitir quebra de linha se necessário
        margin_right = 5.0  # Margem da borda direita em mm
        text_width = 60.0  # Largura inicial aproximada (será ajustada no desenho)
        
        return TextElement(
            x=self.left_margin + self.epw - text_width - margin_right,  # Posiciona à direita
            y=self._svg_to_pdf_y(self.Header.PREFEITURA_SVG_Y),
            value=text,
            width=text_width,  # Largura inicial, será ajustada no desenho
            height=self.Header.TEXT_CELL_HEIGHT,
            font_size=self.Header.PREFEITURA_FONT_SIZE,
            font_style=self.Header.PREFEITURA_FONT_STYLE,
        )


    # ==================== INFO NOTA ====================

    class InfoNote:
        """Dimensões e posicionamento dos elementos da info nota."""
        
        # QR Code
        QR_CODE_SVG_WIDTH = 50.0
        QR_CODE_SVG_HEIGHT = 50.0
        
        # Textos de autenticidade (aproximadamente)
        # Nota: Coordenadas precisas precisam ser verificadas no SVG
        AUTH_TEXT_SVG_Y = 120.0  # Texto "Autenticidade"
        
        # Campos de informação (labels e valores)
        # Chave de Acesso
        CHAVE_LABEL_SVG_Y = 105.0
        CHAVE_VALUE_SVG_Y = 115.0

        DIST_LINE = 22.0
        
        # Número
        NUMERO_LABEL_SVG_Y = CHAVE_LABEL_SVG_Y + DIST_LINE
        NUMERO_VALUE_SVG_Y = CHAVE_VALUE_SVG_Y + DIST_LINE
        
        COMPETENCIA_LABEL_SVG_Y = CHAVE_LABEL_SVG_Y + DIST_LINE
        COMPETENCIA_VALUE_SVG_Y = CHAVE_VALUE_SVG_Y + DIST_LINE

        # Série
        SERIE_LABEL_SVG_Y = 160.0
        SERIE_VALUE_SVG_Y = 170.0
        
        # Data de Emissão
        DATA_LABEL_SVG_Y = CHAVE_LABEL_SVG_Y + DIST_LINE
        DATA_VALUE_SVG_Y = CHAVE_VALUE_SVG_Y + DIST_LINE
        
        # dps
        DPS_LABEL_SVG_Y = CHAVE_LABEL_SVG_Y + DIST_LINE * 2
        DPS_VALUE_SVG_Y = CHAVE_VALUE_SVG_Y + DIST_LINE * 2

        # série da dps
        SERIE_DPS_LABEL_SVG_Y = CHAVE_LABEL_SVG_Y + DIST_LINE * 2
        SERIE_DPS_VALUE_SVG_Y = CHAVE_VALUE_SVG_Y + DIST_LINE * 2

        # data da dps
        DATE_DPS_LABEL_SVG_Y = CHAVE_LABEL_SVG_Y + DIST_LINE * 2
        DATE_DPS_VALUE_SVG_Y = CHAVE_VALUE_SVG_Y + DIST_LINE * 2

        # qr label
        QR_LABEL_SVG_Y = DATE_DPS_VALUE_SVG_Y
        QR_VALUE_SVG_Y = CHAVE_VALUE_SVG_Y
        
        # Configurações de fonte
        AUTH_FONT_SIZE = 7
    
    def get_info_note_qr_code(self) -> Element:
        """
        Retorna o elemento do QR Code da seção Info-Nota.
        
        Returns:
            Element com posição e dimensões do QR Code
        """
        return Element(
            x=self.fourth_column_margin + 15,
            y=self._svg_to_pdf_y(self.InfoNote.QR_VALUE_SVG_Y - 10),
            value=None,  # O conteúdo do QR Code será definido no momento do desenho
            width=self._svg_to_pdf_size(self.InfoNote.QR_CODE_SVG_WIDTH),
            height=self._svg_to_pdf_size(self.InfoNote.QR_CODE_SVG_HEIGHT),
        )
    
    def get_info_note_auth_text(self) -> TextElement:
        """
        Retorna o elemento do texto de autenticidade.
        
        Returns:
            TextElement com posição e formatação do texto
        """
        return TextElement(
            x=self.left_margin,
            y=self._svg_to_pdf_y(self.InfoNote.AUTH_TEXT_SVG_Y),
            value="Autenticidade",  # Será substituído pelo texto real
            width=self.epw,
            height=4,
            font_size=self.InfoNote.AUTH_FONT_SIZE,
            font_style="",
        )
    
    def get_info_note_chave_label(self) -> TextElement:
        """Retorna o elemento do label 'Chave de Acesso'."""
        return TextElement(
            x=self.internal_left_margin,
            y=self._svg_to_pdf_y(self.InfoNote.CHAVE_LABEL_SVG_Y),
            value="Chave de Acesso da NFS-e",
            width=None,
            height=4,
            font_style="B",
            font_size=self.label_font_size,
        )
    
    def get_info_note_chave_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da chave de acesso."""
        return TextElement(
            x=self.internal_left_margin,
            y=self._svg_to_pdf_y(self.InfoNote.CHAVE_VALUE_SVG_Y),
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )
    
    def get_info_note_numero_label(self) -> TextElement:
        """Retorna o elemento do label 'Número'."""
        return TextElement(
            x=self.internal_left_margin,
            y=self._svg_to_pdf_y(self.InfoNote.NUMERO_LABEL_SVG_Y),
            value="Número da NFS-e",
            width=None,
            height=4,
            font_style="B",
            font_size=self.label_font_size,
        )
    
    def get_info_note_numero_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do número."""
        return TextElement(
            x=self.internal_left_margin,  # Offset para alinhar com o valor
            y=self._svg_to_pdf_y(self.InfoNote.NUMERO_VALUE_SVG_Y),
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )


    def get_info_note_competencia_label(self) -> TextElement:
        """Retorna o elemento do label 'Competência'."""
        return TextElement(
            x=self.second_column_margin,
            y=self._svg_to_pdf_y(self.InfoNote.COMPETENCIA_LABEL_SVG_Y),
            value="Competência da NFS-e",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_info_note_competencia_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da competência."""
        return TextElement(
            x=self.second_column_margin,
            y=self._svg_to_pdf_y(self.InfoNote.COMPETENCIA_VALUE_SVG_Y),
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )
    
    def get_info_note_data_label(self) -> TextElement:
        """Retorna o elemento do label 'Data de Emissão'."""
        return TextElement(
            x=self.third_column_margin,
            y=self._svg_to_pdf_y(self.InfoNote.DATA_LABEL_SVG_Y),
            value="Data e Hora da emissão da NFS-e",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_info_note_data_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da data."""
        return TextElement(
            x=self.third_column_margin,
            y=self._svg_to_pdf_y(self.InfoNote.DATA_VALUE_SVG_Y),
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_info_note_number_dps_label(self) -> TextElement:
        """Retorna o elemento do label 'DPS'."""
        return TextElement(
            x=self.internal_left_margin,
            y=self._svg_to_pdf_y(self.InfoNote.DPS_LABEL_SVG_Y),
            value="Número da DPS",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_info_note_number_dps_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do DPS."""
        return TextElement(
            x=self.internal_left_margin,
            y=self._svg_to_pdf_y(self.InfoNote.DPS_VALUE_SVG_Y),
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_info_note_serie_dps_label(self) -> TextElement:
        """Retorna o elemento do label 'Série da DPS'."""
        return TextElement(
            x=self.second_column_margin,
            y=self._svg_to_pdf_y(self.InfoNote.SERIE_DPS_LABEL_SVG_Y),
            value="Série da DPS",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_info_note_serie_dps_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da série da DPS."""
        return TextElement(
            x=self.second_column_margin,
            y=self._svg_to_pdf_y(self.InfoNote.SERIE_DPS_VALUE_SVG_Y),
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_info_note_date_dps_label(self) -> TextElement:
        """Retorna o elemento do label 'Data da DPS'."""
        return TextElement(
            x=self.third_column_margin,
            y=self._svg_to_pdf_y(self.InfoNote.DATE_DPS_LABEL_SVG_Y),
            value="Data e Hora da emissão da DPS",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_info_note_date_dps_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da data da DPS."""
        return TextElement(
            x=self.third_column_margin,
            y=self._svg_to_pdf_y(self.InfoNote.DATE_DPS_VALUE_SVG_Y),
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_info_note_qr_label(self, line_height: float = None) -> TextElement:
        """
        Retorna o elemento do label 'QR Code'.
        
        Args:
            line_height: Altura entre linhas em mm (opcional, padrão: 3.0mm para texto compacto)
        """
        text = "A autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e"
        
        # Largura calculada para o texto ficar ao lado do QR Code
        # QR Code está em x=541.667, então o texto deve ter largura até a margem direita
        # Considerando que o QR Code tem ~17.6mm de largura (50px * PX_TO_MM)
        # e está posicionado próximo à margem direita, o texto deve ter ~40-45mm de largura
        text_width = 60.0  # Largura em mm para o texto
        
        # Espaçamento entre linhas padrão: 3.0mm (mais compacto que o padrão de 4mm)
        # Para fonte de tamanho 6, um line_height de 3mm é apropriado
        default_line_height = 2.0
        line_height = line_height if line_height is not None else default_line_height
        
        return TextElement(
            x=self.fourth_column_margin - 4,
            y=self._svg_to_pdf_y(self.InfoNote.QR_LABEL_SVG_Y),
            value=text,
            width=text_width,
            height=4,  # Altura base (não usada no multi_cell, mas mantida para compatibilidade)
            font_size=6,
            font_style="",
            line_height=line_height,  # Espaçamento entre linhas

        )
    

    # ==================== DADOS EMITENTE ====================
    
    class DadosEmitente:
        """Dimensões e posicionamento dos elementos dos dados do emitente."""
        
        # Título da seção
        def __init__(self, title_y_mm: float, px_to_mm: float):
            # title_y_mm já está em mm (vem de get_section_y)
            # Precisamos converter os offsets SVG para mm
            DIST_LINE_SVG = 22.0  # pixels SVG
            SUBTITLE_OFFSET_SVG = 10.0  # pixels SVG
            
            # Converte offsets SVG para mm
            DIST_LINE_MM = DIST_LINE_SVG * px_to_mm  # ~7.76mm
            SUBTITLE_OFFSET_MM = SUBTITLE_OFFSET_SVG * px_to_mm  # ~3.53mm
            
            self.TITLE_SVG_Y = title_y_mm  # Na verdade já está em mm, mas mantém nome para compatibilidade
            self.SUBTITLE_SVG_Y = self.TITLE_SVG_Y + SUBTITLE_OFFSET_MM

            # Campos do emitente (coordenadas Y em mm)
            # Primeira linha
            self.FIRST_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y
            self.FIRST_LINE_VALUE_SVG_Y = self.SUBTITLE_SVG_Y
            
            # Segunda linha
            self.SECOND_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y + DIST_LINE_MM
            self.SECOND_LINE_VALUE_SVG_Y = self.SUBTITLE_SVG_Y + DIST_LINE_MM
            
            # Terceira linha - Endereço
            self.THIRD_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y + DIST_LINE_MM * 2
            self.THIRD_LINE_VALUE_SVG_Y = self.SUBTITLE_SVG_Y + DIST_LINE_MM * 2

            # Quarta linha - Simples Nacional
            FOURTH_OFFSET_MM = 1.0 * px_to_mm  # ~0.35mm
            self.FOURTH_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y + DIST_LINE_MM * 3 + FOURTH_OFFSET_MM
            self.FOURTH_LINE_VALUE_SVG_Y = self.SUBTITLE_SVG_Y + DIST_LINE_MM * 3 + FOURTH_OFFSET_MM
            
            # Configurações de fonte
            self.TITLE_FONT_SIZE = 10
            self.TITLE_FONT_STYLE = "B"  # Bold
    
    def dados_emitente(self) -> DadosEmitente:
        # get_section_y retorna posição Y em mm
        title_y_mm = self.get_section_y("emitente")
        return self.DadosEmitente(title_y_mm, self.PX_TO_MM)
    
    def get_emitente_title(self) -> TextElement:
        """Retorna o elemento do título da seção Emitente."""
        y = self.dados_emitente().TITLE_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="EMITENTE DA NFS-e",
            width=None,
            height=5,
            font_size=8,
            font_style='',
        )

    def get_emitente_subtitle(self) -> TextElement:
        """Retorna o elemento do subtítulo da seção Emitente."""
        y = self.dados_emitente().SUBTITLE_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="Prestador do Serviço",
            width=None,
            height=4,
            font_size=8,
            font_style='B',
        )
    
    def get_emitente_cnpj_label(self) -> TextElement:
        """Retorna o elemento do label 'CNPJ'."""
        y = self.dados_emitente().FIRST_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.second_column_margin,
            y=y,
            value="CNPJ / CPF / NIF",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_emitente_cnpj_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do CNPJ."""
        y = self.dados_emitente().FIRST_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.second_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_emitente_insc_municipal_label(self) -> TextElement:
        """Retorna o elemento do label 'Inscrição Municipal'."""
        y = self.dados_emitente().FIRST_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="Inscrição Municipal",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_emitente_insc_municipal_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da Inscrição Municipal."""
        y = self.dados_emitente().FIRST_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_emitente_telefone_label(self) -> TextElement:
        """Retorna o elemento do label 'Telefone'."""
        y = self.dados_emitente().FIRST_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value="Telefone",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_emitente_telefone_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Telefone."""
        y = self.dados_emitente().FIRST_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )
    
    def get_emitente_nome_label(self) -> TextElement:
        """Retorna o elemento do label 'Nome'."""
        y = self.dados_emitente().SECOND_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="Nome / Nome Empresarial",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_emitente_nome_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Nome."""
        # Define largura para evitar overflow (até a coluna do Email)
        nome_width = self.third_column_margin - self.internal_left_margin - 2
        y = self.dados_emitente().SECOND_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=nome_width,  # Limita largura para não ultrapassar a coluna do Email
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )
    
    def get_emitente_endereco_label(self) -> TextElement:
        """Retorna o elemento do label 'Endereço'."""
        y = self.dados_emitente().THIRD_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="Endereço",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_emitente_endereco_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Endereço."""
        # Define largura para evitar overflow (até a coluna do Município)
        endereco_width = self.third_column_margin - self.internal_left_margin - 2
        y = self.dados_emitente().THIRD_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML (xLgr, nro, xBairro)
            width=endereco_width,  # Limita largura para não ultrapassar a coluna do Município
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )
    
    def get_emitente_municipio_label(self) -> TextElement:
        """Retorna o elemento do label 'Município'."""
        y = self.dados_emitente().THIRD_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="Município",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_emitente_municipio_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Município."""
        y = self.dados_emitente().THIRD_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    
    def get_emitente_cep_label(self) -> TextElement:
        """Retorna o elemento do label 'CEP'."""
        y = self.dados_emitente().THIRD_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value="CEP",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_emitente_cep_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do CEP."""
        y = self.dados_emitente().THIRD_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )
    
    def get_emitente_email_label(self) -> TextElement:
        """Retorna o elemento do label 'Email'."""
        y = self.dados_emitente().SECOND_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="E-mail",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",  # Removido bold para corresponder ao original
        )
    
    def get_emitente_email_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Email."""
        # Define largura para evitar overflow (até a margem direita)
        email_width = (self.left_margin + self.epw) - self.third_column_margin - 2
        y = self.dados_emitente().SECOND_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="FERNANDA.NEVES@JEXPERTS.COM.BR",  # Será preenchido com dados do XML
            width=email_width,  # Limita largura para não ultrapassar a margem direita
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )
    
    def get_emitente_sn_label(self) -> TextElement:
        """Retorna o elemento do label 'Simples Nacional'."""
        y = self.dados_emitente().FOURTH_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="Simples Nacional na Data de Competência",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_emitente_sn_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Simples Nacional."""
        y = self.dados_emitente().FOURTH_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_emitente_sn_apuracao_label(self) -> TextElement:
        """Retorna o elemento do label 'Apuração'."""
        y = self.dados_emitente().FOURTH_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="Regime de Apuração Tributária pelo SN",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_emitente_sn_apuracao_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Regime de Apuração Tributária pelo SN."""
        y = self.dados_emitente().FOURTH_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )
    # ==================== LINHAS HORIZONTAIS ====================
    
    class Tomador:
        """Dimensões e posicionamento dos elementos dos dados do tomador."""
        
        def __init__(self, title_y_mm: float, px_to_mm: float):
            # title_y_mm já está em mm (vem de get_section_y)
            # Precisamos converter os offsets SVG para mm
            DIST_LINE_SVG = 26.0  # pixels SVG
            VALUE_OFFSET_SVG = 10.0  # pixels SVG
            
            # Converte offsets SVG para mm
            DIST_LINE_MM = DIST_LINE_SVG * px_to_mm  # ~9.18mm
            VALUE_OFFSET_MM = VALUE_OFFSET_SVG * px_to_mm  # ~3.53mm
            
            self.TITLE_SVG_Y = title_y_mm  # Na verdade já está em mm, mas mantém nome para compatibilidade
            
            # Campos do tomador (coordenadas Y em mm)
            # Primeira linha
            self.FIRST_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y
            self.FIRST_LINE_VALUE_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + VALUE_OFFSET_MM
            
            # Segunda linha
            self.SECOND_LINE_LABEL_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.SECOND_LINE_VALUE_SVG_Y = self.FIRST_LINE_VALUE_SVG_Y + DIST_LINE_MM
            
            # Terceira linha
            self.THIRD_LINE_LABEL_SVG_Y = self.SECOND_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.THIRD_LINE_VALUE_SVG_Y = self.SECOND_LINE_VALUE_SVG_Y + DIST_LINE_MM

            # Configurações de fonte
            self.TITLE_FONT_SIZE = 10
            self.TITLE_FONT_STYLE = "B"  # Bold
    
    def dados_tomador(self) -> Tomador:
        # get_section_y retorna posição Y em mm
        title_y_mm = self.get_section_y("tomador")
        return self.Tomador(title_y_mm, self.PX_TO_MM)

    def dados_tomador_null(self) -> Tomador:
        y = self.dados_tomador().TITLE_SVG_Y
        return TextElement(
            x=(self.epw / 4) + 10,
            y=y,
            value="TOMADOR DO SERVIÇO NÃO IDENTIFICADO NA NFS-e",
            width=None,
            height=5,
            font_size=self.title_font_size,
            font_style='B',
        )

    def get_tomador_title(self) -> TextElement:
        """Retorna o elemento do título da seção Tomador."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.get_section_y("tomador"),
            value="TOMADOR DO SERVIÇO",
            width=None,
            height=5,
            font_size=8,
            font_style='B',
        )

    def get_tomador_cnpj_label(self) -> TextElement:
        """Retorna o elemento do label 'CNPJ'."""
        y = self.dados_tomador().FIRST_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.second_column_margin,
            y=y,
            value="CNPJ / CPF / NIF",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_tomador_cnpj_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do CNPJ."""
        y = self.dados_tomador().FIRST_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.second_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_tomador_im_label(self) -> TextElement:
        """Retorna o elemento do label 'Inscrição Municipal'."""
        y = self.dados_tomador().FIRST_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="Inscrição Municipal",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_tomador_im_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da Inscrição Municipal."""
        y = self.dados_tomador().FIRST_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_tomador_telefone_label(self) -> TextElement:
        """Retorna o elemento do label 'Telefone'."""
        y = self.dados_tomador().FIRST_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value="Telefone",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_tomador_telefone_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Telefone."""
        y = self.dados_tomador().FIRST_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_tomador_nome_label(self) -> TextElement:
        """Retorna o elemento do label 'Nome'."""
        y = self.dados_tomador().SECOND_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="Nome / Nome Empresarial",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_tomador_nome_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Nome."""
        # Define largura para evitar overflow (até a coluna do Email)
        nome_width = self.third_column_margin - self.internal_left_margin - 2
        y = self.dados_tomador().SECOND_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=nome_width,  # Limita largura para não ultrapassar a coluna do Email
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_tomador_email_label(self) -> TextElement:
        """Retorna o elemento do label 'Email'."""
        y = self.dados_tomador().SECOND_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="E-mail",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_tomador_email_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Email."""
        # Define largura para evitar overflow (até a margem direita)
        email_width = (self.left_margin + self.epw) - self.third_column_margin - 2
        y = self.dados_tomador().SECOND_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=email_width,  # Limita largura para não ultrapassar a margem direita
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_tomador_endereco_label(self) -> TextElement:
        """Retorna o elemento do label 'Endereço'."""
        y = self.dados_tomador().THIRD_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="Endereço",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
        
    def get_tomador_endereco_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Endereço."""
        # Define largura para evitar overflow (até a coluna do Município)
        endereco_width = self.third_column_margin - self.internal_left_margin - 2
        y = self.dados_tomador().THIRD_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=endereco_width,  # Limita largura para não ultrapassar a coluna do Município
            height=4,
            font_size=self.value_font_size,
            font_style="B",
        )

    def get_tomador_municipio_label(self) -> TextElement:
        """Retorna o elemento do label 'Município'."""
        y = self.dados_tomador().THIRD_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="Município",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
        
    def get_tomador_municipio_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Município."""
        y = self.dados_tomador().THIRD_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    def get_tomador_cep_label(self) -> TextElement:
        """Retorna o elemento do label 'CEP'."""
        y = self.dados_tomador().THIRD_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value="CEP",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_tomador_cep_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do CEP."""
        y = self.dados_tomador().THIRD_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",  # Removido bold para corresponder ao original
        )

    class Intermediario:
        """Dimensões e posicionamento dos elementos dos dados do intermediário."""
        
        def __init__(self, title_y_mm: float, px_to_mm: float):
            # title_y_mm já está em mm (vem de get_section_y)
            # Precisamos converter os offsets SVG para mm
            DIST_LINE_SVG = 26.0  # pixels SVG
            VALUE_OFFSET_SVG = 10.0  # pixels SVG
            
            # Converte offsets SVG para mm
            DIST_LINE_MM = DIST_LINE_SVG * px_to_mm  # ~9.18mm
            VALUE_OFFSET_MM = VALUE_OFFSET_SVG * px_to_mm  # ~3.53mm
            
            self.TITLE_SVG_Y = title_y_mm  # Na verdade já está em mm, mas mantém nome para compatibilidade
            
            # Campos do intermediário (coordenadas Y em mm)
            # Primeira linha
            self.FIRST_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y
            self.FIRST_LINE_VALUE_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + VALUE_OFFSET_MM
            
            # Segunda linha
            self.SECOND_LINE_LABEL_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.SECOND_LINE_VALUE_SVG_Y = self.FIRST_LINE_VALUE_SVG_Y + DIST_LINE_MM
            
            # Terceira linha
            self.THIRD_LINE_LABEL_SVG_Y = self.SECOND_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.THIRD_LINE_VALUE_SVG_Y = self.SECOND_LINE_VALUE_SVG_Y + DIST_LINE_MM

    
    def dados_intermediario(self) -> Intermediario:
        # get_section_y retorna posição Y em mm
        title_y_mm = self.get_section_y("intermediario")
        return self.Intermediario(title_y_mm, self.PX_TO_MM)

    def get_intermediario_null_label(self) -> TextElement:
        """Retorna o elemento do label 'Não há intermediário'."""
        y = self.dados_intermediario().FIRST_LINE_LABEL_SVG_Y
        return TextElement(
            x=(self.epw / 4) + 10,
            y=y,
            value="INTERMEDIÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-e",
            width=None,
            height=4,
            font_size=self.title_font_size,
            font_style='B',
        )

    def get_intermediario_title(self) -> TextElement:
        """Retorna o elemento do título do intermediário."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.get_section_y("intermediario"),
            value="INTERMEDIÁRIO DO SERVIÇO",
            width=None,
            height=5,
            font_size=self.title_font_size,
            font_style="B",
        )

    def get_intermediario_cnpj_label(self) -> TextElement:
        """Retorna o elemento do label 'CNPJ'."""
        y = self.dados_intermediario().FIRST_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.second_column_margin,
            y=y,
            value="CNPJ / CPF / NIF",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_intermediario_cnpj_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do CNPJ."""
        y = self.dados_intermediario().FIRST_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.second_column_margin,
            y=y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_intermediario_insc_mun_label(self) -> TextElement:
        """Retorna o elemento do label 'Inscrição Municipal'."""
        y = self.dados_intermediario().FIRST_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="Inscrição Municipal",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_intermediario_insc_mun_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da Inscrição Municipal."""
        y = self.dados_intermediario().FIRST_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_intermediario_telefone_label(self) -> TextElement:
        """Retorna o elemento do label 'Telefone'."""
        y = self.dados_intermediario().FIRST_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value="Telefone",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_intermediario_telefone_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Telefone."""
        y = self.dados_intermediario().FIRST_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="B",
        )

    def get_intermediario_nome_label(self) -> TextElement:
        """Retorna o elemento do label 'Nome'."""
        y = self.dados_intermediario().SECOND_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="Nome / Nome Empresarial",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_intermediario_nome_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Nome."""
        y = self.dados_intermediario().SECOND_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="B",
        )


    def get_intermediario_email_label(self) -> TextElement:
        """Retorna o elemento do label 'Email'."""
        y = self.dados_intermediario().SECOND_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="E-mail",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_intermediario_email_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Email."""
        y = self.dados_intermediario().SECOND_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_intermediario_endereco_label(self) -> TextElement:
        """Retorna o elemento do label 'Endereço'."""
        y = self.dados_intermediario().THIRD_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="Endereço",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_intermediario_endereco_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Endereço."""
        y = self.dados_intermediario().THIRD_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_intermediario_municipio_label(self) -> TextElement:
        """Retorna o elemento do label 'Município'."""
        y = self.dados_intermediario().THIRD_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="Município",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_intermediario_municipio_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Município."""
        y = self.dados_intermediario().THIRD_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_intermediario_cep_label(self) -> TextElement:
        """Retorna o elemento do label 'CEP'."""
        y = self.dados_intermediario().THIRD_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value="CEP",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_intermediario_cep_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do CEP."""
        y = self.dados_intermediario().THIRD_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    
    class Servico:
        """Dimensões e posicionamento dos elementos dos dados do serviço."""
        
        def __init__(self, title_y_mm: float, px_to_mm: float):
            # title_y_mm já está em mm (vem de get_section_y)
            # Precisamos converter os offsets SVG para mm
            DIST_LINE_SVG = 18.0  # pixels SVG
            VALUE_OFFSET_SVG = 10.0  # pixels SVG
            
            # Converte offsets SVG para mm
            DIST_LINE_MM = DIST_LINE_SVG * px_to_mm  # ~6.35mm
            VALUE_OFFSET_MM = VALUE_OFFSET_SVG * px_to_mm  # ~3.53mm
            
            self.TITLE_SVG_Y = title_y_mm  # Na verdade já está em mm, mas mantém nome para compatibilidade
            
            # Campos do serviço (coordenadas Y em mm)
            # Primeira linha
            self.FIRST_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y
            self.FIRST_LINE_VALUE_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + VALUE_OFFSET_MM
            
            # Segunda linha
            self.SECOND_LINE_LABEL_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.SECOND_LINE_VALUE_SVG_Y = self.FIRST_LINE_VALUE_SVG_Y + DIST_LINE_MM
            
            # Terceira linha
            self.THIRD_LINE_LABEL_SVG_Y = self.SECOND_LINE_LABEL_SVG_Y + (DIST_LINE_MM * 2)
            self.THIRD_LINE_VALUE_SVG_Y = self.SECOND_LINE_VALUE_SVG_Y + (DIST_LINE_MM * 2)

            # Configurações de fonte
            self.TITLE_FONT_SIZE = 8
            self.TITLE_FONT_STYLE = "B"  # Bold
    
    def dados_servico(self) -> Servico:
        # get_section_y retorna posição Y em mm
        title_y_mm = self.get_section_y("servico")
        return self.Servico(title_y_mm, self.PX_TO_MM)

    def get_servico_title(self) -> TextElement:
        """Retorna o elemento do título do serviço."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.get_section_y("servico"),
            value="SERVIÇO PRESTADO",
            width=None,
            height=5,
            font_size=self.dados_servico().TITLE_FONT_SIZE,
            font_style=self.dados_servico().TITLE_FONT_STYLE,
        )

    def get_servico_cod_trib_nac_label(self) -> TextElement:
        """Retorna o elemento do label 'Código Tributação Nacional'."""
        y = self.dados_servico().SECOND_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="Código Tributação Nacional",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_servico_cod_trib_nac_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Código Tributação Nacional."""
        y = self.dados_servico().SECOND_LINE_VALUE_SVG_Y + 1
        text = "01.07.01 - Suporte técnico em\ninformática, inclusive instalação,\ncon..."
        text_width = 60.0  # Largura em mm para o texto
        
        # Espaçamento entre linhas padrão: 3.0mm (mais compacto que o padrão de 4mm)
        default_line_height = 2.0
        
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=text_width,
            height=default_line_height * len(text.split('\n')),
            font_size=self.value_font_size,
            font_style="",
            line_height=default_line_height,  # Espaçamento entre linhas
        )


    def get_servico_cod_trib_mun_label(self) -> TextElement:
        """Retorna o elemento do label 'Código Tributação Municipal'."""
        y = self.dados_servico().SECOND_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.second_column_margin,
            y=y,
            value="Código Tributação Municipal",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_servico_cod_trib_mun_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Código Tributação Municipal."""
        y = self.dados_servico().SECOND_LINE_VALUE_SVG_Y
        text_width = 60.0  # Largura em mm para o texto
        
        # Espaçamento entre linhas padrão: 3.0mm (mais compacto que o padrão de 4mm)
        default_line_height = 1.0

        times_value = len(value.split('\n')) if value else 1
        
        return TextElement(
            x=self.second_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=text_width,
            height=default_line_height * times_value,
            font_size=self.value_font_size,
            font_style="",
            line_height=default_line_height,  # Espaçamento entre linhas
        )


    def get_servico_local_label(self) -> TextElement:
        """Retorna o elemento do label 'Local'."""
        y = self.dados_servico().SECOND_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value="Local da Prestação",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_servico_local_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Local."""
        y = self.dados_servico().SECOND_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.third_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_servico_pais_label(self) -> TextElement:
        """Retorna o elemento do label 'País'."""
        y = self.dados_servico().SECOND_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value="País da Prestação",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_servico_pais_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do País."""
        y = self.dados_servico().SECOND_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.fourth_column_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_servico_desc_label(self) -> TextElement:
        """Retorna o elemento do label 'Descrição do Serviço'."""
        y = self.dados_servico().THIRD_LINE_LABEL_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value="Descrição do Serviço",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_servico_desc_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da Descrição do Serviço."""
        y = self.dados_servico().THIRD_LINE_VALUE_SVG_Y
        return TextElement(
            x=self.internal_left_margin,
            y=y,
            value=value,  # Será preenchido com dados do XML
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="B",
        )

    class TributacaoMunicipal:
        """Dimensões e posicionamento dos elementos dos dados da tributação municipal."""
        
        def __init__(self, title_y_mm: float, px_to_mm: float):
            # title_y_mm já está em mm (vem de get_section_y)
            # Precisamos converter os offsets SVG para mm
            DIST_LINE_SVG = 22.0  # pixels SVG
            VALUE_OFFSET_SVG = 10.0  # pixels SVG
            
            # Converte offsets SVG para mm
            DIST_LINE_MM = DIST_LINE_SVG * px_to_mm  # ~7.76mm
            VALUE_OFFSET_MM = VALUE_OFFSET_SVG * px_to_mm  # ~3.53mm
            
            self.TITLE_SVG_Y = title_y_mm  # Na verdade já está em mm, mas mantém nome para compatibilidade
            
            # Campos da tributação municipal (coordenadas Y em mm)
            # Primeira linha
            self.FIRST_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y
            self.FIRST_LINE_VALUE_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + VALUE_OFFSET_MM
            
            # Segunda linha
            self.SECOND_LINE_LABEL_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.SECOND_LINE_VALUE_SVG_Y = self.FIRST_LINE_VALUE_SVG_Y + DIST_LINE_MM
            
            # Terceira linha
            self.THIRD_LINE_LABEL_SVG_Y = self.SECOND_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.THIRD_LINE_VALUE_SVG_Y = self.SECOND_LINE_VALUE_SVG_Y + DIST_LINE_MM
            
            # Quarta linha
            self.FOURTH_LINE_LABEL_SVG_Y = self.THIRD_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.FOURTH_LINE_VALUE_SVG_Y = self.THIRD_LINE_VALUE_SVG_Y + DIST_LINE_MM

            # Quinta linha
            self.FIFTH_LINE_LABEL_SVG_Y = self.FOURTH_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.FIFTH_LINE_VALUE_SVG_Y = self.FOURTH_LINE_VALUE_SVG_Y + DIST_LINE_MM
    
    def dados_tributacao_municipal(self) -> TributacaoMunicipal:
        # get_section_y retorna posição Y em mm
        title_y_mm = self.get_section_y("tb_municipal")
        return self.TributacaoMunicipal(title_y_mm, self.PX_TO_MM)


    def get_trib_mun_title(self) -> TextElement:
        """Retorna o elemento do título da tributação municipal."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.get_section_y("tb_municipal"),
            value="TRIBUTAÇÃO MUNICIPAL",
            width=None,
            height=5,
            font_size=self.title_font_size,
            font_style='B',
        )

    def get_trib_mun_issqn_label(self) -> TextElement:
        """Retorna o elemento do label 'ISSQN'."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_municipal().SECOND_LINE_LABEL_SVG_Y,
            value="Tributação do ISSQN",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_mun_issqn_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da tributação do ISSQN."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_municipal().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_mun_pais_result_serv_label(self) -> TextElement:
        """Retorna o elemento do label 'País da Prestação'."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_municipal().SECOND_LINE_LABEL_SVG_Y,
            value="País Resultado da Prestação do Serviço",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_mun_pais_result_serv_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do País Resultado da Prestação do Serviço."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_municipal().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_mun_inc_issqn_label(self) -> TextElement:
        """Retorna o elemento do label 'Incidencia do ISSQN'."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_municipal().SECOND_LINE_LABEL_SVG_Y,
            value="Município de Incidência do ISSQN",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_mun_inc_issqn_value(self, value: str = None) -> TextElement:
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_municipal().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_regime_label(self) -> TextElement:
        """Retorna o elemento do label 'Regime de Apuração Tributária'."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_tributacao_municipal().SECOND_LINE_LABEL_SVG_Y,
            value="Regime Especial de Tributação",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_regime_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Regime de Apuração Tributária."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_tributacao_municipal().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )
    
    def get_trib_tipo_imun_label(self) -> TextElement:
        """Retorna o elemento do label 'Tipo de Imunidade'."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_municipal().THIRD_LINE_LABEL_SVG_Y,
            value="Tipo de Imunidade",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_tipo_imun_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Tipo de Imunidade."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_municipal().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_susp_issqn_label(self) -> TextElement:
        """Retorna o elemento do label 'Suspensão do ISSQN'."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_municipal().THIRD_LINE_LABEL_SVG_Y,
            value="Suspensão da Exigibilidade do ISSQN",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_susp_issqn_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da Suspensão do ISSQN."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_municipal().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_num_proc_susp_issqn_label(self) -> TextElement:
        """Retorna o elemento do label 'Número do Processo Suspensão do ISSQN'."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_municipal().THIRD_LINE_LABEL_SVG_Y,
            value="Número Processo Suspensão",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_num_proc_susp_issqn_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Número do Processo Suspensão do ISSQN."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_municipal().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_benef_mun_label(self) -> TextElement:
        """Retorna o elemento do label 'Benefício Municipal'."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_tributacao_municipal().THIRD_LINE_LABEL_SVG_Y,
            value="Benefício Municipal",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_benef_mun_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Benefício Municipal."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_tributacao_municipal().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_valor_serv_label(self) -> TextElement:
        """Retorna o elemento do label 'Valor do Serviço'."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_municipal().FOURTH_LINE_LABEL_SVG_Y,
            value="Valor do Serviço",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_valor_serv_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Valor do Serviço."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_municipal().FOURTH_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_desc_incond_label(self) -> TextElement:
        """Retorna o elemento do label 'Desconto Incondicionada do Serviço'."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_municipal().FOURTH_LINE_LABEL_SVG_Y,
            value="Desconto Incondicionado",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_desc_incond_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Desconto Incondicionado."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_municipal().FOURTH_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_total_deduc_label(self) -> TextElement:
        """Retorna o elemento do label 'Total de Desconto'."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_municipal().FOURTH_LINE_LABEL_SVG_Y,
            value="Total Deduções/Reduções",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_total_deduc_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Total de Desconto."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_municipal().FOURTH_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_total_bm_label(self) -> TextElement:
        """Retorna o elemento do label 'Cálculo do BM'."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_tributacao_municipal().FOURTH_LINE_LABEL_SVG_Y,
            value="Cálculo do BM",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_total_bm_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Cálculo do BM."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_tributacao_municipal().FOURTH_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_bc_issqn_label(self) -> TextElement:
        """Retorna o elemento do label 'Base de Cálculo do ISSQN'."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_municipal().FIFTH_LINE_LABEL_SVG_Y,
            value="BC ISSQN",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_bc_issqn_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da Base de Cálculo do ISSQN."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_municipal().FIFTH_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_aliq_label(self) -> TextElement:
        """Retorna o elemento do label 'Alíquota do ISSQN'."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_municipal().FIFTH_LINE_LABEL_SVG_Y,
            value="Aliquota ISSQN",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_aliq_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da Alíquota do ISSQN."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_municipal().FIFTH_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_ret_issqn_label(self) -> TextElement:
        """Retorna o elemento do label 'Retenção do ISSQN'."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_municipal().FIFTH_LINE_LABEL_SVG_Y,
            value="Retenção ISSQN",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_ret_issqn_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da Retenção do ISSQN."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_municipal().FIFTH_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_valor_issqn_apurado_label(self) -> TextElement:
        """Retorna o elemento do label 'Valor do ISSQN Apurado'."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_tributacao_municipal().FIFTH_LINE_LABEL_SVG_Y,
            value="ISSQN Apurado",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_valor_issqn_apurado_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Valor do ISSQN Apurado."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_tributacao_municipal().FIFTH_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    class TributacaoFederal:
        """Dimensões e posicionamento dos elementos dos dados da tributação federal."""
        
        def __init__(self, title_y_mm: float, px_to_mm: float):
            # title_y_mm já está em mm (vem de get_section_y)
            # Precisamos converter os offsets SVG para mm
            DIST_LINE_SVG = 24.0  # pixels SVG
            VALUE_OFFSET_SVG = 10.0  # pixels SVG
            
            # Converte offsets SVG para mm
            DIST_LINE_MM = DIST_LINE_SVG * px_to_mm  # ~8.47mm
            VALUE_OFFSET_MM = VALUE_OFFSET_SVG * px_to_mm  # ~3.53mm
            
            self.TITLE_SVG_Y = title_y_mm  # Na verdade já está em mm, mas mantém nome para compatibilidade
            
            # Campos da tributação federal (coordenadas Y em mm)
            # Primeira linha
            self.FIRST_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y
            self.FIRST_LINE_VALUE_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + VALUE_OFFSET_MM
            
            # Segunda linha
            self.SECOND_LINE_LABEL_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.SECOND_LINE_VALUE_SVG_Y = self.FIRST_LINE_VALUE_SVG_Y + DIST_LINE_MM
            
            # Terceira linha
            self.THIRD_LINE_LABEL_SVG_Y = self.SECOND_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.THIRD_LINE_VALUE_SVG_Y = self.SECOND_LINE_VALUE_SVG_Y + DIST_LINE_MM

            # Configurações de fonte
            self.TITLE_FONT_SIZE = 10
            self.TITLE_FONT_STYLE = "B"  # Bold
    
    def dados_tributacao_federal(self) -> TributacaoFederal:
        # get_section_y retorna posição Y em mm
        title_y_mm = self.get_section_y("trib_federal")
        return self.TributacaoFederal(title_y_mm, self.PX_TO_MM)


    def get_trib_federal_title(self) -> TextElement:
        """Retorna o elemento do título da seção Tributação Federal."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.get_section_y("trib_federal"),
            value="TRIBUTAÇÃO FEDERAL",
            width=None,
            height=5,
            font_size=self.title_font_size,
            font_style='B',
        )
    
    def get_trib_federal_irrf_label(self) -> TextElement:
        """Retorna o elemento do label do IRRF."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_federal().SECOND_LINE_LABEL_SVG_Y,
            value="IRRF",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_federal_irrf_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do IRRF."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_federal().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )
    
    def get_trib_federal_cp_label(self) -> TextElement:
        """Retorna o elemento do label do CP."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_federal().SECOND_LINE_LABEL_SVG_Y,
            value="CP",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_federal_cp_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do CP."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_federal().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_federal_csll_label(self) -> TextElement:
        """Retorna o elemento do label do CSLL."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_federal().SECOND_LINE_LABEL_SVG_Y,
            value="CSLL",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_federal_csll_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do CSLL."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_federal().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_federal_pis_label(self) -> TextElement:
        """Retorna o elemento do label do PIS."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_federal().THIRD_LINE_LABEL_SVG_Y,
            value="PIS",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_federal_pis_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do PIS."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_tributacao_federal().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_federal_cofins_label(self) -> TextElement:
        """Retorna o elemento do label do COFINS."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_federal().THIRD_LINE_LABEL_SVG_Y,
            value="COFINS",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_federal_cofins_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do COFINS."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_tributacao_federal().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_federal_ret_pis_cofins_label(self) -> TextElement:
        """Retorna o elemento do label do Retencao do PIS e COFINS."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_federal().THIRD_LINE_LABEL_SVG_Y,
            value="Retenção do PIS/COFINS",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )
    
    def get_trib_federal_ret_pis_cofins_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Retorno do PIS e COFINS."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_tributacao_federal().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_trib_federal_total_label(self) -> TextElement:
        """Retorna o elemento do label do Total."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_tributacao_federal().THIRD_LINE_LABEL_SVG_Y,
            value="TOTAL TRIBUTAÇÃO FEDERAL",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_trib_federal_total_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Total."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_tributacao_federal().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    class TotalNFSE:
        """Dimensões e posicionamento dos elementos dos dados dos totais."""
        
        def __init__(self, title_y_mm: float, px_to_mm: float):
            # title_y_mm já está em mm (vem de get_section_y)
            # Precisamos converter os offsets SVG para mm
            DIST_LINE_SVG = 24.0  # pixels SVG
            VALUE_OFFSET_SVG = 10.0  # pixels SVG
            FIRST_LINE_OFFSET_SVG = 8.0  # pixels SVG
            
            # Converte offsets SVG para mm
            DIST_LINE_MM = DIST_LINE_SVG * px_to_mm  # ~8.47mm
            VALUE_OFFSET_MM = VALUE_OFFSET_SVG * px_to_mm  # ~3.53mm
            FIRST_LINE_OFFSET_MM = FIRST_LINE_OFFSET_SVG * px_to_mm  # ~2.82mm
            
            self.TITLE_SVG_Y = title_y_mm  # Na verdade já está em mm, mas mantém nome para compatibilidade
            
            # Campos dos totais (coordenadas Y em mm)
            # Primeira linha
            self.FIRST_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y - FIRST_LINE_OFFSET_MM
            self.FIRST_LINE_VALUE_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + VALUE_OFFSET_MM
            
            # Segunda linha
            self.SECOND_LINE_LABEL_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.SECOND_LINE_VALUE_SVG_Y = self.FIRST_LINE_VALUE_SVG_Y + DIST_LINE_MM
            
            # Terceira linha
            self.THIRD_LINE_LABEL_SVG_Y = self.SECOND_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.THIRD_LINE_VALUE_SVG_Y = self.SECOND_LINE_VALUE_SVG_Y + DIST_LINE_MM

            # Configurações de fonte
            self.TITLE_FONT_SIZE = 10
            self.TITLE_FONT_STYLE = "B"  # Bold
    
    def dados_total_nfse(self) -> TotalNFSE:
        # get_section_y retorna posição Y em mm
        title_y_mm = self.get_section_y("valor_nfse")
        return self.TotalNFSE(title_y_mm, self.PX_TO_MM)

    def get_total_nfse_title(self) -> TextElement:
        """Retorna o elemento do título do Total."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.get_section_y("valor_nfse"),
            value="TOTAL DA NFS-e",
            width=None,
            height=4,
            font_size=self.title_font_size,
            font_style='B',
        )

    def get_total_nfse_vl_servico_label(self) -> TextElement:
        """Retorna o elemento do label do Valor do Serviço."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_total_nfse().SECOND_LINE_LABEL_SVG_Y,
            value="Valor do Serviço",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_total_nfse_vl_servico_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Valor do Serviço."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_total_nfse().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_total_nfse_desc_cond_label(self) -> TextElement:
        """Retorna o elemento do label do Desconto Condicionado."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_total_nfse().SECOND_LINE_LABEL_SVG_Y,
            value="Desconto Condicionado",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_total_nfse_desc_cond_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Desconto Condicionado."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_total_nfse().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_total_nfse_desc_incond_label(self) -> TextElement:
        """Retorna o elemento do label do Desconto Incondicionado."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_total_nfse().SECOND_LINE_LABEL_SVG_Y,
            value="Desconto Incondicionado",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_total_nfse_desc_incond_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Desconto Incondicionado."""
        return TextElement(
            x=self.third_column_margin,
            y=self.dados_total_nfse().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_total_nfse_issqn_label(self) -> TextElement:
        """Retorna o elemento do label do ISSQN."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_total_nfse().SECOND_LINE_LABEL_SVG_Y,
            value="ISSQN Retido",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_total_nfse_issqn_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do ISSQN."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_total_nfse().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_total_nfse_irrf_label(self) -> TextElement:
        """Retorna o elemento do label do IRRF."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_total_nfse().THIRD_LINE_LABEL_SVG_Y,
            value="IRRF, CP,CSLL - Retidos",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_total_nfse_irrf_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do IRRF."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.dados_total_nfse().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_total_nfse_pis_label(self) -> TextElement:
        """Retorna o elemento do label do PIS."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_total_nfse().THIRD_LINE_LABEL_SVG_Y,
            value="PIS/COFINS Retidos",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_total_nfse_pis_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do PIS."""
        return TextElement(
            x=self.second_column_margin,
            y=self.dados_total_nfse().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_total_nfse_liquido_label(self) -> TextElement:
        """Retorna o elemento do label do Liquido."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_total_nfse().THIRD_LINE_LABEL_SVG_Y,
            value="Valor Líquido da NFS-e",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_total_nfse_liquido_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor do Liquido."""
        return TextElement(
            x=self.fourth_column_margin,
            y=self.dados_total_nfse().THIRD_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    class Totais:
        """Dimensões e posicionamento dos elementos dos totais."""
        
        def __init__(self, title_y_mm: float, px_to_mm: float):
            # title_y_mm já está em mm (vem de get_section_y)
            # Precisamos converter os offsets SVG para mm
            DIST_LINE_SVG = 18.0  # pixels SVG
            VALUE_OFFSET_SVG = 10.0  # pixels SVG
            
            # Converte offsets SVG para mm
            DIST_LINE_MM = DIST_LINE_SVG * px_to_mm  # ~6.35mm
            VALUE_OFFSET_MM = VALUE_OFFSET_SVG * px_to_mm  # ~3.53mm
            
            self.TITLE_SVG_Y = title_y_mm  # Na verdade já está em mm, mas mantém nome para compatibilidade
            
            # Campos dos totais (coordenadas Y em mm)
            # Primeira linha
            self.FIRST_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y
            self.FIRST_LINE_VALUE_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + VALUE_OFFSET_MM
            
            # Segunda linha
            self.SECOND_LINE_LABEL_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.SECOND_LINE_VALUE_SVG_Y = self.FIRST_LINE_VALUE_SVG_Y + DIST_LINE_MM

            # Configurações de fonte
            self.TITLE_FONT_SIZE = 10
            self.TITLE_FONT_STYLE = "B"  # Bold
    
    def dados_totais(self) -> Totais:
        # get_section_y retorna posição Y em mm
        title_y_mm = self.get_section_y("totais")
        return self.Totais(title_y_mm, self.PX_TO_MM)

    def get_totais_title(self) -> TextElement:
        """Retorna o elemento do título dos totais."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.get_section_y("totais"),
            value="TOTAIS APROXIMADOS DOS TRIBUTOS",
            width=None,
            height=4,
            font_size=self.title_font_size,
            font_style='B',
        )

    def get_totais_federais_label(self) -> TextElement:
        """Retorna o elemento do label dos totais federais."""
        return TextElement(
            x=self.internal_left_margin + 35,
            y=self.dados_totais().SECOND_LINE_LABEL_SVG_Y,
            value="Federais",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_totais_federais_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor dos totais federais."""
        return TextElement(
            x=self.internal_left_margin + 35,
            y=self.dados_totais().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_totais_estaduais_label(self) -> TextElement:
        """Retorna o elemento do label dos totais estaduais."""
        return TextElement(
            x=self.second_column_margin + 40,
            y=self.dados_totais().SECOND_LINE_LABEL_SVG_Y,
            value="Estaduais",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_totais_estaduais_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor dos totais estaduais."""
        return TextElement(
            x=self.second_column_margin + 40,
            y=self.dados_totais().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    def get_totais_municipais_label(self) -> TextElement:
        """Retorna o elemento do label dos totais municipais."""
        return TextElement(
            x=self.third_column_margin + 45,
            y=self.dados_totais().SECOND_LINE_LABEL_SVG_Y,
            value="Municipais",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style="B",
        )

    def get_totais_municipais_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor dos totais municipais."""
        return TextElement(
            x=self.third_column_margin + 45,
            y=self.dados_totais().SECOND_LINE_VALUE_SVG_Y,
            value=value,
            width=None,
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )

    class InfoComplementar:
        """Dimensões e posicionamento dos elementos das informações complementares."""
        
        def __init__(self, title_y_mm: float, px_to_mm: float):
            # title_y_mm já está em mm (vem de get_section_y)
            # Precisamos converter os offsets SVG para mm
            DIST_LINE_SVG = 18.0  # pixels SVG
            VALUE_OFFSET_SVG = 10.0  # pixels SVG
            
            # Converte offsets SVG para mm
            DIST_LINE_MM = DIST_LINE_SVG * px_to_mm  # ~6.35mm
            VALUE_OFFSET_MM = VALUE_OFFSET_SVG * px_to_mm  # ~3.53mm
            
            self.TITLE_SVG_Y = title_y_mm  # Na verdade já está em mm, mas mantém nome para compatibilidade
            
            # Campos das informações complementares (coordenadas Y em mm)
            # Primeira linha
            self.FIRST_LINE_LABEL_SVG_Y = self.TITLE_SVG_Y
            self.FIRST_LINE_VALUE_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + VALUE_OFFSET_MM
            
            # Segunda linha
            self.SECOND_LINE_LABEL_SVG_Y = self.FIRST_LINE_LABEL_SVG_Y + DIST_LINE_MM
            self.SECOND_LINE_VALUE_SVG_Y = self.FIRST_LINE_VALUE_SVG_Y + DIST_LINE_MM

            # Configurações de fonte
            self.TITLE_FONT_SIZE = 10
            self.TITLE_FONT_STYLE = "B"  # Bold
    
    def dados_info_complementar(self) -> InfoComplementar:
        # get_section_y retorna posição Y em mm
        title_y_mm = self.get_section_y("info_complementar")
        return self.InfoComplementar(title_y_mm, self.PX_TO_MM)

    def get_info_complementar_title(self) -> TextElement:
        """Retorna o elemento do título da seção de informações complementares."""
        return TextElement(
            x=self.internal_left_margin,
            y=self.get_section_y("info_complementar"),
            value="INFORMAÇÕES COMPLEMENTARES",
            width=None,
            height=4,
            font_size=self.label_font_size,
            font_style='B',
        )

    def get_info_complementar_value(self, value: str = None) -> TextElement:
        """Retorna o elemento do valor da seção de informações complementares."""

        x = self.internal_left_margin
        return TextElement(
            x=x,
            y=self.dados_info_complementar().SECOND_LINE_LABEL_SVG_Y,
            value=value,
            width=self.epw - (x - self.internal_left_margin),
            height=4,
            font_size=self.value_font_size,
            font_style="",
        )


    class HorizontalLines:
        """Posições Y das linhas horizontais (Vector) no SVG."""
        
        # Hashmap com as posições Y de cada Vector no SVG
        # Valores extraídos do SVG: coordenadas Y de cada path Vector
        VECTOR_POSITIONS = {
            "info_complementar": 780.0,
            "totais": 740.0,        # Linha antes de "Totais-Tributos"
            "valor_nfse": 680.0,    # Linha antes de "Valor-NFSE"
            "trib_federal": 610.0,  # Linha antes de "Tributacao-Federal"
            "tb_municipal": 500.0,  # Linha antes de "Tributacao-Municipal"
            "servico": 425.0,         # Linha antes de "Servico"
            "intermediario": 350.0, # Linha antes de "Intermediario"
            "tomador": 270.0,      # Linha antes de "Tomador"
            "emitente": 180.0,        # Linha antes de "Emitente"
            "info_nota": 100.0,       # Linha antes de "Info-Nota"
        }
    
    def get_horizontal_line(self, line_name: str) -> LineElement:
        """
        Retorna o elemento de linha horizontal baseado no nome.
        Usa o PositionManager para obter a posição Y.
        
        Args:
            line_name: Nome da linha (ex: "totais", "valor_nfse", "info_nota", etc.)
        
        Returns:
            LineElement com posição e dimensões da linha
            
        Raises:
            ValueError: Se o nome da linha não for encontrado
        """
        # Usa o PositionManager para obter a posição Y
        try:
            y_mm = self.get_section_y(line_name)
        except ValueError:
            # Fallback: tenta usar VECTOR_POSITIONS se não estiver no PositionManager
            if line_name not in self.HorizontalLines.VECTOR_POSITIONS:
                available = ", ".join(self.HorizontalLines.VECTOR_POSITIONS.keys())
                raise ValueError(
                    f"Linha '{line_name}' não encontrada. "
                    f"Linhas disponíveis: {available}"
                )
            y_svg = self.HorizontalLines.VECTOR_POSITIONS[line_name]
            y_mm = self._svg_to_pdf_y(y_svg)

        print(f"line_name: {line_name}, y_mm: {y_mm}")
        
        # Retorna o elemento de linha
        return LineElement(
            x=self.left_margin + (self.left_margin/2),
            y=y_mm,
            width=self.epw - self.left_margin,
            value=line_name
        )

    
