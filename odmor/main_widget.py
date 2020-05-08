from datetime import datetime

from PyQt5.QtCore import QSortFilterProxyModel, Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtSql import QSqlQueryModel, QSqlQuery
from PyQt5.QtWidgets import QTableView, QVBoxLayout, QLineEdit, QHBoxLayout, QSpinBox, QGroupBox, QLabel, QHeaderView
from PyQt5.QtWidgets import QWidget, QPushButton, QMessageBox

from odmor.dialogs import DialogUnosZaposlenika, DialogPregledGodisnjeg, DialogPregledZaPeriod


class QueryModel(QSqlQueryModel):
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.TextAlignmentRole):
            return None
        if role == Qt.TextAlignmentRole:
            if index.column() in (1, 2):
                return Qt.AlignLeft | Qt.AlignVCenter
            return Qt.AlignCenter | Qt.AlignVCenter
        return super(QueryModel, self).data(index, role)


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)
        self.setWindowTitle('Godišnji odmor zaposlenika')
        self.resize(1200, 600)

        self.godina_odmora = self.trenutna_godina

        self.model = QueryModel()
        self.set_model_data(init=True)
        self.model.setHeaderData(0, Qt.Horizontal, 'Rb')
        self.model.setHeaderData(1, Qt.Horizontal, 'Ime')
        self.model.setHeaderData(2, Qt.Horizontal, 'Prezime')
        self.model.setHeaderData(3, Qt.Horizontal, 'Ukupno dana')
        self.model.setHeaderData(4, Qt.Horizontal, 'Iskorišteno')

        self.proxy = QSortFilterProxyModel()
        self.proxy.setSortLocaleAware(True)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.table = QTableView()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setFixedWidth(40)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setModel(self.proxy)

        self.line_pretrazi = QLineEdit()
        self.line_pretrazi.setMaximumWidth(400)
        self.line_pretrazi.setFixedHeight(24)
        self.line_pretrazi.setPlaceholderText(' Ime ili prezime zaposlenika')

        self.spin_godina = QSpinBox()
        self.spin_godina.setMinimumWidth(100)
        self.spin_godina.setRange(2019, 2029)
        self.spin_godina.setButtonSymbols(QSpinBox.NoButtons)
        self.spin_godina.setAlignment(Qt.AlignCenter)
        self.spin_godina.setValue(self.godina_odmora)

        self.btn_nova_god = QPushButton(' Otvori godinu ')
        self.btn_nova_god.setToolTip('Otvaranje nove godine za unos godišnjeg odmora')
        self.btn_nova_god.hide()

        self.lbl_godina = QLabel(f'Godišnji odmor {self.godina_odmora}/{self.godina_odmora + 1} ')
        font = self.lbl_godina.font()
        font.setPointSize(15)
        self.lbl_godina.setFont(font)
        self.setup_ui()

    def setup_ui(self):
        btn_unos = QPushButton('Novi unos')
        btn_unos.setIcon(QIcon(':icons/user.png'))
        btn_unos.setFixedHeight(30)
        btn_unos.setIconSize(QSize(20, 20))
        btn_unos.setToolTip('Novi unos zaposlenika')

        btn_uredi = QPushButton('Uredi')
        btn_uredi.setFixedHeight(30)
        btn_uredi.setIcon(QIcon(':icons/edit.png'))
        btn_uredi.setIconSize(QSize(18, 18))
        btn_uredi.setToolTip('Uredi podatke zaposlenika')

        btn_izbrisi = QPushButton('Izbriši')
        btn_izbrisi.setFixedHeight(30)
        btn_izbrisi.setIcon(QIcon(':icons/delete.png'))
        btn_izbrisi.setIconSize(QSize(18, 18))
        btn_izbrisi.setToolTip('Izbriši zaposlenika')

        btn_pregled = QPushButton('Pregled')
        btn_pregled.setFixedHeight(30)
        btn_pregled.setIcon(QIcon(':icons/search.png'))
        btn_pregled.setIconSize(QSize(18, 18))
        btn_pregled.setToolTip('Pregled zaposlenika koji su na godišnjem')

        hbox_btns = QHBoxLayout()
        hbox_btns.addSpacing(1)
        hbox_btns.addWidget(btn_unos)
        hbox_btns.addWidget(btn_uredi)
        hbox_btns.addWidget(btn_izbrisi)
        hbox_btns.addWidget(btn_pregled)
        hbox_btns.addStretch()
        hbox_btns.addWidget(self.lbl_godina)

        hbox_trazi = QHBoxLayout()
        hbox_trazi.addWidget(self.line_pretrazi)
        hbox_trazi.addStretch()
        hbox_trazi.addWidget(self.btn_nova_god)
        hbox_trazi.addWidget(self.spin_godina)

        vbox_group = QVBoxLayout()
        vbox_group.addLayout(hbox_trazi)
        vbox_group.addWidget(self.table)

        group_table = QGroupBox()
        group_table.setLayout(vbox_group)

        vlayout = QVBoxLayout()
        vlayout.addSpacing(5)
        vlayout.addLayout(hbox_btns)
        vlayout.addSpacing(-10)
        vlayout.addWidget(group_table)
        self.setLayout(vlayout)

        self.line_pretrazi.textChanged.connect(self.proxy.setFilterRegExp)
        self.spin_godina.valueChanged.connect(self.godina_changed)
        self.table.doubleClicked.connect(self.prikazi_godisnji)
        btn_unos.clicked.connect(self.novi_zaposlenik)
        btn_uredi.clicked.connect(self.uredi_zaposlenika)
        btn_izbrisi.clicked.connect(self.izbrisi_korisnika)
        btn_pregled.clicked.connect(DialogPregledZaPeriod.exec_dialog)
        self.btn_nova_god.clicked.connect(self.otvori_godinu)

    @property
    def trenutna_godina(self):
        datum = datetime.now().date()
        return datum.year if datum.month > 6 else datum.year - 1

    def otvori_godinu(self):
        msg = QMessageBox(QMessageBox.Question, 'Novi godišnji',
                          f'Jeste li sigurni da želite otvoriti {self.godina_odmora}. godinu za unos godišnjeg?',
                          QMessageBox.Yes | QMessageBox.No)
        msg.button(QMessageBox.Yes).setText('Otvori')
        msg.button(QMessageBox.No).setText('Odustani')
        if msg.exec_() == QMessageBox.Yes:
            query = QSqlQuery(f"select rb from ukupno_dana where godina = {self.godina_odmora - 1} limit 1;")
            if query.next() and query.record().value(0):  # Ako postoje zapisi u prethodnoj godini
                query.exec_(f"insert into ukupno_dana select null, zaposlenik_rb, {self.godina_odmora}, br_dana "
                            f"from ukupno_dana where godina = {self.godina_odmora - 1};")
                self.set_model_data()
            else:
                QMessageBox.critical(None, 'Novi godišnji',
                                     'Prethodna godina za unos godišnjeg odmora nije otvorena', QMessageBox.Ok)

    def set_model_data(self, init=False):
        self.model.setQuery(
            f"""SELECT z.rb, z.ime, z.prezime, ud.br_dana, count(o.godina) as iskoristeno FROM zaposlenici z 
            left join ukupno_dana ud on z.rb = ud.zaposlenik_rb and ud.godina = {self.godina_odmora}
            left join odmor o on z.rb = o.zaposlenik_rb and o.godina = {self.godina_odmora} group by z.rb;""")
        if not init:  # Nije inicijalno postavljanje
            # novi_go=True. Nije otvorena godina, nijedan zaposlenik nema unesene dane godisnjeg
            novi_go = len(set([self.model.data(self.model.index(row, 3)) for row in range(self.model.rowCount())])) == 1
            self.table.setEnabled(False if novi_go else True)
            self.btn_nova_god.setHidden(False if novi_go else True)

    def godina_changed(self, value):
        self.godina_odmora = value
        self.set_model_data()
        self.lbl_godina.setText(f'Godišnji odmor {self.godina_odmora}/{self.godina_odmora + 1} ')

    def prikazi_godisnji(self):
        zaposlenik = [inx.data() for inx in self.table.selectedIndexes()]
        dialog = DialogPregledGodisnjeg(zaposlenik, self.godina_odmora)
        iskoristeno = dialog.model.rowCount()
        dialog.exec_()
        if iskoristeno != dialog.model.rowCount():
            self.set_model_data()

    def novi_zaposlenik(self):
        dialog = DialogUnosZaposlenika()
        if dialog.exec_():
            ime, prez, br_dana, rb = dialog.get_input_data()
            query = QSqlQuery()
            if query.exec_("INSERT INTO zaposlenici (ime, prezime) VALUES ('{}', '{}')".format(ime, prez)):
                last_id = query.lastInsertId()
                query.exec_(f"select distinct godina from ukupno_dana where godina >= {self.trenutna_godina};")
                while query.next():
                    q = QSqlQuery("INSERT INTO ukupno_dana (zaposlenik_rb, godina, br_dana) VALUES ('{}', '{}', '{}')"
                                  .format(last_id, query.value(0), br_dana))
                row_count = self.model.rowCount()
                self.set_model_data()
                self.table.setFocus()
                src_inx = self.proxy.mapFromSource(self.model.index(row_count, 0))
                self.table.selectRow(src_inx.row())
                self.table.setFocus()

    def uredi_zaposlenika(self):
        selected = self.table.selectedIndexes()
        if selected:
            dialog = DialogUnosZaposlenika()
            old_data = [inx.data() for inx in selected]
            dialog.set_zaposlenik_data(old_data)  # iskoristeni dani nisu potrebni
            if dialog.exec_():
                query = QSqlQuery()
                data = [*dialog.get_input_data()]
                br_dana = data.pop(2)
                if old_data[1:3] != data[:2]:  # Izmjenjeno je ime ili prezime
                    query.exec_("UPDATE zaposlenici SET ime='{}', prezime='{}' WHERE rb={};".format(*data))
                if old_data[3] != br_dana:  # Izmjenjeni broj dana godišnjeg
                    query.exec_("UPDATE ukupno_dana SET br_dana={} WHERE zaposlenik_rb={} and godina={};"
                                .format(br_dana, data[2], self.godina_odmora))
                self.set_model_data()
                self.table.selectRow(selected[0].row())
                self.table.setFocus()

    def izbrisi_korisnika(self):
        selected = self.table.selectedIndexes()
        if selected:
            msg = QMessageBox(QMessageBox.Question, 'Potvrda brisanja',
                              'Jeste li sigurni da želite izbrisati odabranog zaposlenika?')
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            obrisi = msg.button(QMessageBox.Yes)
            obrisi.setText('Obriši')
            odustani = msg.button(QMessageBox.No)
            odustani.setText('Odustani')
            if msg.exec_() == QMessageBox.Yes:
                query = QSqlQuery()
                if query.exec_("DELETE FROM zaposlenici WHERE rb={}".format(selected[0].data())):
                    self.set_model_data()
