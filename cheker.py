import asyncio
import aiohttp
import json
import os
import random
import time

STATE_FILE = "vk_monitor_state.json"
DOMAINS_FILE = "domains.json"

VK_EXECUTE_URL = "https://api.vk.com/method/execute"
VK_API_VERSION = "5.199"

BATCH = 25                  # макс. вызовов API в одном execute
TOKEN_INTERVAL = 1.0        # сек между запросами с одного токена (0.5 -> проход ~12 сек, но риск капчи выше)
REQUEST_TIMEOUT = 10
CAPTCHA_COOLDOWN = 120
MAX_RETRIES = 6

TG_BOT_TOKEN = "8805037958:AAH3ZZFCLj4gif--H8cQRDHXyAY1L_bcLpk"
TG_CHAT_ID = "-1004388437626"

VK_TOKENS = [
    "vk1.a.wAl6aBQ_GmEsQGAi6q7BtV0FYDxuZJORtL3OIAufyutdfThOeKrHw6DAl5EI9Wrh66fEnNyGWp8IDuW30lT5WQrwZi_iZhkapyTXBhVGU4AyXYRqJ3FZ9U3vTd0Q4u83XgQfN8tJgM1pwRghLcmYmRyD32J_m544PAOwBYCXIJb8NJ0JCLIcLrIsy6nLZps82ZOm1XU_fUskrUbL-g433d7BANtFHXWMhszNoFYnlw4",
    "vk1.a.7iqpuE8101IKlxdmvmT6nrmt1alOyChIfcQNu3aVXpXV1c2gRc7wR0cl5ZPOJKNqfbfqGVAaGsIJp2506FyTziX4CFxo964JgmvI_jiTZ3luLN814KnFdXB-v9hPg69_y0Z1iMoWPFbKjCUcK9xrqZa1rcIqGnuEf00_7w1GhNtW4-cp8R74_ixqCJWGAAuxcLxhzYLydlwcsaihXOCh9HbmLEbaX-KB1L2sgOOmFwk",
    "vk1.a.D8E7pkXFH3f_6cJB1yiy3WYSmwuGNBmG1MIa1XHYExgxn_L8TnddrwMAzP7NAl8xm2Bqr_LvXdF7wgnLsSPxGjjXjexPDoJD4cePAEZq-qSFsPXeiYSlmtyx7hUob-QQmbcpEbtykuF5OC_IfklPkDBOU2hVSiw2NKasT6ssihG6q317boqikVmucgi_9eDy2DW5-vz7r2mjr45WlYCM7PSiv2F-AiHzV2A_3i-ssDw",
    "vk1.a.etuL9WYu0qSWi8DxSWjzM6NC5cP5ZNNiGDhib_kfp3mCNmojD35U_5BPeY9j5m62fwCTDp2UPy1g2azuhApbXRJPXEPdaERkjeq44yH8Tx8lhJfLVTd44Exiclqh9aDcOpUPP5k34ONZQdW0ys_XQ4zF-CTGPNk8OerEsXo32-8L0LUPsTZOHkTEZh932273nUvHamwAaLO9olXRV6ukgxJpoGxgmDykRQRSq-l9W7Y",
    "vk1.a.RI19EXM1EVRC9qEph2F3XE0Oksx7W7q_6VUIcsvoNtSD3DIo_qSshe0NACz25_PUqHneeKb6rIi-QekU3jJI1LE0-Coc0uyB8jOSU2hIpLlb_kogKTwWg2bdVMZtXIIt0kXqvapccgWLC-LwCSyr3f3aTzbcHu5l1OJNqXRo-azE28s6hbrsWCK38OdIGTHYGDYy2PMhU74YGYgqLx6sONZJ_XHr5RmC0jQEiLWFJNA",
    "vk1.a.0cnQMXMgwtwqtqhTXZb4aEEH1Do6MP3sbP2mljdfMZ4lwKyntAb6o0sB1JiBDpELp2JkpOe49MyvD6F2Dv5ofOPtX6CcZh-z2g7mutzVvhQCBl9catNi3xp9xX_ZFMy_MR2e1oyGaI983HNRPOKIC33pC_8KMR3jPE9MPjLEFg59qCBS2OCIVbAIPs1ay_K64UqGrazkgczI7mWBNQ5VpjK2u_fKSSYm2ofgClalKRo",
    "vk1.a.nwOhJ9t7VIcMGcID1W9D-5tk7L4yiexgAblS_buC88aQKh7onxxuz273aFbtsLkamKf_ysA9u4Qlgon5F9SozuJidqS6Kz4v3_myQVJ5GRbzGWNCF70j-zV3vbiuvmbKN5IjkBHol24QuvB3hqGBPoJkXybvXbbtqg2J0-0GatAoiPnSyNKD90_u2ox5PYqI-T0PSkjj5cKeXkPIR4-LzNbFRx8CfbOJWfFdNFwc85E",
    "vk1.a.CQP-VM5H6QH4zRFGc9VI876jJhydGIzaigAZZGdfC10BpZ0XmYHTPCy2F-5ciHA0LMsK290HVjKyiJpIryPud8K_-722_xepI8hRWV2WfmdhRkM1B7To4aJqO2XwC5ImU5oMwODLZqhhBpXAgnFynxGjCd6M3xxE2EtklgWWWYVAUztUi3G-QXlEkUyRcF-zNPGvoI_IzNhqDS5FCwIfAc0pkTd--x4I_o-wABmDHLw",
    "vk1.a.zkMELjHGLTYm1ItKA3ASbXjqqmp0aXmoqoJYxVrpSkYOK88nSTUBfhwSIYZv2nCItnfUkD2d0EdBAmliC9p3JSPi-d5bl4Tg4xpAEjCGJsLMmMMHSMhKFgXN0hUfnJy17Cg30liqHUUTrlll9B8x-eqyeBrqH9MPTEyQ8PS_QqY0NH5U5jKuFx0xXzI-mQbkwf6sh1bi9qlDh6aHk9sGALpDg-08vbIRpqJ36NptX-o",
    "vk1.a.NUjSRfXeoIPNO1LdFCTkt64Py7cV0dkV18X0ijumwqx-VvZoTGqS5xIoOLahG-0Ci_IqxHcOL0I2D4j4CtFmz-bLcW5B5MgX_QmUMoW5pTv0LmepTadEeBkf8gWd_oan8zx9I5CTizXlMn9eTt3NdjH3G2I_SI-SKmjgD6eIep-bTImv7LxR8qhbGzXjOkSL8b0YhAmJCB1Pic4YkaevtYzGVQWbNkgZNjwbL9k3TH8",
    "vk1.a.Sy-LCp1kq3r0m3v6bW-9_LyYw2f4Jc8pz2r0Y5tD3rQy_8W1X5_yQy2LwNf9c4Kp3G7dT0nG6kO2bP8dV0CwS8vM3qW6r1zQ2V5kL0_Hn7eQ9T3kR5tM4vN8L2fJ6bZ1pY3Qw8cR0vX4hY9kW1sB3mD5jG7nT2fR8dL0zK6vW4cJ1pB7xS5qN9tM2fP8cV3dL6bY1wJ4kR0tZ5nG2mH9sC3fK7vD1qL8bW6xP2jT4rV5mN0hS3gY9kL2cB7fQ4tX8vP1nD5rM0gW6kJ3",
    "vk1.a.tnfKVGlz8f_NjnFhnvq_9CNTrD85ofMS6c6tiTMvS0gmskN3E0_WY7zqohMBAE4DlIBFrIStZ9qomgPmpfW95hVQ9z8Q5GS9MdVRAdV_i2me8IKQ3Qs3Q4lknT4CQ0XEsPxwfoH-hBtcyY5YX4t-KjF6Vrj5ghVimXGAUY1eFqAmLp4cCmEsqgbd5O0uO6CLfku9uOeZnTATB__2bnZ-kK8sNEJqL9vMwHX1x-xZHHE",
    "vk1.a.PaT0ENF-_5lZqCbDKVHWPbWjFaFkKIPzBBz9V_r4-PjC22_fe6RA7I5JM-8ji37oSo8WhPN7CKtnWKwKqXo8Zb36-jkDdFmp7O9KcLqSb0GfruTuB75kLd0fDZBHHS89JKa6C4Fg9YaP6PyJV1abDNN3Bn9NwcuD7RFCPzF-hXERGgYHEQntDnLmioDsOy2e3h5NZi2YPn1w-aWeVHkgf-ilyo226KqmLNfL9G-iGvw",
    "vk1.a._r6Ut_VTtpmBy4QJrphiDhgroaq4o4ld_WHg2OCofNkNyxrbcZd-JMaEYelHeae2_Jtxvxq1HLLHBCw5oQrgPn_QWY6yC9mo_6dR0Ys8AqFcNEaiq2YTZs_jUGBJPzv5rhT9jQsVWYlEKYm19m73po6VypdtfTTpOsa3qzOjufeRv8zq398QYYYyOuCmANTRzOUPvhQZaThfhiZDjHTWUYuIjziz7YGkt6ymriymL0s",
    "vk1.a.Cn2dW0AOFpU0bBHDZBI6Tpssvu--jJJEvjJgvYEHU11djEuV-ypoFgm3iSM5QQ93QVAHgdWsGbvGpcVw3z-PBNNtTexBN-3ffTSHRTIbJbXWuMWDs9VX0VNEWUjnWCtdtiA9EN3Jri7AA7QQUbzYnKvO5dYHEnimu6zdgVAG4TQAOWZyHf8ScHW0ZnL0AKMkRewsgbrwr07iPS3WOZ-NdCr3lWTZ0Gltzo3y5Wpaxx8",
    "vk1.a.RrZtXGTdt6gDQcr0xzdflPwXeDusuvl4Z3WgIA4yLvbOTmcllADBD33BdsUrKdozEwwtt-HrqZwaya5Ji8gcnoIHmlawVHwbbrizQebOToGqbe1Vg8wp546rFunqzp5mmhp-0veLzSxyWE0OxzP55pP4Al_D6m7Fx7_bdDGjXta1dS4ZW-UwKjLOIi7oRKFi-FrRF9JKMcJn3lvcq8B6-Ehd_nWFLqrfCrcACjHSskA",
    "vk1.a.Iw9XXSuQNtPn0oXKbEPukzYh7FORedjx--_Me-9ybaqsqEFwoh4dlK21zgNM44E_v0W9rFe_PKS798Xb3PyCCUkqKJ2NtFS9-qluEdlJM095z7FpkWCggMksbkBNTJZp3ibyayVI45WvcsIWavtNqEHOVI3s_O0JDzXB3hMMY0yn_ULPe0NC8gwoU0CNKZ057Ev31suYcUzpBGpxXi4tayEFpOLfSn6bFVUMtGJ4gOs",
    "vk1.a.e6SrzCMlLxiHJ2N4EDrNau1Lradl8Sb8-oN_UH9gwOyeJihyklrof91dFi590QWcn5htIB5WLe_ArN-_Xt0pb-TUCyBjHTJR1ioQHS9Dsma1tL339h9F4YFboywvZwY-SgxAD97rgtIHA_m3VyDAiY5bwYoylJ8x7wHdpSiTqsXaXTh8V63QpV5oXikkLDG2S2OvEE603NRCEbzwtVjpg3b2oOmSi3bA7Bsq4Km0ND4",
    "vk1.a.WUCIErVivWNxe164WBy0Y2a5mlwatX8BmpgunVvEQLyGRsts9FLJTD0scFi3R3-730guQ_qGC0VvFr8cILoJP7KCrcLkawxgWnV0Mewf3EIHM8GXyl_bx6K2cuSDA_qZjjirdhYpU6ZwEsV2HLtPwmo9WmsK6h96xsgP6dAn3zQqCTYfTy-3Dg2u7_UfEdyg2yysEnTkU-aIOMKuZj_ap5D4IyfHgFo5SRVXzhfU75E",
    "vk1.a.Pt10zABl2XhHcHDEF2RMWWCNxKwsVqgkwI-O_71OXw1q4XEmX8OC3yIACxGAGD7aK6Lvoyl8Cv_EBkMImcvrX24pBCJ3oNw9eObc9khV-IjoKENFIWUM_gooCYXEb4NWfCtyDO2F0B7kF3TT9MjOGRX4QSO5QtYPryt6QWIshdt4jOyIZEccY6kCD14_thrVJbQ4XYDbX96mAcBX34zV9PdF-DRpbPGjNhuSCo8opI8",
    "vk1.a.o5UtMbriKbUJk40f4Yhzxtjlz-qwsrxqj8SX0TW9rYlEe56Xzn2_O8hWfajMrHuXNtriCAwMEymOYE3oxrSKEkKk7nmjFBVgljHcuZqAItoeLKm0AqDTW2N0njHhCO6hrlkF5Txk_BRAn7bQOVY2adDN1ka8ewAYT5oZdqQiAuhdnF28zKIL87yO3Kvhwj_EGWGeA4W8GlH0iAiZoo4L9e1pdGzqu8v4zndnH3eQVMc",
    "vk1.a.a6LZKMghhjVLQ2YqI51x6BfKR2nzWoiWQ1TB8eoa05vq3fWAJ3Ly0n5QXRf_LyWwdmbDyLNOUYXznzIPKfgbypngQEqQWo37lYq5zAJV511poAt3fqMBJOPHet95n7QcZdrh7mrHzMdwDTl9gjum0gINGLHsXhYOU-G288wa_ZqDtNo8fViXIJa4dM2c-jLffNluUvlrgR_Cx1X-CON7XK73rJu9U8S5Tsth-q5HUas",
    "vk1.a.maMLO0T3MCju4ImfjLH2U7txQc2NMLQGFc0vWdL_mw-_hqcmo6mDl9om9NQhGOVgJXReAZmRlt9S_AF1acDR5pbN7pumu5CvfQpgI_TdB2cI4cSchLUyRc7oDqOqbkDNOIhrKruOdd7ii175DWGr1FCxrxluUqayJCyqXq_lSf89mDeuRvN9l_ljUpiOUwJ5_kiQcUzyirC_znvU3D_aSRnBlJcVXTxcKbR39P54vrg",
    "vk1.a.D5SghUfn6Iy5SYTOg-Ahb2oXxQT4RcNNKt-YGXgefBPJYuf8j5ByGftYg0eys2-bLQiPeFOPtWwfzh4XKYmS9gDvDR-DY_JbrFBYszimWLZOi190VoVoWqF4RsX_UhsYb8O17bXl-Np86xDomN9gHKfs0sqxF6rrljehEKV1i_mlv8e32P4PQuGgEvQDIQcbmPsf-YQbVqCGYKQwpyrv4rObyoX-Bl51HDe_qd95FD0",
    "vk1.a.CqrPIt4um6hd4UBDbURtI9g9ZLL6aVv54Ow1cNExem7zSJ5_raCpfqMJOhuX9TbHjDvB9lhA655wujOlMeax3BDq4h1v4Is-cz3PcncA4HS7cJIs8NI6_AHmCcsb5PcDoov7Qtlwgst15SVAkVZ6X5JUngf-krDvxluN7f2-GjwzzvoUI7ixCcLTxHixvzM7QghPO76oJQ8o6fcRpcdAugC1iBgKF_p6HWor-zhcJck",
    "vk1.a.uG2NCAiAI5XNrswTa-5wl-3guB_e0J2eMdZcuvynOwMKUjIwfUAWY6NgJnY0ww5ohi9aQQZMgCRQ7hMGfxdVO7CHUXJPk2E_934iEDN2pt6-op4Y5iuvz90AnQtjEJ5bclEFlWld88zSe7pnKMXGrk1i7owNmHhRdJKYMQDv3WBqtiFhilEGQC4DqvBR5DFBHrpqKudj4sQk3UKQJoUfLV1YMYaH2aHS0emFbGzTMl8",
    "vk1.a.pzPxrHrHrc9FYSb5iWXATc0zM02yfFfs6or2INq3j9mpgGqN5mzZoQnvFCvDgRg19TYYWq_s5QvtYyjhpMQWyK_tPuXXCGbA32J3C6hxgmuAJIE7wXg4FRhCgQZGehfT6vN6NcZLXWY_t4eaoj5N3w1u6BSB0jh0cF2Q1g0wMQtZPh0t-kPsK0giUXeGGj0WmOVkJY839JQAS93aRuIHmV1z_T0dVUbCZDNKfqid61s",
    "vk1.a.g50LYfet5bARZbE5aUW9QLhmZWH1FwQ_oNUxxwGcHbVr4TFP7gBz1kx1GuaULv2NVmVD_EcHkK-IvGd7-jrXkCibdnW5Hf7psijTWLLK547bgRIjNJj9PZExw2jIGss3qhQvsmwsDxyGctZkBxnEGmQD9v20Rr18zgkSJ6EEXQRoSsMrR98zZKgpw6N0M9k5saJID9LVyMq9oQ5Aa9GeOW8rcX7eN1U4tjojY-RQvBQ",
    "vk1.a.wPYv8TxO4T4MoWf40tWQ22f0sE7CCpgsGZbS0gE_UMN9qv7hLGqO1oOYrp5Nh91kX-4UySad6AEdcAkG1NLGW3lKDPWBLs5J1IVwj4CDM-2WdLIl-MLPkQZKIPUv_GuYVKqlNe83JVPdN2PDzJpDok77FYVeFP-0z9pvVD4aXfGUTUejN8vJnbyBCh67W3y63oY5PGIVunWEn2GW0ROkP4LLCH-Xyoed0IAinVahA9A",
]


