from __future__ import annotations

import html
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer


_FONT_FAMILY = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"
_FONT_REGISTERED = False


def _font_candidates() -> list[tuple[str, str]]:
    return [
        (
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ),
        (
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
    ]


def ensure_pdf_fonts() -> tuple[str, str]:
    global _FONT_REGISTERED, _FONT_FAMILY, _FONT_BOLD

    if _FONT_REGISTERED:
        return _FONT_FAMILY, _FONT_BOLD

    for regular_path, bold_path in _font_candidates():
        if os.path.exists(regular_path) and os.path.exists(bold_path):
            pdfmetrics.registerFont(TTFont("AppPdfRegular", regular_path))
            pdfmetrics.registerFont(TTFont("AppPdfBold", bold_path))
            _FONT_FAMILY = "AppPdfRegular"
            _FONT_BOLD = "AppPdfBold"
            _FONT_REGISTERED = True
            return _FONT_FAMILY, _FONT_BOLD

    _FONT_REGISTERED = True
    return _FONT_FAMILY, _FONT_BOLD


def _paragraph_text(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    return html.escape(raw).replace("\n", "<br/>")


def _question_image_path(root_folder: str, question_id: int) -> str:
    return os.path.join(root_folder, "data", "images", "questions", f"{question_id}.png")


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", value.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or "training"


def _pdf_local_now() -> datetime:
    timezone_name = os.getenv("TZ") or os.getenv("APP_TIMEZONE") or "Europe/Moscow"
    try:
        return datetime.now(UTC).astimezone(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError:
        return datetime.now().astimezone()


def _build_styles() -> dict[str, ParagraphStyle]:
    font_name, font_bold = ensure_pdf_fonts()
    sample = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "WorkPdfTitle",
            parent=sample["Title"],
            fontName=font_bold,
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#111827"),
            spaceAfter=10,
        ),
        "meta": ParagraphStyle(
            "WorkPdfMeta",
            parent=sample["BodyText"],
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4b5563"),
            spaceAfter=4,
        ),
        "question_title": ParagraphStyle(
            "WorkPdfQuestionTitle",
            parent=sample["Heading3"],
            fontName=font_bold,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#111827"),
            spaceAfter=6,
        ),
        "question_text": ParagraphStyle(
            "WorkPdfQuestionText",
            parent=sample["BodyText"],
            fontName=font_name,
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#111827"),
            spaceAfter=8,
        ),
        "note": ParagraphStyle(
            "WorkPdfNote",
            parent=sample["BodyText"],
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#6b7280"),
            backColor=colors.HexColor("#f3f4f6"),
            borderPadding=8,
            borderRadius=8,
            spaceBefore=4,
            spaceAfter=8,
        ),
    }


def _scaled_image(path: str, max_width: float, max_height: float) -> Image:
    image = Image(path)
    width = float(image.imageWidth)
    height = float(image.imageHeight)
    ratio = min(max_width / width, max_height / height, 1)
    image.drawWidth = width * ratio
    image.drawHeight = height * ratio
    image.hAlign = "CENTER"
    return image


def build_work_pdf(
    *,
    root_folder: str,
    work_id: int,
    work_title: str,
    work_type_label: str,
    questions: Iterable,
    output_dir: str | None = None,
) -> tuple[str, str]:
    styles = _build_styles()
    base_output_dir = output_dir or os.path.join(root_folder, "data", "temp", "work_pdfs")
    Path(base_output_dir).mkdir(parents=True, exist_ok=True)

    visible_name = f"{_sanitize_filename(work_title)}_{work_id}.pdf"
    output_path = os.path.join(base_output_dir, visible_name)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=work_title,
        author="Chemistry Bot",
    )

    story = [
        Paragraph(_paragraph_text(work_title), styles["title"]),
        Paragraph(_paragraph_text(f"Тип тренировки: {work_type_label}"), styles["meta"]),
        Paragraph(_paragraph_text(f"Сформировано: {_pdf_local_now().strftime('%d.%m.%Y %H:%M')}"), styles["meta"]),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d1d5db")),
        Spacer(1, 10),
    ]

    image_max_width = min(doc.width * 0.58, 92 * mm)
    image_max_height = 42 * mm

    for index, question in enumerate(questions, start=1):
        question_title = f"Задание №{index} (id{question.id})"
        story.append(Paragraph(_paragraph_text(question_title), styles["question_title"]))

        if getattr(question, "is_selfcheck", False):
            story.append(
                Paragraph(
                    _paragraph_text("Это задание предполагает самопроверку после решения."),
                    styles["note"],
                )
            )

        text = getattr(question, "text", None)
        if text:
            story.append(Paragraph(_paragraph_text(text), styles["question_text"]))

        image_path = _question_image_path(root_folder, question.id)
        if getattr(question, "question_image", False) and os.path.exists(image_path):
            story.append(_scaled_image(image_path, image_max_width, image_max_height))
            story.append(Spacer(1, 8))

        if not text and not (getattr(question, "question_image", False) and os.path.exists(image_path)):
            story.append(Paragraph(_paragraph_text("Текст задания отсутствует."), styles["note"]))

        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#e5e7eb")))
        story.append(Spacer(1, 12))

    def draw_page(canvas, doc):
        canvas.saveState()
        canvas.setFont(ensure_pdf_fonts()[0], 9)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 10 * mm, f"Страница {canvas.getPageNumber()}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return output_path, visible_name
