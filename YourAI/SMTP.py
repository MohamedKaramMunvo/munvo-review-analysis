import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr


def sendEmail(address,subject,message):
    sender_email = "team@youraiplatform.com"
    receiver_email = address
    password = "aD@s788**?kls"

    msg = MIMEMultipart()
    msg['From'] = formataddr(('YourAI', sender_email))
    msg['To'] = receiver_email
    msg['Subject'] = subject
    body = message
    msg.attach(MIMEText(body, 'plain'))

    text = msg.as_string()
    server = smtplib.SMTP('mail.youraiplatform.com', 587)
    server.starttls()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, text)
    server.quit()

