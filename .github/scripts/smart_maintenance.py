import os
import requests
import base64
from groq import Groq

def main():
    groq_key = os.environ.get('GROQ_API_KEY', '').strip()
    token = os.environ.get('GITHUB_TOKEN', '').strip()
    repo = os.environ.get('GITHUB_REPOSITORY', '').strip()
    branch = os.environ.get('GITHUB_REF_NAME', 'main').strip()
    
    if not groq_key:
        return

    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    client = Groq(api_key=groq_key)
    
    # 1. جلب قائمة الملفات في المجلد الرئيسي للمستودع
    url = f"https://api.github.com/repos/{repo}/contents/?ref={branch}"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return
        
    items = res.json()
    # نستهدف فقط الملفات (وليس المجلدات) وذات الامتدادات البرمجية أو النصية
    target_files = [
        item['name'] for item in items 
        if item['type'] == 'file' and item['name'].endswith(('.py', '.js', '.java', '.kt', '.gradle', '.md', '.json', '.yml', '.yaml'))
    ]

    fixed_count = 0
    log_entries = []

    # 2. فحص وإصلاح كل ملف مستهدف
    for file_name in target_files:
        file_url = f"https://api.github.com/repos/{repo}/contents/{file_name}?ref={branch}"
        file_res = requests.get(file_url, headers=headers)
        if file_res.status_code != 200:
            continue
            
        data = file_res.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        sha = data["sha"]

        # 3. الأمر الصارم لـ Groq لإصلاح الملفات التالفة
        prompt = f"""أنت خبير في إصلاح الأكواد والملفات التالفة.
الملف التالي قد يحتوي على أخطاء في الصياغة (Syntax Errors)، أقواس مفقودة، أو أخطاء منطقية.

مهمتك:
1. اكتشف الخطأ وأصلحه فوراً.
2. أعد كتابة الملف كاملاً بشكل صحيح 100%.
3. لا تكتب أي شروحات، لا تكتب "إليك الكود المصحح"، فقط ابدأ مباشرة بمحتوى الملف.

اسم الملف: {file_name}
المحتوى الحالي:
{content}
"""
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4096
            )
            new_content = response.choices[0].message.content.strip()
        except Exception:
            continue

        # تنظيف الرد من علامات Markdown الزائدة
        if new_content.startswith("```"):
            lines = new_content.split("\n")
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            new_content = "\n".join(lines).strip()

        # 4. الحفظ إذا تم الإصلاح
        if new_content != content and len(new_content) > 50: # تأكد من أنه ليس رداً فارغاً
            encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
            put_res = requests.put(file_url, headers=headers, json={
                "message": f"🤖 إصلاح تلقائي لـ {file_name} [skip ci]",
                "content": encoded,
                "sha": sha,
                "branch": branch
            })
            
            if put_res.status_code in [200, 201]:
                fixed_count += 1
                log_entries.append(f"- ✅ تم إصلاح: `{file_name}`")

    # 5. كتابة سجل الإصلاحات لكي تعرف ما حدث
    if fixed_count > 0:
        log_content = f"""# 📋 سجل الإصلاحات التلقائية

تم فحص الملفات وإصلاح الأخطاء التالفة تلقائياً.

## الملفات التي تم إصلاحها:
{chr(10).join(log_entries)}

---
*تم التوليد بواسطة نظام الماسح والمصلح الذكي*
"""
        log_url = f"https://api.github.com/repos/{repo}/contents/FIX_LOG.md"
        
        # التحقق مما إذا كان السجل موجوداً مسبقاً
        check_log = requests.get(log_url, headers=headers)
        log_sha = check_log.json().get("sha") if check_log.status_code == 200 else None
        
        log_data = {
            "message": "📋 تحديث سجل الإصلاحات [skip ci]",
            "content": base64.b64encode(log_content.encode("utf-8")).decode("utf-8"),
            "branch": branch
        }
        if log_sha:
            log_data["sha"] = log_sha
            
        requests.put(log_url, headers=headers, json=log_data)

if __name__ == "__main__":
    main()
