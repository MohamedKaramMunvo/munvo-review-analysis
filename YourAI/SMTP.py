import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import sib_api_v3_sdk


SENDINBLUE_SMTP_TOKEN = "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"

def sendEmail(address,subject,message):

    sender_email = "team@youraiplatform.com"
    receiver_email = address
    password = "aD@s788**?kls"

    # Send email with SENDINBLUE
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = SENDINBLUE_SMTP_TOKEN

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    subject = subject
    html_content = message

    # replace \n with <br> because its HTML content
    html_content = html_content.replace("\n","<br>")

    sender = {"name": "YourAI Platform", "email": sender_email}
    to = [{"email": receiver_email}]
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to,
                                                   html_content=html_content, sender=sender, subject=subject)

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
    except Exception as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
        # if the email fails then send in with the normal way
        msg = MIMEMultipart()
        msg['From'] = formataddr(('YourAI Platform', sender_email))
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




