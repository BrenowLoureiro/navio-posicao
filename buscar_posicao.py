import os, smtplib, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

MMSI               = os.environ["MMSI"]
DATADOCKED_API_KEY = os.environ["DATADOCKED_API_KEY"]
EMAIL_DESTINO      = os.environ["EMAIL_DESTINO"]
EMAIL_REMETENTE    = os.environ["EMAIL_REMETENTE"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

print(f"MMSI: {MMSI}")
print(f"API Key length: {len(DATADOCKED_API_KEY)}")

url = f"https://datadocked.com/api/vessels_operations/get-vessel-location?imo_or_mmsi={MMSI}"
r = requests.get(url, headers={"x-api-key": DATADOCKED_API_KEY, "accept": "application/json"}, timeout=15)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")
r.raise_for_status()

data = r.json()
v    = data.get("detail") or data

lat  = float(v["latitude"])
lon  = float(v["longitude"])


def decimal_para_gms(decimal, tipo):
    """Converte grau decimal para Graus°Minutos'Segundos'' com direção."""
    negativo = decimal < 0
    decimal  = abs(decimal)
    graus    = int(decimal)
    minutos  = int((decimal - graus) * 60)
    segundos = round(((decimal - graus) * 60 - minutos) * 60, 1)
    if tipo == "lat":
        direcao = "S" if negativo else "N"
    else:
        direcao = "W" if negativo else "E"
    return f"{graus}° {minutos}' {segundos}\" {direcao}"


lat_gms = decimal_para_gms(lat, "lat")
lon_gms = decimal_para_gms(lon, "lon")

brt = timezone(timedelta(hours=-3))
agora = datetime.now(brt).strftime("%d/%m/%Y %H:%M BRT")
maps  = f"https://www.google.com/maps?q={lat},{lon}"
mt    = f"https://www.marinetraffic.com/en/ais/details/ships/mmsi:{MMSI}"

html = f"""<html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:0 auto;">
<h2 style="color:#1a73e8;">🚢 Skandi Recife — {agora}</h2>
<table style="border-collapse:collapse;width:100%;">
  <tr style="background:#f0f0f0">
    <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">📅 Data/Hora</td>
    <td style="padding:10px;border:1px solid #ddd;">{agora}</td>
  </tr>
  <tr>
    <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🌐 Latitude</td>
    <td style="padding:10px;border:1px solid #ddd;">{lat_gms}</td>
  </tr>
  <tr style="background:#f0f0f0">
    <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🌐 Longitude</td>
    <td style="padding:10px;border:1px solid #ddd;">{lon_gms}</td>
  </tr>
  <tr>
    <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">💨 Velocidade</td>
    <td style="padding:10px;border:1px solid #ddd;">{v.get('speed','N/A')} nós</td>
  </tr>
  <tr style="background:#f0f0f0">
    <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🧭 Rumo</td>
    <td style="padding:10px;border:1px solid #ddd;">{v.get('course','N/A')}°</td>
  </tr>
  <tr>
    <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">⚓ Status</td>
    <td style="padding:10px;border:1px solid #ddd;">{v.get('navigationalStatus','N/A')}</td>
  </tr>
  <tr style="background:#f0f0f0">
    <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🏁 Destino</td>
    <td style="padding:10px;border:1px solid #ddd;">{v.get('destination','N/A')}</td>
  </tr>
  <tr>
    <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🕐 ETA</td>
    <td style="padding:10px;border:1px solid #ddd;">{v.get('etaUtc','N/A')}</td>
  </tr>
  <tr style="background:#f0f0f0">
    <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">📡 Posição recebida</td>
    <td style="padding:10px;border:1px solid #ddd;">{v.get('positionReceived','N/A')}</td>
  </tr>
  <tr>
    <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🔎 Fonte AIS</td>
    <td style="padding:10px;border:1px solid #ddd;">{v.get('dataSource','N/A')}</td>
  </tr>
</table>
<br>
<a href="{maps}" style="background:#1a73e8;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;margin-right:10px;">
  📍 Ver no Google Maps
</a>
<a href="{mt}" style="background:#ff6600;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">
  🚢 Ver no MarineTraffic
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

print(f"✅ Email enviado! {lat_gms} | {lon_gms}")
