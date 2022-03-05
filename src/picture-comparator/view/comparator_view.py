from __future__ import annotations

import math
import os.path
from enum import Enum
from itertools import chain
from pathlib import Path
from typing import List, Optional, Tuple, Union, Iterable, AnyStr

from PySide6.QtCore import QRect, Qt, QPoint, QSize
from PySide6.QtGui import QPaintEvent, QPainter, QResizeEvent, QMouseEvent, QWheelEvent, QPen, QFont, QColor, \
    QStaticText, QPainterPath, QTextOption
from PySide6.QtWidgets import QWidget

from model.display_settings import DisplaySettings, Zoom
from model.image_info import ImageInfo, ImageQuality


class InfoState(Enum):
    NEUTRAL = 0
    BEST = 1
    WORST = 2


class InfoAttribute:
    BEST = QColor.fromRgb(0x4e, 0xa2, 0xdf)  # '#4ea2df'
    WORST = QColor.fromRgb(0xdf, 0x4e, 0x55)  # '#df4e55'
    NEUTRAL = QColor.fromRgb(255, 255, 255)

    def __init__(self, value):
        self.value = value
        self.raw_text = ''
        self.state = InfoState.NEUTRAL

    @property
    def text(self):
        if self.state == InfoState.BEST:
            return f'<font color="{self.BEST}">{self.raw_text}</font>'
        elif self.state == InfoState.WORST:
            return f'<font color="{self.WORST}">{self.raw_text}</font>'
        return self.raw_text

    def color(self):
        if self.state == InfoState.BEST:
            return self.BEST
        if self.state == InfoState.WORST:
            return self.WORST
        return self.NEUTRAL


class PathAttribute(InfoAttribute):
    def __init__(self, path: str):
        super().__init__(path)
        self.raw_text = os.path.split(path)[-1]

    @staticmethod
    def trim_paths(paths: List[PathAttribute]):
        split_paths: List[Path] = [Path(path.value) for path in paths]
        shared = split_paths[0].parent
        for path in split_paths[1:]:
            p = path.parent
            while p != shared and p not in shared.parents:
                p = path.parent
            shared = p
        shared = str(shared)
        if len(shared) == 1:
            shared = ''
        for path in paths:
            path.raw_text = path.value[len(shared) + 1:]


class ResolutionAttribute(InfoAttribute):
    def __init__(self, size: QSize):
        super().__init__(size)
        self.raw_text = f'{size.width()}x{size.height()}'

    @staticmethod
    def mark_best_worst(resolutions: List[ResolutionAttribute]):
        best = []
        worst = []
        for size in resolutions:
            if all(size.value.width() >= s.value.width() and size.value.height() >= s.value.height() for s in resolutions):
                best.append(size)
            if all(size.value.width() <= s.value.width() and size.value.height() <= s.value.height() for s in resolutions):
                worst.append(size)
        if len(best) != len(resolutions):
            for size in best:
                size.state = InfoState.BEST
        if len(worst) != len(resolutions):
            for size in worst:
                size.state = InfoState.WORST


class FileSizeAttribute(InfoAttribute):
    def __init__(self, file_size: int):
        super().__init__(file_size)
        if not file_size >> 10:
            self.raw_text = str(file_size) + ' B'
        elif not file_size >> 20:
            self.raw_text = str(round(file_size / 0x400, 2)) + ' kB'
        elif not file_size >> 30:
            self.raw_text = str(round(file_size / 0x100000, 2)) + ' MB'

    @staticmethod
    def mark_best_worst(sizes: List[FileSizeAttribute]):
        best = []
        worst = []
        best_val = math.inf
        worst_val = -math.inf
        for size in sizes:
            if size.value < best_val:
                best = [size]
                best_val = size.value
            elif size.value == best_val:
                best.append(size)
            if size.value > worst_val:
                worst = [size]
                worst_val = size.value
            elif size.value == worst_val:
                worst.append(size)
        if len(best) != len(sizes):
            for size in best:
                size.state = InfoState.BEST
        if len(worst) != len(sizes):
            for size in worst:
                size.state = InfoState.WORST


