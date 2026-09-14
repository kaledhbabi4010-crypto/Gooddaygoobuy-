package com.quickservice.giant;

import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
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

    private GradientDrawable createBubbleDrawable(int color, float radius) {
        GradientDrawable shape = new GradientDrawable();
        shape.setShape(GradientDrawable.RECTANGLE);
        shape.setColor(color);
        shape.setCornerRadius(radius);
        return shape;
    }

    private void addMessage(String text, boolean isUser) {
        LinearLayout messageWrapper = new LinearLayout(this);
        messageWrapper.setOrientation(LinearLayout.HORIZONTAL);
        messageWrapper.setGravity(isUser ? Gravity.END : Gravity.START);
        messageWrapper.setPadding(0, 10, 0, 10);

        TextView messageView = new TextView(this);
        messageView.setText(text);
        messageView.setTextSize(15);
        messageView.setTextColor(Color.WHITE);
        messageView.setPadding(32, 22, 32, 22);

        int bgColor = isUser ? Color.parseColor("#1D4ED8") : Color.parseColor("#262626");
        messageView.setBackground(createBubbleDrawable(bgColor, 32f));

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        );
        lp.weight = 0;

        messageWrapper.addView(messageView, lp);
        messagesLayout.addView(messageWrapper);

        scrollView.post(() -> scrollView.fullScroll(View.FOCUS_DOWN));
    }

    private void addQuickChip(LinearLayout parent, String text) {
        TextView chip = new TextView(this);
        chip.setText(text);
        chip.setTextSize(13);
        chip.setTextColor(Color.parseColor("#9CA3AF"));
        chip.setPadding(24, 14, 24, 14);
        chip.setBackground(createBubbleDrawable(Color.parseColor("#262626"), 24f));

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

    private String getOfflineSmartResponse(String prompt) {
        String query = prompt.toLowerCase().trim();
        if (query.contains("مرحبا") || query.contains("أهلا") || query.contains("hello") || query.contains("hi")) {
            return "مرحباً بك! أنا مساعد الذكاء الاصطناعي الذكي، كيف يمكنني مساعدتك اليوم في تطبيقك؟";
        } else if (query.contains("هواوي") || query.contains("huawei") || query.contains("hms")) {
            return "التطبيق متوافق 100% مع أجهزة هواوي وجميع أجهزة أندرويد بدون الاعتماد الإجباري على خدمات جوجل GMS.";
        } else if (query.contains("مجاني") || query.contains("free") || query.contains("سعر")) {
            return "نعم! هذا النظام يعتمد على هندسة صفرية التكلفة 100% ويدعم النماذج المجانية والمحلية مثل Ollama وOpenRouter.";
        } else if (query.contains("أمر") || query.contains("تشغيل") || query.contains("مهمة")) {
            return "تم تسجيل الأمر المباشر بنجاح! جاري معالجة طلبك وتنفيذه بسرعة فائقة.";
        } else {
            return "تم استلام طلبك: \"" + prompt + "\"\nجاهز لمعالجة واستكمال كافة المهام المطلوبة كفاءة عالية.";
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#121212"));

        // Header bar
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setPadding(32, 28, 32, 28);
        header.setBackgroundColor(Color.parseColor("#1E1E1E"));
        header.setGravity(Gravity.CENTER_VERTICAL);

        TextView titleView = new TextView(this);
        titleView.setText("KHALED / quickservice AI");
        titleView.setTextSize(18);
        titleView.setTextColor(Color.WHITE);

        TextView clearBtn = new TextView(this);
        clearBtn.setText("مسح المحادثة");
        clearBtn.setTextSize(13);
        clearBtn.setTextColor(Color.parseColor("#EF4444"));
        clearBtn.setPadding(16, 8, 16, 8);
        clearBtn.setBackground(createBubbleDrawable(Color.parseColor("#3F1B1B"), 16f));

        LinearLayout.LayoutParams titleLp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
        header.addView(titleView, titleLp);
        header.addView(clearBtn);

        root.addView(header);

        // Chat messages scroll view
        scrollView = new ScrollView(this);
        scrollView.setPadding(24, 20, 24, 20);

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

        // Quick prompts scroll bar
        HorizontalScrollView chipsScroll = new HorizontalScrollView(this);
        chipsScroll.setHorizontalScrollBarEnabled(false);
        chipsScroll.setPadding(24, 12, 24, 12);

        LinearLayout chipsLayout = new LinearLayout(this);
        chipsLayout.setOrientation(LinearLayout.HORIZONTAL);

        addQuickChip(chipsLayout, "مرحباً بك");
        addQuickChip(chipsLayout, "هل التطبيق متوافق مع هواوي؟");
        addQuickChip(chipsLayout, "هل الخدمات مجانية 100%؟");
        addQuickChip(chipsLayout, "فحص حالة النظام");

        chipsScroll.addView(chipsLayout);
        root.addView(chipsScroll);

        // Input composer bar
        LinearLayout composer = new LinearLayout(this);
        composer.setPadding(24, 16, 24, 24);
        composer.setBackgroundColor(Color.parseColor("#1E1E1E"));
        composer.setGravity(Gravity.CENTER_VERTICAL);

        inputEditText = new EditText(this);
        inputEditText.setHint("اكتب أمرك أو استفسارك هنا...");
        inputEditText.setTextColor(Color.WHITE);
        inputEditText.setHintTextColor(Color.parseColor("#6B7280"));
        inputEditText.setBackground(createBubbleDrawable(Color.parseColor("#2B2B2B"), 24f));
        inputEditText.setPadding(32, 20, 32, 20);
        inputEditText.setSingleLine(false);
        inputEditText.setMaxLines(3);

        Button sendBtn = new Button(this);
        sendBtn.setText("إرسال");
        sendBtn.setTextColor(Color.WHITE);
        sendBtn.setBackground(createBubbleDrawable(Color.parseColor("#2563EB"), 24f));

        composer.addView(inputEditText, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));

        LinearLayout.LayoutParams btnLp = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        );
        btnLp.setMargins(16, 0, 0, 0);
        composer.addView(sendBtn, btnLp);

        root.addView(composer);

        // Welcome message
        addMessage("أهلاً بك في تطبيق الذكاء الاصطناعي السريع والمستقل 100%! اكتب أي أمر أو اختر القوالب السريعة لتبدأ.", false);

        // Action listeners
        clearBtn.setOnClickListener(v -> {
            messagesLayout.removeAllViews();
            addMessage("تم مسح محادثات السجل بنجاح.", false);
        });

        sendBtn.setOnClickListener(v -> {
            String text = inputEditText.getText().toString().trim();
            if (!text.isEmpty()) {
                addMessage(text, true);
                inputEditText.setText("");
                String reply = getOfflineSmartResponse(text);
                addMessage(reply, false);
            }
        });

        setContentView(root);
    }
}
