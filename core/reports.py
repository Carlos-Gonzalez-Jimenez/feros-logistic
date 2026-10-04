from decimal import Decimal
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from .models import Config
from .serializers import ConfigSerializer


class CommercialInvoicePDF(FPDF):
    """
    Factura Comercial SUMART
    """

    cols = [
        ("No ITEM", 13, "C"),
        ("Referencia", 22, "C"),
        ("Descripción", 45, "L"),
        ("País Origen", 18, "C"),
        ("Cant.\nArtículos", 14, "C"),
        ("Cajas/Art\nículo", 14, "C"),
        ("Precio\nUnitario\n(USD)", 18, "C"),
        ("Importe\n(USD)", 20, "C"),
        ("Peso Neto Total\ndel Ítem (Kgs)", 22, "C"),
        ("Peso Bruto\nTotal del Ítem (Kgs)", 22, "C"),
        ("Unidad de\nMedida", 15, "C"),
        ("Paratida\nArancelaria", 20, "C"),
        ("Número del\nbulto", 15, "C"),
        ("Cantidad de\nBulto", 16, "C"),
    ]
    line_h = 5.5

    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=10)
        self.set_margins(5, 5, 5)
        self.set_font("Helvetica", "", 8)
        self.config = Config.objects.first()
        self.config_data = ConfigSerializer(self.config).data
        self.add_page()
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        logo = self.config.logo_dark
        logo_path = logo.path
        logo_w = 20
        logo_h = 20
        logo_x = self.w - self.r_margin - logo_w
        logo_y = self.t_margin
        self.image(logo_path, x=logo_x, y=logo_y, w=logo_w, h=logo_h)
        self.ln(logo_y + logo_h - self.get_y() + 2)

    def footer(self):
        pass

    def _cell(self, w, h, text, align="C", bold=False, border=1, fill=False):
        self.set_font("Helvetica", "B" if bold else "", 8)
        self.cell(
            w,
            h,
            text,
            border=border,
            align=align,
            fill=fill,
            new_x=XPos.RIGHT,
            new_y=YPos.TOP,
        )

    def _label_value_row(self, label, value, label_w, value_w, h=None):
        h = h or self.line_h
        self.set_font("Helvetica", "", 8)
        self.cell(label_w, h, f" {label}", border=1, align="L")
        self.set_font("Helvetica", "", 8)
        self.cell(
            value_w,
            h,
            f"{value if value is not None else ''}",
            border=1,
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )


