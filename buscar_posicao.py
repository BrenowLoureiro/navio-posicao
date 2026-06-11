import os, smtplib, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

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

v    = r.json()["detail"]
lat  = float(v["latitude"])
lon  = float(v["longitude"])
agora = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
maps = f"https://www.google.com/maps?q={lat},{lon}"

html = f"""<html><body>
<h2>🚢 Skandi Recife — {agora}</h2>
<p><b>Latitude:</b> {lat:.6f}°</p>
<p><b>Longitude:</b> {lon:.6f}°</p>
<p><b>Velocidade:</b> {v.get('speed','N/A')} nós</p>
<p><b>Rumo:</b> {v.get('course','N/A')}°</p>
<p><b>Status:</b> {v.get('navigationalStatus','N/A')}</p>
<p><b>Destino:</b> {v.get('destination','N/A')}</p>
<p><b>ETA:</b> {v.get('etaUtc','N/A')}</p>
<a href="{maps}">📍 Ver no Google Maps</a>
</body></html>"""

msg = MIMEMultipart("alternative")
msg["Subject"] = f"🚢 Skandi Recife — {agora}"
msg["From"]    = EMAIL_REMETENTE
msg["To"]      = EMAIL_DESTINO
msg.attach(MIMEText(html, "html"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
    s.login(EMAIL_REMETENTE, GMAIL_APP_PASSWORD)
    s.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, msg.as_string())

print(f"✅ Email enviado! Lat: {lat} Lon: {lon}")