# ---------- utils ----------
def load_json(filename, default):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(filename, data):
    tmp = filename + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, filename)


def load_tokens():
    tokens = list(dict.fromkeys(x.strip() for x in VK_TOKENS if x and x.strip()))
    if not tokens:
        raise RuntimeError("Нет VK токенов")
    return tokens


def load_domains():
    raw = load_json(DOMAINS_FILE, None)
    if isinstance(raw, dict):
        raw = raw.get("domains", [])
    if not isinstance(raw, list):
        raise RuntimeError(f"{DOMAINS_FILE} должен содержать список")
    result, seen = [], set()
    for d in raw:
        if not isinstance(d, str):
            continue
        d = d.strip().lower()
        for p in ("https://", "http://", "www.vk.com/", "vk.com/"):
            d = d.replace(p, "")
        d = d.lstrip("@").rstrip("/")
        if d and d not in seen:
            seen.add(d)
            result.append(d)
    if not result:
        raise RuntimeError("Нет доменов")
    return result


def owner_number(i):
    return "FREE" if i is None else str(i)


def owner_url(t, i):
    if i is None:
        return "FREE"
    if t == "user":
        return f"vk.com/id{i}"
    if t in ("group", "page"):
        return f"vk.com/club{i}"
    if t == "application":
        return f"vk.com/app{i}"
    return f"vk.com/{t}{i}"