class QualityAttribute(InfoAttribute):
    def __init__(self, quality: ImageQuality):
        super().__init__(quality)
        if quality.ext == 'png':
            self.raw_text = 'png: lossless'
        elif quality.ext == 'jpeg':
            self.raw_text = 'jpg: ' + str(quality.value)
        elif quality.ext == 'webp':
            self.raw_text = 'webp: lossless' if quality.lossless else 'webp: lossy'
        else:
            self.raw_text = 'unknown'

    @staticmethod
    def mark_best_worst(qualities: List[QualityAttribute]):
        best = []
        worst = []
        for size in qualities:
            if all(size.value >= s.value and size.value >= s.value for s in qualities):
                best.append(size)
            if all(size.value <= s.value and size.value <= s.value for s in qualities):
                worst.append(size)
        if len(best) != len(qualities):
            for size in best:
                size.state = InfoState.BEST
        if len(worst) != len(qualities):
            for size in worst:
                size.state = InfoState.WORST


class Info:
    def __init__(self, image: ImageInfo):
        self.path = PathAttribute(image.path)
        self.resolution = ResolutionAttribute(image.size())
        self.file_size = FileSizeAttribute(image.file_size)
        self.quality = QualityAttribute(image.quality)

    def raw_text(self):
        return f"{self.path.raw_text}\n{self.resolution.raw_text}\n{self.file_size.raw_text}\n{self.quality.raw_text}"

    def text(self):
        return QStaticText(
            f'{self.path.text}<br/>{self.resolution.text}<br/>{self.file_size.text}<br/>{self.quality.text}')

    @staticmethod
    def mark_best_worst(info_iter: List[Info]):
        PathAttribute.trim_paths([info.path for info in info_iter])
        ResolutionAttribute.mark_best_worst([info.resolution for info in info_iter])
        FileSizeAttribute.mark_best_worst([info.file_size for info in info_iter])
        QualityAttribute.mark_best_worst([info.quality for info in info_iter])


class Section:
    """Helper for drawing current images."""
    text_padding = 10

    def __init__(self, image: ImageInfo):
        self.image: ImageInfo = image
        self.info = Info(image)
        self._rect: QRect = QRect()
        self.fit_zoom: Optional[float] = None
        self.zoom: float = 1

    @property
    def rect(self) -> QRect:
        return self._rect

    @rect.setter
    def rect(self, value: QRect):
        self._rect = value
        if self.ratio() > self.image.ratio():  # Calculate from height
            self.fit_zoom = self.rect.height() / self.image.height()
        else:  # Calculate from width
            self.fit_zoom = self.rect.width() / self.image.width()

    def ratio(self):
        return self.rect.width() / self.rect.height()

    def _paint_image(self, painter: QPainter, widget: CompareWidget):
        target = QRect(
            self.rect.x() + max(0, (self.rect.width() - (self.image.width() * self.zoom)) / 2),
            self.rect.y() + max(0, (self.rect.height() - (self.image.height() * self.zoom)) / 2),
            min(self.rect.width(), self.image.width() * self.zoom),
            min(self.rect.height(), self.image.height() * self.zoom)
        )
        source = QRect(
            max(0, (self.image.width() - (self.rect.width() / self.zoom)) * widget.position[0]),
            max(0, (self.image.height() - (self.rect.height() / self.zoom)) * widget.position[1]),
            min(self.image.width(), self.rect.width() / self.zoom),
            min(self.image.height(), self.rect.height() / self.zoom)
        )
        painter.drawImage(target, self.image.qimage(), source)

    def _paint_info(self, painter: QPainter, widget: CompareWidget):
        if widget.display_settings.show_info:
            font_size = 20
            font_gap = 4
            font = painter.font()
            font.setPixelSize(font_size)

            pen = painter.pen()
            pen.setWidth(4)

            for i, info in enumerate((self.info.path, self.info.resolution, self.info.file_size, self.info.quality)):
                point = QPoint(self.rect.x() + self.text_padding, self.rect.y() + self.text_padding + font_size * (i + 1) + font_gap * i)
                path = QPainterPath()
                path.addText(point, font, info.raw_text)
                bound = QPainterPath()
                bound.addRect(self.rect)
                path &= bound

                painter.strokePath(path, pen)
                painter.fillPath(path, info.color())

    def _paint_zoom(self, painter):
        rect_width = 40
        rect_height = 20
        path = QPainterPath()
        rect = QRect(self.rect.x() + self.rect.width() - rect_width - self.text_padding,
                     self.rect.y() + self.rect.height() - rect_height - self.text_padding,
                     rect_width, rect_height)
        path.addRoundedRect(rect, 10, 10)
        painter.fillPath(path, QColor.fromRgb(0, 0, 0, 128))
        text = f'{round(self.zoom * 100)}%'
        painter.setPen(QColor.fromRgb(255, 255, 255))
        painter.drawText(rect, Qt.AlignCenter, text)
        painter.setPen(QColor.fromRgb(0, 0, 0))

    def paint(self, painter: QPainter, widget: CompareWidget):
        self._paint_image(painter, widget)
        self._paint_info(painter, widget)
        self._paint_zoom(painter)
        painter.drawRect(self.rect)


class CompareWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.spacing = 5
        self.moving = False
        # Position of zoomed in images, where (0, 0) is top-left corner and (1, 1) bottom-right corner.
        self.position: Tuple[float, float] = (.5, .5)
        self._last_pos: QPoint = QPoint()
        self.sections = []
        self.leading_section: Optional[Section] = None
        self.display_settings: Optional[DisplaySettings] = None
        self.setMouseTracking(True)

    def set_display_settings(self, display_settings: DisplaySettings):
        self.display_settings = display_settings

    def size_update(self):
        if not self.sections:
            return
        can_enlarge = self.leading_section.zoom >= self.leading_section.fit_zoom if self.leading_section else False
        section_width: int = int((self.width() - (self.spacing * len(self.sections) - 1)) / len(self.sections))
        for i, section in enumerate(self.sections):
            rect = QRect(i * (section_width + self.spacing), 0, section_width, self.height())
            section.rect = rect
        if can_enlarge and self.leading_section.zoom < self.leading_section.fit_zoom:
            self.leading_section.zoom = self.leading_section.fit_zoom
            self.adjust_zoom_to_leader()

    def pick_leading_section(self):
        weight = -math.inf
        self.leading_section = None
        for section in self.sections:
            section_weight = section.image.width() * section.image.height()
            if section_weight > weight:
                weight = section_weight
                self.leading_section = section

    def adjust_zoom(self, section: Section, zoom: float, fit_zoom: float):
        section.zoom = zoom * (section.fit_zoom / fit_zoom)

    def adjust_zoom_to_leader(self):
        for section in self.sections:
            if section is not self.leading_section:
                self.adjust_zoom(section, self.leading_section.zoom, self.leading_section.fit_zoom)

    def set_images(self, images: List, group_changed: bool):
        old_zoom = self.leading_section.zoom if self.leading_section and not group_changed else None
        old_fit_zoom = self.leading_section.fit_zoom if self.leading_section and not group_changed else None

        self.sections.clear()
        self.sections = [Section(image) for image in images]
        if self.sections:
            Info.mark_best_worst([s.info for s in self.sections])
            self.size_update()
            self.pick_leading_section()
            if self.display_settings.zoom == Zoom.SCALED:
                if old_zoom is not None:
                    self.adjust_zoom(self.leading_section, old_zoom, old_fit_zoom)
                else:
                    self.leading_section.zoom = self.leading_section.fit_zoom
                self.adjust_zoom_to_leader()
            elif self.display_settings.zoom == Zoom.FLAT:
                if old_zoom is not None:
                    self.leading_section.zoom = old_zoom
                else:
                    self.leading_section.zoom = self.leading_section.fit_zoom
                for section in self.sections:
                    section.zoom = self.leading_section.zoom
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for section in self.sections:
            section.paint(painter, self)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.size_update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton:
            self.moving = True
            self._last_pos = event.pos()
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton:
            self.moving = False
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton:
            if self.moving and self.sections:
                pixel_change = self._last_pos - event.pos()
                w_factor = self.leading_section.image.width() * self.leading_section.zoom - self.leading_section.rect.width()
                h_factor = self.leading_section.image.height() * self.leading_section.zoom - self.leading_section.rect.height()
                self.position = (
                    min(1, max(0, (self.position[0] + pixel_change.x() / w_factor) if w_factor else .5)),
                    min(1, max(0, (self.position[1] + pixel_change.y() / h_factor) if h_factor else .5))
                )
                self._last_pos = event.pos()
                self.update()
        else:
            self.moving = False
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.sections:
            step = event.angleDelta().y()
            if self.display_settings.zoom.SCALED:
                # TODO
                # better zooming math
                # min/max zoom
                # relative to mouse position
                before = self.leading_section.zoom
                after = self.leading_section.zoom + step / 1000
                if before < 1 and after > 1 or before > 1 and after < 1:
                    after = 1
                self.leading_section.zoom = after
                self.adjust_zoom_to_leader()
                self.update()
        event.accept()
