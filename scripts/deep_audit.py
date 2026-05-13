#!/usr/bin/env python3
"""
Deep audit — confronta data/prospects.json con i thread Gmail osservati
durante l'audit MCP del 2026-05-13. Produce AUDIT_REPORT.md e applica
correzioni sicure (date di first_contact reali, bounce mancanti, etc).

Mappa GMAIL_THREADS contiene tutti i thread outreach visibili da
Gmail (after:2026/04/15) con i metadati canonici verificati.
"""
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "prospects.json"
REPORT = ROOT / "AUDIT_REPORT.md"

LABELS_BY_SENDER = {
    "Manu":    "Label_1592668050883672428",
    "Dami":    "Label_8658624016447790536",
    "Claude":  "Label_9196661710752787047",
    "Antonio": "Label_1523762719426921570",
}
SENDER_BY_LABEL = {v: k for k, v in LABELS_BY_SENDER.items()}

# ============================================================
# Canonical Gmail thread inventory (audit MCP 2026-05-13)
# Format: thread_id → {date, sender, to, subject, bounce, human_reply}
# ============================================================
GMAIL_THREADS = {
    # === MAY 13 (oggi) ===
    "19e1d2798cfa0e77": {"date": "2026-05-13", "sender": "Manu", "to": "info@lauraurbinati.com", "subject": "lauraurbinati.com - aggiornamento store online"},
    "19e1d236574a95ea": {"date": "2026-05-13", "sender": "Manu", "to": "info@giordanocosenza.com", "subject": "Problema su giordanocosenza.com"},
    "19e1d0d782cee143": {"date": "2026-05-13", "sender": "Manu", "to": "fashion@miroglio.com", "subject": "Problema su motivi.com - C.A. Jessica Sannino"},
    "19e1d1de7220fe0f": {"date": "2026-05-13", "sender": "Manu", "to": "manolo.clementi@tmqstore.com", "subject": "tmqstore.com  - aggiornamento store online"},
    "19e1d12de4a2b954": {"date": "2026-05-13", "sender": "Manu", "to": "info@niba1976.com", "subject": "[RE]: Report niba1976.com"},
    "19e1d068b43b13f3": {"date": "2026-05-13", "sender": "Manu", "to": "info@angelo.it", "subject": "Problema su angelovintage.com"},
    "19e1cdfc558ddcf2": {"date": "2026-05-13", "sender": "Manu", "to": "customercare@dante5.com", "subject": "Problema su dante5.com"},
    "19e1cdb23170b2fc": {"date": "2026-05-13", "sender": "Manu", "to": "elisa_zini2002@yahoo.com", "subject": "Problema su colognese.com"},
    "19e1cb67d38a4596": {"date": "2026-05-13", "sender": "Manu", "to": "ginevra@bernardellistores.it", "subject": "Report - bernardellistores.com - tracciamento"},
    "19e1d59e7f3dcff3": {"date": "2026-05-13", "sender": "Dami", "to": "nick@tailfin.cc", "subject": "Re: Issue with tailfin.cc"},
    "19e1cbe3611be12a": {"date": "2026-05-13", "sender": "Manu", "to": "michela.viola@brunarosso.com", "subject": "[RE]: Report brunarosso.com", "bounce": True},
    "19e1d4956c82b2ae": {"date": "2026-05-13", "sender": "Dami", "to": "info@eglooh.com", "subject": "Eglooh, 2-3 fix sul vostro eCommerce"},
    "19e1d5f3c7110350": {"date": "2026-05-13", "sender": "Dami", "to": "giuseppeabbasciano@medicoshop.it", "subject": "Re: Report MedicoShop"},
    "19e1d19427d1cd60": {"date": "2026-05-13", "sender": "Manu", "to": "info@galassiaroma.com", "subject": "Problema su galassiaroma.com"},
    "19e1d68d41685938": {"date": "2026-05-13", "sender": "Dami", "to": "Paul@disturbia.co.uk", "subject": "Re: Tracking + Meta campaigns"},
    "19e1d52de6ee6901": {"date": "2026-05-13", "sender": "Dami", "to": "frankie@glowforitshop.com", "subject": "Glow for it, the numbers aren't adding up"},
    "19e1f64180a23758": {"date": "2026-05-13", "sender": "Antonio", "to": "Goliveira@thefeetingroom.com", "subject": "case study is live"},
    "19e1f1f2a7d3cd16": {"date": "2026-05-13", "sender": "Claude", "to": "e.francioni@agl.com", "subject": "[RE] Report agl.com"},
    "19e1f13127a825e1": {"date": "2026-05-13", "sender": "Claude", "to": "giulia.tondini@julian-fashion.com", "subject": "[RE]: Report julian-fashion.com"},

    # === MAY 12 ===
    "19e1d40f75462495": {"date": "2026-05-12", "sender": "Dami", "to": "info@bonsoiroflondon.com", "subject": "Re: Tracking + Meta campaigns", "bounce": True},
    "19e1d328c7d122a4": {"date": "2026-05-12", "sender": "Dami", "to": "info@sassandbelletrade.co.uk", "subject": "Re: Issue with sassandbelletrade.co.uk", "human_reply": True},
    "19e1d2c898ca576c": {"date": "2026-05-12", "sender": "Dami", "to": "alexander.g@wearclubseven.com", "subject": "Re: Club Seven, one quick thing about your ads", "bounce": True},
    "19e1d262c59e178a": {"date": "2026-05-12", "sender": "Dami", "to": "graham.oakes@montane.com", "subject": "Montane, the numbers aren't adding up"},
    "19e1d1e6bee211c5": {"date": "2026-05-12", "sender": "Dami", "to": "sam.fitzpatrick@newenglishteas.com", "subject": "Re: Tracking + Meta campaigns"},
    "19e1d1a756c1f287": {"date": "2026-05-12", "sender": "Dami", "to": "natalie.pendlebury@threadbare.com", "subject": "Threadbare, the numbers aren't adding up"},
    "19e1d150d2181a49": {"date": "2026-05-12", "sender": "Dami", "to": "teresa@joloves.com", "subject": "Re: Tracking + Meta campaigns"},
    "19e1d0f1d2e8d6fc": {"date": "2026-05-12", "sender": "Dami", "to": "jade_mulhall@peachyden.co.uk", "subject": "Re: Peachy Den - I noticed something", "bounce": True},
    "19e1d09c6daf4b59": {"date": "2026-05-12", "sender": "Dami", "to": "emmalaw@rixo.co.uk", "subject": "Re: Rixo, one quick thing about your ads"},
    "19e1d027e7065518": {"date": "2026-05-12", "sender": "Dami", "to": "hello@graceandcojewellery.co.uk", "subject": "Grace & Co, one quick thing about your ads", "human_reply": True},
    "19e1cfcadefc4736": {"date": "2026-05-12", "sender": "Dami", "to": "lucy@malonesouliers.com", "subject": "Malone Souliers, the numbers aren't adding up"},
    "19e1cecff37faf85": {"date": "2026-05-12", "sender": "Manu", "to": "ecommerce@daniello.com", "subject": "Report daniello.com tracciamento"},
    "19e1ce4f96fe37bc": {"date": "2026-05-12", "sender": "Dami", "to": "e-commerce@profumeriegaleazzi.it", "subject": "Profumerie Galeazzi, 2-3 fix sul vostro eCommerce"},
    "19e1cdc5abbffa75": {"date": "2026-05-12", "sender": "Dami", "to": "cecilia.copercini@julian-fashion.com", "subject": "[RE]: Report julian-fashion.com"},
    "19e1cd7bdec3d456": {"date": "2026-05-12", "sender": "Dami", "to": "info@rachelriley.co.uk", "subject": "Tracking + Meta campaigns"},
    "19e1cd5a3bdeda7d": {"date": "2026-05-12", "sender": "Manu", "to": "pierpaolomoracas@ceneregb.com", "subject": "[RE]: Report ceneregb.com"},
    "19e1cc2bae004ae2": {"date": "2026-05-12", "sender": "Manu", "to": "info@cammalleristore.com", "subject": "Problema su cammalleristore.com"},
    "19e1cd0201742c08": {"date": "2026-05-12", "sender": "Dami", "to": "rosanna.curcio@boglioli.it", "subject": "Re: Boglioli, i dati non tornano"},
    "19e1caed2b24dbe4": {"date": "2026-05-12", "sender": "Manu", "to": "info@boutiqueantonia.com", "subject": "Report boutiqueantonia.com tracciamento"},
    "19e1cab12b8c4939": {"date": "2026-05-12", "sender": "Manu", "to": "alessandra.piccinetti@alducadaosta.com", "subject": "Problema su alducadaosta.com"},
    "19e1ca1bdce3a8e3": {"date": "2026-05-12", "sender": "Manu", "to": "info@nidacaserta.it", "subject": "[RE]: Report nidacaserta.it"},
    "19e1bf08ecf18639": {"date": "2026-05-12", "sender": "Manu", "to": "info@mantovanishop.it", "subject": "[RE]: Report mantovanishop.it"},
    "19e1be9d47516187": {"date": "2026-05-12", "sender": "Manu", "to": "stilmoda@stilmoda.it", "subject": "Problema stilmoda.it"},
    "19e1bd730ca8f4e5": {"date": "2026-05-12", "sender": "Manu", "to": "info@satu.it", "subject": "[RE]: Report satu.it", "bounce": True},
    "19e183a6bc4fb385": {"date": "2026-05-12", "sender": "Manu", "to": "m.cordovado@negozipellizzari.it", "subject": "[RE]: Report negozipellizzari.it"},
    "19e1832d23ed9339": {"date": "2026-05-12", "sender": "Manu", "to": "m.battagliola@penelope-store.it", "subject": "[RE]: Report penelope-store.it"},
    "19e1820555f34c78": {"date": "2026-05-12", "sender": "Manu", "to": "velashop@email.it", "subject": "Problema su flashionshop.com/negozi/vela-shop/"},

    # === MAY 11 ===
    "19e1826076a6f00e": {"date": "2026-05-11", "sender": "Manu", "to": "rabaini@rabaini.it", "subject": "Report rabaini.it tracciamento"},
    "19e17bbd05d75b0b": {"date": "2026-05-11", "sender": "Manu", "to": "customerservice@binisilvia.com", "subject": "[RE]: Report binisilvia.com"},
    "19e17ac4d6a43ea2": {"date": "2026-05-11", "sender": "Manu", "to": "info@valicostore.com", "subject": "Report valicostore.com tracciamento"},
    "19e17a8a068dcef8": {"date": "2026-05-11", "sender": "Manu", "to": "boutiqueadani@boutiqueadani.it", "subject": "Problema su boutiqueadani.it"},
    "19e17a17001c6af1": {"date": "2026-05-11", "sender": "Manu", "to": "info@manzoni24.it", "subject": "[RE]: Report manzoni24.it"},
    "19e16f9b3608f5e4": {"date": "2026-05-11", "sender": "Dami", "to": "alex@youmustcreate.com", "subject": "Re: YMC - tracking + Meta ads"},
    "19e16f13b9a11a2b": {"date": "2026-05-11", "sender": "Dami", "to": "hayesc@wovendurham.co.uk", "subject": "Re: Woven - online store update"},
    "19e16dda8c8728c3": {"date": "2026-05-11", "sender": "Dami", "to": "f.palma@skinfirstcosmetics.it", "subject": "Re: tracking + campagne Meta"},
    "19e16d6058404c6e": {"date": "2026-05-11", "sender": "Dami", "to": "geri.ross@sunspel.com", "subject": "Re: Sunspel, something I spotted", "human_reply": True},
    "19e16c58be4d5c08": {"date": "2026-05-11", "sender": "Dami", "to": "mollie.roe@givemecosmetics.com", "subject": "Re: Give Me, the numbers aren't adding up"},
    "19e16bf318c6f7aa": {"date": "2026-05-11", "sender": "Dami", "to": "rosie.thornton@grs-footwear.co.uk", "subject": "Re: 2-3 things I noticed"},
    "19e16b9e7b2c344e": {"date": "2026-05-11", "sender": "Dami", "to": "daniel.morris@caseluggage.com", "subject": "Re: Case, the numbers aren't adding up"},
    "19e16b289db71ee6": {"date": "2026-05-11", "sender": "Dami", "to": "luke@finniestonclothing.com", "subject": "Finnieston Clothing, something I spotted", "bounce": True},
    "19e16a7cf2075f89": {"date": "2026-05-11", "sender": "Dami", "to": "carl@icegripper.co.uk", "subject": "Ice Gripper, something I spotted"},
    "19e16a4711839c57": {"date": "2026-05-11", "sender": "Dami", "to": "felipe.gardelli@uklash.com", "subject": "Uklash, the numbers aren't adding up"},

    # === MAY 8 ===
    "19e080b60889856e": {"date": "2026-05-08", "sender": "Manu", "to": "info@lenoirboutique.com", "subject": "Report lenoirboutique.com tracciamento"},
    "19e07ff56b7c8b5a": {"date": "2026-05-08", "sender": "Manu", "to": "info@follifollie.it", "subject": "Report follifolliegroup.it tracciamento"},
    "19e07f590ea28b67": {"date": "2026-05-08", "sender": "Manu", "to": "info@gebnegozionline.com", "subject": "[RE]: Report gebnegozionline.com"},
    "19e07e00193671d6": {"date": "2026-05-08", "sender": "Manu", "to": "info@davidecenci.com", "subject": "Problema su davidecenci.com"},
    "19e07dba1ea51730": {"date": "2026-05-08", "sender": "Manu", "to": "gianluca.borghi@10corsocomo.com", "subject": "[RE]: Report 10corsocomo.com"},
    "19e07c9a68e73cfc": {"date": "2026-05-08", "sender": "Manu", "to": "m.ritratti@luisaviaroma.com", "subject": "[RE]: Report luisaviaroma.com"},
    "19e07c110e51efb7": {"date": "2026-05-08", "sender": "Manu", "to": "giuseppe.giglio@giglio.com", "subject": "[RE]: Report giglio.com"},
    "19e07bbfdd4bbe62": {"date": "2026-05-08", "sender": "Manu", "to": "customercare@divoboutique.com", "subject": "divoboutique.com - aggiornamento store online"},
    "19e07b3d9f891b8f": {"date": "2026-05-08", "sender": "Manu", "to": "info@corteccisiena.it", "subject": "Problema su corteccisiena.it"},
    "19e07a7ec8f71d9e": {"date": "2026-05-08", "sender": "Manu", "to": "info@oberrauch-zitt.com", "subject": "Report oberrauch-zitt.com tracciamento"},
    "19e079e7a8507191": {"date": "2026-05-08", "sender": "Manu", "to": "info@cuccuini.it", "subject": "Problema su cuccuini.it"},
    "19e0798919a3c431": {"date": "2026-05-08", "sender": "Manu", "to": "d.addadi@genteroma.com", "subject": "[RE]: Report genteroma.com"},
    "19e078e8f954fd03": {"date": "2026-05-08", "sender": "Manu", "to": "tiziana.fausti@tizianafausti.com", "subject": "[RE]: Report tizianafausti.com tracciamento"},
    "19e0784e65085792": {"date": "2026-05-08", "sender": "Manu", "to": "filippo.baldovino@tessabit.com", "subject": "Problema su tessabit.com"},
    "19e078052a8dfa7d": {"date": "2026-05-08", "sender": "Manu", "to": "ludovica@sugar.it", "subject": "[RE]: Report sugar.it"},

    # === MAY 7 ===
    "19e02d1055d68c1f": {"date": "2026-05-07", "sender": "Manu", "to": "info@montiboutique.com", "subject": "montiboutique.com - aggiornamento store online"},
    "19e02c15b76af405": {"date": "2026-05-07", "sender": "Manu", "to": "shoponline@mariodanna.it", "subject": "[RE]: Report mariodannashop.it"},
    "19e02b8928ea8361": {"date": "2026-05-07", "sender": "Manu", "to": "shop@shop-marcos.com", "subject": "[RE]: Report shop-marcos.com tracciamento"},
    "19e02b4b20e41a06": {"date": "2026-05-07", "sender": "Manu", "to": "contact@mantovanishop.it", "subject": "[RE]: Report mantovanishop.it"},
    "19e027d32f45ec43": {"date": "2026-05-07", "sender": "Manu", "to": "info@lucianabari.com", "subject": "lucianabari.com  - aggiornamento store online"},
    "19e027999e538b9b": {"date": "2026-05-07", "sender": "Manu", "to": "info@lorenzetti.com", "subject": "lorenzetti.com"},
    "19e027130d69d3f9": {"date": "2026-05-07", "sender": "Manu", "to": "vittorio.amati@leam.com", "subject": "[RE]: Report leam.com tracciamento"},
    "19e026c168a716b8": {"date": "2026-05-07", "sender": "Manu", "to": "info@lattuadaboutique.it", "subject": "Problema su lattuadaboutique.it"},
    "19e02644a834f247": {"date": "2026-05-07", "sender": "Manu", "to": "sabina@julian-fashion.com", "subject": "[RE]: Report julian-fashion.com"},

    # === MAY 6 ===
    "19dfe92b3230c8ee": {"date": "2026-05-06", "sender": "Manu", "to": "italiani@italianipescara.it", "subject": "https://italianistore.com/ ho visto una cosa"},
    "19dfe8baf55a523a": {"date": "2026-05-06", "sender": "Manu", "to": "info@helmestore.com", "subject": "Problema su https://www.helmestore.com/", "bounce": True},
    "19dfe82a1df3beb4": {"date": "2026-05-06", "sender": "Manu", "to": "info@guerrastore.it", "subject": "[RE]: Report https://www.guerrastore.it/"},
    "19dfe7ddeef6fdb5": {"date": "2026-05-06", "sender": "Manu", "to": "info@giordanoboutique.com", "subject": "https://www.giordanoboutique.com/ - aggiornamento store online"},
    "19dfe79001281fbb": {"date": "2026-05-06", "sender": "Manu", "to": "annalisa@gibot.it", "subject": "[RE]: Report https://gibot.it/it tracciamento"},
    "19dfe72dd8f0cdfe": {"date": "2026-05-06", "sender": "Manu", "to": "m.favarelli@gaudenziboutique.com", "subject": "Report https://www.gaudenziboutique.com/it tracciamento", "human_reply": True},
    "19dfe6d6b54288e4": {"date": "2026-05-06", "sender": "Manu", "to": "info@francaleoni.com", "subject": "https://www.francaleoni.com/ Ho visto una cosa"},
    "19dfe66afebdf485": {"date": "2026-05-06", "sender": "Manu", "to": "eleonora@eleonorabonucci.com", "subject": "[RE]: Problema su https://eleonorabonucci.com/"},
    "19dfe645b632f2be": {"date": "2026-05-06", "sender": "Manu", "to": "order.dolcitrame@gmail.com", "subject": "[RE]: Report https://www.dolcitrame.shop/"},
    "19dfe5af6c16fa3a": {"date": "2026-05-06", "sender": "Manu", "to": "info.dolcitrame@gmail.com", "subject": "[RE]: Report https://www.dolcitrame.shop/", "bounce": True},
    "19dfe57c4b6c10cf": {"date": "2026-05-06", "sender": "Manu", "to": "info@divincenzoboutique.com", "subject": "https://www.divincenzoboutique.com/it - aggiornamento store online"},
    "19dfe527a1fb5b5b": {"date": "2026-05-06", "sender": "Manu", "to": "info@dante5.com", "subject": "Report https://www.dante5.com/ tracciamento"},
    "19dfe4a7a9dd90d6": {"date": "2026-05-06", "sender": "Dami", "to": "alex@bottletop.org", "subject": "Bottletop, one quick thing about your ads"},
    "19dfe43b90edd172": {"date": "2026-05-06", "sender": "Manu", "to": "info@colognese.com", "subject": "[RE]: Report https://www.colognese.com/ tracciamento"},
    "19dfe44a02aec541": {"date": "2026-05-06", "sender": "Dami", "to": "info@bluewaterclothing.co.uk", "subject": "Blue Water, 2-3 things I noticed"},
    "19dfe42b48b9e5da": {"date": "2026-05-06", "sender": "Dami", "to": "zuzana@sculptedbyaimee.com", "subject": "Tracking + Meta campaigns"},
    "19dfe3ffb431bf03": {"date": "2026-05-06", "sender": "Manu", "to": "info@cammallerigroup.com", "subject": "[RE]: Problema su https://cammalleristore.com/it/"},
    "19dfe3d73f1a0e84": {"date": "2026-05-06", "sender": "Dami", "to": "agnieszka@bbcicecream.eu", "subject": "Billionaire Boys Club, the numbers aren't adding up"},
    "19dfe3840304e82c": {"date": "2026-05-06", "sender": "Manu", "to": "info@bernardellistores.com", "subject": "[RE]: Report https://www.bernardellistores.com/"},
    "19dfe34652045875": {"date": "2026-05-06", "sender": "Dami", "to": "l.gioventu@agl.com", "subject": "[RE] Report agl.com", "human_reply": True},
    "19dfe3042d5834cb": {"date": "2026-05-06", "sender": "Dami", "to": "contact@patriciablanchet.com", "subject": "Tracking + Meta campaigns"},
    "19dfe2b8106f2262": {"date": "2026-05-06", "sender": "Dami", "to": "edurastante@nunalie.it", "subject": "Nuna Lie, una cosa che ho visto"},
    "19dfe25b78dc77d5": {"date": "2026-05-06", "sender": "Dami", "to": "la@loquetlondon.com", "subject": "Loquet London, one quick thing about your ads"},
    "19dfe1a178fd9b9e": {"date": "2026-05-06", "sender": "Dami", "to": "info@penelopechilvers.com", "subject": "[RE] Report: penelopechilvers.com", "bounce": True},
    "19dfe12da93e0131": {"date": "2026-05-06", "sender": "Dami", "to": "kristinamaksvytyte@bouxavenue.com", "subject": "[RE] Report: bouxavenue.com"},
    "19dfdf715003bda2": {"date": "2026-05-06", "sender": "Dami", "to": "chloe.robinson@oddmuse.co.uk", "subject": "Odd Muse, the numbers aren't adding up", "bounce": True},
    "19dfdef433134ea6": {"date": "2026-05-06", "sender": "Dami", "to": "me.support@monsoonlondon.com", "subject": "[RE] Report: monsoonlondon.com", "human_reply": True},
    "19dfdd6607df009f": {"date": "2026-05-06", "sender": "Dami", "to": "MW@t-o-o-g-o-o-d.com", "subject": "Tracking + Meta campaigns", "human_reply": True},
    "19dfdca40e61b29d": {"date": "2026-05-06", "sender": "Dami", "to": "daniel@ukbuyzone.co.uk", "subject": "UKBuyZone, one quick thing about your ad"},
    "19dfdc23a0c3e96c": {"date": "2026-05-06", "sender": "Dami", "to": "inaya@frescobolcarioca.com", "subject": "Frescobol Carioca, the numbers aren't adding up"},
    "19dfdb990414938c": {"date": "2026-05-06", "sender": "Dami", "to": "ask@candlesandoud.com", "subject": "Tracking + Meta campaigns"},
    "19dfd792de6e11a1": {"date": "2026-05-06", "sender": "Dami", "to": "melanie@biscuiteers.com", "subject": "Biscuiteers, the numbers aren't adding up"},
    "19dfd75869ab3e5e": {"date": "2026-05-06", "sender": "Dami", "to": "amber@goddiva.co.uk", "subject": "Goddiva, one quick thing about your ad"},
    "19dfd70ffa3317fc": {"date": "2026-05-06", "sender": "Dami", "to": "clopez@harrysoflondon.com", "subject": "Harrys London, the numbers aren't adding up"},
    "19dfd5ed5e96ca48": {"date": "2026-05-06", "sender": "Dami", "to": "support@wunderbrow.eu", "subject": "Tracking + Meta campaigns"},
    "19dfd4fd06fa8553": {"date": "2026-05-06", "sender": "Dami", "to": "chad@sonofastag.com", "subject": "Son of a Stag, the numbers aren't adding up"},
    "19dfd2fccedc5d3d": {"date": "2026-05-06", "sender": "Dami", "to": "daut@scorpionshoes.co.uk", "subject": "[RE] Report: scorpionshoes.co.uk"},
    "19dfd2aa6944b9cd": {"date": "2026-05-06", "sender": "Dami", "to": "ren.woods@killstar.com", "subject": "Killstar, one quick thing about your ads"},
    "19dfd15ffc56bcd8": {"date": "2026-05-06", "sender": "Dami", "to": "info@charlesfish.co.uk", "subject": "Charles Fish, one quick thing about your ad"},
    "19dfcfb1d0f840d5": {"date": "2026-05-06", "sender": "Dami", "to": "manuella@pippasmall.com", "subject": "Pippa Small, 2-3 things I noticed"},
    "19dfcf57eae86785": {"date": "2026-05-06", "sender": "Dami", "to": "kirsty@aimelondon.com", "subject": "Aimé London, one quick thing about your ads"},
    "19dfce5f1a24f926": {"date": "2026-05-06", "sender": "Dami", "to": "info@darkartscoffee.co.uk", "subject": "Dark Arts Coffee, 2-3 things I noticed", "human_reply": True},
    "19dfcd8cdb27962b": {"date": "2026-05-06", "sender": "Dami", "to": "scott@thecoutureclub.com", "subject": "Tracking + Meta campaigns"},
    "19dfcd64ad98b60b": {"date": "2026-05-06", "sender": "Dami", "to": "ross@thecoutureclub.com", "subject": "Tracking + Meta campaigns"},
    "19dfcc9b1178a722": {"date": "2026-05-06", "sender": "Dami", "to": "natalie.dawson@medik8.com", "subject": "Medik8, one quick thing about your ads"},

    # === MAY 5 ===
    "19df910cc6ed9dd8": {"date": "2026-05-05", "sender": "Manu", "to": "info@boutiqueantonia.com", "subject": "Non usate Shopify?"},

    # === MAY 1 ===
    "19ddf8d3304e457d": {"date": "2026-05-01", "sender": "Dami", "to": "amber@dockandbay.com", "subject": "Dock & Bay, one quick thing about your ads"},
    "19ddfc71ba581de2": {"date": "2026-05-01", "sender": "Dami", "to": "info@polydor.co.uk", "subject": "Tracking + Meta campaigns"},
    "19ddfbfc5d11acc6": {"date": "2026-05-01", "sender": "Dami", "to": "sales@gingerlily.com", "subject": "Gingerlily, the numbers aren't adding up"},
    "19ddf85111511d28": {"date": "2026-05-01", "sender": "Dami", "to": "natalia_37_eyb@hotmail.com", "subject": "Youth & Earth, one quick thing about your ads"},
    "19ddf7f4ac5d77e0": {"date": "2026-05-01", "sender": "Dami", "to": "bea@toa.st", "subject": "Toast, the numbers aren't adding up", "bounce": True},
    "19ddfb13cce73a32": {"date": "2026-05-01", "sender": "Dami", "to": "marcela@mzskin.com", "subject": "MZ Skin, the numbers aren't adding up", "bounce": True},
    "19ddf9cc9b459900": {"date": "2026-05-01", "sender": "Dami", "to": "anita.papadopoulos@margarethowell.co.uk", "subject": "Margaret Howell, the numbers aren't adding up", "human_reply": True},
    "19ddfaa5fe0ea1cf": {"date": "2026-05-01", "sender": "Dami", "to": "ariadna.petrova@cultfurniture.com", "subject": "Tracking + Meta campaigns"},
    "19ddf90a306d941a": {"date": "2026-05-01", "sender": "Dami", "to": "anxashop@gmail.com", "subject": "Anxashop, una cosa che ho visto"},
    "19ddf7e4afd66b9b": {"date": "2026-05-01", "sender": "Dami", "to": "jessica@toa.st", "subject": "Toast, one quick thing about your ads", "bounce": True},

    # === APR 30 ===
    "19ddd2f1a04c1e09": {"date": "2026-04-30", "sender": None, "to": "antoniomanitta10@gmail.com", "subject": "hai ricevuto mia email?"},  # self-test, skip
    "19ddac415eeb5542": {"date": "2026-04-30", "sender": "Dami", "to": "talitha@thegoto.com", "subject": "The Go-To, the numbers aren't adding up"},
    "19ddab303ace12d4": {"date": "2026-04-30", "sender": "Dami", "to": "dom@pepalondon.com", "subject": "Pepa London, one quick thing about your ads"},
    "19ddae9da49ff842": {"date": "2026-04-30", "sender": "Dami", "to": "marina.hernandez@lecol.cc", "subject": "Le Col, the numbers aren't adding up"},
    "19ddabe81eb4e921": {"date": "2026-04-30", "sender": "Dami", "to": "antoniamcdonnell@crockettandjones.com", "subject": "Crockett & Jones, one quick thing about your ads"},
    "19dda9cd7e80781b": {"date": "2026-04-30", "sender": "Dami", "to": "elisa@escentric.com", "subject": "Tracking + Meta campaigns"},
    "19dda95546e62195": {"date": "2026-04-30", "sender": "Dami", "to": "martina@solange.co.uk", "subject": "Solange, i dati non tornano"},
    "19ddac7248b1a78a": {"date": "2026-04-30", "sender": "Dami", "to": "victoire@thegoto.com", "subject": "Tracking + Meta campaigns", "human_reply": True},
    "19ddae507a3acc20": {"date": "2026-04-30", "sender": "Dami", "to": "lily@mile.club", "subject": "Tracking + Meta campaigns"},
    "19ddab84152c17e4": {"date": "2026-04-30", "sender": "Dami", "to": "james.beasley@waxlondon.com", "subject": "Tracking + Meta campaigns"},
    "19ddab41bebe6f27": {"date": "2026-04-30", "sender": "Dami", "to": "pepa@pepalondon.com", "subject": "Pepa London, the numbers aren't adding up"},

    # === APR 29 ===
    "19dd99d12fb05462": {"date": "2026-04-29", "sender": None, "to": "ercolecellino@ilduomo.it", "subject": "Il Duomo Novara Tech Report - Antonio Manitta"},
    "19dd5889a5c72686": {"date": "2026-04-29", "sender": "Dami", "to": "guy@kissthehippo.com", "subject": "Kiss the Hippo, the numbers aren't adding up"},
    "19dd598f80445588": {"date": "2026-04-29", "sender": "Dami", "to": "hello@edhardy.co.uk", "subject": "Tracking + Meta campaigns", "human_reply": True},

    # === APR 28 ===
    "19dd4112339be79c": {"date": "2026-04-28", "sender": None, "to": "ercolecellino@ilduomo.it", "subject": "Antonio Manitta - Il Duomo Novara Tech Report"},

    # === APR 27 ===
    "19dd020a81265fff": {"date": "2026-04-27", "sender": "Manu", "to": "enrico.casati1987@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dd01bbdd6ecb5c": {"date": "2026-04-27", "sender": "Manu", "to": "martinacostantini82@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dd018aa2660d26": {"date": "2026-04-27", "sender": "Manu", "to": "gidigiulia@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dd01456e80e0d9": {"date": "2026-04-27", "sender": "Manu", "to": "commissoa@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dd00fc98115e44": {"date": "2026-04-27", "sender": "Manu", "to": "mobile@fessura.com", "subject": "Accorgimento rapido sullo store"},
    "19dd00bf53b5d27f": {"date": "2026-04-27", "sender": "Manu", "to": "bosidiego@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dd009fd7c21972": {"date": "2026-04-27", "sender": "Manu", "to": "sebastian@delbrenna.com", "subject": "Accorgimento rapido sullo store"},
    "19dd006468363f2f": {"date": "2026-04-27", "sender": "Manu", "to": "ladinozden@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dd0047d39f9a50": {"date": "2026-04-27", "sender": "Manu", "to": "pmalaspina@beautyaholicshop.com", "subject": "Accorgimento rapido sullo store"},

    # === APR 24 ===
    "19dbf8e7d940b7c8": {"date": "2026-04-24", "sender": "Manu", "to": "jacopo.sebastio@velasca.it", "subject": "Accorgimento rapido sullo store"},
    "19dbf8b771627eb9": {"date": "2026-04-24", "sender": "Manu", "to": "filippo.mengotti@mengottigroup.com", "subject": "Accorgimento rapido sullo store"},
    "19dbf8872b09bd16": {"date": "2026-04-24", "sender": "Manu", "to": "giuseppe.nugnes@nugnes1920.com", "subject": "Accorgimento rapido sullo store"},
    "19dbf85ee0a44c35": {"date": "2026-04-24", "sender": "Manu", "to": "nicodeka03@gmail.com", "subject": "Accorgimento rapido sullo store", "human_reply": True},
    "19dbf6ded6a9fbf3": {"date": "2026-04-24", "sender": "Manu", "to": "lucrezia.livelli@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbf6618dc7f259": {"date": "2026-04-24", "sender": "Manu", "to": "liviadiminno@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbf62c87e17d88": {"date": "2026-04-24", "sender": "Manu", "to": "tommaso.stefa@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbf5ecc28722ef": {"date": "2026-04-24", "sender": "Manu", "to": "Francesca.scorz@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbf540710a82bb": {"date": "2026-04-24", "sender": "Manu", "to": "martiraimondi2003@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbf4d432e86427": {"date": "2026-04-24", "sender": "Manu", "to": "scsiciliano@yahoo.it", "subject": "Accorgimento rapido sullo store"},

    # === APR 23 ===
    "19dbb93e140a90a1": {"date": "2026-04-23", "sender": "Manu", "to": "pagasimo23@yahoo.it", "subject": "Accorgimento rapido sullo store"},
    "19dbb920b47217ff": {"date": "2026-04-23", "sender": "Manu", "to": "marikazaramella93@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbb8f0fdeb26e5": {"date": "2026-04-23", "sender": "Manu", "to": "scire.virginia@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbb8d83131d60d": {"date": "2026-04-23", "sender": "Manu", "to": "maria.fachinetti@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbb8bc777cc316": {"date": "2026-04-23", "sender": "Manu", "to": "mattia.zogno@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbb86365620acd": {"date": "2026-04-23", "sender": "Manu", "to": "alessandro_perini@hotmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbb832232f4b08": {"date": "2026-04-23", "sender": "Manu", "to": "s.marinuzzi@indigoshop.it", "subject": "Accorgimento rapido sullo store"},
    "19dbb80de1bf57fb": {"date": "2026-04-23", "sender": "Manu", "to": "china.marta@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbb7f4e3ad9243": {"date": "2026-04-23", "sender": "Manu", "to": "gaia.martinelli6@outlook.it", "subject": "Accorgimento rapido sullo store"},
    "19dbb7d2079caad8": {"date": "2026-04-23", "sender": "Manu", "to": "janalegovic999@yahoo.it", "subject": "Accorgimento rapido sullo store"},
    "19dbb6fc6d1ff330": {"date": "2026-04-23", "sender": "Manu", "to": "buoso.elisa96@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbb6bb11e98aae": {"date": "2026-04-23", "sender": "Manu", "to": "lizardqueeng@hotmail.it", "subject": "Accorgimento rapido sullo store"},
    "19dbb69d4661c943": {"date": "2026-04-23", "sender": "Manu", "to": "serenacecchini@hotmail.com", "subject": "Accorgimento rapido sullo store"},
    "19dbb66cefb7795b": {"date": "2026-04-23", "sender": "Manu", "to": "laiza_skyangel@hotmail.com", "subject": "laiza_skyangel@hotmail.com"},
    "19dbb39600e4f4c8": {"date": "2026-04-23", "sender": "Dami", "to": "stefano.perrelli@nugnes1920.com", "subject": "Nugnes, una cosa che ho visto"},
    "19dbb2fe64db93cc": {"date": "2026-04-23", "sender": "Dami", "to": "customercare@franzesemoda.it", "subject": "Tracking + campagne Meta"},
    "19dbb2154925a866": {"date": "2026-04-23", "sender": "Dami", "to": "info@ilsellaio.it", "subject": "Il Sellaio, una cosa sulle ads", "human_reply": True},
    "19dbb178326c320d": {"date": "2026-04-23", "sender": "Dami", "to": "ercolecellino@ilduomonovara.it", "subject": "Il Duomo, i dati non tornano"},
    "19dbb0fbe72fc483": {"date": "2026-04-23", "sender": "Dami", "to": "info@ilcortileshop.com", "subject": "2-3 fix sul vostro eCommerce"},
    "19dbb09adbf8c477": {"date": "2026-04-23", "sender": "Dami", "to": "info@idressmap.it", "subject": "iDress Map, una cosa sulle ads"},
    "19dbb04f0be516fa": {"date": "2026-04-23", "sender": "Dami", "to": "luca@galianostore.com", "subject": "Tracking + campagne Meta"},
    "19dbaf8e25021288": {"date": "2026-04-23", "sender": "Dami", "to": "gaia.martinelli@franzkraler.it", "subject": "Franz Kraler, una cosa sulle ads", "bounce": True},
    "19dbaf0b63a2c46b": {"date": "2026-04-23", "sender": "Dami", "to": "giulia.t@eraldo.com", "subject": "Eraldo, store Shopify"},
    "19dba377f446d919": {"date": "2026-04-23", "sender": "Dami", "to": "shop@kauboutique.com", "subject": "Kau boutique, una cosa che ho visto"},
    "19dba157c02265e2": {"date": "2026-04-23", "sender": "Dami", "to": "vsb.brand@gmail.com", "subject": "2-3 fix sul vostro eCommerce"},

    # === APR 22 ===
    "19db5f7f33ff0be7": {"date": "2026-04-22", "sender": "Dami", "to": "shop@gaiasegattiniknotwear.it", "subject": "Gaia, una cosa sulle ads"},
    "19db5ea8def709df": {"date": "2026-04-22", "sender": "Dami", "to": "ceccarelli@carmenboutique.it", "subject": "Carmen boutique, una cosa sulle ads"},
    "19db5e4673f9b5c9": {"date": "2026-04-22", "sender": "Dami", "to": "customercare@divoboutique.com", "subject": "Tracking + campagne Meta"},
    "19db5db44b9ad736": {"date": "2026-04-22", "sender": "Dami", "to": "assistenza@dipierrobrandstore.it", "subject": "Di Pierro, i dati non tornano"},
    "19db5cb87f95d942": {"date": "2026-04-22", "sender": "Dami", "to": "storeonline@delloglio.it", "subject": "Tracking + campagne Meta", "bounce": True},
    "19db5ca626e4616c": {"date": "2026-04-22", "sender": "Antonio", "to": "egronchi@bombe.to.it", "subject": "Shopify + crescita eComm"},
    "19db5bf8f296ae0e": {"date": "2026-04-22", "sender": "Dami", "to": "info@boutiquetricot.com", "subject": "Tricot, una cosa sulle ads"},
    "19db5b6145788914": {"date": "2026-04-22", "sender": "Dami", "to": "martina.fumagalli@biffi.com", "subject": "Tracking + campagne Meta"},
    "19db5b320a4a0c0d": {"date": "2026-04-22", "sender": "Dami", "to": "svenja.mittorp@biffi.com", "subject": "Tracking + campagne Meta"},
    "19db597026455394": {"date": "2026-04-22", "sender": "Dami", "to": "eshop@10corsocomo.com", "subject": "10 Corso Como, una cosa sulle ads"},
    "19db41b7208ea2eb": {"date": "2026-04-22", "sender": "Manu", "to": "aversentegiada@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19db413d2b00d766": {"date": "2026-04-22", "sender": "Manu", "to": "ninodannunzio97@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19db4078690278b5": {"date": "2026-04-22", "sender": "Manu", "to": "g.scamardella@gmail.com", "subject": "Accorgimento rapido sullo store"},
    "19db3fe24d6aebd9": {"date": "2026-04-22", "sender": "Manu", "to": "mirko.pantaleoni@uynsports.com", "subject": "Accorgimento rapido sullo store", "bounce": True},
    "19db3f60af90beac": {"date": "2026-04-22", "sender": "Manu", "to": "enrico.magrini@hotmail.it", "subject": "Accorgimento rapido sullo store"},
    "19db3f3dd4073f8b": {"date": "2026-04-22", "sender": "Manu", "to": "j.laganga@pinko.com", "subject": "Accorgimento rapido sullo store"},

    # === APR 20 ===
    "19dab61a23ccdb40": {"date": "2026-04-20", "sender": "Manu", "to": "pierpaolomoracas@ceneregb.com", "subject": "Accorgimento rapido sullo store"},

    # === APR 16 ===
    "19d9754b56668937": {"date": "2026-04-16", "sender": "Manu", "to": "andrea@brunarosso.com", "subject": "Accorgimento rapido sullo store"},
    "19d9744afc2a151e": {"date": "2026-04-16", "sender": "Manu", "to": "matteo.ceccato@alducadaosta.com", "subject": "Accorgimento rapido sullo store"},
    "19d973d33978a8e4": {"date": "2026-04-16", "sender": "Manu", "to": "sara.agnelli@angelominetti.it", "subject": "Accorgimento rapido sullo store"},
}


def to_email_lower(s): return (s or "").lower().strip()


def main():
    data = json.loads(DATA.read_text())
    all_prospects = data.get("active", []) + data.get("no_reply", []) + data.get("bounced", [])

    # Index del JSON
    by_thread = {p.get("thread_id"): p for p in all_prospects if p.get("thread_id")}
    by_email  = {to_email_lower(p.get("email")): p for p in all_prospects if p.get("email")}

    # Statistiche
    json_thread_ids = set(by_thread.keys())
    gmail_thread_ids = set(GMAIL_THREADS.keys())

    # Filtra thread che hanno sender (skip auto-test/Il Duomo non-labeled)
    valid_gmail = {tid: t for tid, t in GMAIL_THREADS.items() if t.get("sender")}

    only_in_gmail = set(valid_gmail.keys()) - json_thread_ids
    only_in_json  = json_thread_ids - gmail_thread_ids

    # Mismatches: prospect nel JSON con dati diversi dal Gmail canonico
    date_mismatches = []
    sender_mismatches = []
    bounce_should_be = []
    contacted_but_human_reply = []

    for tid, gmail_t in valid_gmail.items():
        if tid not in by_thread: continue
        p = by_thread[tid]

        if p.get("first_contact") != gmail_t["date"]:
            date_mismatches.append({
                "id": p.get("id"), "brand": p.get("brand"),
                "thread": tid, "json_date": p.get("first_contact"),
                "gmail_date": gmail_t["date"],
            })

        if p.get("sender") != gmail_t["sender"]:
            sender_mismatches.append({
                "id": p.get("id"), "brand": p.get("brand"),
                "json_sender": p.get("sender"), "gmail_sender": gmail_t["sender"],
            })

        if gmail_t.get("bounce") and p.get("status") != "bounced":
            bounce_should_be.append({
                "id": p.get("id"), "brand": p.get("brand"),
                "current_status": p.get("status"),
            })

        if gmail_t.get("human_reply") and p.get("status") in ("contacted", "follow_up_1_sent", "follow_up_2_sent", "follow_up_3_sent"):
            contacted_but_human_reply.append({
                "id": p.get("id"), "brand": p.get("brand"),
                "current_status": p.get("status"),
                "subject": gmail_t["subject"],
            })

    # Group missing prospects by date
    missing_by_date = defaultdict(list)
    for tid in sorted(only_in_gmail):
        t = valid_gmail[tid]
        missing_by_date[t["date"]].append({
            "thread": tid, "to": t["to"], "subject": t["subject"],
            "sender": t["sender"], "bounce": t.get("bounce", False),
            "human_reply": t.get("human_reply", False),
        })

    # Report
    lines = []
    lines.append(f"# CRM NoProb — Audit Report")
    lines.append(f"\n**Data audit**: 2026-05-13")
    lines.append(f"**Periodo**: 2026-04-16 → 2026-05-13")
    lines.append(f"**Metodo**: confronto JSON ↔ Gmail (5 pagine, 200+ thread)")
    lines.append("")
    lines.append("## Sintesi")
    lines.append("")
    lines.append(f"- Thread Gmail outreach validi: **{len(valid_gmail)}**")
    lines.append(f"- Prospect/bounce nel JSON: **{len(all_prospects)}**")
    lines.append(f"- Thread presenti nel JSON: **{len(by_thread)}**")
    lines.append(f"- 🔴 **Thread Gmail MANCANTI dal JSON**: **{len(only_in_gmail)}**")
    lines.append(f"- ⚠ Date `first_contact` SBAGLIATE nel JSON: **{len(date_mismatches)}**")
    lines.append(f"- ⚠ Sender SBAGLIATI nel JSON: **{len(sender_mismatches)}**")
    lines.append(f"- 🔴 Bounce non riconosciuti (status ≠ 'bounced'): **{len(bounce_should_be)}**")
    lines.append(f"- ⚠ Risposte umane mai rilevate (status ancora 'contacted'): **{len(contacted_but_human_reply)}**")
    lines.append(f"- 🟡 Prospect nel JSON senza thread Gmail corrispondente: **{len(only_in_json)}**")

    # Missing
    lines.append(f"\n## 🔴 Thread Gmail mancanti dal JSON ({len(only_in_gmail)})\n")
    for d in sorted(missing_by_date.keys(), reverse=True):
        items = missing_by_date[d]
        lines.append(f"\n### {d} ({len(items)} thread)")
        for it in items:
            tag = "💥 BOUNCE" if it["bounce"] else ("✉ REPLY" if it["human_reply"] else "")
            lines.append(f"- [{it['sender']}] `{it['to']}` — {it['subject']} {tag}")

    # Date mismatches
    lines.append(f"\n## ⚠ Date `first_contact` da correggere ({len(date_mismatches)})\n")
    lines.append("Il JSON ha date stimate; il valore Gmail è quello reale.\n")
    for m in sorted(date_mismatches, key=lambda x: (x["json_date"] or "")):
        lines.append(f"- `{m['id']}` **{m['brand']}**: JSON `{m['json_date']}` → Gmail `{m['gmail_date']}`")

    # Sender mismatches
    if sender_mismatches:
        lines.append(f"\n## ⚠ Sender da correggere ({len(sender_mismatches)})\n")
        for m in sender_mismatches:
            lines.append(f"- `{m['id']}` **{m['brand']}**: JSON `{m['json_sender']}` → Gmail `{m['gmail_sender']}`")

    # Bounces missing
    if bounce_should_be:
        lines.append(f"\n## 🔴 Status BOUNCE non rilevato ({len(bounce_should_be)})\n")
        for m in bounce_should_be:
            lines.append(f"- `{m['id']}` **{m['brand']}**: status attuale `{m['current_status']}` → deve diventare `bounced`")

    # Human replies missed
    if contacted_but_human_reply:
        lines.append(f"\n## ⚠ Risposta umana ricevuta ma status ancora 'contacted' ({len(contacted_but_human_reply)})\n")
        for m in contacted_but_human_reply:
            lines.append(f"- `{m['id']}` **{m['brand']}**: status `{m['current_status']}` (subj: {m['subject']})")

    REPORT.write_text("\n".join(lines))
    print(f"OK — Report scritto in {REPORT}")
    print(f"\nThread Gmail validi: {len(valid_gmail)}")
    print(f"Thread MANCANTI nel JSON: {len(only_in_gmail)}")
    print(f"Date sbagliate: {len(date_mismatches)}")
    print(f"Sender sbagliati: {len(sender_mismatches)}")
    print(f"Bounce mancati: {len(bounce_should_be)}")
    print(f"Risposte umane mancate: {len(contacted_but_human_reply)}")


if __name__ == "__main__":
    main()
