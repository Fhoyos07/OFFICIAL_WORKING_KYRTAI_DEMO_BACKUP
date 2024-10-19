from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import smtplib
import os
import logging
from .file import load_json


def send_email(subject: str,
               body: str = "",
               attachments: [str] = (),
               config_json_path: str = None,
               to: str | list[str] = None,
               username: str = None,
               password: str = None):
    """
    Send email using Gmail account
    Usage:

    from vlad_utils.email import send_email
    send_email(subject="Test by config JSON", config_json_path="etc/config.json")
    send_email(subject="Test by parameters", to="tva1992@gmail.com", username="bot@gmail.com", password="password")
    """
    # read config from JSON (if specified)
    if config_json_path:
        if username or password:
            raise AttributeError('Ambiguous configuration. Use either config json or password.')

        config = load_json(config_json_path)
        username = config['BOT_EMAIL']
        password = config['BOT_PASSWORD']
        if not to:
            to = config['EMAIL_TO']

    to = [to] if isinstance(to, str) else to

    # generate MIME
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = ', '.join(to)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))  # html

    for file_path in attachments:
        with open(file_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
        part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file_path)
        msg.attach(part)

    # send email
    logging.info(f"Sending email: {subject}. From: {username} to: {', '.join(to)}")
    try:
        _make_gmail_request(username, password, to, msg)
        logging.info('Email was sent successfully')
        return True

    except Exception as e:
        logging.error(f'Error sending email: {str(e)}')
        return False


def _make_gmail_request(username: str, password: str, to: list[str], msg: MIMEMultipart):
    server = smtplib.SMTP(host='smtp.gmail.com', port=587)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(from_addr=username, to_addrs=to, msg=msg.as_string())
    server.close()
    return server
