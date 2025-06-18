from app.presentation.web.streamlit.chat_ui import render_chat_ui

import nltk
nltk.download("punkt_tab")


if __name__ == "__main__":
    render_chat_ui()
