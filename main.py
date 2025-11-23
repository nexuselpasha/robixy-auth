# main.py – ROBIXYENİ ROBIXY AUTH API (phra3 + Grok 4 optimize etti)
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import os
import random
import string
from threading import Lock

# Thread-safe için lock
db_lock = Lock()

app = Flask(__name__)

DB_FILE = "licenses.json"

# Veritabanını güvenli yükle
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            print("Veritabanı bozuk! Yedek alınıyor ve sıfırlanıyor...")
            os.rename(DB_FILE, DB_FILE + ".corrupt")
            return {}
    else:
        return {}

# Global licenses
licenses = load_db()

def save_db():
    with db_lock:
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(licenses, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"DB kaydetme hatası: {e}")

# Ana sayfa
@app.route("/")
def home():
    return """
    <h1 style="color: #00ff00; font-family: Arial;">ROBIXY AUTH API ÇALIŞIYOR!</h1>
    <p>phra3 + Grok 4 tarafından güçlendirildi ✅</p>
    <p>Toplam lisans: <b>{}</b> adet</p>
    <hr>
    <small>Sunucu zamanı: {}</small>
    """.format(len(licenses), datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

# CORS desteği (tarayıcıdan test için şart)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# OPTIONS ön uçuş (CORS)
@app.route("/<path:path>", methods=["OPTIONS"])
def options(path):
    return '', 204

# LİSANS KONTROL (ana endpoint)
@app.route("/check", methods=["POST"])
def check():
    try:
        data = request.get_json(force=True)  # JSON yoksa bile hata vermesin
    except:
        return jsonify({"success": False, "message": "Geçersiz JSON"}), 400

    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"success": False, "message": "key ve hwid gerekli"}), 400

    if key in licenses:
        lic = licenses[key]
        expiry_date = datetime.strptime(lic["expiry"], "%Y-%m-%d")
        
        if expiry_date >= datetime.now():
            # İlk girişte HWID kaydet
            if not lic["hwid"] or lic["hwid"] in ["", "any"]:
                lic["hwid"] = hwid
                save_db()
                return jsonify({
                    "success": True,
                    "user": lic["user"],
                    "expiry": lic["expiry"],
                    "message": "İlk giriş başarılı, HWID kaydedildi!"
                })

            # HWID kontrol
            if lic["hwid"] == hwid:
                return jsonify({
                    "success": True,
                    "user": lic["user"],
                    "expiry": lic["expiry"],
                    "message": "Giriş başarılı!"
                })
            else:
                return jsonify({
                    "success": False, 
                    "message": "HWID eşleşmedi! Farklı bilgisayar."
                })
        else:
            return jsonify({"success": False, "message": "Lisans süresi dolmuş!"})
    else:
        return jsonify({"success": False, "message": "Lisans bulunamadı!"})

# Diğer endpointler aynı ama daha güvenli
@app.route("/add", methods=["POST"])
def add():
    try:
        data = request.get_json(force=True)
        key = data.get("key")
        user = data.get("user", "Bilinmiyor")
        days = int(data.get("days", 30))

        if not key:
            return jsonify({"success": False, "message": "key gerekli"}), 400

        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        licenses[key] = {
            "user": user,
            "expiry": expiry,
            "hwid": ""
        }
        save_db()
        return jsonify({"success": True, "key": key, "user": user, "expiry": expiry})
    except:
        return jsonify({"success": False, "message": "Hatalı istek"}), 400

@app.route("/resethwid", methods=["POST"])
def reset_hwid():
    try:
        data = request.get_json(force=True)
        key = data.get("key")
        if key in licenses:
            licenses[key]["hwid"] = ""
            save_db()
            return jsonify({"success": True, "message": "HWID sıfırlandı"})
        return jsonify({"success": False})
    except:
        return jsonify({"success": False})

@app.route("/list")
def list_all():
    return jsonify(licenses)

@app.route("/create")
def create_test():
    key = "ROBIXY-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=16))
    expiry = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    licenses[key] = {"user": "TEST", "expiry": expiry, "hwid": ""}
    save_db()
    return f"<b>Yeni test lisansı:</b> <code>{key}</code> → {expiry}"

# Hata yakalama
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "message": "Endpoint bulunamadı"}), 404

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║     ROBIXY AUTH API BAŞLADI!         ║
    ║       phra3 + Grok 4 Edition         ║
    ╚══════════════════════════════════════╝
    """)
    # PORT'U ortam değişkeninden al (Render, Railway, VPS vs için)
    port = int(os.environ.get("PORT", 8080))
    # Production için Waitress veya Gunicorn önerilir ama yerel için debug=True
    app.run(host='0.0.0.0', port=port, debug=False)
