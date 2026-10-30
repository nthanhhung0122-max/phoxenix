#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
  BOT AUTO PLAY 24/7 SIÊU CẤP - PHOINEXES TAP (@PHOINEXES_TaP_BOT)
  Platform: Base44 App (https://phoinexes.base44.app/)
  Bot     : @PHOINEXES_TaP_BOT (ID: 8650334863)

  TÍNH NĂNG TỰ ĐỘNG HÓA TỐI ĐA (ALL-IN-ONE AUTOMATION):
    1. AUTO INDATA 100%: Tự động kết nối Telethon StringSession lấy
       init_data mới từ @PHOINEXES_TaP_BOT (không bao giờ hết hạn token).
    2. AUTO FREE SPIN WHEEL (VÒNG QUAY MAY MẮN):
       Tự động quay Vòng quay Lửa mỗi ngày, nhận từ +1.000 đến +5.000 Feathers.
    3. AUTO FEED & CARE (CHO ĂN MIỄN PHÍ - KHÔNG MUA TRÁNH LỖ):
       Tự động kiểm tra độ no (satiety). Chỉ cho ăn khi có sẵn đồ ăn miễn phí
       trong kho, tuyệt đối không mua bằng Lông Vũ tránh bẫy lỗ 60%.
    4. AUTO DRINK BOOSTERS (NƯỚC TĂNG LỰC):
       Khi cạn năng lượng, tự kiểm tra túi nước tăng lực (Inferno, Storm, Fortune).
       Nếu có -> Uống ngay lập tức để hồi 100% pin tức thì + buff x2 Feathers!
    5. AUTO UPGRADE CHIM PHƯỢNG HOÀNG (NÂNG CẤP TỐI ĐA):
       Dồn 100% Lông Vũ nâng cấp ngay khi đạt đủ Level và Feathers:
       - Sức mạnh (power)     : +1, +2, +3 Feathers mỗi cú tap
       - Pin tối đa (energy)  : 1000 -> 1100 -> 1200 -> 1500 pin
       - Tốc độ hồi (recovery): Hồi năng lượng siêu nhanh 24/7
       - Tiết kiệm (impulse)  : Giảm hao hụt năng lượng khi tap
    6. AUTO CLAIM EVOLUTION (NHẬN THƯỞNG TIẾN HÓA):
       Tự động nhận thưởng Feathers & GEP mỗi khi chim Phượng Hoàng lên cấp.
    7. AUTO TAPPER THÔNG MINH (ANTI-BAN SAFE):
       Gửi gói tap 20 - 30 cú, giãn cách 1.5s - 2.8s ngẫu nhiên như người thật.
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
CURRENT_DAY = ""
CURRENT_SERVER_TIME = 0

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
            log("ERR", "Phiên Telegram chưa được ủy quyền!", Fore.RED)
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
def call_phx_action(action_obj, sequence=1):
    global CURRENT_INIT_DATA, CURRENT_REVISION, CURRENT_DAY, CURRENT_SERVER_TIME
    if not CURRENT_INIT_DATA:
        get_fresh_init_data_sync()

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
        "Origin": "https://phoinexes.base44.app",
        "Referer": "https://phoinexes.base44.app/"
    }

    payload = {
        "action": action_obj,
        "requestId": str(uuid.uuid4()),
        "sequenceNumber": sequence,
        "initData": CURRENT_INIT_DATA,
        "ref": None,
        "trafficHints": {},
        "compactTaps": True,
        "knownRevision": CURRENT_REVISION,
        "snapshotDay": CURRENT_DAY or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "snapshotTime": CURRENT_SERVER_TIME or int(time.time() * 1000)
    }

    try:
        r = requests.post(API_BASE_URL, headers=headers, json=payload, timeout=20)
        if r.status_code == 401 or "expired" in r.text.lower() or "unauthorized" in r.text.lower():
            log("AUTH_EXPIRED", "Token hết hạn, đang tự động cấp mới init_data...", Fore.YELLOW)
            get_fresh_init_data_sync()
            payload["initData"] = CURRENT_INIT_DATA
            r = requests.post(API_BASE_URL, headers=headers, json=payload, timeout=20)

        res = r.json()
        if res.get("revision"):
            CURRENT_REVISION = res.get("revision")
        if res.get("serverTime"):
            CURRENT_SERVER_TIME = res.get("serverTime")
        return res
    except Exception as e:
        log("API_ERR", f"Lỗi gọi API: {e}", Fore.RED)
        return {"error": str(e)}

