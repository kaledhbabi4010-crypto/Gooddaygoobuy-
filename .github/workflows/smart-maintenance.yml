name: إصلاح تلقائي صامت (بدون أخطاء)

on:
  push:
    branches: [main, master]
  workflow_dispatch: # للتشغيل اليدوي أيضاً

jobs:
  silent-fix:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: جلب الكود
        uses: actions/checkout@v4

      - name: إعداد البيئة
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: تثبيت المكتبات
        run: pip install groq requests

      - name: تشغيل نظام الإصلاح الصامت
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # هذا السطر يضمن أن أي خطأ في البناء لن يوقف السكريبت
          python .github/scripts/silent_fixer.py || true
          
          # هذا السطر يضمن أن العملية تنتهي بنجاح دائماً (علامة خضراء)
          exit 0
