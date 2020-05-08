"""
    Name: "OdmorZaposlenika"
    Version: "1.1.0"
    Description: "Aplikacija za evidenciju godišnjeg odmora"
    Author: "Antonio Kulić"
    Author email: "Kulic96@gmail.com"
    Date created: "7.2.2020."
    OS: "Windows"
    System type: "64-bit Operating System"
"""

import sys
from datetime import datetime
from traceback import format_exception

from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication

from database_create import create_connection
from odmor import main_widget
from resources import resources


def exception_hook(exctype, value, traceback):
    error = format_exception(exctype, value, traceback)
    error[0] = error[0].replace('\n', f' {datetime.now()}\n')
    with open('appexc.log', 'a') as file:
        file.write(f'{"".join(error)}\n')
    sys.__excepthook__(exctype, value, traceback)
    sys.exit(1)


sys.excepthook = exception_hook

if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont('Arial', 10)
    app.setWindowIcon(QIcon(':icons/calendar.png'))
    app.setStyle('Fusion')
    app.setFont(font)
    create_connection()
    run = main_widget.CentralWidget()
    run.show()
    sys.exit(app.exec_())