# ---------- telegram ----------
async def send_telegram(session, text):
    if not TG_BOT_TOKEN:
        print(text)
        return False
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        async with session.post(url, data={"chat_id": TG_CHAT_ID, "text": text}) as r:
            return r.status == 200
    except Exception as e:
        print(f"[TG ERROR] {e}")
        return False


# ---------- VK batch ----------
def build_code(batch):
    calls = ",".join(
        f'API.utils.resolveScreenName({{"screen_name":{json.dumps(d)}}})'
        for d in batch
    )
    return f"return [{calls}];"


def parse_item(item):
    """None -> ошибка; (None, None) -> свободен; (id, type) -> занят"""
    if item is False or item is None:
        return None
    if isinstance(item, dict) and item.get("object_id") is not None:
        try:
            oid = int(item["object_id"])
        except Exception:
            oid = item["object_id"]
        return (oid, item.get("type"))
    return (None, None)


async def call_execute(session, token, batch):
    data = {"code": build_code(batch), "access_token": token, "v": VK_API_VERSION}
    try:
        async with session.post(
            VK_EXECUTE_URL,
            data=data,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
        ) as r:
            if r.status != 200:
                return "fail", None
            js = await r.json(content_type=None)
    except Exception:
        return "fail", None

    err = js.get("error")
    if err:
        code = err.get("error_code")
        if code == 14:
            return "captcha", None
        if code in (6, 9):
            return "rate", None
        if code in (5, 17, 27, 28, 29):
            return "badtoken", None
        return "fail", None

    resp = js.get("response")
    if not isinstance(resp, list) or len(resp) != len(batch):
        return "fail", None
    return "ok", [parse_item(x) for x in resp]


