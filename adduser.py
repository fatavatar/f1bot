import storage
import sys
import hashlib
import smtplib
import os
from email.mime.text import MIMEText
def send_email(subject, body, sender, recipients, password):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "F1 " + sender
    msg['To'] = ', '.join(recipients)
    smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtp_server.login(sender, password)
    smtp_server.sendmail(sender, recipients, msg.as_string())
    smtp_server.quit()


if len(sys.argv) != 3:
    print("Usage: " + sys.argv[0] + " <name> <email>")
    sys.exit(1)

name=sys.argv[1]
email=sys.argv[2]
print("Adding user " + name + " with email " + email)
salt="f1bot"
m = hashlib.sha1()
m.update(salt.encode())
m.update(name.encode())
if storage.addUser(name, email, m.hexdigest()):
    password = os.environ['GMAIL_PASSWORD']
    sender = os.environ['GMAIL_USER']
    baseurl = os.environ['F1_BASE_URL']
    print("Adding user with code: " + m.hexdigest())
    print("Success!")
    subject = "Welcome to F1!"
    body = """ 
You've been entered into the F1 pick-em tournament (be excited!)

Click the link below to login on your device and make your picks.  
(To use any device with the pick-em website you will need to use this link first)
https://""" + baseurl + "/login/" + m.hexdigest()
    body = body + "\n\nBe sure to bookmark https://" + baseurl + "/ to enter your picks in future weeks\n"
    recipients = [email]
    send_email(subject, body, sender, recipients, password)
else:
    print("Failed!")


