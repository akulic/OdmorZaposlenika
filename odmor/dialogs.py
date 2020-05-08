import json
from datetime import timedelta

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
from PyQt5.QtSql import QSqlTableModel, QSqlQuery


class DialogPregledZaPeriod(QtWidgets.QDialog):
    def __init__(self, period, parent=None):
        super(DialogPregledZaPeriod, self).__init__(parent)
        self.setWindowFlags(Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint)
        self.setWindowTitle('Pregled godišnjeg odmora')
        self.resize(840, 450)
        self.zaposlenici = {}
        sql = """select strftime('%d.%m.%Y', o.datum), z.prezime || ' ' || z.ime as zaposlenik
                    from zaposlenici z left join odmor o on z.rb = o.zaposlenik_rb
                    where datum between '{}' and '{}';""".format(*[str(d) for d in period])

        datum_od, datum_do = period
        delta = timedelta(days=1)
        while datum_od <= datum_do:  # Kreiranje stupaca s datumom za odabrani period
            self.zaposlenici[datum_od.strftime('%d.%m.%Y')] = []
            datum_od += delta

        query = QSqlQuery(sql)
        query.exec_()
        while query.next():  # Ključ je datum a vrijednost su zaposlenici koji su na taj dan bili na odmoru
            self.zaposlenici[query.value(0)].append(query.value(1))

        self.table = QtWidgets.QTableWidget()
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.setColumnCount(len(self.zaposlenici))
        self.table.setHorizontalHeaderLabels(self.zaposlenici)

        self.table.setRowCount(max([len(self.zaposlenici[x]) for x in self.zaposlenici]))
        for col, datum in enumerate(self.zaposlenici):
            for row, zaposlenik in enumerate(self.zaposlenici[datum]):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(zaposlenik)))

        btn_zatvori = QtWidgets.QPushButton('Zatvori')
        btn_zatvori.clicked.connect(self.close)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self.table)
        vlayout.addWidget(btn_zatvori, 0, Qt.AlignRight)
        self.setLayout(vlayout)

    @staticmethod
    def exec_dialog():
        period = DialogPeriod()
        if period.exec_():
            dialog = DialogPregledZaPeriod(period.get_dates())
            dialog.exec_()