async def scan(session, domains, tokens, on_batch=None):
    """tokens — изменяемый список: мёртвые токены удаляются из него насовсем.
    on_batch(batch, parsed, token) вызывается СРАЗУ после каждого батча."""
    queue = asyncio.Queue()
    for i in range(0, len(domains), BATCH):
        queue.put_nowait((domains[i:i + BATCH], 0))

    checked = 0
    left = queue.qsize()

    async def worker(token, idx, total):
        nonlocal left, checked
        await asyncio.sleep(idx * TOKEN_INTERVAL / max(total, 1))
        while left > 0:
            try:
                batch, tries = queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.05)
                continue

            t0 = time.monotonic()
            status, parsed = await call_execute(session, token, batch)

            if status == "ok":
                checked += sum(1 for p in parsed if p is not None)
                if on_batch:
                    on_batch(batch, parsed, token)
                left -= 1
            elif status == "badtoken":
                print(f"[TOKEN] невалидный токен ...{token[-6:]} удалён из ротации")
                if token in tokens:
                    tokens.remove(token)
                queue.put_nowait((batch, tries))
                return
            elif status == "captcha":
                print(f"[CAPTCHA] токен ...{token[-6:]} на паузе {CAPTCHA_COOLDOWN}с")
                queue.put_nowait((batch, tries))
                await asyncio.sleep(CAPTCHA_COOLDOWN)
                continue
            else:
                if status == "rate":
                    await asyncio.sleep(2)
                if tries + 1 >= MAX_RETRIES:
                    left -= 1
                else:
                    queue.put_nowait((batch, tries + 1))

            spent = time.monotonic() - t0
            if spent < TOKEN_INTERVAL:
                await asyncio.sleep(TOKEN_INTERVAL - spent)

    snapshot = list(tokens)
    await asyncio.gather(*(worker(t, i, len(snapshot)) for i, t in enumerate(snapshot)))
    return checked


