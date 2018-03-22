import smtplib
from email.encoders import encode_base64
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


class Sender:
    def __init__(self, loop, from_addr, smtp_server, smtp_port, smtp_user=None, smtp_passwd=None):
        self.from_addr = from_addr
        self.loop = loop
        self.host = smtp_server
        self.port = smtp_port
        self.user = smtp_user
        self.passwd = smtp_passwd

    def _send_mail(self, job, data):
        msg = MIMEMultipart()
        msg['Subject'] = job.title
        msg['From'] = self.from_addr
        msg['To'] = job.user.kindle_mail
        msg['Date'] = formatdate(localtime=True)

        mobi = MIMEApplication(data)
        encode_base64(mobi)
        mobi.add_header('Content-Disposition',
                        'attachment; filename={id}.{format}'.format(id=job.article, format=job.format))

        msg.attach(mobi)

        smtp = smtplib.SMTP(host=self.host, port=self.port)
        smtp.starttls()
        if self.user is not None:
            smtp.login(self.user, self.passwd)
        smtp.sendmail(self.from_addr, job.user.kindle_mail, msg.as_string())
        smtp.quit()

    async def send_mail(self, job, data):
        return self.loop.run_in_executor(None, self._send_mail, job, data)

    def _send_warning(self, user, config):
        msg = MIMEMultipart()
        msg['Subject'] = "Wallabag-Kindle-Consumer Notice"
        msg['From'] = self.from_addr
        msg['To'] = user.email
        msg['Date'] = formatdate(localtime=True)

        txt = MIMEText(("the Wallabag-Kindle-Consumer for your Wallabag "
                        "account on {wallabag} was not able to refresh "
                        "the access token. Please go to {url}/update and log "
                        "in again to retrieve a new api token.").format(wallabag=config.wallabag_host,
                                                                        url=config.domain))

        msg.attach(txt)

        smtp = smtplib.SMTP(host=self.host, port=self.port)
        smtp.starttls()
        if self.user is not None:
            smtp.login(self.user, self.passwd)
        smtp.sendmail(self.from_addr, user.email, msg.as_string())
        smtp.quit()

    async def send_warning(self, user, config):
        return self.loop.run_in_executor(None, self._send_warning, user, config)
