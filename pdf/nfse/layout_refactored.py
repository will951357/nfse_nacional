"""
Módulo simplificado para cálculo de posições dinâmicas das seções da NFSe.
Usa 3 layouts fixos (hardcoded) para os 3 cenários possíveis.
"""

from typing import Dict, List, Optional, Literal

# Fator de conversão: SVG tem área útil ~595x842px, PDF A4 é 210x297mm
PX_TO_MM = 210 / 595  # ≈ 0.3529
BASE_HEIGHT = 40.0 * PX_TO_MM
# Offset do SVG (a borda do SVG começa em x=65, y=65)
SVG_OFFSET_Y = 65

# Posições Y no SVG (do VECTOR_POSITIONS do layout.py)
# Valores originais quando TODAS as seções existem
SVG_POSITIONS_ALL = {
    "info_nota": 100.0,
    "emitente": 180.0,
    "tomador": 270.0,
    "intermediario": 350.0,
    "servico": 425.0,
    "tb_municipal": 500.0,
    "trib_federal": 610.0,
    "valor_nfse": 680.0,
    "totais": 740.0,
    "info_complementar": 780.0,
}

SVG_HEIGHTS_ALL = {
    "info_nota": 80.0,
    "emitente": 90.0,
    "tomador": 80.0,
    "intermediario": 75.0,
    "servico": 75.0,
    "tb_municipal": 110.0,
    "trib_federal": 70.0,
    "valor_nfse": 60.0,
    "totais": 40.0,
    "info_complementar": 50.0,
}

ORDEM_SECOES = [
        "info_nota", "emitente", "tomador", "intermediario", 
        "servico", "tb_municipal", "trib_federal", "valor_nfse", 
        "totais", "info_complementar"
    ]

def _svg_to_pdf_y(svg_y: float, top_margin: float) -> float:
    """Converte coordenada Y do SVG para PDF em mm."""
    return top_margin + (svg_y - SVG_OFFSET_Y) * PX_TO_MM

def _pdf_to_svg_y(pdf_y: float, top_margin: float) -> float:
    """Converte coordenada Y do PDF para SVG em px."""
    return SVG_OFFSET_Y + (pdf_y - top_margin) / PX_TO_MM

def _calculate_heights(svg_positions: Dict[str, float]) -> Dict[str, float]:
    """Calcula alturas baseadas nas diferenças entre posições consecutivas."""
    sections_order = [
        "info_nota", "emitente", "tomador", "intermediario", 
        "servico", "tb_municipal", "trib_federal", "valor_nfse", 
        "totais", "info_complementar"
    ]
    
    heights = {}
    for i, section in enumerate(sections_order):
        if i + 1 < len(sections_order):
            next_section = sections_order[i + 1]
            if section in svg_positions and next_section in svg_positions:
                heights[section] = (svg_positions[next_section] - svg_positions[section]) * PX_TO_MM
            else:
                # Seção não existe ou próxima não existe
                heights[section] = 0.0
        else:
            # Última seção
            heights[section] = 40.0 * PX_TO_MM
    
    return heights

# ==================== LAYOUTS FIXOS ====================

def _create_layout_all(top_margin: float, left_margin: float) -> Dict[str, Dict[str, float]]:
    """Layout quando tomador E intermediário existem (todos existem)."""
    positions = {}
    
    # Header (sempre começa em top_margin)
    header_height = (SVG_POSITIONS_ALL["info_nota"] - 0.0) * PX_TO_MM
    positions["header"] = {
        'x': left_margin,
        'y': top_margin,
        'height': header_height,
    }
    
    # Demais seções usando posições originais
    heights = _calculate_heights(SVG_POSITIONS_ALL)
    for section, svg_y in SVG_POSITIONS_ALL.items():
        positions[section] = {
            'x': left_margin,
            'y': _svg_to_pdf_y(svg_y, top_margin),
            'height': heights.get(section, 0.0),
        }
    
    return positions

def _create_general_layout(top_margin: float, left_margin: float, exclude_sections: List[str]) -> Dict[str, Dict[str, float]]:
    """Layout geral para qualquer combinação de seções."""
    positions = {}

    base_position = 100.0
    base_height = 80.0

    next_y = 0.0
    for i, section in enumerate(ORDEM_SECOES):
        if i == 0:
            height = base_height
            y = base_position

            positions[section] = {
                'x': left_margin,
                'y': y,
                'height': height,
            }

            next_y = y + height
            continue

        if section not in exclude_sections:
            height = SVG_HEIGHTS_ALL[section]
        else:
            height = BASE_HEIGHT

        y = next_y

        positions[section] = {
            'x': left_margin,
            'y': y,
            'height': height,
        }

        next_y = y + height

    header_height = (positions["info_nota"]["y"] - 0.0) * PX_TO_MM
    positions["header"] = {
        'x': left_margin,
        'y': top_margin,
        'height': header_height,
    }

    for section, pos in positions.items():
        positions[section]['y'] = _svg_to_pdf_y(pos['y'], top_margin)

    print(positions)
    
    return positions
    