# -----------------------------------------------------------------
#  1. ĐỒNG BỘ GAME (SYNC)
# -----------------------------------------------------------------
def sync_game():
    global CURRENT_REVISION, CURRENT_DAY, CURRENT_SERVER_TIME
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://phoinexes.base44.app",
        "Referer": "https://phoinexes.base44.app/"
    }
    try:
        r = requests.post(API_BASE_URL, headers=headers, json={"action": {"type": "sync"}, "initData": CURRENT_INIT_DATA}, timeout=20)
        res = r.json()
        if res.get("revision"):
            CURRENT_REVISION = res.get("revision")
        if res.get("serverTime"):
            CURRENT_SERVER_TIME = res.get("serverTime")
        if res.get("state", {}).get("day"):
            CURRENT_DAY = res.get("state", {}).get("day")
        return res
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------
#  2. TỰ ĐỘNG QUAY VÒNG QUAY MAY MẮN (FREE SPIN WHEEL)
# -----------------------------------------------------------------
def auto_spin_wheel(state):
    wheel_day = state.get("wheelDay", "")
    day = state.get("day", CURRENT_DAY)

    if wheel_day != day:
        log("WHEEL", "Phát hiện Vòng quay May mắn hàng ngày chưa quay! Đang kích hoạt...", Fore.MAGENTA)
        res = call_phx_action({"type": "spinWheel"})
        if res.get("error"):
            log("WHEEL_WARN", f"Chưa quay được: {res.get('error')}", Fore.YELLOW)
        else:
            w_res = res.get("state", {}).get("wheelResult", {})
            kind = w_res.get("kind", "")
            amount = w_res.get("amount", 0)
            log("WHEEL_OK", f"🎉 VÒNG QUAY TRÚNG THƯỞNG: +{amount:,} {kind.upper()}!", Fore.GREEN)

# -----------------------------------------------------------------
#  3. TỰ ĐỘNG CHO CHIM ĂN (FEED FOOD - CHỈ ĂN MIỄN PHÍ)
# -----------------------------------------------------------------
def auto_feed_food(state):
    food_count = state.get("food", 0)
    satiety = state.get("satiety", 100)

    # Nếu chim đói (< 90%) và có thức ăn miễn phí trong kho
    if food_count > 0 and satiety < 90:
        log("FEED", f"Chim hơi đói (Độ no: {satiety:.1f}%). Đang cho ăn hạt ngũ cốc miễn phí...", Fore.CYAN)
        res = call_phx_action({"type": "feed", "food": "grain"})
        if not res.get("error"):
            new_sat = res.get("patch", {}).get("satiety", 100)
            log("FEED_OK", f"🍖 Đã cho ăn no nê! Độ no mới: {new_sat:.1f}%", Fore.GREEN)

# -----------------------------------------------------------------
#  4. TỰ ĐỘNG UỐNG NƯỚC TĂNG LỰC (DRINK BOOSTERS)
# -----------------------------------------------------------------
def auto_drink_booster(state):
    energy = state.get("energy", 0)
    active_drink = state.get("activeDrink")
    now_ms = int(time.time() * 1000)

    # Đang có hiệu ứng nước tăng lực hoạt động
    if active_drink and active_drink.get("until", 0) > now_ms:
        return True

    # Chỉ uống khi pin cạn (< 50)
    if energy < 50:
        potions = state.get("energyPotions", {})
        available = [d_id for d_id, count in potions.items() if count > 0]
        if available:
            drink_to_use = available[0]
            log("DRINK", f"Cạn pin! Đang uống bình nước tăng lực [{drink_to_use}] để hồi 100% pin tức thì...", Fore.LIGHTMAGENTA_EX)
            res = call_phx_action({"type": "drink", "drink": drink_to_use})
            if not res.get("error"):
                log("DRINK_OK", f"⚡ ĐÃ HỒI ĐẦY 100% NĂNG LƯỢNG & NHẬN BUFF X2 LÔNG VŨ!", Fore.GREEN)
                return True
    return False

