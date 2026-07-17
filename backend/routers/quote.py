from fastapi import APIRouter, HTTPException

from providers.quotes import get_quote_with_fallback

router = APIRouter(prefix="/api/quote", tags=["quote"])


@router.get("/{symbol}")
async def get_quote(symbol: str):
    quote = await get_quote_with_fallback(symbol)
    if quote is None:
        raise HTTPException(status_code=502, detail="fiyat verisi alınamadı")
    return quote
