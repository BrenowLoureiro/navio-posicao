"""
buscar_posicao.py
Busca a posição (lat/lon) do navio Skandi Recife via MarineTraffic
e envia por email.

Variáveis de ambiente necessárias:
  MMSI=710033160
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

MMSI = os.getenv("MMSI", "710033160")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "brecolo@gmail.com")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "brecolo@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def buscar_posicao_myshiptracking():
    """Busca posição via MyShipTracking (sem autenticação)."""
    url = f"https://www.myshiptracking.com/requests/vesselinfo.php?mmsi={MMSI}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    lat = data.get("LAT") or data.get("lat")
    lon = data.get("LON") or data.get("lon")
    speed = data.get("SPEED") or data.get("speed", "N/A")
    heading = data.get("COURSE") or data.get("course", "N/A")
    timestamp = data.get("TIMESTAMP") or data.get("timestamp", "N/A")
    if lat and lon:
        return {
            "lat": float(lat),
            "lon": float(lon),
            "speed": speed,
            "heading": heading,
            "timestamp": timestamp,
            "source": "MyShipTracking"
        }
    raise ValueError(f"Posição não encontrada na resposta: {data}")


def buscar_posicao_vesselfinder():
    """Fallback: busca via VesselFinder."""
    url = f"https://www.vesselfinder.com/api/pub/vesseltrack/v1?mmsi={MMSI}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list) and len(data) > 0:
        v = data[0]
        return {
            "lat": float(v.get("lat", 0)),
            "lon": float(v.get("lng", 0)),
            "speed": v.get("sog", "N/A"),
            "heading": v.get("cog", "N/A"),
            "timestamp": v.get("time", "N/A"),
            "source": "VesselFinder"
        }
    raise ValueError(f"Posição não encontrada: {data}")


def buscar_posicao():
    """Tenta múltiplas fontes até obter posição."""
    fontes = [
        ("MyShipTracking", buscar_posicao_myshiptracking),
        ("VesselFinder", buscar_posicao_vesselfinder),
    ]
    erros = []
    for nome, fn in fontes:
        try:
            pos = fn()
            print(f"✅ Posição obtida via {nome}")
            return pos
        except Exception as e:
            print(f"⚠️  {nome} falhou: {e}")
            erros.append(f"{nome}: {e}")
    raise RuntimeError("Todas as fontes falharam:\n" + "\n".join(erros))


def google_maps_link(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"


def enviar_email(posicao):
    agora = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    lat = posicao["lat"]
    lon = posicao["lon"]
    speed = posicao["speed"]
    heading = posicao["heading"]
    source = posicao["source"]
    maps_link = google_maps_link(lat, lon)

    assunto = f"🚢 Skandi Recife — Posição {agora}"

    corpo_html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
      <h2>🚢 Posição do Skandi Recife</h2>
      <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        <tr style="background:#f0f0f0">
          <td style="padding:8px; border:1px solid #ddd;"><b>Data/Hora</b></td>
          <td style="padding:8px; border:1px solid #ddd;">{agora}</td>
        </tr>
        <tr>
          <td style="padding:8px; border:1px solid #ddd;"><b>Latitude</b></td>
          <td style="padding:8px; border:1px solid #ddd;">{lat:.6f}°</td>
        </tr>
        <tr style="background:#f0f0f0">
          <td style="padding:8px; border:1px solid #ddd;"><b>Longitude</b></td>
          <td style="padding:8px; border:1px solid #ddd;">{lon:.6f}°</td>
        </tr>
        <tr>
          <td style="padding:8px; border:1px solid #ddd;"><b>Velocidade</b></td>
          <td style="padding:8px; border:1px solid #ddd;">{speed} nós</td>
        </tr>
        <tr style="background:#f0f0f0">
          <td style="padding:8px; border:1px solid #ddd;"><b>Rumo</b></td>
          <td style="padding:8px; border:1px solid #ddd;">{heading}°</td>
        </tr>
        <tr>
          <td style="padding:8px; border:1px solid #ddd;"><b>MMSI</b></td>
          <td style="padding:8px; border:1px solid #ddd;">{MMSI}</td>
        </tr>
        <tr style="background:#f0f0f0">
          <td style="padding:8px; border:1px solid #ddd;"><b>Fonte</b></td>
          <td style="padding:8px; border:1px solid #ddd;">{source}</td>
        </tr>
      </table>
      <br>
      <a href="{maps_link}" style="background:#1a73e8; color:white; padding:10px 20px;
         text-decoration:none; border-radius:5px;">
        📍 Ver no Google Maps
      </a>
      <br><br>
      <small style="color:#999;">Enviado automaticamente pelo skill Navio Posição</small>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINO
    msg.attach(MIMEText(corpo_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_REMETENTE, GMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, msg.as_string())

    print(f"✅ Email enviado para {EMAIL_DESTINO}")
    print(f"   Lat: {lat:.6f} | Lon: {lon:.6f}")
    print(f"   Maps: {maps_link}")


def main():
    print(f"🔍 Buscando posição do Skandi Recife (MMSI: {MMSI})...")
    posicao = buscar_posicao()
    print("📧 Enviando email...")
    enviar_email(posicao)
    print("✅ Concluído!")


if __name__ == "__main__":
    main()
