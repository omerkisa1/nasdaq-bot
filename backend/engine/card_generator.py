import json
import logging

from google import genai

from config import settings

logger = logging.getLogger(__name__)

MODELS = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]

SYSTEM_PROMPT = """Sen kısa vadeli momentum trade setuplarını değerlendiren bir analiz motorusun. Sana bir penny hissesinin fiyat verileri, seviyeleri, hacim durumu ve haberleri verilecek. İKİ karar vereceksin:

KARAR 1 — SETUP VAR MI?
Şu koşullardan en az İKİSİ sağlanmıyorsa setup YOK de ve geç:
- Hacim ortalamanın belirgin üstünde (RVOL >= 2) ve fiyat hareketiyle uyumlu
- Fiyat anlamlı bir seviyeye yakın (destek üstü toparlanma VEYA direnç kırılımı + retest)
- Haber katalizörü var VE fiyat hareketi haberle aynı yönde
- Gün içi yapı sağlıklı (VWAP üstünde tutunma, higher-lows, düzenli hacim)

ŞUNLARI GÖRÜRSEN SETUP YOK DE (tuzak filtreleri):
- Fiyat gün içi zirvesinden %15+ düşmüş (pump bitmiş, sen geç kaldın)
- Hacim var ama fiyat gidemiyor (dağıtım/distribution)
- Tek dev mumla gelen hareket, devamı yok (pump&dump riski)
- Haber eski (24 saatten önce) ama fiyat yeni hareketleniyor (manipülasyon riski)
- Spread/likidite şüphesi: hacim düşük, fiyat sıçramalı

KARAR 2 — SETUP VARSA KART ÜRET:
- entry_zone: mevcut fiyata veya mantıklı geri çekilme seviyesine dayalı DAR bölge (genişlik max %3)
- stop: en yakın anlamlı destek ALTINA, ATR'nin 1-2 katı mesafede. Stop mesafesi %15'ten fazlaysa setup YOK de (risk çok büyük).
- target_1: ilk direnç veya 1.5R mesafesi (hangisi yakınsa)
- target_2: ikinci direnç veya 3R mesafesi
- horizon: Setup'ın doğasına göre seç — "30m" | "2h" | "1d" | "2d" | "3d". ASLA 3 günden uzun verme.
  * Gün içi momentum/haber patlaması → 30m veya 2h
  * Kırılım + retest → 1d
  * Taban oluşumu + hacim artışı → 2d-3d
- confidence: 0.0-1.0. Dürüst ol. 0.5 altıysa kart üretme, setup YOK de.
- reasoning: 2-4 cümle Türkçe. Neden bu setup, en büyük risk ne.
- invalidation: Kartı geçersiz kılan koşul (ör: "VWAP altına saatlik kapanış")

ASLA UNUTMA: Emin değilsen setup YOK demek her zaman doğru karardır. Az ve kaliteli kart > çok ve çöp kart. Günde 3-5 kaliteli kart hedefi, 50 çöp kart değil.

SADECE şu JSON'ı dön:
{
  "has_setup": true|false,
  "skip_reason": "setup yoksa tek cümle neden",
  "card": {
    "direction": "long",
    "entry_zone_low": 0.0, "entry_zone_high": 0.0,
    "stop": 0.0, "target_1": 0.0, "target_2": 0.0,
    "horizon": "30m|2h|1d|2d|3d",
    "confidence": 0.0,
    "reasoning": "...", "invalidation": "...",
    "catalyst": "haber varsa tek cümle, yoksa null"
  }
}"""

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def build_user_prompt(symbol: str, snapshot: dict) -> str:
    return json.dumps({"symbol": symbol, **snapshot}, ensure_ascii=False, default=str)


def parse_gemini_response(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Gemini yanıtında JSON bulunamadı")
    return json.loads(cleaned[start : end + 1])


async def generate_card(symbol: str, snapshot: dict) -> dict | None:
    client = _get_client()
    prompt = build_user_prompt(symbol, snapshot)

    for model in MODELS:
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=[SYSTEM_PROMPT, prompt],
            )
            return parse_gemini_response(response.text)
        except Exception as exc:
            logger.warning("Gemini model %s failed for %s: %s", model, symbol, exc)
            continue

    logger.error("Tüm Gemini modelleri %s için başarısız oldu", symbol)
    return None
