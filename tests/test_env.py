import polars as pl
import flet as ft

def test_imports():
    assert pl.__version__ is not None
    assert ft.__version__ is not None
