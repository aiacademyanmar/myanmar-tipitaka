package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.os.Build;
import android.view.Gravity;
import android.view.View;
import android.view.WindowInsets;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Reusable 5-tab fixed bottom footer, positioned ABOVE Android navigation gestures/buttons. */
public final class TipitakaFooter {
  private static final int GREEN=0xff174f3c, WHITE=Color.WHITE;
  private TipitakaFooter(){}
  private static int dp(Activity a,int d){return (int)(d*a.getResources().getDisplayMetrics().density+0.5f);}
  public static void attach(Activity a,LinearLayout root,int currentPage){
    LinearLayout nav=new LinearLayout(a);
    nav.setGravity(Gravity.CENTER);
    nav.setOrientation(LinearLayout.HORIZONTAL);
    nav.setBackgroundColor(0xfffffcf3);
    String[] symbols={"⌂","▦","⌕","🔖","☰"};
    String[] names={"Home","Books","Search","Saved","More"};
    int selected=currentPage==1?0:currentPage==4||currentPage==5?1:currentPage==10?2:currentPage==12?3:currentPage==21?4:-1;
    int[] targets={1,4,10,12,21};
    for(int n=0;n<names.length;n++){
       final int destination=targets[n];final int item=n;
       LinearLayout col=new LinearLayout(a);
       col.setOrientation(LinearLayout.VERTICAL);col.setGravity(Gravity.CENTER);
       TextView ico=new TextView(a);ico.setText(symbols[n]);ico.setTextSize(22);
       ico.setGravity(Gravity.CENTER);ico.setTextColor(selected==n?GREEN:0xff718375);
       TextView label=new TextView(a);label.setText(names[n]);label.setTextSize(10);
       label.setGravity(Gravity.CENTER);label.setTextColor(selected==n?GREEN:0xff718375);
       col.addView(ico);col.addView(label);
       col.setClickable(true);col.setFocusable(true);
       GradientDrawable bg=new GradientDrawable();bg.setColor(selected==n?0xffe6eee4:0x00ffffff);
       bg.setCornerRadius(dp(a,12));
       col.setBackground(new RippleDrawable(ColorStateList.valueOf(0x44247a5b),bg,null));
       LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(a,59),1);
       p.setMargins(dp(a,2),dp(a,3),dp(a,2),dp(a,3));nav.addView(col,p);
       col.setOnClickListener(v->{
         if(a instanceof NativeFrontPagesActivity){
           ((NativeFrontPagesActivity)a).navigateTo(destination);
           return;
         }
         if(destination==4){a.startActivity(new Intent(a,Mcu45CatalogActivity.class));return;}
         if(destination==10){a.startActivity(new Intent(a,PaliOfflineSearchActivity.class));return;}
         if(destination==12){a.startActivity(new Intent(a,PaliSourceLibraryActivity.class));return;}
         Intent intent=new Intent(a,NativeFrontPagesActivity.class);
         intent.putExtra("openPage",destination);
         a.startActivity(intent);
       });
    }
    root.addView(nav,new LinearLayout.LayoutParams(-1,dp(a,66)));
    // Android 15 (target SDK 35) enforces edge-to-edge. Reserve both system-bar
    // inset areas so fixed nav never falls behind gesture bar or 3-button nav.
    if(Build.VERSION.SDK_INT>=35){
       root.setOnApplyWindowInsetsListener((v,insets)->{
          android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars());
          root.setPadding(0,bars.top,0,bars.bottom);
          return insets;
       });
       root.requestApplyInsets();
    }
  }
}