class DialogPeriod(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(DialogPeriod, self).__init__(parent, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle('Period')
        self.setFixedSize(250, 130)

        praznici = KalendarWidget.load_praznici()
        current_date = QDate.currentDate()
        self.datum_od = QtWidgets.QDateEdit()
        self.datum_od.setCalendarPopup(True)
        self.datum_od.setCalendarWidget(KalendarWidget(praznici))
        self.datum_od.setAlignment(Qt.AlignCenter)
        self.datum_od.setDate(current_date)

        self.datum_do = QtWidgets.QDateEdit()
        self.datum_do.setCalendarPopup(True)
        self.datum_do.setCalendarWidget(KalendarWidget(praznici))
        self.datum_do.setAlignment(Qt.AlignCenter)
        self.datum_do.setDate(current_date.addDays(7))

        lbl_naslov = QtWidgets.QLabel('Pregled godišnjeg odmora')
        font = lbl_naslov.font()
        font.setPointSize(11)
        lbl_naslov.setFont(font)

        btn_prikaz = QtWidgets.QPushButton('Prikaži')

        form_layout = QtWidgets.QFormLayout()
        form_layout.setVerticalSpacing(5)
        form_layout.setHorizontalSpacing(15)
        form_layout.addRow(lbl_naslov)
        form_layout.addRow(QtWidgets.QLabel('Od datuma: '), self.datum_od)
        form_layout.addRow(QtWidgets.QLabel('Do datuma: '), self.datum_do)
        form_layout.addWidget(btn_prikaz)

        self.setLayout(form_layout)
        btn_prikaz.clicked.connect(self.validate_dates)

    def validate_dates(self):
        if self.datum_od.date() < self.datum_do.date():
            return self.accept()
        QtWidgets.QToolTip.showText(self.mapToGlobal(self.datum_do.pos()), 'Neispravan unos')

    def get_dates(self):
        return self.datum_od.date().toPyDate(), self.datum_do.date().toPyDate()


class DialogUnosZaposlenika(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(DialogUnosZaposlenika, self).__init__(parent, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle('Unos zaposlenika')
        self.setFixedSize(330, 180)
        self.setWindowIcon(QIcon(':icons/user.png'))
        self.zaposlenik_rb = None

        self.line_ime = QtWidgets.QLineEdit()
        self.line_prezime = QtWidgets.QLineEdit()
        self.spin_dana = QtWidgets.QSpinBox()
        self.spin_dana.setFixedWidth(70)
        self.spin_dana.setRange(0, 99)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow('Ime: ', self.line_ime)
        form_layout.addRow('Prezime: ', self.line_prezime)
        form_layout.addRow('Ukupno dana godišnjeg: ', self.spin_dana)

        self.btn_spremi = QtWidgets.QPushButton('Spremi')
        self.btn_spremi.setEnabled(False)
        btn_odustani = QtWidgets.QPushButton('Odustani')

        hbox_btn = QtWidgets.QHBoxLayout()
        hbox_btn.addStretch()
        hbox_btn.addWidget(self.btn_spremi, 0, Qt.AlignRight)
        hbox_btn.addWidget(btn_odustani, 0, Qt.AlignRight)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addLayout(form_layout)
        vlayout.addLayout(hbox_btn)
        self.setLayout(vlayout)

        btn_odustani.clicked.connect(self.reject)
        self.btn_spremi.clicked.connect(self.accept)
        self.line_ime.textChanged.connect(self.validate_input)
        self.line_prezime.textChanged.connect(self.validate_input)

    def set_zaposlenik_data(self, data):
        self.zaposlenik_rb = data[0]
        self.line_ime.setText(data[1])
        self.line_prezime.setText(data[2])
        self.spin_dana.setValue(int(data[3]))

    def get_input_data(self):
        return self.line_ime.text(), self.line_prezime.text(), self.spin_dana.value(), self.zaposlenik_rb

    def validate_input(self):
        self.btn_spremi.setEnabled(bool(self.line_ime.text() and self.line_prezime.text()))


# ############################## Zaposlenik pregled godisnjeg #########################################################
class SqlTableModel(QSqlTableModel):
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.TextAlignmentRole:
            if index.column() == 5:  # Napomena
                return Qt.AlignLeft | Qt.AlignVCenter
            return Qt.AlignCenter | Qt.AlignVCenter
        value = super(SqlTableModel, self).data(index, role)
        if role == Qt.DisplayRole:
            if index.column() == 0 and value == 0:
                return None
        return value

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return super(SqlTableModel, self).flags(index)


class DialogPregledGodisnjeg(QtWidgets.QDialog):
    def __init__(self, zaposlenik, godina, parent=None):
        super(DialogPregledGodisnjeg, self).__init__(parent, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.resize(800, 450)
        self.setWindowTitle(f'Pregled i unos godišnjeg - {zaposlenik[1]} {zaposlenik[2]}')
        self.zaposlenik_rb = zaposlenik[0]
        self.ukupno_dana = zaposlenik[3]
        self.godina = godina

        self.model = SqlTableModel()
        self.model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.model.setTable('odmor')

        self.table = QtWidgets.QTableView()
        self.table.verticalHeader().setFixedWidth(40)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.horizontalHeader().setDefaultSectionSize(170)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setItemDelegateForColumn(2, DateColumnDelegate(self))
        self.table.setItemDelegateForColumn(3, GodinaDelegate(self))

        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.setSelectionMode(QtWidgets.QTableView.SingleSelection)
        self.table.setModel(self.model)
        self.model.setFilter(f'zaposlenik_rb={self.zaposlenik_rb} and godina={self.godina}')
        self.model.select()
        self.table.hideColumn(1)
        self.table.sortByColumn(2, Qt.AscendingOrder)

        btn_novi = QtWidgets.QPushButton('Novi unos')
        btn_novi.setAutoDefault(False)
        btn_izbrisi = QtWidgets.QPushButton('Izbriši')
        btn_izbrisi.setAutoDefault(False)
        btn_spremi = QtWidgets.QPushButton('Spremi')
        btn_spremi.setAutoDefault(False)
        btn_zatvori = QtWidgets.QPushButton('Zatvori')
        btn_zatvori.setAutoDefault(False)

        hbox_btns = QtWidgets.QHBoxLayout()
        hbox_btns.addWidget(btn_novi)
        hbox_btns.addWidget(btn_izbrisi)
        hbox_btns.addWidget(btn_spremi)
        hbox_btns.addStretch()
        hbox_btns.addWidget(btn_zatvori)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self.table)
        vlayout.addLayout(hbox_btns)
        self.setLayout(vlayout)

        btn_novi.clicked.connect(self.novi_unos)
        btn_izbrisi.clicked.connect(self.izbrisi_unos)
        btn_spremi.clicked.connect(self.spremi_promjene)
        btn_zatvori.clicked.connect(self.close)

    def closeEvent(self, event):
        if self.model.isDirty():
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, 'Spremanje promjena',
                                        'Neke od unesenih promjena nisu spremljene. \n\nŽelite li ih spremiti?')
            msg.addButton('Da', QtWidgets.QMessageBox.AcceptRole)
            msg.addButton('Ne', QtWidgets.QMessageBox.RejectRole)
            if msg.exec_() == QtWidgets.QMessageBox.AcceptRole:
                self.model.submitAll()
            self.model.revertAll()  # Da se ustanovi je li bilo promjena
        return super(DialogPregledGodisnjeg, self).closeEvent(event)

    def novi_unos(self):
        last_row = self.model.rowCount()
        if self.ukupno_dana > last_row:
            self.table.setFocus()
            self.model.insertRow(last_row)
            self.model.setData(self.model.index(last_row, 1), self.zaposlenik_rb)
            self.model.setData(self.model.index(last_row, 3), self.godina)
            self.table.scrollTo(self.model.index(last_row, 0))
            return self.table.setCurrentIndex(self.model.index(last_row, 2))
        QtWidgets.QMessageBox().critical(None, 'Iskorišten godišnji',
                                         'Zaposlenik je iskoristio sve dane godišnjeg odmora', QtWidgets.QMessageBox.Ok)

    def spremi_promjene(self):
        dates = [self.model.data(self.model.index(row, 2)) for row in range(self.model.rowCount())]
        if not self.model.isDirty():
            return False
        if len(dates) != len(set(dates)):  # Provjera unique vrijednosti
            return QtWidgets.QMessageBox().critical(None, 'Duplicirana vrijednost', 'Uneseni datum već postoji ',
                                                    QtWidgets.QMessageBox.Ok)
        self.model.submitAll()

    def izbrisi_unos(self):
        selected = self.table.selectedIndexes()
        if selected:
            self.model.removeRow(selected[0].row())
            self.model.submitAll()


class DateColumnDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(DateColumnDelegate, self).__init__(parent)
        self.format = "dd.MM.yyyy"
        self.praznici = KalendarWidget.load_praznici()  # Da se ne ucitava za svaku instancu zasebno

    def displayText(self, value, locale):
        return QDate.fromString(value, "yyyy-MM-dd").toString(self.format)

    def createEditor(self, parent, option, index):
        dateedit = QtWidgets.QDateEdit(parent)
        dateedit.setDisplayFormat(self.format)
        dateedit.setCalendarPopup(True)
        dateedit.setCalendarWidget(KalendarWidget(self.praznici))
        dateedit.setAlignment(Qt.AlignCenter)
        return dateedit

    def setEditorData(self, editor, index):
        value = index.data(Qt.DisplayRole)
        editor.setDate(QDate.fromString(value, "yyyy-MM-dd") if value else QDate().currentDate())

    def setModelData(self, editor, model, index):
        date = editor.date().toString('yyyy-MM-dd')
        model.setData(index, date)


class KalendarWidget(QtWidgets.QCalendarWidget):
    def __init__(self, praznici=None, parent=None):
        super(KalendarWidget, self).__init__(parent)
        self.setVerticalHeaderFormat(QtWidgets.QCalendarWidget.NoVerticalHeader)
        self.praznici = praznici or {}
        if not self.praznici:
            self.praznici = self.load_praznici()
        self.postavi_praznike()

    @staticmethod
    def load_praznici():
        try:  # Vraca rijecnik praznika ako postoji, inace prazan rijecnik
            with open('holidays.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def postavi_praznike(self):
        char_format = self.weekdayTextFormat(Qt.Saturday)
        for datum, tekst in self.praznici.items():
            char_format.setToolTip(tekst)
            char_format.setFontUnderline(True)
            char_format.setUnderlineColor(Qt.red)
            self.setDateTextFormat(QDate.fromString(datum, Qt.ISODate), char_format)


# Onemogucava izmjenu godine
class GodinaDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return None
