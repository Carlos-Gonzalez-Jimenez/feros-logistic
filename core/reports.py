from fpdf import FPDF
from .models import Config
from .serializers import ConfigSerializer

PRIMARY = (13, 71, 161)
PRIMARY_LIGHT = (227, 236, 250)
ACCENT = (255, 111, 0)
GREY_DARK = (55, 55, 55)
GREY_MED = (130, 130, 130)
GREY_LIGHT = (240, 242, 245)
WHITE = (255, 255, 255)

class ModernCommercialInvoicePDF(FPDF):
    def __init__(self, invoice):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.invoice = invoice
        self.config = Config.objects.first()
        self.config_data = ConfigSerializer(self.config).data
        self.logo_path = self.config.logo_dark.path
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(12, 12, 12)

    @staticmethod
    def _fmt_date(value):
        if not value:
            return ""
        if isinstance(value, str):
            return value
        return value.strftime("%d/%m/%Y")

    @staticmethod
    def _fmt(value, decimals=2):
        if value in (None, ""):
            return "0.00"
        try:
            return f"{float(value):,.{decimals}f}"
        except (TypeError, ValueError):
            return str(value)

    def _txt(self, w, h, text, **kwargs):
        text = str(text)
        self.cell(w, h, text, **kwargs)

    def _multi(self, w, h, text, **kwargs):
        text = str(text)
        self.multi_cell(w, h, text, **kwargs)

    def header(self):
        self.set_fill_color(*PRIMARY)
        self.rect(0, 0, 210, 26, style="F")

        if self.logo_path:
            try:
                self.image(self.logo_path, x=12, y=0, h=40)
            except Exception:
                self._draw_brand_text()
        else:
            self._draw_brand_text()

        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 18)
        self.set_xy(120, 6)
        self.cell(78, 8, "FACTURA COMERCIAL", align="R")

        self.set_font("Helvetica", "", 10)
        self.set_xy(120, 15)
        self._txt(78, 5, f"No. {getattr(self.invoice, 'bill_number', '')}", align="R")

        self.set_xy(120, 21)
        self._txt(78, 5, f"Fecha emisión: {self._fmt_date(getattr(self.invoice, 'emission_date', ''))}", align="R")
        
        self.set_text_color(*GREY_DARK)
        self.set_y(32)

    def _draw_brand_text(self):
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 20)
        self.set_xy(14, 6)
        self.cell(80, 8, "SUMART", align="L")
        self.set_font("Helvetica", "", 8)
        self.set_xy(14, 15)
        self.cell(80, 5, "SUMART GRUPO S.U.R.L.", align="L")

    def footer(self):
        self.set_y(-12)
        self.set_draw_color(*GREY_MED)
        self.set_line_width(0.2)
        self.line(12, self.get_y() - 1, 198, self.get_y() - 1)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GREY_MED)
        self.cell(
            0, 5, f"Factura Comercial  |  Pagina {self.page_no()}/{{nb}}", align="C"
        )

    def _draw_info_cards(self):
        booking = getattr(self.invoice, "booking", None)
        customer = getattr(self.invoice, "customer", None)
        importing_company = getattr(self.invoice, "importing_company", None)
        currency = getattr(getattr(self.invoice, "currency", None), "initials", "USD")
        incoterms = getattr(self.invoice, "incoterms", None)
        port_discharge = booking.port_discharge
        shipping_company_invoices = self.invoice.booking.shipping_company_invoices
        bl = shipping_company_invoices[0].bl_number

        y0 = self.get_y()
        card_h = 30
        card_w = 59
        gap = 4

        self._draw_card(12, y0, card_w, card_h, "PROVEEDOR / EXPORTADOR")
        self.set_xy(16, y0 + 8)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*GREY_DARK)
        self._multi(card_w - 8, 4.5, getattr(self.config, "business_name", ""))
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GREY_MED)
        address = getattr(self.config, "business_address", "")
        self.set_x(16)
        self._multi(card_w - 8, 4, address)

        x_importer = 12 + card_w + gap
        self._draw_card(x_importer, y0, card_w, card_h, "IMPORTADOR")
        self.set_xy(x_importer + 4, y0 + 8)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*GREY_DARK)
        self._multi(card_w - 8, 4.5, getattr(importing_company, "name", ""))
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GREY_MED)
        address = getattr(importing_company, "address", "")
        self.set_x(x_importer + 4)
        self._multi(card_w - 8, 4, address)

        x_client = 76 + card_w + gap
        self._draw_card(x_client, y0, card_w, card_h, "CLIENTE / CONSIGNATARIO")
        self.set_xy(x_client + 4, y0 + 8)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*GREY_DARK)
        self._multi(card_w - 8, 4.5, getattr(customer, "business_name", ""))
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GREY_MED)
        self.set_x(x_client + 4)
        self._multi(card_w - 8, 4, getattr(customer, "address", ""))
        self.set_y(y0 + card_h + 4)

        y1 = self.get_y()
        small_h = 22
        small_w = (186 - 2 * gap) / 3

        containers = " / ".join(
            c.container_number for c in booking.containers.all()
        )

        cards = [
            (
                "CONTRATO / B/L",
                f"Contrato: {getattr(self.invoice, 'contract', '')}\n" f"B/L: {bl}",
            ),
            ("CONTENEDORES", containers or "-"),
            (
                "INCOTERM / MONEDA",
                f"{getattr(incoterms, 'abbreviation', "")} {port_discharge.name} |  {currency}\n",
            ),
        ]

        for i, (title, value) in enumerate(cards):
            x = 12 + i * (small_w + gap)
            self._draw_card(x, y1, small_w, small_h, title)
            self.set_xy(x + 4, y1 + 8)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*GREY_DARK)
            self._multi(small_w - 8, 4, value)

        self.set_y(y1 + small_h + 6)

    def _draw_card(self, x, y, w, h, title, fill=GREY_LIGHT):
        self.set_fill_color(*fill)
        self.set_draw_color(*GREY_LIGHT)
        self.rect(x, y, w, h, style="F")

        self.set_fill_color(*PRIMARY)
        self.rect(x, y, 1.5, h, style="F")

        self.set_xy(x + 4, y + 2)
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*PRIMARY)
        self._txt(w - 8, 4, title)

    def _draw_items_table(self):
        headers = [
            ("#", 8),
            ("REF.", 20),
            ("DESCRIPCION", 70),
            ("CANTIDAD", 14),
            ("P. UNITARIO", 20),
            ("IMPORTE", 22),
            ("P. NETO", 16),
            ("P. BRUTO", 16),
        ]

        self.set_font("Helvetica", "B", 7.5)
        self.set_fill_color(*PRIMARY)
        self.set_text_color(*WHITE)
        for title, w in headers:
            self._txt(w, 8, title, border=0, align="C", fill=True)
        self.ln(8)

        items = list(self.invoice.invoice_items.all())
        totals = {"qty": 0, "net": 0, "gross": 0, "importe": 0, "unit": 0}

        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GREY_DARK)

        for idx, item in enumerate(items, start=1):
            product = getattr(item, "product", None)
            qty = getattr(item, "quantity", 0) or 0
            unit_price = getattr(item, "unit_price", 0) or 0
            net = getattr(item, "net_weight", 0) or 0
            gross = getattr(item, "gross_weight", 0) or 0
            importe = qty * unit_price

            totals["qty"] += qty
            totals["net"] += net
            totals["gross"] += gross
            totals["importe"] += importe
            totals["unit"] += 1

            if idx % 2 == 0:
                self.set_fill_color(248, 249, 251)
            else:
                self.set_fill_color(*WHITE)

            row = [
                (str(idx), 8, "C"),
                (getattr(product, "code_sku", ""), 20, "C"),
                (getattr(product, "name", "")[:62], 70, "L"),
                (f"{qty:,.0f}", 14, "R"),
                (self._fmt(unit_price), 20, "R"),
                (self._fmt(importe), 22, "R"),
                (self._fmt(net), 16, "R"),
                (self._fmt(gross), 16, "R"),
            ]
            y_row = self.get_y()
            x_row = self.l_margin
            desc = row[2][0]
            line_h = 5
            if len(desc) > 42:
                self.set_xy(x_row + 28, y_row + 1)
                self.set_font("Helvetica", "", 7)
                self._multi(58, line_h, desc)
                h_row = max(self.get_y() - y_row + 1, 7)
                self.set_font("Helvetica", "", 8)
            else:
                h_row = 7

            for value, w, align in row:
                self.set_xy(x_row, y_row)
                self._txt(w, h_row, str(value), border=0, align=align, fill=True)
                x_row += w
            self.set_xy(self.l_margin, y_row + h_row)

        self._draw_totals(totals)

    def _draw_totals(self, totals):
        fob = totals["importe"]
        freight = sum(
            invoice.total_amount for invoice in self.invoice.booking.invoices.all()
        )
        insurance = self.invoice.booking.cargo_insurance
        cif = fob + freight + insurance
        currency = getattr(getattr(self.invoice, "currency", None), "initials", "USD")

        y0 = self.get_y() + 4
        box_w = 90
        box_h = 26
        self.set_fill_color(*GREY_LIGHT)
        self.rect(12, y0, box_w, box_h, style="F")
        self.set_fill_color(*PRIMARY)
        self.rect(12, y0, 1.5, box_h, style="F")

        self.set_xy(16, y0 + 2)
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*PRIMARY)
        self._txt(box_w - 8, 4, "RESUMEN")

        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GREY_DARK)
        self.set_xy(16, y0 + 8)
        self._txt(box_w - 8, 4, f"Peso Neto Total:   {self._fmt(totals['net'])} kg")
        self.set_x(16)
        self._txt(box_w - 8, 14, f"Peso Bruto Total:  {self._fmt(totals['gross'])} kg")
        self.set_x(16)
        self._txt(box_w - 8, 24, f"Total de Bultos:   {totals['qty']:,.0f}")

        x_right = 110
        y_right = y0
        w_right = 88

        self.set_fill_color(*PRIMARY)
        self.rect(x_right, y_right, w_right, 8, style="F")
        self.set_xy(x_right, y_right)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self._txt(w_right, 8, "  TOTALES", align="L")

        self.set_text_color(*GREY_DARK)
        self.set_font("Helvetica", "", 8)
        rows = [
            (f"FOB {currency}", self._fmt(fob)),
            (f"Flete {currency}", self._fmt(freight)),
            (f"Seguro {currency}", self._fmt(insurance)),
        ]
        y_r = y_right + 8
        for label, value in rows:
            self.set_fill_color(248, 249, 251)
            self.rect(x_right, y_r, w_right, 6, style="F")
            self.set_xy(x_right + 2, y_r)
            self._txt(w_right - 30, 6, label)
            self.set_xy(x_right + w_right - 28, y_r)
            self._txt(26, 6, value, align="R")
            y_r += 6

        self.set_fill_color(*ACCENT)
        self.rect(x_right, y_r, w_right, 8, style="F")
        self.set_xy(x_right + 2, y_r)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self._txt(w_right - 30, 8, f"CIF {currency}")
        self.set_xy(x_right + w_right - 32, y_r)
        self._txt(30, 8, self._fmt(cif), align="R")


def generate_commercial_invoice_pdf(invoice):
    pdf = ModernCommercialInvoicePDF(invoice)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf._draw_info_cards()
    pdf._draw_items_table()
    return bytes(pdf.output())
