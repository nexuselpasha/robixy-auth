# main.py – ROBIXY AUTH API (phra3 özel – 2025)
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import os
import random
import string

app = Flask(__name__)
DB_FILE = "licenses.json"

# Veritabanını yükle
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        licenses = json.load(f)
else:
    licenses = {}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(licenses, f, indent=4)

@app.route("/")
def home():
    return """
    <h1 style="color:#00ff41; font-family:consolas;">ROBIXY AUTH API AKTİF</h1>
    <p>phra3 KRALI TARAFINDAN YAPILDI</p>
    <p>7/24 AÇIK – CRACKLENEMEZ</p>
    """

# LİSANS KONTROL (ROBIXY buraya bağlanacak)
@app.route("/check", methods=["POST"])
def check():
    data = request.json or {}
    key = data.get("key")
    hwid = data.get("hwid", "")

    if not key:
        return jsonify({"success": False, "message": "Anahtar eksik"}), 400

    if key in licenses:
        lic = licenses[key]
        if lic["expiry"] >= datetime.now().strftime("%Y-%m-%d"):
            # İlk girişte HWID kaydet
            if not lic["hwid"] or lic["hwid"] == "any":
                lic["hwid"] = hwid
                save_db()
                return jsonify({
                    "success": True,
                    "user": lic["user"],
                    "expiry": lic["expiry"],
                    "message": "HWID kaydedildi!"
                })
            # HWID kontrol
            if lic["hwid"] == hwid:
                return jsonify({
                    "success": True,
                    "user": lic["user"],
                    "expiry": lic["expiry"]
                })
            else:
                return jsonify({"success": False, "message": "HWID EŞLEŞMEDİ!"})
        else:
            return jsonify({"success": False, "message": "LİSANS SÜRESİ DOLDU"})
    else:
        return jsonify({"success": False, "message": "LİSANS BULUNAMADI"})

# LİSANS EKLEME (Discord botu kullanacak)
@app.route("/add", methods=["POST"])
def add():
    data = request.json or {}
    key = data.get("key")
    user = data.get("user", "Bilinmiyor")
    days = int(data.get("days", 30))
    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    licenses[key] = {
        "user": user,
        "expiry": expiry,
        "hwid": data.get("hwid", "")
    }
    save_db()
    return jsonify({"success": True, "key": key, "expiry": expiry})

# LİSANS SİLME
@app.route("/delete", methods=["POST"])
def delete():
    key = request.json.get("key")
    if key and key in licenses:
        del licenses[key]
        save_db()
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Lisans yok"})

# TÜM LİSANSLAR
@app.route("/list")
def list_all():
    return jsonify(licenses)

# TEST LİSANS OLUŞTUR (ilk kurulum için)
@app.route("/test")
def test_key():
    key = "ROBIXY-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    expiry = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    licenses[key] = {"user": "TEST", "expiry": expiry, "hwid": ""}
    save_db()
    return f"<h2>YENİ TEST LİSANSI:</h2><code style='font-size:20px'>{key}</code><br>7 gün geçerli"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
