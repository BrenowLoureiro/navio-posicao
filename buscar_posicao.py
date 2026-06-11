import os, smtplib, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

MMSI               = os.environ["MMSI"]
DATADOCKED_API_KEY = os.environ["DATADOCKED_API_KEY"]
EMAIL_DESTINO      = os.environ["EMAIL_DESTINO"]
EMAIL_REMETENTE    = os.environ["EMAIL_REMETENTE"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

url = f"https://datadocked.com/api/vessels_operations/get-vessel-location?imo_or_mmsi={MMSI}"
r = requests.get(url, headers={"x-api-key": DATADOCKED_API_KEY, "accept": "application/json"}, timeout=15)
r.raise_for_status()

data = r.json()
v    = data.get("detail") or data

lat = float(v["latitude"])
lon = float(v["longitude"])


def decimal_para_gms(decimal, tipo):
    negativo = decimal < 0
    decimal  = abs(decimal)
    graus    = int(decimal)
    minutos  = int((decimal - graus) * 60)
    segundos = round(((decimal - graus) * 60 - minutos) * 60, 1)
    direcao  = ("S" if negativo else "N") if tipo == "lat" else ("W" if negativo else "E")
    return f"{graus}° {minutos}' {segundos}\" {direcao}"


lat_gms = decimal_para_gms(lat, "lat")
lon_gms = decimal_para_gms(lon, "lon")

brt   = timezone(timedelta(hours=-3))
agora = datetime.now(brt).strftime("%d/%m/%Y %H:%M BRT")
maps  = f"https://www.google.com/maps?q={lat},{lon}"

html = f"""<html><body style="font-family:Arial,sans-serif;color:#333;max-width:400px;margin:0 auto;">
<h2 style="color:#1a73e8;">🚢 Skandi Recife</h2>
<p><b>📅 Data/Hora:</b> {agora}</p>
<p><b>🌐 Latitude:</b> {lat_gms}</p>
<p><b>🌐 Longitude:</b> {lon_gms}</p>
<br>
<a href="{maps}" style="background:#1a73e8;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">
  📍 Ver no Google Maps
</a>
<br><br>
<small style="color:#999;">Enviado automaticamente às 06h BRT</small>
</body></html>"""

msg = MIMEMultipart("alternative")
msg["Subject"] = f"🚢 Skandi Recife — {agora}"
msg["From"]    = EMAIL_REMETENTE
msg["To"]      = EMAIL_DESTINO
msg.attach(MIMEText(html, "html"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
    s.login(EMAIL_REMETENTE, GMAIL_APP_PASSWORD)
    s.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, msg.as_string())

print(f"✅ Email enviado! {agora} | {lat_gms} | {lon_gms}")
