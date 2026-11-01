package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.io.File;

/** Actual Pali paragraph reader for all 45 offline book groups.
 * Opens the shipped SQLite in the background before querying, including
 * when a volume is tapped immediately after app launch.
 */
public class ParagraphExplanationActivity extends Activity {
  private static final int PAGE_SIZE=50;
  private static final int GREEN=0xff144638;
  private SQLiteDatabase db;
  private LinearLayout rows,pager;
  private int volume,page=0;
  private String selected;
  private boolean hasMyanmarContent=false;
  private volatile boolean destroyed=false;
  private final String PREF="tipitaka_paragraph_progress";

  private void notice(String value){
    TextView t=new TextView(this);
    t.setText(value);t.setTextColor(GREEN);t.setTextSize(18);
    t.setPadding(22,24,22,24);
    rows.addView(t);
  }

  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    volume=Math.max(1,Math.min(45,getIntent().getIntExtra("volume",1)));
    selected=getIntent().getStringExtra("paragraph_id");
    if(selected==null){
      page=Math.max(0,getSharedPreferences(PREF,MODE_PRIVATE).getInt("volume_"+volume+"_page",0));
    }
    LinearLayout root=new LinearLayout(this);
    root.setOrientation(LinearLayout.VERTICAL);
    root.setBackgroundColor(0xfffaf6eb);
    TextView title=new TextView(this);
    title.setText("☸ ကျမ်း "+volume+" — မူရင်းပါဠိ ကျမ်းပိုဒ်များ");
    title.setTextSize(21);title.setTextColor(-1);
    title.setPadding(18,22,16,22);title.setBackgroundColor(GREEN);
    root.addView(title);
    ScrollView scroll=new ScrollView(this);
    rows=new LinearLayout(this);rows.setOrientation(LinearLayout.VERTICAL);
    scroll.addView(rows);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    pager=new LinearLayout(this);root.addView(pager);
    setContentView(root);
    notice("Offline ကျမ်းစာဒေတာကို ဖွင့်နေပါသည်။ ပထမအကြိမ်တွင် SQLite Database ကို ဖုန်းထဲသို့ ကူးယူရပါမည်။");
    new Thread(this::openCorpus,"offline-pali-reader").start();
  }

  private void openCorpus(){
    SQLiteDatabase opened=null;
    try{
      // Both library and reader share one synchronized installer.
      File file=OfflineCorpusInstaller.prepare(getApplicationContext());
      opened=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
      long count;
      try(Cursor c=opened.rawQuery(
          "SELECT COUNT(*) FROM paragraphs WHERE volume=?",
          new String[]{Integer.toString(volume)})){
        if(!c.moveToFirst())throw new IllegalStateException("Cannot read paragraphs table");
        count=c.getLong(0);
      }
      if(count==0)throw new IllegalStateException("ကျမ်း "+volume+" တွင် ပါဠိစာသား မရှိပါ။");
      boolean has=false;
      try(Cursor c=opened.rawQuery(
          "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paragraph_myanmar_content'",
          null)){has=c.moveToFirst();}
      if(destroyed){opened.close();return;}
      db=opened;
      final boolean canTranslate=has;
      final long segments=count;
      runOnUiThread(()->{
        if(destroyed)return;
        hasMyanmarContent=canTranslate;
        rows.removeAllViews();
        notice("✓ Offline ကျမ်း "+volume+" — စာပိုဒ် "+segments+" ပိုဒ်။");
        loadPage();
      });
    }catch(Exception err){
      if(opened!=null && opened!=db)try{opened.close();}catch(Exception ignored){}
      final String message=err.getMessage()==null?err.getClass().getSimpleName():err.getMessage();
      runOnUiThread(()->{
        if(destroyed)return;
        rows.removeAllViews();
        notice("ကျမ်းစာဖွင့်၍မရပါ: "+message+"\nဖုန်း Storage နေရာလွတ်နှင့် APK ထဲရှိ Offline Database ကို စစ်ဆေးပါ။");
        Button retry=new Button(this);retry.setText("ပြန်ဖွင့်မည်");
        rows.addView(retry);retry.setOnClickListener(v->recreate());
      });
    }
  }

  private void loadPage(){
    if(db==null || destroyed)return;
    rows.removeAllViews();pager.removeAllViews();
    final String translationExpression=hasMyanmarContent?"tr.text_my":"NULL AS text_my";
    final String translationJoin=hasMyanmarContent?
        " LEFT JOIN paragraph_myanmar_content tr ON tr.segment_id=p.segment_id AND tr.content_type='translation' AND tr.reviewed=1 ":"";
    final String where=selected==null?" WHERE p.volume=? ":" WHERE p.volume=? AND p.id=? ";
    final String reviewColumns=hasMyanmarContent?
        ",tr.source_ref,tr.reviewer_1,tr.reviewer_2,tr.review_reference,tr.reviewed_at,"+
        "ex.text_my,ex.source_ref,ex.reviewer_1,ex.reviewer_2,ex.review_reference,ex.reviewed_at":
        ",NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL";
    final String explanationJoin=hasMyanmarContent?
        " LEFT JOIN paragraph_myanmar_content ex ON ex.segment_id=p.segment_id AND ex.content_type='explanation' AND ex.reviewed=1 ":"";
    final String sql="SELECT p.id,p.segment_id,p.body,e.explanation_my,e.source_ref,"+
        translationExpression+reviewColumns+" FROM paragraphs p "+
        " LEFT JOIN paragraph_explanations e ON e.paragraph_id=p.id AND e.language='my' AND e.reviewed=1 "+
        translationJoin+explanationJoin+where+" ORDER BY p.id LIMIT "+PAGE_SIZE+" OFFSET "+(page*PAGE_SIZE);
    final String[] args=selected==null?new String[]{Integer.toString(volume)}:
        new String[]{Integer.toString(volume),selected};
    try(Cursor c=db.rawQuery(sql,args)){
      int count=0;
      while(c.moveToNext()){
        final String paraId=c.getString(0);
        final String segmentId=c.getString(1);
        final String pali=c.getString(2);
        final String explanation=c.isNull(3)?null:c.getString(3);
        final String source=c.isNull(4)?"":c.getString(4);
        final String translation=c.isNull(5)?null:c.getString(5);
        final String trSource=c.isNull(6)?"":c.getString(6);
        final String trReviewer1=c.isNull(7)?"":c.getString(7);
        final String trReviewer2=c.isNull(8)?"":c.getString(8);
        final String trReviewRef=c.isNull(9)?"":c.getString(9);
        final String trReviewedAt=c.isNull(10)?"":c.getString(10);
        final String reviewedExplanation=c.isNull(11)?null:c.getString(11);
        final String exSource=c.isNull(12)?"":c.getString(12);
        final String exReviewer1=c.isNull(13)?"":c.getString(13);
        final String exReviewer2=c.isNull(14)?"":c.getString(14);
        final String exReviewRef=c.isNull(15)?"":c.getString(15);
        final String exReviewedAt=c.isNull(16)?"":c.getString(16);
        TextView t=new TextView(this);
        t.setText("§ "+segmentId+"\n"+pali+"\n\n☸ မြန်မာဘာသာပြန်နှင့် ရှင်းလင်းချက်");
        t.setTextSize(18);t.setTextColor(0xff17493c);
        t.setPadding(22,18,22,18);
        rows.addView(t);
        t.setOnClickListener(v->popup(paraId,segmentId,pali,translation,explanation,source,
            trSource,trReviewer1,trReviewer2,trReviewRef,trReviewedAt,
            reviewedExplanation,exSource,exReviewer1,exReviewer2,exReviewRef,exReviewedAt));
        if(selected!=null)popup(paraId,segmentId,pali,translation,explanation,source,
            trSource,trReviewer1,trReviewer2,trReviewRef,trReviewedAt,
            reviewedExplanation,exSource,exReviewer1,exReviewer2,exReviewRef,exReviewedAt);
        count++;
      }
      if(count==0 && page>0 && selected==null){
        page=0;
        loadPage();
        return;
      }
      if(count==0)notice("ကျမ်း "+volume+" တွင် ယခုစာမျက်နှာအတွက် စာသားမရှိပါ။");
      if(selected==null){
        getSharedPreferences(PREF,MODE_PRIVATE).edit().putInt("volume_"+volume+"_page",page).apply();
        Button prev=new Button(this);prev.setText("‹ ရှေ့စာမျက်နှာ");
        prev.setEnabled(page>0);
        pager.addView(prev,new LinearLayout.LayoutParams(0,-2,1));
        prev.setOnClickListener(v->{page--;loadPage();});
        TextView info=new TextView(this);
        info.setText(" "+(page+1)+" ");info.setTextSize(17);info.setGravity(Gravity.CENTER);
        pager.addView(info);
        Button next=new Button(this);next.setText("နောက်စာမျက်နှာ ›");
        next.setEnabled(count==PAGE_SIZE);
        pager.addView(next,new LinearLayout.LayoutParams(0,-2,1));
        next.setOnClickListener(v->{page++;loadPage();});
      }
    }catch(Exception e){
      notice("ကျမ်းစာ SQL ဖတ်၍မရပါ: "+e.getMessage());
    }
  }

  private void popup(String paraId,String segmentId,String pali,String translation,String explanation,String source,
      String trSource,String trReviewer1,String trReviewer2,String trReviewRef,String trReviewedAt,
      String reviewedExplanation,String exSource,String exReviewer1,String exReviewer2,String exReviewRef,String exReviewedAt){
    LinearLayout box=new LinearLayout(this);box.setOrientation(1);
    box.setPadding(20,18,20,18);box.setBackgroundColor(0xfffaf6eb);
    TextView original=new TextView(this);
    original.setText("မူရင်းပါဠိ • "+segmentId+"\n"+pali);
    original.setTextSize(18);original.setTextColor(0xff194b3d);box.addView(original);
    TextView myTranslation=new TextView(this);
    myTranslation.setText((translation==null||translation.trim().isEmpty()?
        "မြန်မာဘာသာပြန် — မရရှိသေးပါ။":"✓ စိစစ်အတည်ပြုထားသော မြန်မာဘာသာပြန်\n"+translation));
    myTranslation.setTextSize(18);myTranslation.setPadding(0,18,0,10);box.addView(myTranslation);
    TextView myExplanation=new TextView(this);
    String explanationText=reviewedExplanation!=null&&!reviewedExplanation.trim().isEmpty()?reviewedExplanation:explanation;
    myExplanation.setText((explanationText==null||explanationText.trim().isEmpty()?
        "မြန်မာရှင်းလင်းချက် — မရရှိသေးပါ။":"✓ စိစစ်အတည်ပြုထားသော မြန်မာရှင်းလင်းချက်\n"+explanationText));
    myExplanation.setTextColor(0xff55422a);
    myExplanation.setTextSize(18);myExplanation.setPadding(0,16,0,10);box.addView(myExplanation);
    addReviewEvidence(box,"ဘာသာပြန်",trSource,trReviewer1,trReviewer2,trReviewRef,trReviewedAt);
    addReviewEvidence(box,"ရှင်းလင်းချက်",exSource,exReviewer1,exReviewer2,exReviewRef,exReviewedAt);
    if(!source.isEmpty()){
      TextView sourceView=new TextView(this);sourceView.setText("အဋ္ဌကထာ/ရှင်းလင်းချက် ရင်းမြစ်: "+source);
      sourceView.setTextSize(13);box.addView(sourceView);
    }
    boolean saved=getSharedPreferences(PREF,MODE_PRIVATE).getBoolean("bookmark_"+paraId,false);
    new AlertDialog.Builder(this).setTitle("☸ ကျမ်းပိုဒ် အဓိပ္ပာယ်")
      .setView(box)
      .setNeutralButton(saved?"🔖 Bookmark ဖယ်ရန်":"🔖 Bookmark သိမ်းရန်",(d,w)->{
        getSharedPreferences(PREF,MODE_PRIVATE).edit().putBoolean("bookmark_"+paraId,!saved).apply();
        Toast.makeText(this,!saved?"Bookmark သိမ်းပြီး":"Bookmark ဖယ်ပြီး",Toast.LENGTH_SHORT).show();
      }).setPositiveButton("ပိတ်မည်",null).show();
  }
  private void addReviewEvidence(LinearLayout box,String label,String source,String r1,String r2,String ref,String date){
    if(source.isEmpty()&&r1.isEmpty()&&r2.isEmpty()&&ref.isEmpty()&&date.isEmpty())return;
    TextView evidence=new TextView(this);
    evidence.setText("အတည်ပြုမှတ်တမ်း ("+label+")\n"+
        (source.isEmpty()?"":"ရင်းမြစ်: "+source+"\n")+
        (r1.isEmpty()?"":"စိစစ်သူ ၁: "+r1+"\n")+
        (r2.isEmpty()?"":"စိစစ်သူ ၂: "+r2+"\n")+
        (ref.isEmpty()?"":"စိစစ်မှတ်တမ်း: "+ref+"\n")+
        (date.isEmpty()?"":"စိစစ်သည့်နေ့: "+date));
    evidence.setTextSize(13);evidence.setTextColor(0xff66553b);
    evidence.setPadding(0,10,0,8);box.addView(evidence);
  }
  @Override protected void onDestroy(){
    destroyed=true;
    if(db!=null)try{db.close();}catch(Exception ignored){}
    super.onDestroy();
  }
}