# -----------------------------------------------------------------
#  5. TỰ ĐỘNG NÂNG CẤP CHIM PHƯỢNG HOÀNG (AUTO UPGRADES)
# -----------------------------------------------------------------
def auto_upgrade_phoenix(state):
    upgrades = state.get("upgrades", {})
    upgrade_reqs = state.get("upgradeRequirements", {})
    current_level = state.get("currentLevel", 1)
    feathers = state.get("feathers", 0)

    # Ưu tiên: power (tăng tap) -> energy (tăng pin) -> recovery (hồi pin) -> impulse (tiết kiệm)
    priority_keys = ["power", "energy", "recovery", "impulse"]

    for key in priority_keys:
        lvl = upgrades.get(key, 0)
        if lvl >= 10:
            continue

        req_table = upgrade_reqs.get(key, []) if isinstance(upgrade_reqs, dict) else []
        req_player_lvl = req_table[lvl] if (isinstance(req_table, list) and lvl < len(req_table)) else 15

        # Đủ cấp độ mở khóa
        if current_level >= req_player_lvl:
            res = call_phx_action({"type": "upgrade", "key": key})
            if not res.get("error"):
                new_lvl = res.get("patch", {}).get("upgrades", {}).get(key, lvl + 1)
                log("UPGRADE_OK", f"⭐ NÂNG CẤP THÀNH CÔNG: [{key.upper()}] LÊN CẤP {new_lvl}!", Fore.GREEN)
                return True
            else:
                err = str(res.get("error", ""))
                if "недостаточно" in err.lower() or "not enough" in err.lower():
                    # Không đủ Feathers thì dừng đợi cày thêm
                    break
    return False

# -----------------------------------------------------------------
#  6. TỰ ĐỘNG NHẬN THƯỞNG TIẾN HÓA (EVOLUTION REWARDS)
# -----------------------------------------------------------------
def auto_claim_evolution_rewards(state):
    current_level = state.get("currentLevel", 1)
    evolution_claims = state.get("evolutionRewardClaims", [])

    if isinstance(evolution_claims, dict):
        claimed_set = set(str(k) for k in evolution_claims.keys())
    elif isinstance(evolution_claims, list):
        claimed_set = set(str(x) for x in evolution_claims)
    else:
        claimed_set = set()

    for lvl in range(1, current_level + 1):
        if str(lvl) not in claimed_set and lvl not in claimed_set:
            res = call_phx_action({"type": "claimEvolutionReward", "level": lvl})
            if not res.get("error"):
                log("EVO_OK", f"🏆 Nhận thưởng tiến hóa Cấp {lvl} thành công!", Fore.GREEN)
                claimed_set.add(str(lvl))

# -----------------------------------------------------------------
#  7. GỬI GÓI TAP (TAP BATCH)
# -----------------------------------------------------------------
def auto_tap_batch(count=25, sequence=1):
    payload = {
        "type": "tap",
        "count": count,
        "source": "manual"
    }
    return call_phx_action(payload, sequence=sequence)