def _create_layout_tomador_sem_intermediario(top_margin: float, left_margin: float) -> Dict[str, Dict[str, float]]:
    """Layout quando tomador existe mas intermediário NÃO existe."""
    positions = {}
    
    # Quando intermediário não existe, servico e todas as seções seguintes são deslocadas para cima
    # Altura do intermediário: 350.0 - 270.0 = 80px SVG = ~28.24mm
    # Servico original: 425.0 -> novo: 350.0 (deslocamento de -75px)
    # Todas as seções após intermediário são deslocadas de -75px
    
    base_position = 100.0
    base_height = 80.0

    next_y = 0.0
    for i, section in enumerate(ORDEM_SECOES):
        if i == 0:
            height = base_height
            y = base_position

            positions[section] = {
                'x': left_margin,
                'y': y,
                'height': height,
            }

            next_y = y + height
            continue

        if section in SVG_HEIGHTS_ALL:
            height = SVG_HEIGHTS_ALL[section]
        else:
            height = BASE_HEIGHT

        y = next_y

        positions[section] = {
            'x': left_margin,
            'y': y,
            'height': height,
        }

        next_y = y + height

    svg_positions = {
        "info_nota": {
            "y": 100.0,
            "height": 80.0
        },
        "emitente": {
            "y": 180.0,
            "height": 90.0
        },
        "tomador": {
            "y": 270.0,
            "height": 80.0
        },
        "intermediario": {
            "y": 350.0,
            "height": BASE_HEIGHT
        },
        "servico": {
            "y": 350.0 + BASE_HEIGHT,
            "height": 75.0
        },
        "tb_municipal": {
            "y": 350.0 + BASE_HEIGHT + 75.0,
            "height": 110.0
        },
        "trib_federal": {
            "y": 350.0 + BASE_HEIGHT + 75.0 + 110.0,
            "height": 70.0
        },
        "valor_nfse": {
            "y": 350.0 + BASE_HEIGHT + 75.0 + 110.0 + 70.0,
            "height": 60.0
        },
        "totais": {
            "y":  350.0 + BASE_HEIGHT + 75.0 + 110.0 + 70.0 + 60.0,
            "height": 40.0
        },
        "info_complementar": {
            "y": 350.0 + BASE_HEIGHT + 75.0 + 110.0 + 70.0 + 60.0 + 40.0,
            "height": 50.0
        },
    }
    
    # Header
    header_height = (svg_positions["info_nota"]["y"] - 0.0) * PX_TO_MM
    positions["header"] = {
        'x': left_margin,
        'y': top_margin,
        'height': header_height,
    }
    
    # Seções que existem
    for section, svg_data in svg_positions.items():
        positions[section] = {
            'x': left_margin,
            'y': _svg_to_pdf_y(svg_data["y"], top_margin),
            'height': svg_data["height"] * PX_TO_MM,
        }
    
    return positions

def _create_layout_intermediario_sem_tomador(top_margin: float, left_margin: float) -> Dict[str, Dict[str, float]]:
    """Layout quando intermediário existe mas tomador NÃO existe."""
    positions = {}
    
    # Quando tomador não existe, intermediário e todas as seções seguintes são deslocadas para cima
    # Altura do tomador: 270.0 - 180.0 = 90px SVG = ~31.76mm
    # Intermediário original: 350.0 -> novo: 270.0 (deslocamento de -80px)
    # Todas as seções após tomador são deslocadas de -80px
    
    svg_positions = {
        "info_nota": {
            "y": 100.0,
            "height": 80.0
        },
        "emitente": {
            "y": 180.0,
            "height": 90.0
        },
        "tomador": {
            "y": 270.0,
            "height": BASE_HEIGHT
        },
        "intermediario": {
            "y": 270.0 + BASE_HEIGHT,
            "height": 75.0
        },
        "servico": {
            "y": 270.0 + BASE_HEIGHT + 75.0,
            "height": 75.0
        },
        "tb_municipal": {
            "y": 270.0 + BASE_HEIGHT + 75.0 + 75.0,
            "height": 110.0
        },
        "trib_federal": {
            "y": 270.0 + BASE_HEIGHT + 75.0 + 75.0 + 110.0,
            "height": 70.0
        },
        "valor_nfse": {
            "y": 270.0 + BASE_HEIGHT + 75.0 + 75.0 + 110.0 + 70.0,
            "height": 60.0
        },
        "totais": {
            "y":  270.0 + BASE_HEIGHT + 75.0 + 75.0 + 110.0 + 70.0 + 60.0,
            "height": 40.0
        },
        "info_complementar": {
            "y": 270.0 + BASE_HEIGHT + 75.0 + 75.0 + 110.0 + 70.0 + 60.0 + 40.0,
            "height": 50.0
        },
    }
    
    # Header
    header_height = (svg_positions["info_nota"]["y"] - 0.0) * PX_TO_MM
    positions["header"] = {
        'x': left_margin,
        'y': top_margin,
        'height': header_height,
    }
    
    # Seções que existem
    for section, svg_data in svg_positions.items():
        positions[section] = {
            'x': left_margin,
            'y': _svg_to_pdf_y(svg_data["y"], top_margin),
            'height': svg_data["height"] * PX_TO_MM,
        }
    
    return positions

