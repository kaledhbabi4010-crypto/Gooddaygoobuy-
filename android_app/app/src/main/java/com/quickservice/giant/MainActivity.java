
package com.quickservice.giant;

import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private LinearLayout messages;
    private EditText input;

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

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(18, 18, 18));

        TextView header = title("quickservice AI", 22);
        header.setGravity(Gravity.CENTER_VERTICAL);
        root.addView(header,
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                70
            )
        );

        ScrollView scroll = new ScrollView(this);

        messages = new LinearLayout(this);
        messages.setOrientation(LinearLayout.VERTICAL);
        messages.setPadding(12, 12, 12, 12);

        addMessage(
            "مرحبًا، أنا quickservice AI. اكتب الأمر الذي تريد تنفيذه.",
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
        input.setHint("اكتب أمرك...");
        input.setTextColor(Color.WHITE);
        input.setHintTextColor(Color.GRAY);
        input.setSingleLine(false);

        Button send = new Button(this);
        send.setText("إرسال");

        send.setOnClickListener(v -> {
            String command = input.getText().toString().trim();

            if (!command.isEmpty()) {
                addMessage(command, true);

                // Backend connection will be connected in the
                // next Stage 19 steps.
                addMessage(
                    "تم استلام الأمر — بانتظار ربط quickservice Runtime.",
                    false
                );

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

// KHALED_REAL_REPAIR_CHALLENGE
this_is_a_real_khaled_build_failure;
