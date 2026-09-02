import datetime
import secrets
import string
from django.core.mail import EmailMessage


def send_mail(to, subject, message, excel_file=None):
    subject = subject
    msg = EmailMessage(subject, message, to=to)
    msg.content_subtype = "html"
    if excel_file is not None:
        msg.attach(
            f"Nueva solicitud de compra {datetime.datetime.now()}.xlsx",
            excel_file.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    msg.send()


class password_generator:
    @staticmethod
    def generate() -> str:
        letters = string.ascii_letters
        digits = string.digits
        special_chars = string.punctuation

        alphabet = letters + digits + special_chars

        pwd_length = 20

        while True:
            pwd = ""
            for _ in range(pwd_length):
                pwd += "".join(secrets.choice(alphabet))

            if (
                any(char in special_chars for char in pwd)
                and sum(char in digits for char in pwd) >= 2
            ):
                break
        return pwd
