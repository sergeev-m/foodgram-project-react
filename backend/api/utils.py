from io import BytesIO
from typing import (
    TypeVar,
    Generic,
    Any
)
from collections import OrderedDict
from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet
from rest_framework.validators import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.colors import gray
from reportlab.lib.colors import black
from reportlab.pdfbase.ttfonts import TTFont


ModelType = TypeVar('ModelType', bound=models.Model)


def create_list_obj(cls: Generic[ModelType], items: list[OrderedDict | dict],
                    **kwargs) -> list[Generic[ModelType]]:
    try:
        return [cls(**item, **kwargs) for item in items]
    except Exception as exc:
        raise ValueError(exc)


def empty_validator(value: Any) -> Any:
    if not value:
        raise ValidationError('Обязательное поле.')
    return value


class DynamicUniqueTogetherValidator(UniqueTogetherValidator):
    """Проверяет на уникальность поля модели."""
    def __init__(self, model: Generic[ModelType], fields=None, message=None):
        try:
            # fields and message
            _data = settings.UNIQUE_TOGETHER_VALIDATOR_DATA[model.__name__]

            queryset = model.objects.all()
            fields = fields or _data.get('fields')
            message = message or _data.get('message')
            del _data
        except Exception as exc:
            raise ValueError(exc)
        super().__init__(queryset, fields, message)


def create_pdf(recipes: QuerySet, ingredients: QuerySet, **kwargs) -> BytesIO:
    """Запись списка покупок в pdf"""
    request = kwargs.get('request')
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    pdfmetrics.registerFont(TTFont('DejaVuSerif', 'DejaVuSerif.ttf'))

    # header
    c.setFillColor(gray)
    c.rect(0, 10.4 * inch, 8.5 * inch, 0.6 * inch, fill=1, stroke=0)
    c.setFillColor(black)
    c.setFont('DejaVuSerif', settings.PDF_FONT_SIZE + 4)
    c.drawCentredString(8.5 * inch/2, 10.6 * inch, 'Продуктовый помощник')

    # список рецептов
    c.drawString(x := 20, y := 10 * inch, 'Список рецептов:')
    c.setFont('DejaVuSerif', settings.PDF_FONT_SIZE)
    for item in recipes:
        y -= 20
        c.drawString(x, y, '\u2022 {recipe__name}'.format(**item))
    y -= 0.5 * inch

    # список ингредиентов
    ingredients_text = '\u2022 {ingredient__name} ({measurement}) - {amount}'
    c.setFont('DejaVuSerif', settings.PDF_FONT_SIZE + 4)
    c.drawString(x, y, 'Список ингредиентов:')
    c.setFont('DejaVuSerif', settings.PDF_FONT_SIZE)
    for item in ingredients:
        y -= 20
        c.drawString(x, y, ingredients_text.format(**item))
    y -= 0.5 * inch

    # footer
    c.line(0, y, 8.5 * inch, y)
    footer_text = 'Foodgram'
    if request:
        footer_text += ' ' + request._request.META['HTTP_HOST']
    c.drawRightString(8.5 * inch - 50, y - 20, footer_text)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
