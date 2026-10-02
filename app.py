from __future__ import annotations

import sys
from pathlib import Path
import streamlit.components.v1 as components


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from utils.helpers import bootstrap_legacy_path, setup_logging  # noqa: E402

setup_logging()
bootstrap_legacy_path()

st.set_page_config(
    page_title="IntelliQR — QR estático y códigos de barras",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Identidad visual heredada de la app de escritorio (azul #2563EB).
st.markdown(
    """
    <style>
      .block-container {padding-top: 2.2rem; max-width: 1180px;}
      h1, h2, h3 {letter-spacing: -0.01em;}
      div[data-testid="stMetric"] {
        background: #F8FAFC; border: 1px solid #E2E8F0;
        border-radius: 12px; padding: 14px 18px;
      }
      .iq-brand {font-size: 1.45rem; font-weight: 700; color: #2563EB; margin-bottom: 0;}
      .iq-sub {color: #64748B; font-size: 0.82rem; margin-top: -4px;}
      .iq-pill {
        display:inline-block; padding:2px 10px; border-radius:999px;
        font-size:0.75rem; background:#EFF6FF; color:#2563EB; border:1px solid #DBEAFE;
      }
      code {font-size: 0.85em;}
      .iq-footer {
        text-align: center; color: #64748B; font-size: 0.82rem;
        margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #E2E8F0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def _sidebar_header() -> None:
    with st.sidebar:
        st.markdown('<p class="iq-brand">IntelliQR</p>', unsafe_allow_html=True)
        st.markdown('<p class="iq-sub">Generador de QR estático</p>', unsafe_allow_html=True)
        st.divider()


def _sidebar_footer() -> None:
    with st.sidebar:
        st.divider()
        st.caption("🔒 No guardamos tus datos: todo se genera en el momento.")
        st.caption("Developed by Ashleidy")


_sidebar_header()

pages = [
    st.Page("pages/create_qr.py", title="Crear QR", icon="✨", default=True),
    st.Page("pages/barcode.py", title="Códigos de barras", icon="🏷️"),
    st.Page("pages/scanner.py", title="Escáner", icon="🔍"),
]

navigation = st.navigation(pages, position="sidebar")
_sidebar_footer()


components.html(
    """
    <script>
      const d = window.parent.document;
      d.documentElement.lang = "es";
      d.documentElement.setAttribute("translate", "yes");
      d.querySelectorAll('meta[name="google"]').forEach(m => m.remove());
      d.querySelectorAll('.notranslate').forEach(e => e.classList.remove('notranslate'));
    </script>
    """,
    height=0,
)
navigation.run()

st.markdown(
    '<div class="iq-footer">Developed by Ashleidy</div>',
    unsafe_allow_html=True,
)
