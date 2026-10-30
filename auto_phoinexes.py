#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
  BOT AUTO PLAY 24/7 - PHOINEXES TAP (@PHOINEXES_TaP_BOT)
  Platform: Base44 App (https://phoinexes.base44.app/)
  Bot     : @PHOINEXES_TaP_BOT (ID: 8650334863)

  TÍNH NĂNG ĐẲNG CẤP:
    - AUTO INDATA 100%: Tự động kết nối Telethon StringSession lấy
      init_data mới từ @PHOINEXES_TaP_BOT (không cần người dùng lấy tay).
    - AUTO SYNC: Đồng bộ thông tin chim Phượng Hoàng, Feathers, Năng lượng, Level.
    - AUTO TAP THÔNG MINH:
      + Đóng gói số lượng tap theo từng packet chuẩn 20 - 30 taps.
      + Tạo requestId (UUIDv4) và sequenceNumber chuẩn xác theo Base44 engine.
      + Tự động tính toán lượng tiêu hao năng lượng và nhận Feathers.
      + Giãn cách giữa các lần tap ngẫu nhiên 1.5s - 2.5s như người thật,
        chống spam, chống checkpoint/ban 100%.
    - AUTO RECHARGE & REST:
      + Khi cạn năng lượng (< 25), bot tự chuyển sang chế độ nghỉ để chim hồi sức.
      + Tự động thức dậy ngay khi năng lượng hồi phục để tiếp tục cày.
    - HỖ TRỢ CHẠY 24/7: Cả trên máy tính cá nhân và GitHub Actions.
====================================================================
"""

import time
import json
import urllib.parse
import re
import os
import uuid
import asyncio
import base64
import sqlite3
import tempfile
import random
import requests
from datetime import datetime, timezone
from colorama import Fore, Style, init

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.crypto import AuthKey
from telethon.tl.functions.messages import RequestWebViewRequest

init(autoreset=True)

# -----------------------------------------------------------------
#  CẤU HÌNH HỆ THỐNG
# -----------------------------------------------------------------
API_ID = 39182276
API_HASH = "f02b155d895a3a3fbf8a1cbe810b5338"

# StringSession chuẩn Telethon 353 ký tự (hoạt động hoàn toàn trên RAM)
KNOWN_GOOD_STRING_SESSION = (
    "1BVtsOHIBuxmpWiBJ9hvwV9pSrzWw5U2I5Fe20Ww8l1LCk9rnsG6T6lLZEJXZE1JJC_qUH_yyWHnRoedRNI5lJYnfjRN4gyGeDrCxquDU12ZflrpCz0VLhMZx2C0LlyUCy2eHRSRE1wUCpEYZaymL0P7Z9eAHwMy4Oogewh5TqyO4x4MF6j0yTq8Zvfpv43O4aQDzErNv3GRqpx8DXBcOJIMP9yVhq-Mby5VH5J9cF-h-bJ5ws3xKjA4GY7YKjHxDt9OI-Zr7mr-V3qZy99UxJooThJj51f2RqOKhODdLh9XZQ0ygSoAd3iFAZDOPMEo8Ch5TrrzLXi2Q3N0HorIL1JfV0xoFQlY="
)

BOT_USERNAME = "PHOINEXES_TaP_BOT"
WEBAPP_URL = "https://phoinexes.base44.app/?lang=vi&tab=phoenix"
API_BASE_URL = "https://api.phoinexes.app/api/apps/6aabe6b48f01b5435b7ee4d7/functions/phoenix-game"

CURRENT_INIT_DATA = ""
CURRENT_USER_NAME = ""
CURRENT_USER_ID = ""
CURRENT_REVISION = 8

def log(tag, msg, color=Fore.WHITE):
    t = datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] [{tag}] {color}{msg}{Style.RESET_ALL}", flush=True)

def get_clean_string_session():
    raw = (
        os.getenv("TELEGRAM_STRING_SESSION") or
        os.getenv("TELEGRAM_SESSION_B64_ACC1") or
        os.getenv("TELEGRAM_SESSION_B64") or
        ""
    ).strip()

    if not raw:
        return KNOWN_GOOD_STRING_SESSION

    if raw.startswith("1") and 300 <= len(raw) <= 450:
        return raw

    try:
        bdata = base64.b64decode(raw)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".session") as tmp:
            tmp.write(bdata)
            tmp_path = tmp.name

        conn = sqlite3.connect(tmp_path)
        c = conn.cursor()
        c.execute("SELECT dc_id, server_address, port, auth_key FROM sessions")
        row = c.fetchone()
        conn.close()
        try: os.remove(tmp_path)
        except Exception: pass

        if row and row[3]:
            ss = StringSession()
            ss.set_dc(row[0], row[1], row[2])
            ss.auth_key = AuthKey(data=row[3])
            extracted = ss.save()
            if extracted:
                return extracted
    except Exception:
        pass

    return KNOWN_GOOD_STRING_SESSION

# -----------------------------------------------------------------
#  LẤY INIT_DATA MỚI 100% TỪ TELEGRAM (AUTO INDATA)
# -----------------------------------------------------------------
async def fetch_fresh_init_data():
    global CURRENT_INIT_DATA, CURRENT_USER_NAME, CURRENT_USER_ID
    log("INIT", "Đang kết nối Telegram qua Telethon để lấy init_data mới cho PHOINEXES TAP...", Fore.CYAN)

    session_str = get_clean_string_session()
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.connect()

    try:
        if not await client.is_user_authorized():
            log("ERR", "Phiên Telegram chưa được ủy quyền! Kiểm tra lại session.", Fore.RED)
            return None

        me = await client.get_me()
        CURRENT_USER_ID = str(me.id)
        CURRENT_USER_NAME = f"{me.first_name} {me.last_name or ''}".strip() or me.username or CURRENT_USER_ID

        bot = await client.get_input_entity(BOT_USERNAME)
        web_view = await client(RequestWebViewRequest(
            peer=bot,
            bot=bot,
            platform="android",
            from_bot_menu=False,
            url=WEBAPP_URL
        ))

        frag = urllib.parse.urlparse(web_view.url).fragment
        params = urllib.parse.parse_qs(frag)
        init_data = params.get("tgWebAppData", [None])[0]

        if not init_data:
            query = urllib.parse.urlparse(web_view.url).query
            params = urllib.parse.parse_qs(query)
            init_data = params.get("tgWebAppData", [None])[0]

        CURRENT_INIT_DATA = init_data
        log("OK", f"Đã lấy thành công init_data PHOINEXES! Chủ nick: {CURRENT_USER_NAME} (ID: {CURRENT_USER_ID})", Fore.GREEN)
        return init_data
    except Exception as e:
        log("ERR", f"Lỗi lấy init_data PHOINEXES: {e}", Fore.RED)
        return None
    finally:
        await client.disconnect()

def get_fresh_init_data_sync():
    return asyncio.run(fetch_fresh_init_data())

# -----------------------------------------------------------------
#  GỌI API GAME PHOINEXES (BASE44 FUNCTION)
# -----------------------------------------------------------------
def call_phx_api(payload):
    global CURRENT_INIT_DATA
    if not CURRENT_INIT_DATA:
        get_fresh_init_data_sync()

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
        "Origin": "https://phoinexes.base44.app",
        "Referer": "https://phoinexes.base44.app/"
    }

    payload["initData"] = CURRENT_INIT_DATA

    try:
        r = requests.post(API_BASE_URL, headers=headers, json=payload, timeout=20)
        if r.status_code == 401 or "expired" in r.text.lower() or "unauthorized" in r.text.lower():
            log("AUTH_EXPIRED", "Token hết hạn, đang tự động cấp mới init_data...", Fore.YELLOW)
            get_fresh_init_data_sync()
            payload["initData"] = CURRENT_INIT_DATA
            r = requests.post(API_BASE_URL, headers=headers, json=payload, timeout=20)

        return r.json()
    except Exception as e:
        log("API_ERR", f"Lỗi gọi API Phoinexes: {e}", Fore.RED)
        return {"error": str(e)}

# -----------------------------------------------------------------
#  ĐỒNG BỘ THÔNG TIN GAME (SYNC)
# -----------------------------------------------------------------
def sync_game():
    global CURRENT_REVISION
    payload = {"action": {"type": "sync"}}
    res = call_phx_api(payload)
    if res.get("revision"):
        CURRENT_REVISION = res.get("revision")
    return res

# -----------------------------------------------------------------
#  AUTO TAP PHƯỢNG HOÀNG (AUTO TAPPER)
# -----------------------------------------------------------------
def auto_tap_batch(count=25, sequence=1, snapshot_day="2026-10-30", snapshot_time=0):
    global CURRENT_REVISION
    req_id = str(uuid.uuid4())

    payload = {
        "action": {
            "type": "tap",
            "count": count,
            "source": "manual"
        },
        "requestId": req_id,
        "sequenceNumber": sequence,
        "ref": None,
        "trafficHints": {},
        "compactTaps": True,
        "knownRevision": CURRENT_REVISION,
        "snapshotDay": snapshot_day,
        "snapshotTime": snapshot_time or int(time.time() * 1000)
    }

    res = call_phx_api(payload)
    if res.get("revision"):
        CURRENT_REVISION = res.get("revision")
    return res

# -----------------------------------------------------------------
#  VÒNG LẶP CHÍNH 24/7 PHOINEXES TAP
# -----------------------------------------------------------------
def run_loop():
    print(Fore.RED + """
====================================================================
      BOT AUTO PHOINEXES TAP 24/7 (BASE44 ENGINE) ĐANG CHẠY
====================================================================
|  - TỰ ĐỘNG LẤY INIT_DATA MỚI 100% QUA TELETHON (AUTO INDATA)     |
|  - TỰ ĐỘNG TAP KIẾM FEATHERS THEO TỪNG PACKET (20 - 30 TAPS)      |
|  - MÔ PHỎNG GIÃN CÁCH NHƯ NGƯỜI THẬT (ANTI-BOT CHECK SAFE)        |
|  - TỰ ĐỘNG QUẢN LÝ NĂNG LƯỢNG, NGHỈ HỒI PHỤC KHI CẠN PIN         |
|  - ĐỒNG BỘ LIÊN TỤC VỚI SERVER BASE44 REVISION REALTIME          |
====================================================================
    """ + Style.RESET_ALL)

    # 1. Khởi động lấy init_data mới
    get_fresh_init_data_sync()

    cycle = 1
    seq = 1
    last_refresh_init = time.time()

    while True:
        try:
            # 1. Đồng bộ thông tin trước mỗi vòng tap
            sync_res = sync_game()
            if sync_res.get("error"):
                log("SYNC_ERR", f"Không thể đồng bộ game: {sync_res.get('error')}", Fore.YELLOW)
                time.sleep(10)
                continue

            state = sync_res.get("state", {})
            energy = state.get("energy", 0)
            feathers = state.get("feathers", 0)
            day = state.get("day", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            server_time = sync_res.get("serverTime", int(time.time() * 1000))
            user_name = state.get("name", CURRENT_USER_NAME)
            tasks = state.get("tasks", {})

            log("STATUS", f"🔥 [{user_name}] | Lông Vũ (Feathers): {feathers:,} | Năng lượng: {energy:.1f}/1000 | Taps ngày: {tasks.get('tap', 0)}", Fore.LIGHTYELLOW_EX)

            # 2. Kiểm tra năng lượng để tap
            if energy < 25:
                # Năng lượng quá thấp -> Chờ hồi phục
                recover_wait = 120 # Nghỉ 2 phút
                log("REST", f"⚡ Năng lượng cạn ({energy:.1f}). Chim Phượng Hoàng đang nghỉ ngơi ({recover_wait}s)...", Fore.CYAN)
                time.sleep(recover_wait)
                continue

            # 3. Tiến hành tap từng đợt
            batch_count = random.randint(20, 30)
            log("TAP", f"Đang gửi {batch_count} cú tap (Seq: #{seq})...", Fore.YELLOW)

            tap_res = auto_tap_batch(
                count=batch_count,
                sequence=seq,
                snapshot_day=day,
                snapshot_time=server_time
            )

            seq += 1

            if tap_res.get("error"):
                log("TAP_WARN", f"Lỗi tap: {tap_res.get('error')}", Fore.YELLOW)
                time.sleep(5)
            else:
                tap_ack = tap_res.get("tapAck", {})
                accepted = tap_ack.get("accepted", 0)
                reward = tap_ack.get("reward", 0)
                patch = tap_res.get("patch", {})
                new_feathers = patch.get("feathers", feathers + reward)
                new_energy = patch.get("energy", max(0, energy - batch_count))

                log("TAP_OK", f"✨ Đã nhận +{reward} Feathers! (Tổng: {new_feathers:,}) | Pin còn: {new_energy:.1f}", Fore.GREEN)

            # 4. Giãn cách ngẫu nhiên 1.5 - 2.8s giữa các cú tap như người thật
            delay = round(random.uniform(1.5, 2.8), 2)
            time.sleep(delay)

            # 5. Làm mới init_data sau mỗi 60 phút
            if time.time() - last_refresh_init > 3600:
                log("REFRESH", "Làm mới init_data sau 60 phút hoạt động...", Fore.MAGENTA)
                get_fresh_init_data_sync()
                last_refresh_init = time.time()

            cycle += 1

        except Exception as e:
            log("ERR", f"Lỗi vòng lặp: {e}", Fore.RED)
            time.sleep(10)

if __name__ == "__main__":
    run_loop()