def _recalculate_positions(sections: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """Recalcula as posições das seções."""
    for section, data in sections.items():
        idx = ORDEM_SECOES.index(section)

class PositionManager:
    
    """
    Gerencia o cálculo de posições das seções usando 3 layouts fixos.
    
    Cenários:
    1. tomador=True, intermediario=True -> Layout completo (todos existem)
    2. tomador=True, intermediario=False -> Layout sem intermediário
    3. tomador=False, intermediario=True -> Layout sem tomador
    """
    
    def __init__(self, left_margin: float, top_margin: float, effective_page_width: float):
        """
        Inicializa o gerenciador de posições.
        
        Args:
            left_margin: Margem esquerda em mm
            top_margin: Margem superior em mm
            effective_page_width: Largura efetiva da página em mm
        """
        self.left_margin = left_margin
        self.internal_left_margin = left_margin + (left_margin / 2)
        self.top_margin = top_margin
        self.epw = effective_page_width
        self.positions = {}
    
    def calculate_positions(
        self, 
        exclude_sections: List[str] = []
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcula as posições usando um dos 3 layouts fixos.
        
        Args:
            tomador_exists: Se tomador existe no XML
            intermediario_exists: Se intermediário existe no XML
        
        Returns:
            Dicionário com {seção: {x, y, height}}
        """
        return self._create_general_layout(self.top_margin, self.left_margin, exclude_sections)

        
    def _create_general_layout(self, top_margin: float, left_margin: float, exclude_sections: List[str]) -> Dict[str, Dict[str, float]]:
        """Layout geral para qualquer combinação de seções."""

        base_position = 100.0
        base_height = 80.0

        next_y = 0.0
        for i, section in enumerate(ORDEM_SECOES):
            if i == 0:
                height = base_height
                y = base_position

                self.positions[section] = {
                    'x': left_margin,
                    'y': y,
                    'height': height,
                }

                next_y = y + height
                continue

            if section not in exclude_sections:
                height = SVG_HEIGHTS_ALL[section]
            else:
                height = BASE_HEIGHT

            y = next_y

            self.positions[section] = {
                'x': left_margin,
                'y': y,
                'height': height,
            }

            next_y = y + height

        header_height = (self.positions["info_nota"]["y"] - 0.0) * PX_TO_MM
        self.positions["header"] = {
            'x': left_margin,
            'y': top_margin,
            'height': header_height,
        }

        for section, pos in self.positions.items():
            self.positions[section]['y'] = _svg_to_pdf_y(pos['y'], top_margin)
            # Converte altura de pixels SVG para mm (exceto header que já está em mm)
            if section != 'header':
                self.positions[section]['height'] = pos['height'] * PX_TO_MM
        
        return self.positions

    def _recalculate_positions(self, sections: dict[str, float]):
        
        print('Lista original ', self.positions)
        print('Seções a serem recalculadas ', sections)
        
        for section, data in sections.items():
            idx = ORDEM_SECOES.index(section)

            curr_y = self.positions[section]['y']
            curr_height = self.positions[section]['height']

            # Atualiza apenas a altura da seção atual (data já está em mm)
            self.positions[section]['height'] = curr_height + data
            
            # Recalcula posições das seções seguintes
            # Começa da posição final da seção atual (tudo em mm)
            next_y = curr_y + self.positions[section]['height']

            for i in range(idx + 1, len(ORDEM_SECOES)):
                section_name = ORDEM_SECOES[i]
                self.positions[section_name]['y'] = next_y
                next_y = next_y + self.positions[section_name]['height']

        print('Lista recalculada ', self.positions)


# ==================== EXEMPLO DE USO ====================

if __name__ == "__main__":
    # Exemplo de uso
    pm = PositionManager(left_margin=3.0, top_margin=3.0, effective_page_width=204.0)
    
    print("=" * 70)
    print("CENÁRIO 1: Tomador E Intermediário existem (todos existem)")
    print("=" * 70)
    positions1 = pm.calculate_positions(tomador_exists=True, intermediario_exists=True)
    for section, pos in positions1.items():
        y = pos['y']
        height = pos['height']
        print(f"  {section:20s} y={y:7.2f}mm  altura={height:7.2f}mm")
    
    print("\n" + "=" * 70)
    print("CENÁRIO 2: Tomador existe, Intermediário NÃO existe")
    print("=" * 70)
    positions2 = pm.calculate_positions(tomador_exists=True, intermediario_exists=False)
    for section, pos in positions2.items():
        y = pos['y']
        height = pos['height']
        print(f"  {section:20s} y={y:7.2f}mm  altura={height:7.2f}mm")
    
    print("\n" + "=" * 70)
    print("CENÁRIO 3: Intermediário existe, Tomador NÃO existe")
    print("=" * 70)
    positions3 = pm.calculate_positions(tomador_exists=False, intermediario_exists=True)
    for section, pos in positions3.items():
        y = pos['y']
        height = pos['height']
        print(f"  {section:20s} y={y:7.2f}mm  altura={height:7.2f}mm")
