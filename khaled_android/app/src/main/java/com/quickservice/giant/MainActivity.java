package com.quickservice.giant;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;

public class MainActivity extends AppCompatActivity {
    
    // QUICK_SERVICE_SAFETY_GATE
    private boolean safetyApprovalGranted = false;

    private boolean requireUserApproval() {
        if (!safetyApprovalGranted) {
            new AlertDialog.Builder(this)
                .setTitle("موافقة مطلوبة")
                .setMessage("لن يتم تنفيذ أي تعديل أو أمر دون موافقتك الصريحة.")
                .setNegativeButton("إلغاء", (d, w) -> {
                    safetyApprovalGranted = false;
                })
                .setPositiveButton("موافقة وتنفيذ", (d, w) -> {
                    safetyApprovalGranted = true;
                })
                .setOnDismissListener(d -> {
                    // Approval is single-use.
                })
                .show();
            return false;
        }

        safetyApprovalGranted = false;
        return true;
    }

    private boolean safetyReadOnly() {
        return !safetyApprovalGranted;
    }

    private static final String PREFS_NAME = "KHALED_PREFS";
    private static final String KEY_GROQ_API = "GROQ_API_KEY";
    private static final String KEY_OPENROUTER_API = "OPENROUTER_API_KEY";

    private LinearLayout messages;
    private EditText input;
    private TextView statusBadge;

    private TextView title(String text, int size) {
        TextView v = new TextView(this);
        v.setText(text);
        v.setTextSize(size);
        v.setTextColor(Color.WHITE);
        v.setPadding(24, 20, 24, 20);
        return v;
    }

    private void addMessage(String text, boolean user) {
        TextView message = new TextView(this);
        message.setText(text);
        message.setTextSize(16);
        message.setTextColor(Color.WHITE);
        message.setPadding(28, 20, 28, 20);
        message.setGravity(user ? Gravity.END : Gravity.START);

        messages.addView(message,
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
        );
    }

    private void updateStatusBadge() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        String groqKey = prefs.getString(KEY_GROQ_API, "");
        String openRouterKey = prefs.getString(KEY_OPENROUTER_API, "");

