name: Auto Phoinexes Tap 24/7

on:
  schedule:
    # Chạy lại mỗi 5 tiếng để workflow duy trì liên tục không bị gián đoạn
    - cron: '0 */5 * * *'
  workflow_dispatch:

concurrency:
  group: phoinexes-run
  cancel-in-progress: true

jobs:
  run-bot:
    runs-on: ubuntu-latest
    timeout-minutes: 350

    steps:
      - name: Checkout mã nguồn
        uses: actions/checkout@v4

      - name: Cài đặt Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Cài đặt thư viện phụ thuộc
        run: |
          pip install --upgrade pip
          pip install telethon requests colorama

      - name: Chạy Bot Auto Phoinexes Tap
        env:
          TELEGRAM_STRING_SESSION: ${{ secrets.TELEGRAM_STRING_SESSION || secrets.TELEGRAM_SESSION_B64_ACC1 || secrets.TELEGRAM_SESSION_B64 }}
          MAX_RUNTIME_SECONDS: '18000'
        run: |
          python auto_phoinexes.py
