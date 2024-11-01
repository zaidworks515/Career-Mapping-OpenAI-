import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_email(username, pdf_file_path):
    HOST = "smtp.gmail.com"
    PORT = 587
    FROM_EMAIL = "razorshariq@gmail.com"
    TO_EMAIL = "hr1938082@gmail.com"
    # TO_EMAIL = "anaskhankin1999@gmail.com"
    PASSWORD = "xhkjchgrxezlsnvz"

    subject = f"Generated Career Plan from {username}"
    body = f"""
    Dear Admin,

    I wanted to let you know that the user {username} has generated a career plan. The PDF document is attached for your review.

    Please take a moment to review the attached plan and send it to the user once you have completed your evaluation.

    Thank you for your assistance!

    """

    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with open(pdf_file_path, "rb") as pdf_file:
            part = MIMEApplication(pdf_file.read(), Name="career_plan.pdf")
            part['Content-Disposition'] = f'attachment; filename="career_plan.pdf"'
            msg.attach(part)
    except Exception as e:
        print(f"Failed to attach PDF file: {str(e)}")
        return

    try:
        server = smtplib.SMTP(HOST, PORT)
        server.starttls()
        server.login(FROM_EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()

        print("Email sent successfully")

    except Exception as e:
        print(f"Failed to send email: {str(e)}")

