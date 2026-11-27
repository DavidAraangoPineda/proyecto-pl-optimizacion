"""Prueba de humo de la interfaz: la aplicación arranca, resuelve cada ejemplo y muestra todas las pestañas sin errores."""
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lp.model import EXAMPLES  # noqa: E402


@pytest.mark.parametrize("ejemplo", list(EXAMPLES))
@pytest.mark.parametrize("metodo", ["bigm", "revised"])
def test_resolver_cada_ejemplo_sin_errores(ejemplo, metodo):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    at.sidebar.selectbox(key="ex_select").select(ejemplo).run()
    at.sidebar.radio[0].set_value(metodo).run()
    next(b for b in at.button if "Resolver" in b.label).click().run()
    assert not at.exception, at.exception
    assert len(at.tabs) == 6
    assert at.success or at.error or at.warning      # siempre informa el estado del problema
