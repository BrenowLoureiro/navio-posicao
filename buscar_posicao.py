"""
buscar_posicao.py
Busca a posição (lat/lon) do navio Skandi Recife via DataDocked API
e envia por email.

Variáveis de ambiente necessárias:
  MMSI=710033160
  DATADOCKED_API_KEY=sua_chave_aqui
  EMAIL_DESTINO=brecolo@gmail.com
  EMAIL_REMETENTE=brecolo@gmail.com
  GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
"""

import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

MMSI               = os.getenv("MMSI", "710033160")
DATADOCKED_API_KEY = os.getenv("DATADOCKED_API_KEY")
EMAIL_DESTINO      = os.getenv("EMAIL_DESTINO", "brecolo@gmail.com")
EMAIL_REMETENTE    = os.getenv("EMAIL_REMETENTE", "brecolo@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def buscar_posicao():
    url = f"https://datadocked.com/api/vessels_operations/get-vessel-location?imo_or_mmsi={MMSI}"
    headers = {
        "accept": "application/json",
        "x-api-key": DATADOCKED_API_KEY
    }
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    v = data.get("detail", {})

    lat  = v.get("latitude")
    lon  = v.get("longitude")
    if not lat or not lon:
        raise ValueError(f"Posição não encontrada: {data}")

    return {
        "name":   v.get("name", "Skandi Recife"),
        "lat":    float(lat),
        "lon":    float(lon),
        "speed":  v.get("speed", "N/A"),
        "course": v.get("course", "N/A"),
        "heading":v.get("heading", "N/A"),
        "status": v.get("navigationalStatus", "N/A"),
        "dest":   v.get("destination", "N/A"),
        "eta":    v.get("etaUtc", "N/A"),
        "pos_recv":v.get("positionReceived", "N/A"),
        "source": v.get("dataSource", "N/A"),
    }


def enviar_email(p):
    agora      = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    maps_link  = f"https://www.google.com/maps?q={p['lat']},{p['lon']}"
    mt_link    = f"https://www.marinetraffic.com/en/ais/details/ships/mmsi:{MMSI}"

    assunto = f"🚢 Skandi Recife — Posição {agora}"

    corpo_html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:0 auto;">
      <h2 style="color:#1a73e8;">🚢 Posição do Skandi Recife</h2>
      <table style="border-collapse:collapse;width:100%;">
        <tr style="background:#f0f0f0">
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">📅 Data/Hora</td>
          <td style="padding:10px;border:1px solid #ddd;">{agora}</td>
        </tr>
        <tr>
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🌐 Latitude</td>
          <td style="padding:10px;border:1px solid #ddd;">{p['lat']:.6f}°</td>
        </tr>
        <tr style="background:#f0f0f0">
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🌐 Longitude</td>
          <td style="padding:10px;border:1px solid #ddd;">{p['lon']:.6f}°</td>
        </tr>
        <tr>
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">💨 Velocidade</td>
          <td style="padding:10px;border:1px solid #ddd;">{p['speed']} nós</td>
        </tr>
        <tr style="background:#f0f0f0">
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🧭 Rumo</td>
          <td style="padding:10px;border:1px solid #ddd;">{p['course']}°</td>
        </tr>
        <tr>
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">⚓ Status</td>
          <td style="padding:10px;border:1px solid #ddd;">{p['status']}</td>
        </tr>
        <tr style="background:#f0f0f0">
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🏁 Destino</td>
          <td style="padding:10px;border:1px solid #ddd;">{p['dest']}</td>
        </tr>
        <tr>
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🕐 ETA</td>
          <td style="padding:10px;border:1px solid #ddd;">{p['eta']}</td>
        </tr>
        <tr style="background:#f0f0f0">
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">📡 Posição recebida</td>
          <td style="padding:10px;border:1px solid #ddd;">{p['pos_recv']}</td>
        </tr>
        <tr>
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">🔎 Fonte AIS</td>
          <td style="padding:10px;border:1px solid #ddd;">{p['source']}</td>
        </tr>
        <tr style="background:#f0f0f0">
          <td style="padding:10px;border:1px solid #ddd;font-weight:bold;">📡 MMSI</td>
          <td style="padding:10px;border:1px solid #ddd;">{MMSI}</td>
        </tr>
      </table>
      <br>
      <a href="{maps_link}" style="background:#1a73e8;color:white;padding:10px 20px;
         text-decoration:none;border-radius:5px;margin-right:10px;">
        📍 Ver no Google Maps
      </a>
      <a href="{mt_link}" style="background:#ff6600;color:white;padding:10px 20px;
         text-decoration:none;border-radius:5px;">
        🚢 Ver no MarineTraffic
      </a>
      <br><br>
      <small style="color:#999;">Enviado automaticamente às 06h BRT</small>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = EMAIL_REMETENTE
    msg["To"]      = EMAIL_DESTINO
    msg.attach(MIMEText(corpo_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_REMETENTE, GMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, msg.as_string())

    print(f"✅ Email enviado para {EMAIL_DESTINO}")
    print(f"   {p['name']} | Lat: {p['lat']:.6f} | Lon: {p['lon']:.6f}")
    print(f"   Maps: {maps_link}")


def main():
    print(f"🔍 Buscando posição do Skandi Recife (MMSI: {MMSI})...")
    posicao = buscar_posicao()
    print(f"✅ Posição obtida: {posicao['lat']:.6f}, {posicao['lon']:.6f}")
    print("📧 Enviando email...")
    enviar_email(posicao)
    print("✅ Concluído!")


if __name__ == "__main__":
    main()
