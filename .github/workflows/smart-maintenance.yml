import os
import sys
import requests
import base64
import re
import time
from groq import Groq

print("=" * 70)
print("🤖 نظام الصيانة الشاملة الذكي")
print("=" * 70)

# قراءة المتغيرات
groq_key = os.environ.get('GROQ_API_KEY')
token = os.environ.get('GITHUB_TOKEN')
repo = os.environ.get('GITHUB_REPOSITORY')
branch = os.environ.get('GITHUB_REF_NAME', 'main')
file_path = os.environ.get('FILE_PATH', '')
task_type = os.environ.get('TASK_TYPE', '')
custom_command = os.environ.get('CUSTOM_COMMAND', '')
verify_after = os.environ.get('VERIFY_AFTER', '')

if not groq_key:
    print("❌ مفتاح GROQ_API_KEY غير موجود في Secrets")
    sys.exit(1)

if not file_path:
    print("❌ لم يتم تحديد الملف")
    sys.exit(1)

print(f"\n📁 الملف المستهدف: {file_path}")
print(f"🎯 نوع المهمة: {task_type}")
if custom_command:
    print(f"💬 الأمر المخصص: {custom_command}")
print(f"✅ التحقق بعد التنفيذ: {verify_after}")

# 1. قراءة الملف الأصلي
print(f"\n📖 جاري قراءة الملف...")
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
res = requests.get(url, headers=headers)

if res.status_code != 200:
    print(f"❌ لم أجد الملف: {file_path}")
    print(f"تأكد من كتابة المسار بشكل صحيح")
    sys.exit(1)

data = res.json()
original_content = base64.b64decode(data["content"]).decode("utf-8")
original_sha = data["sha"]
print(f"✅ تم القراءة ({len(original_content)} حرف)")

# 2. بناء الأمر الكامل لـ Groq
print(f"\n🧠 جاري تحليل المهمة...")

# دمج نوع المهمة مع الأمر المخصص
if custom_command.strip():
    full_instruction = f"{task_type}\n\nأمر إضافي: {custom_command}"
else:
    full_instruction = task_type

prompt = f"""أنت مساعد ذكي لصيانة الملفات والبرامج.

المهمة المطلوبة:
{full_instruction}

الملف الحالي:
---
{original_content}
---

التعليمات الصارمة:
1. نفّذ المهمة المطلوبة بدقة
2. أعد الملف كاملاً بعد التعديل فقط
3. لا تضف أي شروحات أو كلام خارج الملف
4. لا تضع علامات ``` في البداية أو النهاية
5. حافظ على التنسيق الأصلي للملف ما لم يُطلب تغييره
6. إذا كان الكود، تأكد من صحته وعدم وجود أخطاء syntax"""

# 3. استدعاء Groq
print(f"🤖 جاري الاتصال بـ Groq...")
client = Groq(api_key=groq_key)

try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=4096
    )
    new_content = response.choices[0].message.content.strip()
    print(f"✅ تم استلام الرد ({len(new_content)} حرف)")
except Exception as e:
    print(f"❌ خطأ في Groq: {e}")
    sys.exit(1)

# تنظيف الرد من علامات الكود إن وجدت
if new_content.startswith("```"):
    lines = new_content.split("\n")
    if lines[-1].strip() == "```":
        lines = lines[1:-1]
    else:
        lines = lines[1:]
    new_content = "\n".join(lines).strip()

# 4. التحقق من أن التغييرات مختلفة
if new_content == original_content:
    print("\n⚠️ لم يقم Groq بأي تغييرات (ربما الملف سليم بالفعل)")
    sys.exit(0)

print(f"\n📊 ملخص التغييرات:")
print(f"   - الحجم الأصلي: {len(original_content)} حرف")
print(f"   - الحجم الجديد: {len(new_content)} حرف")
print(f"   - الفرق: {len(new_content) - len(original_content):+d} حرف")

# 5. حفظ الملف المصحح
print(f"\n💾 جاري حفظ التعديلات...")
update_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

put_res = requests.put(update_url, headers=headers, json={
    "message": f"🤖 صيانة ذكية: {task_type[:50]} [skip ci]",
    "content": encoded,
    "sha": original_sha,
    "branch": branch
})

if put_res.status_code not in [200, 201]:
    print(f"❌ فشل الحفظ: {put_res.status_code}")
    print(put_res.text)
    sys.exit(1)

print(f"✅ تم حفظ الملف بنجاح")

# 6. التحقق من التنفيذ (Verification)
if "نعم" in verify_after:
    print(f"\n🔍 جاري التحقق من تنفيذ التعديلات...")
    time.sleep(2)  # انتظار لتطبيق التغييرات على GitHub
    
    verify_url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
    verify_res = requests.get(verify_url, headers=headers)
    
    if verify_res.status_code == 200:
        verified_data = verify_res.json()
        verified_content = base64.b64decode(verified_data["content"]).decode("utf-8")
        
        if verified_content == new_content:
            print(f"✅ تم التحقق: التعديلات طُبقت بنجاح 100%")
        elif verified_content == original_content:
            print(f"⚠️ تحذير: الملف لم يتغير! قد تكون هناك مشكلة")
        else:
            print(f"⚠️ الملف يحتوي على محتوى مختلف عما هو متوقع")
            print(f"   الحجم الحالي: {len(verified_content)} حرف")
        
        # حفظ تقرير التحقق
        report = f"""# 📋 تقرير الصيانة الذكي

**التاريخ:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**الملف:** `{file_path}`
**الفرع:** `{branch}`

## 🎯 المهمة المنفذة
{full_instruction}

## 📊 الإحصائيات
- الحجم الأصلي: {len(original_content)} حرف
- الحجم الجديد: {len(new_content)} حرف
- الفرق: {len(new_content) - len(original_content):+d} حرف

## ✅ حالة التحقق
{"تم التحقق بنجاح - التعديلات طُبقت 100%" if verified_content == new_content else "لم يتم التحقق بالكامل"}

## 📝 ملاحظات
- تم التنفيذ بواسطة Groq AI
- النموذج المستخدم: llama-3.3-70b-versatile
- للمراجعة اليدوية، قارن بين النسخة الحالية والسابقة في صفحة Commits

---
*تم التوليد تلقائياً بواسطة نظام الصيانة الذكي*
"""
        
        report_path = "MAINTENANCE_REPORT.md"
        report_url = f"https://api.github.com/repos/{repo}/contents/{report_path}"
        
        check_report = requests.get(report_url, headers=headers)
        report_sha = check_report.json().get("sha") if check_report.status_code == 200 else None
        
        encoded_report = base64.b64encode(report.encode("utf-8")).decode("utf-8")
        report_data = {
            "message": "📋 تقرير الصيانة الذكي [skip ci]",
            "content": encoded_report,
            "branch": branch
        }
        if report_sha:
            report_data["sha"] = report_sha
        
        requests.put(report_url, headers=headers, json=report_data)
        print(f"📄 تم حفظ التقرير في: {report_path}")
    else:
        print(f"⚠️ تعذر التحقق من التعديلات")

print("\n" + "=" * 70)
print("🎉 انتهت عملية الصيانة بنجاح!")
print("=" * 70)
