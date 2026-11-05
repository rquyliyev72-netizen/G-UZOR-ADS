# G‘uzorda Ishla — Android ilova (APK)

G‘uzor tumanidagi ish e’lonlari ilovasi.

**Imkoniyatlar:** vakansiyalar ro‘yxati, qidiruv, yo‘nalish bo‘yicha saralash,
e’lon tafsilotlari, qo‘ng‘iroq / Telegram tugmalari, saqlab qo‘yish, ulashish,
ish beruvchilar uchun “E’lon berish” formasi. Internet bo‘lmasa ham ishlaydi.

## APK'ni qayerdan olish
GitHub → **Releases** bo‘limida eng so‘nggi `GuzordaIshla-*.apk` faylini yuklab oling.
Har safar shu papkadagi kod yoki `app-data/jobs.json` o‘zgarsa, GitHub Actions yangi APK yig‘adi.

## E’lonlarni yangilash (ilovani qayta o‘rnatmasdan)
`app-data/jobs.json` faylini tahrirlang. Ilova internetga ulanganda yangi
e’lonlarni repozitoriyaning asosiy (default) branchidagi shu fayldan oladi.
- `"namuna": true` — misol e’lonlar; ularni haqiqiy e’lonlar bilan almashtiring.
- `phone` va `telegram` maydonlarini to‘ldirsangiz, “Qo‘ng‘iroq” va “Telegram” tugmalari ishlaydi.
- `config.adminTelegram` — e’lon beruvchilar xabarni kimga yuborishi kerakligi (masalan `guzorda_admin`).

Eslatma: repozitoriya **private** bo‘lsa, ilova faylni internetdan o‘qiy olmaydi va
APK ichiga joylangan e’lonlarni ko‘rsatadi (yangi e’lonlar yangi APK bilan keladi).

## Play Market uchun imzo (ixtiyoriy)
Hozir APK test kaliti bilan imzolanadi. Doimiy kalit uchun GitHub Secrets'ga
`KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`, `KEY_PASSWORD` qo‘shing.
