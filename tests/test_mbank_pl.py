import datetime
from decimal import Decimal
from collections import namedtuple
from unittest import mock

import pytest

from ofxstatement.plugins.mbank_pl import MBankPLParser
from ofxstatement.statement import StatementLine

InputLine = namedtuple('InputLine', [
    'data_operacji',
    'data_ksiegowania',
    'opis_operacji',
    'tytul',
    'nadawca_odbiorca',
    'numer_konta',
    'kwota',
    'saldo_po_operacji',
    'trailing_blank_string',
])


class OutputLine(StatementLine):

    def __init__(self, id=None, date=None, memo=None, amount=None,
                 date_user=None, payee=None):
        self.id = id
        self.date = date
        self.memo = memo
        self.amount = amount

        self.date_user = date_user
        self.payee = payee
        self.check_no = None
        self.refnum = None

    def __eq__(self, other):
        for attr in ('id', 'amount', 'date', 'date_user', 'memo', 'payee'):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True


@pytest.fixture
def parser():
    _file = mock.Mock()
    parser = MBankPLParser(_file)
    parser.parsing_header = False
    return parser


@pytest.mark.parametrize(['input_line', 'output_line'], [
    (
        InputLine(
            data_operacji='2019-09-26',
            data_ksiegowania='2019-09-26',
            opis_operacji='BLIK ZAKUP E-COMMERCE',
            tytul='PAYPRO S.A.',
            nadawca_odbiorca='  ',
            numer_konta="''",
            kwota='-340,91',
            saldo_po_operacji='20 477,63',
            trailing_blank_string='',
        ),
        OutputLine(
            id='bfe43d945b128af56a34999a2805aaabda929cf4',
            amount=Decimal('-340.91'),
            date=datetime.datetime(2019, 9, 26, 0, 0),
            date_user=datetime.datetime(2019, 9, 26, 0, 0),
            payee='PAYPRO S.A.',
            memo='BLIK ZAKUP E-COMMERCE',
        ),
    ),
    (
        InputLine(
            data_operacji='2019-09-26',
            data_ksiegowania='2019-09-26',
            opis_operacji='ZWROT Z TYTUŁU PROMOCJI MONEYBACK',
            tytul='PREMIA POLECAMBANK',
            nadawca_odbiorca='  ',
            numer_konta="''",
            kwota='200,00',
            saldo_po_operacji='20 677,63',
            trailing_blank_string='',
        ),
        OutputLine(
            id='43a7c654b3093a5d1ddc185d577aeff471b13437',
            amount=Decimal('200.00'),
            date=datetime.datetime(2019, 9, 26, 0, 0),
            date_user=datetime.datetime(2019, 9, 26, 0, 0),
            payee='PREMIA POLECAMBANK',
            memo='ZWROT Z TYTUŁU PROMOCJI MONEYBACK',
        ),
    ),
    (
        InputLine(
            data_operacji='2019-09-26',
            data_ksiegowania='2019-09-26',
            opis_operacji='ZAKUP PRZY UŻYCIU KARTY',
            tytul='SKLEP SPC NR 112   /WARSZAWA                                          DATA TRANSAKCJI: 2019-09-24',  # noqa
            nadawca_odbiorca='  ',
            numer_konta="''",
            kwota='-6,20',
            saldo_po_operacji='20 671,43',
            trailing_blank_string='',
        ),
        OutputLine(
            id='2bcf876311067e219620a58f48334f771e65eb19',
            amount=Decimal('-6.20'),
            date=datetime.datetime(2019, 9, 26, 0, 0),
            date_user=datetime.datetime(2019, 9, 24, 0, 0),
            payee='SKLEP SPC NR 112',
            memo='ZAKUP PRZY UŻYCIU KARTY',
        ),
    ),
    (
        InputLine(
            data_operacji='2019-09-30',
            data_ksiegowania='2019-09-30',
            opis_operacji='PRZELEW ZEWNĘTRZY PRZYCHODZĄCY',
            tytul='R.500+ Świadczenie wychowawcze za  okres do 2019-09-30.',
            nadawca_odbiorca='URZAD DZIELNICY BEMOWO             UL. POWST. SLASKICH 70  01-381 WARSZAWA',  # noqa
            numer_konta='69103015080000000550002213',
            kwota='500,00',
            saldo_po_operacji='17 455,65',
            trailing_blank_string='',
        ),
        OutputLine(
            id='149466274aaf1ee4f6c203a8ec85724df011f254',
            amount=Decimal('500.00'),
            date=datetime.datetime(2019, 9, 30, 0, 0),
            date_user=datetime.datetime(2019, 9, 30, 0, 0),
            payee='URZAD DZIELNICY BEMOWO UL. POWST. SLASKICH 70 01-381 WARSZAWA - 69103015080000000550002213',  # noqa
            memo='PRZELEW ZEWNĘTRZY PRZYCHODZĄCY - R.500+ Świadczenie wychowawcze za okres do 2019-09-30.',  # noqa
        ),
    ),
    (
        InputLine(
            data_operacji='2019-09-30',
            data_ksiegowania='2019-09-30',
            opis_operacji='PRZELEW ZEWNĘTRZY PRZYCHODZĄCY',
            tytul='Zwrot za piwo',
            nadawca_odbiorca='ORZOŁ MICHAŁ                       UL GOWOROWSKA 17M27  07-410    OSTROŁĘKA',  # noqa
            numer_konta='69116022020000000363113727',
            kwota='23,00',
            saldo_po_operacji='17 478,65',
            trailing_blank_string='',
        ),
        OutputLine(
            id='3aeec2dc5227ce35df9b04944b0350add34e3cb3',
            amount=Decimal('23.00'),
            date=datetime.datetime(2019, 9, 30, 0, 0),
            date_user=datetime.datetime(2019, 9, 30, 0, 0),
            payee='ORZOŁ MICHAŁ UL GOWOROWSKA 17M27 07-410 OSTROŁĘKA - 69116022020000000363113727',  # noqa
            memo='PRZELEW ZEWNĘTRZY PRZYCHODZĄCY - Zwrot za piwo',
        ),
    ),
    (
        InputLine(
            data_operacji='2019-10-01',
            data_ksiegowania='2019-09-30',
            opis_operacji='OPŁATA MIES. ZA POLECENIE ZAPŁATY',
            tytul='""',
            nadawca_odbiorca='"  "',
            numer_konta="''",
            kwota='-2,00',
            saldo_po_operacji='17 336,07',
            trailing_blank_string='',
        ),
        OutputLine(
            id='bab1440baea754d4645a28095579d1026c520b5d',
            amount=Decimal('-2.00'),
            date=datetime.datetime(2019, 9, 30, 0, 0),
            date_user=datetime.datetime(2019, 10, 1, 0, 0),
            payee='OPŁATA MIES. ZA POLECENIE ZAPŁATY',
            memo='',
        ),
    ),
])
def test_mbank_parse_record(parser, input_line, output_line):
    assert parser.parse_record(input_line) == output_line
