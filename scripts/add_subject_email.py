#!/usr/bin/env python3
"""
Aggiunge `subject_email` a tutti i prospect/bounce esistenti in
data/prospects.json usando il mapping thread_id → subject derivato
da Gmail (raccolto durante l'audit MCP).

Idempotente: se il prospect ha già subject_email valorizzato, non lo tocca.
Per i thread non in mapping: derive il subject dal brand come fallback
("Re: [brand] update").
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "prospects.json"

# Mapping thread_id → subject reale da Gmail (audit 2026-05-13)
THREAD_SUBJECTS = {
    # === Page 1 (May 11-13) ===
    "19e1d2798cfa0e77": "lauraurbinati.com - aggiornamento store online",
    "19e1d236574a95ea": "Problema su giordanocosenza.com",
    "19e1d0d782cee143": "Problema su motivi.com - C.A. Jessica Sannino",
    "19e1d1de7220fe0f": "tmqstore.com  - aggiornamento store online",
    "19e1d12de4a2b954": "[RE]: Report niba1976.com",
    "19e1d068b43b13f3": "Problema su angelovintage.com",
    "19e1cdfc558ddcf2": "Problema su dante5.com",
    "19e1cdb23170b2fc": "Problema su colognese.com",
    "19e1cb67d38a4596": "Report - bernardellistores.com - tracciamento",
    "19e1d59e7f3dcff3": "Re: Issue with tailfin.cc",
    "19e1cbe3611be12a": "[RE]: Report brunarosso.com",
    "19e1d4956c82b2ae": "Eglooh, 2-3 fix sul vostro eCommerce",
    "19e1d5f3c7110350": "Re: Report MedicoShop",
    "19e1d19427d1cd60": "Problema su galassiaroma.com",
    "19e1d68d41685938": "Re: Tracking + Meta campaigns",
    "19e1d52de6ee6901": "Glow for it, the numbers aren't adding up",
    "19e1f1f2a7d3cd16": "[RE] Report agl.com",
    "19e1f13127a825e1": "[RE]: Report julian-fashion.com",
    "19e1d40f75462495": "Re: Tracking + Meta campaigns",
    "19e1d328c7d122a4": "Re: Issue with sassandbelletrade.co.uk",
    "19e1d2c898ca576c": "Re: Club Seven, one quick thing about your ads",
    "19e1d262c59e178a": "Montane, the numbers aren't adding up",
    "19e1d1e6bee211c5": "Re: Tracking + Meta campaigns",
    "19e1d1a756c1f287": "Threadbare, the numbers aren't adding up",
    "19e1d150d2181a49": "Re: Tracking + Meta campaigns",
    "19e1d0f1d2e8d6fc": "Re: Peachy Den - I noticed something",
    "19e1d09c6daf4b59": "Re: Rixo, one quick thing about your ads",
    "19e1d027e7065518": "Grace & Co, one quick thing about your ads",
    "19e1cfcadefc4736": "Malone Souliers, the numbers aren't adding up",
    "19e1cecff37faf85": "Report daniello.com tracciamento",
    "19e1ce4f96fe37bc": "Profumerie Galeazzi, 2-3 fix sul vostro eCommerce",
    "19e1cdc5abbffa75": "[RE]: Report julian-fashion.com",
    "19e1cd7bdec3d456": "Tracking + Meta campaigns",
    "19e1cd5a3bdeda7d": "[RE]: Report ceneregb.com",
    "19e1cc2bae004ae2": "Problema su cammalleristore.com",
    "19e1cd0201742c08": "Re: Boglioli, i dati non tornano",
    "19e1caed2b24dbe4": "Report boutiqueantonia.com tracciamento",
    "19e1cab12b8c4939": "Problema su alducadaosta.com",
    "19e1ca1bdce3a8e3": "[RE]: Report nidacaserta.it",
    "19e1bf08ecf18639": "[RE]: Report mantovanishop.it",
    "19e1be9d47516187": "Problema stilmoda.it",
    "19e1bd730ca8f4e5": "[RE]: Report satu.it",
    "19e183a6bc4fb385": "[RE]: Report negozipellizzari.it",
    "19e1832d23ed9339": "[RE]: Report penelope-store.it",
    "19e1820555f34c78": "Problema su flashionshop.com/negozi/vela-shop/",
    "19e1826076a6f00e": "Report rabaini.it tracciamento",
    "19e17bbd05d75b0b": "[RE]: Report binisilvia.com",
    "19e17ac4d6a43ea2": "Report valicostore.com tracciamento",
    "19e17a8a068dcef8": "Problema su boutiqueadani.it",
    "19e17a17001c6af1": "[RE]: Report manzoni24.it",
    # === Page 2 (May 7-11) ===
    "19e16f9b3608f5e4": "Re: YMC - tracking + Meta ads",
    "19e16f13b9a11a2b": "Re: Woven - online store update",
    "19e16dda8c8728c3": "Re: tracking + campagne Meta",
    "19e16d6058404c6e": "Re: Sunspel, something I spotted",
    "19e16c58be4d5c08": "Re: Give Me, the numbers aren't adding up",
    "19e16bf318c6f7aa": "Re: 2-3 things I noticed",
    "19e16b9e7b2c344e": "Re: Case, the numbers aren't adding up",
    "19e16b289db71ee6": "Finnieston Clothing, something I spotted",
    "19e16a7cf2075f89": "Ice Gripper, something I spotted",
    "19e16a4711839c57": "Uklash, the numbers aren't adding up",
    "19e150b0cc1ab9d0": "Re: Dock & Bay, one quick thing about your ads",
    "19e15098a1e20266": "Re: Gingerlily, the numbers aren't adding up",
    "19e1508cef9c33e7": "Re: Youth & Earth, one quick thing about your ads",
    "19e1508047c20c29": "Re: Margaret Howell, the numbers aren't adding up",
    "19e15060fbcb7b5c": "Re: Anxashop, una cosa che ho visto",
    "19e080b60889856e": "Report lenoirboutique.com tracciamento",
    "19e07ff56b7c8b5a": "Report follifolliegroup.it tracciamento",
    "19e07f590ea28b67": "[RE]: Report gebnegozionline.com",
    "19e07e00193671d6": "Problema su davidecenci.com",
    "19e07dba1ea51730": "[RE]: Report 10corsocomo.com",
    "19e07c9a68e73cfc": "[RE]: Report luisaviaroma.com",
    "19e07c110e51efb7": "[RE]: Report giglio.com",
    "19e07bbfdd4bbe62": "divoboutique.com - aggiornamento store online",
    "19e07b3d9f891b8f": "Problema su corteccisiena.it",
    "19e07a7ec8f71d9e": "Report oberrauch-zitt.com tracciamento",
    "19e079e7a8507191": "Problema su cuccuini.it",
    "19e0798919a3c431": "[RE]: Report genteroma.com",
    "19e078e8f954fd03": "[RE]: Report tizianafausti.com tracciamento",
    "19e0784e65085792": "Problema su tessabit.com",
    "19e078052a8dfa7d": "[RE]: Report sugar.it",
    "19e02d1055d68c1f": "montiboutique.com - aggiornamento store online",
    "19e02c15b76af405": "[RE]: Report mariodannashop.it",
    "19e02b8928ea8361": "[RE]: Report shop-marcos.com tracciamento",
    "19e02b4b20e41a06": "[RE]: Report mantovanishop.it",
    "19e028452e01c448": "Re: Accorgimento rapido sullo store",
    "19e02842dc63cde4": "Re: Accorgimento rapido sullo store",
    "19e028402a7d1b10": "Re: Accorgimento rapido sullo store",
    "19e0283dca8a5b71": "Re: Accorgimento rapido sullo store",
    "19e0283b5ed240fa": "Re: Accorgimento rapido sullo store",
    "19e02832d982bf52": "Re: 10 Corso Como, una cosa sulle ads",
    "19e027d32f45ec43": "lucianabari.com  - aggiornamento store online",
    "19e028303af97c5d": "Re: Tracking + campagne Meta",
    "19e0282cf6bcb7db": "Re: Tracking + campagne Meta",
    "19e0282a9957b919": "Re: Tricot, una cosa sulle ads",
    "19e02822b79fb990": "Re: Shopify + crescita eComm",
    "19e027999e538b9b": "lorenzetti.com",
    "19e027130d69d3f9": "[RE]: Report leam.com tracciamento",
    "19e026c168a716b8": "Problema su lattuadaboutique.it",
    "19e02678be8ebff4": "Re: Shopify + crescita eComm",
    "19e026763f269fef": "Re: Tracking + campagne Meta",
    # === Page 3 (May 6-7) ===
    "19e02673fcc64ac1": "Re: Di Pierro, i dati non tornano",
    "19e02671615e0181": "Re: Tracking + campagne Meta",
    "19e02644a834f247": "[RE]: Report julian-fashion.com",
    "19e0266c6d339161": "Re: Carmen boutique, una cosa sulle ads",
    "19e0266a21e2f255": "Re: Gaia, una cosa sulle ads",
    "19e02667c4daf481": "Re: 2-3 fix sul vostro eCommerce",
    "19e026658a3ef53a": "Re: Kau boutique, una cosa che ho visto",
    "19e0266130279422": "Re: Eraldo, store Shopify",
    "19e0265ecd8ec21f": "Re: Franz Kraler, una cosa sulle ads",
    "19e0265c9b972acb": "Re: Tracking + campagne Meta",
    "19e0265a4296e96a": "Re: iDress Map, una cosa sulle ads",
    "19e0265617f4d1f1": "Re: 2-3 fix sul vostro eCommerce",
    "19e026540b01048b": "Re: Il Sellaio, una cosa sulle ads",
    "19e02651b68df109": "Re: Tracking + campagne Meta",
    "19e0264f6109b0ba": "Re: Nugnes, una cosa che ho visto",
    "19e0264ad0bd02b6": "Re: Sana Osmani",
    "19e026489e0de105": "Re: Accorgimento rapido sullo store",
    "19e0264653e576a2": "Re: Accorgimento rapido sullo store",
    "19e0264415b43e69": "Re: Accorgimento rapido sullo store",
    "19e0263fa22f85a7": "Re: Accorgimento rapido sullo store",
    "19e0263d5f4b62ce": "Re: Accorgimento rapido sullo store",
    "19e0263b1f442d52": "Re: Accorgimento rapido sullo store",
    "19e02638a59caf7a": "Re: Accorgimento rapido sullo store",
    "19e02629b3e073dd": "Re: Accorgimento rapido sullo store",
    "19e026276cefea10": "Re: Accorgimento rapido sullo store",
    "19e02625012672d2": "Re: Accorgimento rapido sullo store",
    "19e0262073293d39": "Re: Accorgimento rapido sullo store",
    "19e0261d66e08cf1": "Re: Accorgimento rapido sullo store",
    "19e0261a71a7912b": "Re: Accorgimento rapido sullo store",
    "19e026159e019fc5": "Re: Accorgimento rapido sullo store",
    "19e026132c723968": "Re: Accorgimento rapido sullo store",
    "19e026109f48de1e": "Re: Accorgimento rapido sullo store",
    "19e0260b10e1a2b0": "Re: Accorgimento rapido sullo store",
    "19e026071b6190c2": "Re: Accorgimento rapido sullo store",
    "19e02604b5efa2cb": "Re: Accorgimento rapido sullo store",
    "19e025ffc6d0a773": "Re: Accorgimento rapido sullo store",
    "19e025fd86222729": "Re: Accorgimento rapido sullo store",
    "19e025fb21686ff3": "Re: Accorgimento rapido sullo store",
    "19e025f6010c2c5f": "Re: Accorgimento rapido sullo store",
    "19e025f3d93df421": "Re: Accorgimento rapido sullo store",
    "19e025eea7f51ff1": "Re: Accorgimento rapido sullo store",
    "19e025e1b5271cba": "Re: Accorgimento rapido sullo store",
    "19e025d29a2d439b": "Re: Accorgimento rapido sullo store",
    "19e0259b8f6e05a6": "Re: Accorgimento rapido sullo store",
    "19e0257dacaba8e3": "Re: Accorgimento rapido sullo store",
    "19e02560cbd9da7d": "Re: Accorgimento rapido sullo store",
    "19e02554dc5ad82b": "Re: Accorgimento rapido sullo store",
    "19e02500be7a0353": "Re: Antonio Manitta - Il Duomo Novara Tech Report",
    "19dfe92b3230c8ee": "https://italianistore.com/ ho visto una cosa",
    # === Older bounces / threads dalla prima audit ===
    "19dfe5af6c16fa3a": "[RE]: Report https://www.dolcitrame.shop/",
    "19dfe1a178fd9b9e": "[RE] Report: penelopechilvers.com",
    "19dfdf715003bda2": "Odd Muse, the numbers aren't adding up",
    "19dfe8baf55a523a": "Problema su https://www.helmestore.com/",
    "19db3fe24d6aebd9": "Accorgimento rapido sullo store",
    "19ddac7248b1a78a": "Tracking + Meta campaigns",  # The Go-To
    "19dd598f80445588": "Tracking + Meta campaigns",  # Ed Hardy
}


def main():
    data = json.loads(DATA.read_text())
    updated = 0
    missing = []

    def fill(p):
        nonlocal updated
        if p.get("subject_email"):
            return
        tid = p.get("thread_id")
        subj = THREAD_SUBJECTS.get(tid)
        if subj:
            p["subject_email"] = subj
            updated += 1
        else:
            # Fallback: lascia stringa vuota (mai inventare)
            p["subject_email"] = ""
            missing.append((p.get("id"), p.get("brand"), tid))

    for p in data.get("active", []): fill(p)
    for p in data.get("no_reply", []): fill(p)
    for b in data.get("bounced", []): fill(b)

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"OK — subject_email aggiunto a {updated} prospect/bounce")
    print(f"Mancanti (subject_email=''): {len(missing)}")
    for pid, brand, tid in missing[:10]:
        print(f"  - {pid} {brand} (thread {tid})")


if __name__ == "__main__":
    main()
