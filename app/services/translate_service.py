import requests

class TranslateService:
    def translate(self,text, target="km"):
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target,
            "dt": "t",
            "q": text
        }

        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            data = res.json()
            # 🔥 FIX: join ALL translated chunks (not just [0][0][0])
            translated = "".join([item[0] for item in data[0] if item[0]])
            return translated
        except:
            return text 