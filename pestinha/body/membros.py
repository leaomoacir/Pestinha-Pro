"""
MEMBROS - bracinhos e perninhas animados do pet.

Desenha membros articulados e expressivos ao redor do corpo:
- Perninhas proporcionais com ciclo de caminhada bípede natural (ritmo suave, sola cravada no chão).
- Bracinhos com gestos expressivos (andar, digitar no notebook, comemorar, acenar, cruzar braços).
"""

import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

BODY_W, BODY_H = 120, 90

# Altura da sola dos sapatos em repouso (pixel-perfect no topo da barra de tarefas: y = 45.0)
CHAO_SOLA_Y = 45.0
PE_RAIO_X, PE_RAIO_Y = 14.0, 6.0


def draw_legs(p: QPainter, aparencia, walk_phase: float, is_walking: bool, grounded: bool,
              sitting: bool = False, body_offset_y: float = -14.0):
    """
    Desenha os pezinhos e perninhas proporcionais saindo da base do corpo.
    Avança com ritmo bípede orgânico e sola perfeitamente assentada no topo da barra de início.
    """
    if sitting:
        # Quando sentado no notebook, os pezinhos ficam recolhidos
        return

    p.save()
    p.setRenderHint(QPainter.Antialiasing)

    cor_haste = aparencia.casca
    cor_borda = aparencia.moldura
    cor_pe = aparencia.casca

    pen_haste = QPen(cor_borda, 6.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    pen_pe = QPen(cor_borda, 2.5)

    base_perna_y = body_offset_y + 38.0  # ~24.0 px: ancoragem dentro da casca inferior do corpo
    pe_centro_repouso_y = CHAO_SOLA_Y - PE_RAIO_Y  # 39.0 px: base do sapatinho encosta em 45.0 (barra de tarefas)

    # Âncoras das duas pernas (esquerda e direita)
    anchors = [(-22.0, 1), (22.0, -1)]

    for i, (orig_x, dir_fase) in enumerate(anchors):
        if not grounded:
            # No ar: perninhas recolhidas balançando suavemente
            dx = dir_fase * 3.0
            dy = -4.0 + math.sin(time.monotonic() * 4.0 + i) * 2.0
            rot = dir_fase * 10.0
        elif is_walking:
            # Caminhada bípede cartunesca com passada suave e cadenciada
            fase = walk_phase + (0.0 if i == 0 else math.pi)

            # Passada horizontal
            dx = math.sin(fase) * 12.0

            # Pé de apoio encosta exatamente no chão (sola em CHAO_SOLA_Y = 45.0).
            # Pé que avança levanta em arco suave (máximo de 6.5px do chão).
            levantamento = max(0.0, -math.cos(fase)) * 6.5
            dy = -levantamento

            # Rotação suave do pé acompanhando a passada
            rot = math.sin(fase) * 12.0
        else:
            # Parado: ambos os pés repousam firmemente no topo da barra de tarefas
            dx = 0.0
            dy = 0.0
            rot = 0.0

        pe_x = orig_x + dx
        pe_y = pe_centro_repouso_y + dy

        # Desenha a perninha (haste cilíndrica robusta)
        p.setPen(pen_haste)
        p.drawLine(QPointF(orig_x, base_perna_y), QPointF(pe_x, pe_y - PE_RAIO_Y + 1.0))

        # Desenha o sapatinho com sola e detalhes
        p.save()
        p.translate(pe_x, pe_y)
        p.rotate(rot)

        # Corpo do sapatinho arredondado
        p.setPen(pen_pe)
        p.setBrush(cor_pe)
        p.drawRoundedRect(QRectF(-PE_RAIO_X, -PE_RAIO_Y, PE_RAIO_X * 2, PE_RAIO_Y * 2), 5, 5)

        # Sola de borracha com cor da moldura
        p.setPen(QPen(cor_borda, 2.2, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(-PE_RAIO_X + 2, PE_RAIO_Y - 0.5), QPointF(PE_RAIO_X - 2, PE_RAIO_Y - 0.5))

        # Detalhe do bico do sapatinho
        p.setPen(QPen(cor_borda, 1.5))
        p.drawArc(QRectF(-PE_RAIO_X + 3, -PE_RAIO_Y + 1, 6, 6), 45 * 16, 90 * 16)
        p.restore()

    p.restore()


def draw_arms(p: QPainter, aparencia, gesture: str, walk_phase: float, is_walking: bool,
              now: float = None, body_offset_y: float = -14.0):
    """
    Desenha os bracinhos e mãozinhas nas laterais do corpo com gestos orgânicos.
    Renderizados na frente do corpo para gestos expressivos e digitação.
    """
    now = time.monotonic() if now is None else now

    p.save()
    p.setRenderHint(QPainter.Antialiasing)

    cor_borda = aparencia.moldura
    cor_braco = aparencia.casca

    pen_braco = QPen(cor_borda, 5.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    pen_mao = QPen(cor_borda, 2.5)

    ombro_esq = (-BODY_W / 2 + 3, body_offset_y + 12.0)
    ombro_dir = (BODY_W / 2 - 3, body_offset_y + 12.0)

    # Configuração dos braços para cada gesto
    bracos = _calcular_bracos(gesture, walk_phase, is_walking, now, ombro_esq, ombro_dir)

    for (ox, oy), (mx, my), rot_mao in bracos:
        mid_x = (ox + mx) / 2
        mid_y = max(oy, my) + 4.0 if gesture in ("cheer", "wave", "hold_ball") else (oy + my) / 2 + 3.0

        caminho = QPainterPath()
        caminho.moveTo(ox, oy)
        caminho.quadTo(mid_x, mid_y, mx, my)

        # Braço
        p.setPen(pen_braco)
        p.setBrush(Qt.NoBrush)
        p.drawPath(caminho)

        # Mãozinha arredondada (luva)
        p.save()
        p.translate(mx, my)
        p.rotate(rot_mao)
        p.setPen(pen_mao)
        p.setBrush(cor_braco)
        p.drawEllipse(QRectF(-7.5, -7.5, 15, 15))

        # Detalhe do polegar / junta
        p.setPen(QPen(cor_borda, 1.8))
        p.drawArc(QRectF(-4, -5, 8, 8), 30 * 16, 120 * 16)
        p.restore()

    p.restore()


def _calcular_bracos(gesture, walk_phase, is_walking, now, ombro_esq, ombro_dir):
    """Calcula as posições da mão para os gestos suportados."""
    ox_e, oy_e = ombro_esq
    ox_d, oy_d = ombro_dir

    if gesture == "typing":
        # Digitando com as duas mãos no teclado do notebook: toques rápidos alternados!
        t = now * 16.0
        tap_esq = abs(math.sin(t)) * 4.0
        tap_dir = abs(math.cos(t)) * 4.0
        m_esq = (ox_e + 24.0, oy_e + 26.0 - tap_esq)
        m_dir = (ox_d - 24.0, oy_d + 26.0 - tap_dir)
        return [(ombro_esq, m_esq, 15.0), (ombro_dir, m_dir, -15.0)]

    if gesture == "cheer":
        # Comemorando com os dois braços para o alto vibrando!
        vibra = math.sin(now * 22.0) * 3.0
        m_esq = (ox_e - 14.0, oy_e - 36.0 + vibra)
        m_dir = (ox_d + 14.0, oy_d - 36.0 - vibra)
        return [(ombro_esq, m_esq, -30.0), (ombro_dir, m_dir, 30.0)]

    if gesture == "wave":
        # Acenando com a mão direita, mão esquerda relaxada
        wave_balanco = math.sin(now * 12.0) * 12.0
        m_esq = (ox_e - 8.0, oy_e + 16.0)
        m_dir = (ox_d + 18.0 + wave_balanco, oy_d - 26.0)
        return [(ombro_esq, m_esq, 10.0), (ombro_dir, m_dir, wave_balanco * 2.0)]

    if gesture == "hold_ball":
        # Segurando a bolinha no alto com ambas as mãos
        m_esq = (ox_e + 18.0, oy_e - 38.0)
        m_dir = (ox_d - 18.0, oy_d - 38.0)
        return [(ombro_esq, m_esq, 45.0), (ombro_dir, m_dir, -45.0)]

    if gesture == "juggle":
        # Malabarismo: mãos alternando movimentos circulares
        t = now * 8.0
        m_esq = (ox_e + 10.0 + math.cos(t) * 12.0, oy_e - 15.0 + math.sin(t) * 12.0)
        m_dir = (ox_d - 10.0 + math.cos(t + math.pi) * 12.0, oy_d - 15.0 + math.sin(t + math.pi) * 12.0)
        return [(ombro_esq, m_esq, math.sin(t) * 20.0), (ombro_dir, m_dir, -math.sin(t) * 20.0)]

    if gesture == "cross":
        # Braços cruzados no peito (bravo / emburrado)
        m_esq = (ox_e + 30.0, oy_e + 18.0)
        m_dir = (ox_d - 30.0, oy_d + 18.0)
        return [(ombro_esq, m_esq, 25.0), (ombro_dir, m_dir, -25.0)]

    if gesture == "scratch":
        # Coçando a cabeça (dúvida / curioso)
        m_esq = (ox_e - 8.0, oy_e + 16.0)
        m_dir = (ox_d - 4.0, oy_d - 20.0 + math.sin(now * 14.0) * 3.0)
        return [(ombro_esq, m_esq, 10.0), (ombro_dir, m_dir, -40.0)]

    if is_walking:
        # Andando: balanço natural e suave dos braços
        balanco = math.sin(walk_phase) * 10.0
        m_esq = (ox_e - 8.0, oy_e + 16.0 - balanco)
        m_dir = (ox_d + 8.0, oy_d + 16.0 + balanco)
        return [(ombro_esq, m_esq, -balanco * 1.5), (ombro_dir, m_dir, balanco * 1.5)]

    # Idle padrão: braços repousando nas laterais com respiração sutil
    respiro = math.sin(now * 2.2) * 2.0
    m_esq = (ox_e - 8.0, oy_e + 18.0 + respiro)
    m_dir = (ox_d + 8.0, oy_d + 18.0 + respiro)
    return [(ombro_esq, m_esq, 8.0), (ombro_dir, m_dir, -8.0)]


def draw_blush(p: QPainter, aparencia):
    """Desenha bochechas coradinhas rosadas nas laterais dos olhos quando feliz/corado."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    cor_rubor = QColor("#ff5252")
    cor_rubor.setAlpha(95)
    p.setBrush(cor_rubor)

    for side in (-1, 1):
        cx = side * 36.0
        cy = 16.0
        p.drawEllipse(QRectF(cx - 8.0, cy - 5.0, 16.0, 10.0))
    p.restore()