def generate_commercial_invoice_pdf(commercial_invoice) -> bytes:

    pdf = CommercialInvoicePDF()

    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    x0 = pdf.l_margin
    y0 = pdf.get_y()

    pdf.rect(x0, y0, page_w, 18)

    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(x0, y0 + 18)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(
        page_w,
        7,
        "FACTURA COMERCIAL",
        border=1,
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    y_block = pdf.get_y()
    label_w = 38
    value_w = 68
    block_w = label_w + value_w
    right_col_w = page_w - block_w

    containers = ""
    for container in commercial_invoice.containers.all():
        containers += f" {container.container_number} /"

    total_packages = 0
    total_fob_amount = 0
    sale_orders = commercial_invoice.booking.sale_orders.all()
    for sale_order in sale_orders:
        packages = sum(item.quantity for item in sale_order.sale_order_items.all())
        fob_amount = sum(invoice.total_amount for invoice in sale_order.invoices.all())
        total_packages += packages
        total_fob_amount += fob_amount

    total_freight = sum(
        invoice.total_amount for invoice in commercial_invoice.booking.invoices.all()
    )

    total_gross_weight = sum(
        invoice_item.gross_weight
        for invoice_item in commercial_invoice.invoice_items.all()
    )
    total_net_weight = sum(
        invoice_item.net_weight
        for invoice_item in commercial_invoice.invoice_items.all()
    )

    rows = [
        ("Nombre del Proveedor:", pdf.config.business_name),
        ("Importador:", commercial_invoice.importing_company.name),
        ("Cliente:", commercial_invoice.customer.business_name),
        ("Contrato:", commercial_invoice.contract),
        ("B/L:", commercial_invoice.booking.shipping_company_invoices[0].bl_number),
        ("Contenedor(es):", containers),
        ("Condición de Entrega:", commercial_invoice.incoterms.abbreviation),
        ("Total de Bultos:", total_packages),
        ("Importe FOB:", total_fob_amount),
        ("Peso Bruto:", total_gross_weight),
        ("Peso Neto:", total_net_weight),
        ("Flete:", total_freight),
        ("Seguro:", commercial_invoice.booking.cargo_insurance),
        (
            "Importe CIF:",
            total_fob_amount
            + total_freight
            + commercial_invoice.booking.cargo_insurance,
        ),
        ("Moneda:", getattr(commercial_invoice, "currency", "USD")),
        ("Núm. de Factura:", commercial_invoice.bill_number),
    ]

    block_start_y = y_block
    total_block_h = len(rows) * pdf.line_h

    pdf.set_xy(x0 + block_w, y_block)
    date_str = f"Fecha: {commercial_invoice.emission_date if commercial_invoice.emission_date else ''}"
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(
        right_col_w,
        7,
        date_str,
        border=1,
        align="R",
        new_x=XPos.LMARGIN,
        new_y=YPos.TOP,
    )

    pdf.set_xy(x0 + block_w, y_block + 7)
    pdf.cell(
        right_col_w, total_block_h - 7, "", border=1, new_x=XPos.LMARGIN, new_y=YPos.TOP
    )

    for label, value in rows:
        # pdf.set_xy(x0, pdf.get_y() if False else None)

        y = pdf.get_y()
        pdf.set_xy(x0, y)
        pdf._label_value_row(label, value, label_w, value_w)

    pdf.ln(1)

    header_y = pdf.get_y()
    header_h = 12
    pdf.set_xy(x0, header_y)
    pdf.set_font("Helvetica", "B", 7)
    for title, w, _align in pdf.cols:
        x_before = pdf.get_x()
        y_before = pdf.get_y()
        pdf.multi_cell(
            w, 4, title, border=1, align="C", new_x=XPos.RIGHT, new_y=YPos.TOP
        )
        pdf.set_xy(x_before + w, y_before)
    pdf.set_xy(x0, header_y + header_h)

    row_h = 14
    items = list(commercial_invoice.invoice_items.all())
    for item in items:
        y = pdf.get_y()
        if y + row_h > pdf.h - 20:
            pdf.add_page()
            y = pdf.get_y()

        product = getattr(item.product, "display_name", None) or str(item.product)
        row_data = [
            ("1", "C"),
            (getattr(item, "reference", ""), "C"),
            (product, "L"),
            (
                getattr(item, "country_of_origin", getattr(item, "origin_country", "")),
                "C",
            ),
            (str(item.quantity), "C"),
            (str(getattr(item, "boxes", item.quantity)), "C"),
            (item.unit_price, "C"),
            (item.amount, "C"),
            (item.net_weight, "C"),
            (item.gross_weight, "C"),
            (str(getattr(item, "measurement_unit", "")), "C"),
            (getattr(item, "tariff_code", ""), "C"),
            ("", "C"),
            (str(getattr(item, "quantity_per_package", item.quantity)), "C"),
        ]
        pdf.set_xy(x0, y)
        for (title, w, _a), (text, align) in zip(pdf.cols, row_data):
            pdf.set_font("Helvetica", "", 7)
            pdf.multi_cell(
                w,
                row_h,
                str(text),
                border=1,
                align=align,
                new_x=XPos.RIGHT,
                new_y=YPos.TOP,
            )
        pdf.set_xy(x0, y + row_h)

    y = pdf.get_y()

    w_importe = pdf.cols[7][1]
    w_pneto = pdf.cols[8][1]
    w_pbruto = pdf.cols[9][1]
    w_cant = pdf.cols[13][1]
    w_label = page_w - (w_importe + w_pneto + w_pbruto + w_cant)

    totals = [
        (
            "Total FOB USD",
            total_fob_amount,
            total_net_weight,
            total_gross_weight,
            total_packages,
        ),
        (
            "Seguro USD",
            commercial_invoice.booking.cargo_insurance,
            "",
            "",
            "",
        ),
        (
            "Flete",
            total_freight,
            "",
            "",
            "",
        ),
        (
            "Importe CIF USD",
            total_fob_amount
            + total_freight
            + commercial_invoice.booking.cargo_insurance,
            "",
            "",
            "",
        ),
    ]

    # for label, imp, pn, pb, cant in totals:
    #     pdf.set_xy(x0, pdf.get_y())
    #     pdf.set_font("Helvetica", "B", 8)
    #     pdf.cell(w_label, pdf.line_h, label, border=1, align="R")
    #     # pdf.cell(w_importe, pdf.line_h, imp, border=1, align="C")
    #     pdf.cell(w_pneto, pdf.line_h, pn, border=1, align="C")
    #     pdf.cell(w_pbruto, pdf.line_h, pb, border=1, align="C")
    #     pdf.cell(
    #         pdf.cols[10][1] + pdf.cols[11][1] + pdf.cols[12][1],
    #         pdf.line_h,
    #         "",
    #         border=1,
    #     )
    #     pdf.cell(
    #         w_cant,
    #         pdf.line_h,
    #         str(cant),
    #         border=1,
    #         align="C",
    #         new_x=XPos.LMARGIN,
    #         new_y=YPos.NEXT,
    #     )

    return bytes(pdf.output())
