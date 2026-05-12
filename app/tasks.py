from celery import shared_task

from parsing.parser import parse_invoice_pdf

@shared_task
def parse_pdf(filepath):
    parse_invoice_pdf(filepath)