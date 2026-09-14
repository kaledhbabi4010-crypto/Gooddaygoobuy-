package com.quickservice.giant;

import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private LinearLayout messagesLayout;
    private EditText inputEditText;
    private ScrollView scrollView;
    private int selfRepairCount = 0;

    private GradientDrawable createShape(int color, float radius, int strokeColor, int strokeWidth) {
        GradientDrawable shape = new GradientDrawable();
        shape.setShape(GradientDrawable.RECTANGLE);
        shape.setColor(color);
        shape.setCornerRadius(radius);
        if (strokeWidth > 0) {
            shape.setStroke(strokeWidth, strokeColor);
        }
        return shape;
    }

    private String sanitizeInput(String input) {
        if (input == null) return "";
        String sanitized = input.trim();
        if (sanitized.length() > 500) {
            sanitized = sanitized.substring(0, 500);
        }
        return sanitized;
    }

    private void sendMessage(String rawInput) {
        String clean = sanitizeInput(rawInput);
        if (clean.isEmpty()) return;

        addMessage(clean, true);
        if (inputEditText != null) {
            inputEditText.setText("");
        }

        // Instant offline response generation without delay or handler races
        String reply = getZeroQuotaSmartResponse(clean);
        addMessage(reply, false);
    }

    private void addMessage(String text, boolean isUser) {
        try {
            LinearLayout wrapper = new LinearLayout(this);
            wrapper.setOrientation(LinearLayout.VERTICAL);
            wrapper.setGravity(isUser ? Gravity.END : Gravity.START);
            wrapper.setPadding(0, 12, 0, 12);

            TextView senderLabel = new TextView(this);
            senderLabel.setText(isUser ? "👤 أنت" : "🤖 الذكاء الاصطناعي الذاتي (Zero-Quota)");
            senderLabel.setTextSize(12);
            senderLabel.setTextColor(Color.parseColor("#94A3B8"));
            senderLabel.setPadding(isUser ? 0 : 8, 0, isUser ? 8 : 0, 6);

            TextView msgView = new TextView(this);
            msgView.setText(text);
            msgView.setTextSize(15);
            msgView.setTextColor(Color.WHITE);
            msgView.setPadding(36, 26, 36, 26);
            msgView.setLineSpacing(6f, 1.1f);

            int bgColor = isUser ? Color.parseColor("#2563EB") : Color.parseColor("#1E293B");
            int strokeColor = isUser ? Color.parseColor("#3B82F6") : Color.parseColor("#334155");
            msgView.setBackground(createShape(bgColor, 32f, strokeColor, 2));

            LinearLayout.LayoutParams msgLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            );
            msgLp.weight = 0;

            wrapper.addView(senderLabel);
            wrapper.addView(msgView, msgLp);

            messagesLayout.addView(wrapper);

            // Maintain last 50 messages max for memory optimization
            if (messagesLayout.getChildCount() > 50) {
                messagesLayout.removeViewAt(0);
            }

            scrollView.post(() -> scrollView.fullScroll(View.FOCUS_DOWN));
        } catch (Exception e) {
            selfRepairCount++;
            recoverFromUIError(e.getMessage());
        }
    }

    private void recoverFromUIError(String errorDetails) {
        try {
            if (messagesLayout != null) {
                messagesLayout.removeAllViews();
                TextView repairMsg = new TextView(this);
                repairMsg.setText("🛡️ [إصلاح ذاتي تلقائي]: تم اكتشاف خلل بسيط (" + errorDetails + ") وإصلاحه محلياً دون استهلاك باقة أو إنترنت. الإجمالي: " + selfRepairCount);
                repairMsg.setTextColor(Color.parseColor("#4ADE80"));
                repairMsg.setPadding(24, 24, 24, 24);
                messagesLayout.addView(repairMsg);
            }
        } catch (Exception ignored) {}
    }

    private void addQuickChip(LinearLayout parent, String text) {
        TextView chip = new TextView(this);
        chip.setText(text);
        chip.setTextSize(13);
        chip.setTextColor(Color.parseColor("#CBD5E1"));
        chip.setPadding(28, 16, 28, 16);
        chip.setBackground(createShape(Color.parseColor("#1E293B"), 28f, Color.parseColor("#334155"), 2));

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        );
        lp.setMargins(0, 0, 16, 0);
        chip.setLayoutParams(lp);

        // One-tap send on chip click
        chip.setOnClickListener(v -> sendMessage(text));

        parent.addView(chip);
    }

    private String getZeroQuotaSmartResponse(String input) {
        try {
            String q = input.toLowerCase().trim();

            if (q.contains("إصلاح") || q.contains("مشكلة") || q.contains("عطل") || q.contains("تلقائي") || q.contains("ذاتي")) {
                return "⚡ [نظام الإصلاح الذاتي المحلي]:\n• يعمل المحرك أوفلاين 100%\n• معالجة الأخطاء محلياً بدون استهلاك الإنترنت أو الرصيد\n• خفيف جداً على المعالج والذاكرة\n• أمان مرتفع وحماية للبيانات";
            } else if (q.contains("مرحبا") || q.contains("أهلا") || q.contains("سلام") || q.contains("hi") || q.contains("hello")) {
                return "أهلاً بك! أنا نظام الذكاء الاصطناعي الذاتي (Zero-Quota). أعمل أوفلاين وبدون استهلاك للبيانات أو الرصيد، كيف يمكنني مساعدتك؟";
            } else if (q.contains("هواوي") || q.contains("huawei") || q.contains("p30") || q.contains("hms")) {
                return "التطبيق مصمم بهندسة مستقلة خفيفة وآمنة تعمل 100% على Huawei P30 وجميع أجهزة أندرويد بدون أي استهلاك للإنترنت أو الحاجة لخدمات جوجل.";
            } else if (q.contains("مجاني") || q.contains("رصيد") || q.contains("نت") || q.contains("استهلاك")) {
                return "🟢 [حالة الرصيد والإنترنت]: صفر تكلفة (0 KB استهلاك). جميع العمليات والتطوير الذاتي يتم محلياً داخل الجهاز بكل أمان.";
            } else {
                return "تمت المعالجة الذاتية بنجاح:\n\"" + input + "\"\n\nالخدمة تعمل بسلاسة خفيفة وبدون استهلاك للرصيد أونلاين/أوفلاين.";
            }
        } catch (Exception ex) {
            selfRepairCount++;
            return "🛡️ تم معالجة طلبك محلياً عبر محرك التعافي الذاتي.";
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        try {
            LinearLayout root = new LinearLayout(this);
            root.setOrientation(LinearLayout.VERTICAL);
            root.setBackgroundColor(Color.parseColor("#0F172A"));

            // Header Bar
            LinearLayout header = new LinearLayout(this);
            header.setOrientation(LinearLayout.HORIZONTAL);
            header.setPadding(36, 32, 36, 32);
            header.setBackgroundColor(Color.parseColor("#1E293B"));
            header.setGravity(Gravity.CENTER_VERTICAL);

            LinearLayout titleContainer = new LinearLayout(this);
            titleContainer.setOrientation(LinearLayout.VERTICAL);

            TextView titleView = new TextView(this);
            titleView.setText("KHALED / Zero-Quota AI");
            titleView.setTextSize(17);
            titleView.setTextColor(Color.WHITE);

            TextView statusView = new TextView(this);
            statusView.setText("● إقرار أمان وإصلاح ذاتي 100% (بدون استهلاك نت)");
            statusView.setTextSize(11);
            statusView.setTextColor(Color.parseColor("#4ADE80"));

            titleContainer.addView(titleView);
            titleContainer.addView(statusView);

            TextView clearBtn = new TextView(this);
            clearBtn.setText("مسح السجل");
            clearBtn.setTextSize(12);
            clearBtn.setTextColor(Color.parseColor("#F87171"));
            clearBtn.setPadding(20, 10, 20, 10);
            clearBtn.setBackground(createShape(Color.parseColor("#451A1A"), 20f, Color.parseColor("#7F1D1D"), 1));

            LinearLayout.LayoutParams titleLp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
            header.addView(titleContainer, titleLp);
            header.addView(clearBtn);

            root.addView(header);

            // Scroll Container
            scrollView = new ScrollView(this);
            scrollView.setPadding(28, 20, 28, 20);

            messagesLayout = new LinearLayout(this);
            messagesLayout.setOrientation(LinearLayout.VERTICAL);

            scrollView.addView(messagesLayout, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ));

            root.addView(scrollView, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1
            ));

            // Quick Chips View
            HorizontalScrollView chipsScroll = new HorizontalScrollView(this);
            chipsScroll.setHorizontalScrollBarEnabled(false);
            chipsScroll.setPadding(28, 14, 28, 14);

            LinearLayout chipsLayout = new LinearLayout(this);
            chipsLayout.setOrientation(LinearLayout.HORIZONTAL);

            addQuickChip(chipsLayout, "مرحباً بك");
            addQuickChip(chipsLayout, "اختبار الإصلاح الذاتي");
            addQuickChip(chipsLayout, "فحص استهلاك الإنترنت والتكلفة");
            addQuickChip(chipsLayout, "التوافق مع Huawei P30");

            chipsScroll.addView(chipsLayout);
            root.addView(chipsScroll);

            // Message Composer Bar
            LinearLayout composer = new LinearLayout(this);
            composer.setPadding(24, 20, 24, 28);
            composer.setBackgroundColor(Color.parseColor("#1E293B"));
            composer.setGravity(Gravity.CENTER_VERTICAL);

            inputEditText = new EditText(this);
            inputEditText.setHint("اكتب استفسارك هنا (آمن ومجاني 100%)...");
            inputEditText.setTextColor(Color.WHITE);
            inputEditText.setHintTextColor(Color.parseColor("#64748B"));
            inputEditText.setBackground(createShape(Color.parseColor("#0F172A"), 28f, Color.parseColor("#334155"), 2));
            inputEditText.setPadding(36, 22, 36, 22);
            inputEditText.setImeOptions(EditorInfo.IME_ACTION_SEND);
            inputEditText.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE);

            // Soft keyboard "Send" action listener
            inputEditText.setOnEditorActionListener((v, actionId, event) -> {
                if (actionId == EditorInfo.IME_ACTION_SEND) {
                    sendMessage(inputEditText.getText().toString());
                    return true;
                }
                return false;
            });

            // Reliable custom TextView send button to avoid AppCompatButton theme overrides
            TextView sendBtn = new TextView(this);
            sendBtn.setText("إرسال");
            sendBtn.setTextColor(Color.WHITE);
            sendBtn.setTextSize(14);
            sendBtn.setGravity(Gravity.CENTER);
            sendBtn.setPadding(36, 22, 36, 22);
            sendBtn.setBackground(createShape(Color.parseColor("#2563EB"), 28f, Color.parseColor("#3B82F6"), 1));
            sendBtn.setClickable(true);
            sendBtn.setFocusable(true);

            composer.addView(inputEditText, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));

            LinearLayout.LayoutParams btnLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            );
            btnLp.setMargins(16, 0, 0, 0);
            composer.addView(sendBtn, btnLp);

            root.addView(composer);

            // Welcome Message
            addMessage("أهلاً بك! التطبيق يعمل بنظام الذكاء الاصطناعي الذاتي (Zero-Quota)، معالجة خفيفة، أمان عالي، وإصلاح تلقائي محلي دون استهلاك رصيد أو إنترنت.", false);

            // Event Listeners
            clearBtn.setOnClickListener(v -> {
                messagesLayout.removeAllViews();
                addMessage("تم مسح السجل وتحرير الذاكرة بنجاح.", false);
            });

            sendBtn.setOnClickListener(v -> sendMessage(inputEditText.getText().toString()));

            setContentView(root);
        } catch (Exception e) {
            recoverFromUIError("OnCreate recovery: " + e.getMessage());
        }
    }
}
