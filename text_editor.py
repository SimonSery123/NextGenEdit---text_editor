import sys
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QMessageBox, QMenu, QTextEdit
from PyQt5.QtGui import QIcon, QTextCursor, QColor, QTextCharFormat
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtCore import Qt


class HighlightingTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super(HighlightingTextEdit, self).__init__(parent)
        self.spellCheckResults = []
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def highlight_spelling_errors(self, spellCheckResults):
        for error in spellCheckResults:
            if isinstance(error, dict) and 'offset' in error and 'bad' in error:
                self.highlightWord(error['offset'], error['offset'] + len(error['bad']))
            else:
                print("Error in spellCheckResults format:", error)

    def highlight_word(self, start, end):
        cursor = QTextCursor(self.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        format = QTextCharFormat()
        format.setUnderlineColor(QColor("red"))
        format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        cursor.mergeCharFormat(format)

    def show_context_menu(self, position):
        menu = QMenu(self)
        cursor = self.cursorForPosition(position)
        cursor.select(QTextCursor.WordUnderCursor)
        selected_word = cursor.selectedText()

        for error in self.spellCheckResults:
            if error['bad'] == selected_word:
                for suggestion in error['better']:
                    action = menu.addAction(suggestion)
                    action.triggered.connect(lambda _, s=suggestion: self.replace_word(cursor, s))
                break
        menu.exec_(self.mapToGlobal(position))

    @staticmethod
    def replace_word(self, cursor, word):

        """replaces misspelled word with corrected response from API"""

        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(word)
        cursor.endEditBlock()


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):

        """initialise GUI window"""

        self.textEdit = HighlightingTextEdit()
        self.setCentralWidget(self.textEdit)
        self.setWindowTitle('NextGenEdit')
        self.setWindowIcon(QtGui.QIcon('next_gen_edit.jpg'))
        self.setGeometry(300, 300, 600, 400)
        self.setup_menu_bar()

    def setup_menu_bar(self):

        """Sets up menu in GUI"""

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(self.create_action('&Open', 'Ctrl+O', 'Open new File', self.open_file))
        file_menu.addAction(self.create_action('&Save', 'Ctrl+S', 'Save File', self.save_file))
        file_menu.addAction(self.create_action('New', 'Ctrl+N', 'New File', self.new_file))

        edit_menu = menu_bar.addMenu('Edit')
        edit_menu.addAction(self.create_action('Cut', 'Ctrl+X', 'Cut to clipboard', self.textEdit.cut))
        edit_menu.addAction(self.create_action('Copy', 'Ctrl+C', 'Copy to clipboard', self.textEdit.copy))
        edit_menu.addAction(self.create_action('Paste', 'Ctrl+V', 'Paste from clipboard', self.textEdit.paste))
        edit_menu.addAction(self.create_action('Spell Check', 'Ctrl+Shift+S', 'Check Spelling', self.spell_check))

    def create_action(self, text, shortcut, status_tip, triggered_method, icon=None):
        if icon:
            action = QAction(QIcon(icon), text, self)
        else:
            action = QAction(text, self)
        action.setShortcut(shortcut)
        action.setStatusTip(status_tip)
        action.triggered.connect(triggered_method)
        return action

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open File', '/')
        if filename:
            with open(filename, 'r') as file:
                self.textEdit.setText(file.read())

    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save File', '/')
        if filename:
            with open(filename, 'w') as file:
                file.write(self.textEdit.toPlainText())

    def new_file(self):
        self.textEdit.clear()

    def spell_check(self):
        text = self.textEdit.toPlainText()
        corrected_sentence = self.callSpellCheckAPI(text)
        if corrected_sentence:
            self.textEdit.setText(corrected_sentence)
        else:
            QMessageBox.information(self, "Spell Check", "No corrections made or error in spell checking.")

    def show_corrections(self, corrected_sentence):
        if corrected_sentence:
            QMessageBox.information(self, "Spell Check Result", f"Corrected Sentence:\n{corrected_sentence}")
        else:
            QMessageBox.information(self, "Spell Check", "No corrections found or error in spell checking.")

    def call_spell_check_API(self, text):

        """Sends needed info to text gear API. for now, there is hardcoded API key, for production it should be changed.
        get response from API and check if the response have all requirements met, than returns a corrected JSON"""

        url = "https://textgears-textgears-v1.p.rapidapi.com/correct"
        payload = {"text": text}
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "X-RapidAPI-Key": "a91faafd10msh03c095485451088p1c4251jsn4089358e6598"  # Your API key
        }

        try:
            # assign variables for data collected from API

            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            print('API response:', data)
            # Check if 'status' is True, and 'response' and 'corrected' keys exist

            if data.get('status') is True and 'response' in data and 'corrected' in data['response']:
                return data['response']['corrected']
            # if there's no errors
            else:
                print('API response', data)
                QMessageBox.information(self, "Spell Check", "No errors found or response format is incorrect.")
                return None
        # if there's API connection error
        except requests.RequestException as e:
            QMessageBox.warning(self, "API Error", f"API request failed: {e}")
            return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec_())