# -----------------------------------------------------------------
#  VÒNG LẶP CHÍNH 24/7 SIÊU CẤP
# -----------------------------------------------------------------
def run_loop():
    print(Fore.LIGHTRED_EX + """
====================================================================
  BOT AUTO PHOINEXES TAP 24/7 (TOÀN DIỆN: TAP, ĂN, NÂNG CẤP, NƯỚC TĂNG LỰC)
====================================================================
|  - AUTO INDATA 100%: Tự lấy token mới qua Telethon không lo hết hạn|
|  - AUTO SPIN WHEEL : Tự quay Vòng quay may mắn hàng ngày (+Feathers) |
|  - AUTO FEED FOOD  : Tự cho ăn khi đói (<90%) giữ thể lực tối đa  |
|  - AUTO DRINK BOOST: Tự uống nước tăng lực hồi đầy pin + buff x2   |
|  - AUTO UPGRADES   : Tự nâng cấp Power, Energy, Recovery, Impulse |
|  - AUTO CLAIM REWARD: Tự nhận quà tiến hóa cấp độ Phượng Hoàng     |
|  - AUTO TAPPER     : Gửi đợt tap 20-30 taps, giãn cách như người thật |
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
            max_energy = state.get("energyRules", {}).get("cap", 1000)
            feathers = state.get("feathers", 0)
            level = state.get("currentLevel", 1)
            cur_taps = state.get("currentTaps", 0)
            req_taps = state.get("requiredTaps", 2000)
            user_name = state.get("name", CURRENT_USER_NAME)
            upgrades = state.get("upgrades", {})

            log("STATUS", f"🦅 [{user_name}] Lv.{level} (Taps: {cur_taps}/{req_taps}) | Lông Vũ: {feathers:,} | Pin: {energy:.1f}/{max_energy} | Upgrades: {upgrades}", Fore.LIGHTYELLOW_EX)

            # 2. Tự động kiểm tra quay Vòng quay may mắn
            auto_spin_wheel(state)

            # 3. Tự động nhận thưởng tiến hóa nếu có
            auto_claim_evolution_rewards(state)

            # 4. Tự động nâng cấp Phượng hoàng (Power, Energy, Recovery, Impulse)
            auto_upgrade_phoenix(state)

            # 5. Tự động cho ăn nếu đói (chỉ dùng đồ miễn phí)
            auto_feed_food(state)

            # 6. Kiểm tra năng lượng để tap
            if energy < 25:
                # Thử kích hoạt nước tăng lực trước
                drank = auto_drink_booster(state)
                if not drank:
                    # Không có nước tăng lực -> Nghỉ ngơi 90 giây để hồi pin
                    log("REST", f"⚡ Pin cạn ({energy:.1f}). Chim Phượng Hoàng đang nghỉ ngơi để hồi pin (90s)...", Fore.CYAN)
                    time.sleep(90)
                    continue

            # 7. Tiến hành tap từng đợt 20 - 30 taps
            batch_count = random.randint(20, 30)
            log("TAP", f"Đang gửi {batch_count} cú tap (Seq: #{seq})...", Fore.YELLOW)

            tap_res = auto_tap_batch(count=batch_count, sequence=seq)
            seq += 1

            if tap_res.get("error"):
                log("TAP_WARN", f"Lỗi tap: {tap_res.get('error')}", Fore.YELLOW)
                time.sleep(5)
            else:
                tap_ack = tap_res.get("tapAck", {})
                reward = tap_ack.get("reward", 0)
                patch = tap_res.get("patch", {})
                new_feathers = patch.get("feathers", feathers + reward)
                new_energy = patch.get("energy", max(0, energy - batch_count))

                log("TAP_OK", f"✨ Nhận +{reward} Feathers! (Tổng: {new_feathers:,}) | Pin còn: {new_energy:.1f}", Fore.GREEN)

            # 8. Giãn cách ngẫu nhiên 1.5s - 2.8s như người thật
            delay = round(random.uniform(1.5, 2.8), 2)
            time.sleep(delay)

            # 9. Làm mới init_data sau mỗi 60 phút
            if time.time() - last_refresh_init > 3600:
                log("REFRESH", "Làm mới init_data Telegram sau 60 phút hoạt động...", Fore.MAGENTA)
                get_fresh_init_data_sync()
                last_refresh_init = time.time()

            cycle += 1

        except Exception as e:
            log("ERR", f"Lỗi vòng lặp: {e}", Fore.RED)
            time.sleep(10)

if __name__ == "__main__":
    run_loop()
