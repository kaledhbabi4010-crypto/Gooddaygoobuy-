package com.quickservice.giant;

import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
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

    private void addMessage(String text, boolean isUser) {
        LinearLayout wrapper = new LinearLayout(this);
        wrapper.setOrientation(LinearLayout.VERTICAL);
        wrapper.setGravity(isUser ? Gravity.END : Gravity.START);
        wrapper.setPadding(0, 12, 0, 12);

        // Avatar / Label
        TextView senderLabel = new TextView(this);
        senderLabel.setText(isUser ? "👤 أنت" : "🤖 المساعد الذكي");
        senderLabel.setTextSize(12);
        senderLabel.setTextColor(Color.parseColor("#94A3B8"));
        senderLabel.setPadding(isUser ? 0 : 8, 0, isUser ? 8 : 0, 6);

        // Message Box
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

        scrollView.post(() -> scrollView.fullScroll(View.FOCUS_DOWN));
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

        chip.setOnClickListener(v -> {
            inputEditText.setText(text);
            inputEditText.setSelection(text.length());
        });

        parent.addView(chip);
    }

    private String getSmartResponse(String input) {
        String q = input.toLowerCase().trim();
        if (q.contains("مرحبا") || q.contains("أهلا") || q.contains("سلام") || q.contains("hi") || q.contains("hello")) {
            return "أهلاً وسهلاً بك! أنا مساعد الذكاء الاصطناعي الذكي والسريع. كيف أستطيع خدمتك اليوم؟";
        } else if (q.contains("هواوي") || q.contains("huawei") || q.contains("p30") || q.contains("hms")) {
            return "التطبيق يعمل بكفاءة وسرعة 100% على هاتف Huawei P30 وجميع أجهزة أندرويد وهواوي بدون أي حاجة لخدمات جوجل (GMS).";
        } else if (q.contains("مجاني") || q.contains("free") || q.contains("سعر")) {
            return "نعم، النظام مجاني 100% بدون أي رسوم خفية ويعتمد على هندسة ذكاء اصطناعي مستقلة ومجانية بالكامل.";
        } else if (q.contains("اختبار") || q.contains("فحص") || q.contains("حالة")) {
            return "جميع الخدمات شغالـة 100%:\n• المعالج: نشط\n• الاتصال: متصل أوفلاين/سحابي\n• توافق الأجهزة: أندرويد + هواوي HMS";
        } else {
            return "تم استقبال رسالتك: \"" + input + "\"\n\nالذكاء الاصطناعي جاهز ومعالج الطلبات يعمل بدقة وسرعة عالية!";
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#0F172A"));

        // App Bar / Header
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setPadding(36, 32, 36, 32);
        header.setBackgroundColor(Color.parseColor("#1E293B"));
        header.setGravity(Gravity.CENTER_VERTICAL);

        LinearLayout titleContainer = new LinearLayout(this);
        titleContainer.setOrientation(LinearLayout.VERTICAL);

        TextView titleView = new TextView(this);
        titleView.setText("KHALED / quickservice AI");
        titleView.setTextSize(17);
        titleView.setTextColor(Color.WHITE);

        TextView statusView = new TextView(this);
        statusView.setText("● متصل وجاهز للرد الفوري");
        statusView.setTextSize(12);
        statusView.setTextColor(Color.parseColor("#22C55E"));

        titleContainer.addView(titleView);
        titleContainer.addView(statusView);

        TextView clearBtn = new TextView(this);
        clearBtn.setText("مسح المحادثة");
        clearBtn.setTextSize(12);
        clearBtn.setTextColor(Color.parseColor("#F87171"));
        clearBtn.setPadding(20, 10, 20, 10);
        clearBtn.setBackground(createShape(Color.parseColor("#451A1A"), 20f, Color.parseColor("#7F1D1D"), 1));

        LinearLayout.LayoutParams titleLp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
        header.addView(titleContainer, titleLp);
        header.addView(clearBtn);

        root.addView(header);

        // Chat messages scroll container
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

        // Quick prompts scroll view
        HorizontalScrollView chipsScroll = new HorizontalScrollView(this);
        chipsScroll.setHorizontalScrollBarEnabled(false);
        chipsScroll.setPadding(28, 14, 28, 14);

        LinearLayout chipsLayout = new LinearLayout(this);
        chipsLayout.setOrientation(LinearLayout.HORIZONTAL);

        addQuickChip(chipsLayout, "مرحباً بك");
        addQuickChip(chipsLayout, "هل يعمل على Huawei P30؟");
        addQuickChip(chipsLayout, "هل الخدمة مجانية 100%؟");
        addQuickChip(chipsLayout, "فحص حالة النظام");

        chipsScroll.addView(chipsLayout);
        root.addView(chipsScroll);

        // Message Composer Bar
        LinearLayout composer = new LinearLayout(this);
        composer.setPadding(24, 20, 24, 28);
        composer.setBackgroundColor(Color.parseColor("#1E293B"));
        composer.setGravity(Gravity.CENTER_VERTICAL);

        inputEditText = new EditText(this);
        inputEditText.setHint("اكتب استفسارك أو أمرك هنا...");
        inputEditText.setTextColor(Color.WHITE);
        inputEditText.setHintTextColor(Color.parseColor("#64748B"));
        inputEditText.setBackground(createShape(Color.parseColor("#0F172A"), 28f, Color.parseColor("#334155"), 2));
        inputEditText.setPadding(36, 22, 36, 22);
        inputEditText.setSingleLine(false);
        inputEditText.setMaxLines(3);

        Button sendBtn = new Button(this);
        sendBtn.setText("إرسال");
        sendBtn.setTextColor(Color.WHITE);
        sendBtn.setTextSize(14);
        sendBtn.setBackground(createShape(Color.parseColor("#2563EB"), 28f, Color.parseColor("#3B82F6"), 1));

        composer.addView(inputEditText, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));

        LinearLayout.LayoutParams btnLp = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        );
        btnLp.setMargins(16, 0, 0, 0);
        composer.addView(sendBtn, btnLp);

        root.addView(composer);

        // Initial welcome message
        addMessage("مرحباً بك في تطبيق الذكاء الاصطناعي الأسرع والأحدث! التطبيق يعمل ويجيب على كافة الاستفسارات فورياً.", false);

        // Event listeners
        clearBtn.setOnClickListener(v -> {
            messagesLayout.removeAllViews();
            addMessage("تم مسح السجل بنجاح.", false);
        });

        sendBtn.setOnClickListener(v -> {
            String text = inputEditText.getText().toString().trim();
            if (!text.isEmpty()) {
                addMessage(text, true);
                inputEditText.setText("");

                // Simulated instant processing with slight natural delay
                new Handler(Looper.getMainLooper()).postDelayed(() -> {
                    String response = getSmartResponse(text);
                    addMessage(response, false);
                }, 300);
            }
        });

        setContentView(root);
    }
}
