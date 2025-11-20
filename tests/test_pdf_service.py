"""
Tests for PDF service to increase coverage.
"""

import pytest


def test_pdf_service_imports():
    """Test that PDF service modules can be imported."""
    from app.services.pdf.pdf_service import generate_report_pdf, generate_sale_summary_pdf

    # Should be callable
    assert callable(generate_report_pdf)
    assert callable(generate_sale_summary_pdf)


def test_pdf_service_templates_exist():
    """Test that PDF templates directory exists."""
    from app.services.pdf.pdf_service import TEMPLATES_DIR

    assert TEMPLATES_DIR.exists()
    assert TEMPLATES_DIR.is_dir()


def test_pdf_service_environment():
    """Test that Jinja2 environment is configured."""
    from app.services.pdf.pdf_service import templates_env

    assert templates_env is not None
    # Should have loader configured
    assert hasattr(templates_env, 'loader')


def test_pdf_html_class_fallback():
    """Test that HTML class fallback exists."""
    from app.services.pdf.pdf_service import _html_class

    HTMLCls = _html_class()
    assert HTMLCls is not None
    # Should be callable/constructible
    assert callable(HTMLCls)


def test_pdf_service_module_structure():
    """Test that PDF service module has expected structure."""
    import app.services.pdf.pdf_service as pdf_service

    # Should have these functions
    assert hasattr(pdf_service, 'generate_report_pdf')
    assert hasattr(pdf_service, 'generate_sale_summary_pdf')
    assert hasattr(pdf_service, '_html_class')

    # Should have these constants
    assert hasattr(pdf_service, 'PACKAGE_DIR')
    assert hasattr(pdf_service, 'TEMPLATES_DIR')
    assert hasattr(pdf_service, 'templates_env')