# ---------- подтверждение и уведомление ----------
async def confirm_and_notify(session, d, new, last_id, finder, tokens, state, pending):
    """Перепроверяем ДВУМЯ другими токенами параллельно. Оба должны подтвердить."""
    try:
        others = [t for t in tokens if t != finder]
        random.shuffle(others)
        verifiers = others[:2] or [finder]

        results = await asyncio.gather(*(call_execute(session, t, [d]) for t in verifiers))

        confirmed = None
        for status, parsed in results:
            if status != "ok" or parsed[0] is None or parsed[0][0] != new[0]:
                return  # не подтвердилось: state не трогаем, проверим в следующем проходе
            confirmed = parsed[0]

        cid, ctype = confirmed
        state[d] = {"object_id": cid, "object_type": ctype}

        if cid is None:
            msg = f"✅ Detected release! {d}: {owner_number(last_id)} → FREE"
        else:
            msg = f"✅ Detected swap! {d}: {owner_number(last_id)} → {owner_url(ctype, cid)}"
        await send_telegram(session, msg)
    finally:
        pending.discard(d)


async def run_pass(session, domains, tokens, state, pending):
    notify_tasks = set()

    def handle(batch, parsed, token):
        for d, p in zip(batch, parsed):
            if p is None:
                continue
            cid, ctype = p
            old = state.get(d)
            if not isinstance(old, dict):
                state[d] = {"object_id": cid, "object_type": ctype}
                continue
            lid = old.get("object_id")
            if cid == lid:
                if ctype != old.get("object_type"):
                    state[d] = {"object_id": cid, "object_type": ctype}
                continue
            if d in pending:
                continue
            pending.add(d)
            t = asyncio.create_task(
                confirm_and_notify(session, d, p, lid, token, tokens, state, pending)
            )
            notify_tasks.add(t)
            t.add_done_callback(notify_tasks.discard)

    checked = await scan(session, domains, tokens, on_batch=handle)

    if notify_tasks:
        await asyncio.gather(*list(notify_tasks), return_exceptions=True)

    return checked


async def main():
    tokens = load_tokens()
    domains = load_domains()
    state = load_json(STATE_FILE, {})
    state = {k: v for k, v in state.items() if isinstance(v, dict)}
    pending = set()

    print(f"Доменов: {len(domains)}, токенов: {len(tokens)}")

    connector = aiohttp.TCPConnector(limit=200, ttl_dns_cache=3600)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            if not tokens:
                print("[ОШИБКА] не осталось рабочих токенов")
                return
            started = time.monotonic()
            checked = await run_pass(session, domains, tokens, state, pending)
            save_json(STATE_FILE, state)
            print(f"[CHECK] {checked}/{len(domains)} за {time.monotonic() - started:.1f} сек "
                  f"(токенов: {len(tokens)})")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