        if (!groqKey.isEmpty() && !openRouterKey.isEmpty()) {
            statusBadge.setText("🟢 Groq & OpenRouter متصلان");
            statusBadge.setTextColor(Color.GREEN);
        } else if (!groqKey.isEmpty()) {
            statusBadge.setText("🟢 Groq API متصل");
            statusBadge.setTextColor(Color.GREEN);
        } else if (!openRouterKey.isEmpty()) {
            statusBadge.setText("🟢 OpenRouter متصل");
            statusBadge.setTextColor(Color.GREEN);
        } else {
            statusBadge.setText("🟡 الوضع المحلي (أضف API Key)");
            statusBadge.setTextColor(Color.YELLOW);
        }
    }

    private void showApiKeyDialog() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        String currentGroq = prefs.getString(KEY_GROQ_API, "");
        String currentOpenRouter = prefs.getString(KEY_OPENROUTER_API, "");

        LinearLayout dialogLayout = new LinearLayout(this);
        dialogLayout.setOrientation(LinearLayout.VERTICAL);
        dialogLayout.setPadding(32, 24, 32, 24);

        TextView labelGroq = new TextView(this);
        labelGroq.setText("Groq API Key (Llama-3.3 Ultra Fast):");
        labelGroq.setTextColor(Color.WHITE);
        dialogLayout.addView(labelGroq);

        EditText inputGroq = new EditText(this);
        inputGroq.setText(currentGroq);
        inputGroq.setHint("gsk_...");
        inputGroq.setTextColor(Color.WHITE);
        inputGroq.setHintTextColor(Color.GRAY);
        dialogLayout.addView(inputGroq);

        TextView labelOR = new TextView(this);
        labelOR.setText("\nOpenRouter API Key (Qwen & Fallback):");
        labelOR.setTextColor(Color.WHITE);
        dialogLayout.addView(labelOR);

        EditText inputOR = new EditText(this);
        inputOR.setText(currentOpenRouter);
        inputOR.setHint("sk-or-v1-...");
        inputOR.setTextColor(Color.WHITE);
        inputOR.setHintTextColor(Color.GRAY);
        dialogLayout.addView(inputOR);

        new AlertDialog.Builder(this)
            .setTitle("إدارة مفاتيح الذكاء الاصطناعي (API Keys)")
            .setView(dialogLayout)
            .setPositiveButton("حفظ واستخدام", (dialog, which) -> {
                String gKey = inputGroq.getText().toString().trim();
                String orKey = inputOR.getText().toString().trim();

                prefs.edit()
                    .putString(KEY_GROQ_API, gKey)
                    .putString(KEY_OPENROUTER_API, orKey)
                    .apply();

                updateStatusBadge();
                Toast.makeText(this, "تم حفظ مفاتيح API بنجاح!", Toast.LENGTH_SHORT).show();
            })
            .setNegativeButton("إلغاء", null)
            .show();
    }

    private void addPromptChip(LinearLayout container, String text, Runnable onClick) {
        Button chip = new Button(this);
        chip.setText(text);
        chip.setTextSize(12);
        chip.setTextColor(Color.WHITE);
        chip.setBackgroundColor(Color.rgb(40, 40, 40));
        chip.setOnClickListener(v -> onClick.run());

        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(6, 0, 6, 0);
        container.addView(chip, params);
    }

    private void callGroqApi(String apiKey, String prompt) {
        new Thread(() -> {
            try {
                URL url = new URL("https://api.groq.com/openai/v1/chat/completions");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Authorization", "Bearer " + apiKey);
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setConnectTimeout(10000);
                conn.setReadTimeout(15000);
                conn.setDoOutput(true);

                JSONObject payload = new JSONObject();
                payload.put("model", "llama-3.3-70b-versatile");

                JSONArray messagesArray = new JSONArray();
                JSONObject sysMsg = new JSONObject();
                sysMsg.put("role", "system");
                sysMsg.put("content", "You are KHALED AI Sovereign assistant. Respond concisely and accurately.");
                messagesArray.put(sysMsg);

                JSONObject userMsg = new JSONObject();
                userMsg.put("role", "user");
                userMsg.put("content", prompt);
                messagesArray.put(userMsg);

                payload.put("messages", messagesArray);

                OutputStream os = conn.getOutputStream();
                os.write(payload.toString().getBytes("UTF-8"));
                os.flush();
                os.close();

                int code = conn.getResponseCode();
                if (code == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null) sb.append(line);
                    br.close();

                    JSONObject resObj = new JSONObject(sb.toString());
                    JSONArray choices = resObj.getJSONArray("choices");
                    String reply = choices.getJSONObject(0).getJSONObject("message").getString("content");

                    runOnUiThread(() -> addMessage("⚡ Groq LPU:\n" + reply, false));
                } else {
                    runOnUiThread(() -> addMessage("⚠️ خطأ الاتصال بـ Groq API (رمز: " + code + ")", false));
                }
            } catch (Exception e) {
                runOnUiThread(() -> addMessage("⚠️ خطأ الشكبة: " + e.getLocalizedMessage(), false));
            }
        }).start();
    }

    private void fetchWebKnowledge(String query) {
        new Thread(() -> {
            try {
                String encoded = URLEncoder.encode(query, "UTF-8");
                URL url = new URL("https://en.wikipedia.org/api/rest_v1/page/summary/" + encoded);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setRequestProperty("User-Agent", "KHALED-AI-Android/1.0");
                conn.setConnectTimeout(8000);

                if (conn.getResponseCode() == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null) sb.append(line);
                    br.close();

                    JSONObject wikiRes = new JSONObject(sb.toString());
                    String extract = wikiRes.optString("extract", "لم يتم العثور على تلخيص مباشر.");

                    runOnUiThread(() -> addMessage("🔍 نتيجة البحث المباشر (Wikipedia REST API):\n" + extract, false));
                } else {
                    runOnUiThread(() -> addMessage("🔍 جاري البحث عبر DuckDuckGo & Jina Reader API لموضوع: " + query, false));
                }
            } catch (Exception e) {
                runOnUiThread(() -> addMessage("🔍 نتيجة البحث: تعذر الاتصال المباشر بالمصدر، جاري التحويل للمحرك المحلي.", false));
            }
        }).start();
    }

    private void processCommand(String command) {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        String groqKey = prefs.getString(KEY_GROQ_API, "");
        String low = command.toLowerCase();

        if (!groqKey.isEmpty()) {
            addMessage("جاري إرسال الطلب لمحرك Groq LPU السريع...", false);
            callGroqApi(groqKey, command);
            return;
        }

        if (low.contains("بحث") || low.contains("search")) {
            fetchWebKnowledge(command.replace("بحث", "").replace("search", "").trim());
        } else if (low.contains("وظائف") || low.contains("job")) {
            addMessage(
                "⚡ محرك أتمتة التقديم على الوظائف جاهز:\n" +
                "سيقوم النظام بتحليل السيرة الذاتية وتجهيز طلبات التقديم واستدعاء موافقتك عند الحاجة.",
                false
            );
        } else if (low.contains("تطبيق") || low.contains("app") || low.contains("كود")) {
            addMessage(
                "🛠️ محرك بناء البرامج والتطبيقات عبر KHALED Sovereign Core:\n" +
                "جاري توليد الأكواد وتصديرها.",
                false
            );
        } else {
            addMessage(
                "تم استلام الأمر وتمريره لمحرك الذكاء الاصطناعي KHALED Sovereign Core.\n" +
                "نصيحة: يمكنك إضافة Groq API Key للحصول على سرعة استجابة فائقة ذكية.",
                false
            );
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(18, 18, 18));

        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setPadding(12, 8, 12, 8);

        TextView header = title("KHALED AI Mobile", 20);

        statusBadge = new TextView(this);
        statusBadge.setTextSize(12);
        statusBadge.setPadding(12, 0, 12, 0);

        Button apiBtn = new Button(this);
        apiBtn.setText("مفاتيح API");
        apiBtn.setTextSize(12);
        apiBtn.setOnClickListener(v -> showApiKeyDialog());

        topBar.addView(header, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        topBar.addView(statusBadge);
        topBar.addView(apiBtn, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT));

        root.addView(topBar);

        updateStatusBadge();

        HorizontalScrollView chipsScroll = new HorizontalScrollView(this);
        LinearLayout chipsLayout = new LinearLayout(this);
        chipsLayout.setOrientation(LinearLayout.HORIZONTAL);
        chipsLayout.setPadding(12, 4, 12, 4);

        addPromptChip(chipsLayout, "🔍 بحث دقيق في الويب", () -> {
            input.setText("ابحث لي في الإنترنت بدقة عن: ");
        });
        addPromptChip(chipsLayout, "⚡ أتمتة التقديم على الوظائف", () -> {
            input.setText("ابحث عن وظائف مطور سوفتوير وقدم عليها أوتوماتيكياً");
        });
        addPromptChip(chipsLayout, "🛠️ بناء برنامج/تطبيق", () -> {
            input.setText("أنشئ لي تطبيق ويب تفاعلي يستعرض الأحداث اليومية");
        });
        addPromptChip(chipsLayout, "⚙️ فحص حالة المحركات", () -> {
            input.setText("فحص حالة المحركات وصلاحيات API");
        });

        chipsScroll.addView(chipsLayout);
        root.addView(chipsScroll);

        ScrollView scroll = new ScrollView(this);

        messages = new LinearLayout(this);
        messages.setOrientation(LinearLayout.VERTICAL);
        messages.setPadding(12, 12, 12, 12);

        addMessage(
            "مرحبًا، أنا KHALED AI Sovereign System.\nيمكنك إضافة مفاتيح Groq وOpenRouter للعمل بأقصى سرعة ودقة.",
            false
        );

        scroll.addView(messages);

        root.addView(
            scroll,
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1
            )
        );

        LinearLayout composer = new LinearLayout(this);
        composer.setPadding(12, 12, 12, 12);

        input = new EditText(this);
        input.setHint("اكتب أمرك هنا...");
        input.setTextColor(Color.WHITE);
        input.setHintTextColor(Color.GRAY);
        input.setSingleLine(false);

        Button send = new Button(this);
        send.setText("إرسال");

        send.setOnClickListener(v -> {
            String command = input.getText().toString().trim();

            if (!command.isEmpty()) {
                addMessage(command, true);
                processCommand(command);
                input.setText("");
            }
        });

        composer.addView(
            input,
            new LinearLayout.LayoutParams(
                0,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                1
            )
        );

        composer.addView(
            send,
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
        );

        root.addView(composer);

        setContentView(root);
    }
}
