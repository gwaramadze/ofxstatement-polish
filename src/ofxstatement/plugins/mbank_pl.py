import csv
from datetime import datetime
import re

from ofxstatement import statement
from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin


class MBankPLPlugin(Plugin):
    """Polish mBank (www.mbank.pl) CSV history plugin
    """

    def get_parser(self, filename):
        encoding = self.settings.get('charset', 'cp1250')
        f = open(filename, "r", encoding=encoding)
        parser = MBankPLParser(f)
        parser.statement.bank_id = self.settings.get('bank', 'BREXPLPWMUL')
        return parser


class MBankPLParser(CsvStatementParser):
    mappings = {
        "date_user": 0,
        "date": 1,
        "amount": 6,
    }

    date_format = "%Y-%m-%d"

    def parse(self):
        self.parsing_header = True
        self.last_line = None
        return super(MBankPLParser, self).parse()

    def split_records(self):
        return csv.reader(self.fin, delimiter=';', quotechar='"')

    def parse_record(self, line):

        if self.parsing_header:
            return self.parse_header(line)

        if len(line) != 9:
            return None

        # footer
        if line[6] == "#Saldo końcowe":
            self.statement.end_balance = self.parse_float(line[7])
            return None

        sl = super(MBankPLParser, self).parse_record(line)

        title, date_user = self.parse_title(line[3])
        if date_user:
            sl.date_user = datetime.strptime(date_user, self.date_format)

        payee = ' '.join(line[4].split())
        if not re.search('[a-zA-Z]', payee):
            payee = None

        memo = ' '.join(line[2].split())

        sl.payee = payee or title or memo
        account_number = line[5].strip("'")
        if account_number:
            sl.payee = ' - '.join([sl.payee, account_number])

        sl.memo = memo if payee or title else ''
        if payee and title:
            sl.memo = ' - '.join([sl.memo, title])

        # generate transaction id out of available data
        sl.id = statement.generate_transaction_id(sl)

        if line[2].startswith("PRZ"):
            sl.trntype = "XFER"
        elif line[2].startswith("WYPŁATA"):
            sl.trntype = "ATM"
        elif line[2].startswith("ZAKUP"):
            sl.trntype = "DEBIT"
        elif line[2].startswith("PODATEK"):
            sl.trntype = "FEE"
        elif line[2].startswith("OPŁATA"):
            sl.trntype = "SRVCHG"
        elif line[2].startswith("KAPITALIZACJA"):
            sl.trntype = "INT"

        return sl

    def parse_float(self, value):
        return super(MBankPLParser, self).parse_float(
            re.sub("[ .a-zA-Z]", "", value).replace(",", "."))

    def parse_header(self, line):

        stmt = self.statement
        last = self.last_line

        if not line:
            pass
        elif line[0] == "Łącznie":
            stmt.total_amount = self.parse_float(line[2])
        elif line[0] == "#Saldo początkowe":
            stmt.start_balance = self.parse_float(line[1])
        elif line[0] == "#Data operacji":
            stmt.end_balance = stmt.start_balance + stmt.total_amount
            self.parsing_header = False
        elif not last:
            pass
        elif last[0] == "#Za okres:":
            stmt.start_date = datetime.strptime(line[0], "%d.%m.%Y")
            stmt.end_date = datetime.strptime(line[1], "%d.%m.%Y")
        elif last[0] == "#Waluta":
            stmt.currency = line[0].strip()
        elif last[0] == "#Numer rachunku":
            stmt.account_id = "PL" + line[0].replace(" ", "")

        self.last_line = line

        return None

    def parse_title(self, title):
        title = ' '.join(title.strip().split())
        title, *date = title.split(' DATA TRANSAKCJI: ')
        date = date[0][:10] if date else None
        return self.clean_title(title), date

    def clean_title(self, title):
        title = title.strip()
        if title.endswith('('):
            title = title[:-1].strip()
        if '/' in title:
            title = ''.join(title.split('/')[:-1])
        title = ' '.join(title.split())
        if not re.search('[a-zA-Z]', title):
            return None
        return title
