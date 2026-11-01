package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.widget.*;
import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.ArrayList;

/**
 * On-device editorial workbench. Drafts are stored separately from the shipped
 * read-only corpus. This screen cannot approve or publish canonical text.
 */
public final class MyanmarEditorialActivity extends Activity {
  private static final int GREEN=0xff144638, CREAM=0xfffaf6eb, GOLD=0xffb88730;
  private EditText volumeInput, paragraphInput, translationInput, explanationInput;
  private EditText sourceInput, rightsInput, reviewer1Input, reviewer2Input, reviewRefInput;
  private TextView paliPreview, statusView;
  private DraftDb drafts;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private TextView text(String s,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);t.setPadding(dp(12),dp(10),dp(12),dp(10));return t;
  }
  private EditText field(String hint,int lines,boolean multiline){
    EditText e=new EditText(this);e.setHint(hint);e.setTextSize(16);e.setMinLines(lines);
    if(multiline){e.setGravity(Gravity.TOP|Gravity.START);e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);}
    else e.setSingleLine(true);
    e.setPadding(dp(12),dp(8),dp(12),dp(8));return e;
  }
  private void section(LinearLayout root,String title){
    root.addView(text(title,17,GREEN,true));
  }
  private void addField(LinearLayout root,EditText e){
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(0,dp(2),0,dp(5));root.addView(e,p);
  }
  private String value(EditText e){return e.getText().toString().trim();}
  private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}

  @Override public void onCreate(Bundle state){
    super.onCreate(state);getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    drafts=new DraftDb();
    ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(CREAM);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(16),dp(12),dp(16),dp(28));scroll.addView(root);
    TextView head=text("☸ မြန်မာစာတည်းဖြတ်ရေးခန်း",22,Color.WHITE,true);head.setBackgroundColor(GREEN);root.addView(head);
    root.addView(text("Editorial Draft • Review Workflow",14,GOLD,true));
    root.addView(text("ဤနေရာတွင် ရေးသားသောစာသားများသည် Draft အဖြစ်သာ သီးခြားသိမ်းဆည်းမည်။ လူနှစ်ဦး စစ်ဆေးပြီး ရင်းမြစ်နှင့် မူပိုင်ခွင့်အထောက်အထား အတည်ပြုခြင်းမရှိဘဲ Offline Reader ၏ အတည်ပြုစာသားအဖြစ် မထည့်သွင်းပါ။",14,0xff665b49,false));
    section(root,"၁။ မူရင်းပါဠိကျမ်းပိုဒ် ရွေးချယ်ရန်");
    volumeInput=field("ကျမ်းအမှတ် (၁ မှ ၄၅)",1,false);volumeInput.setInputType(InputType.TYPE_CLASS_NUMBER);volumeInput.setText("1");addField(root,volumeInput);
    paragraphInput=field("Paragraph ID / Segment ID",1,false);addField(root,paragraphInput);
    Button load=new Button(this);load.setText("ပါဠိမူရင်းကို ဖတ်ယူရန်");root.addView(load);
    paliPreview=text("ရွေးချယ်ထားသော ပါဠိစာပိုဒ်ကို ဤနေရာတွင် ပြသမည်။",17,GREEN,false);root.addView(paliPreview);
    load.setOnClickListener(v->loadPali());
    section(root,"၂။ မြန်မာအကြောင်းအရာ ရေးသားရန်");
    section(root,"မြန်မာအတည်ပြုဘာသာပြန် (Draft)");
    translationInput=field("ပါဠိမူရင်း၏ မြန်မာဘာသာပြန်ကို ရေးပါ...",5,true);addField(root,translationInput);
    section(root,"မြန်မာအတည်ပြုရှင်းလင်းချက် (Draft)");
    explanationInput=field("အဋ္ဌကထာ/ဋီကာနှင့် အခြားယုံကြည်စိတ်ချရသော ရင်းမြစ်များကို ကိုးကား၍ ရှင်းလင်းပါ...",5,true);addField(root,explanationInput);
    section(root,"၃။ ရင်းမြစ်နှင့် စိစစ်သူများ");
    sourceInput=field("မူရင်းရင်းမြစ် / စာအုပ် / စာမျက်နှာ / URL",2,true);addField(root,sourceInput);
    rightsInput=field("ပြန်လည်အသုံးပြုခွင့် / လိုင်စင် / Public-domain အထောက်အထား",2,true);addField(root,rightsInput);
    reviewer1Input=field("စိစစ်သူ (၁) အမည်",1,false);addField(root,reviewer1Input);
    reviewer2Input=field("စိစစ်သူ (၂) အမည်",1,false);addField(root,reviewer2Input);
    reviewRefInput=field("စိစစ်မှတ်တမ်း / အစည်းအဝေး / အတည်ပြုစာညွှန်း",2,true);addField(root,reviewRefInput);
    statusView=text("အခြေအနေ — Draft မသိမ်းရသေးပါ",14,GOLD,true);root.addView(statusView);
    Button save=new Button(this);save.setText("Draft သိမ်းဆည်းရန်");root.addView(save);save.setOnClickListener(v->saveDraft("draft"));
    Button submit=new Button(this);submit.setText("စိစစ်ရန် တင်သွင်းမည်");root.addView(submit);submit.setOnClickListener(v->saveDraft("submitted_for_review"));
    Button list=new Button(this);list.setText("သိမ်းထားသော Draft များ ကြည့်ရန်");root.addView(list);list.setOnClickListener(v->showDrafts());
    Button review=new Button(this);review.setText("Reviewer Queue ဖွင့်ရန်");root.addView(review);review.setOnClickListener(v->showReviewQueue());
    root.addView(text("မှတ်ချက် — ဤ Version သည် Offline Reader database ကို မပြင်ဆင်ပါ။ Approve/Publish လုပ်ဆောင်ချက်ကိုလည်း မပေးထားပါ။ Approved CSV import သည် သီးခြား QA workflow ဖြင့်သာ လုပ်ဆောင်ရမည်။",13,0xff665b49,false));
    setContentView(scroll);
  }

  private void loadPali(){
    try{
      int vol=Integer.parseInt(value(volumeInput));if(vol<1||vol>45)throw new Exception("ကျမ်းအမှတ် ၁ မှ ၄၅ အတွင်း ထည့်ပါ။");
      String id=value(paragraphInput);if(id.isEmpty())throw new Exception("Paragraph ID ထည့်ပါ။");
      File file=OfflineCorpusInstaller.prepare(getApplicationContext());
      try(SQLiteDatabase db=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
          Cursor c=db.rawQuery("SELECT id,segment_id,body FROM paragraphs WHERE volume=? AND (CAST(id AS TEXT)=? OR segment_id=?) LIMIT 1",
            new String[]{Integer.toString(vol),id,id})){
        if(!c.moveToFirst())throw new Exception("ဤကျမ်းပိုဒ်ကို Offline SQLite တွင် မတွေ့ပါ။");
        paragraphInput.setText(c.getString(0));
        paliPreview.setText("§ "+c.getString(1)+"\n\n"+c.getString(2));
      }
    }catch(Exception e){toast(e.getMessage()==null?"ပါဠိစာသား ဖတ်မရပါ။":e.getMessage());}
  }

  private void saveDraft(String status){
    String vol=value(volumeInput),pid=value(paragraphInput),tr=value(translationInput),ex=value(explanationInput);
    if(vol.isEmpty()||pid.isEmpty()||(tr.isEmpty()&&ex.isEmpty())){toast("ကျမ်းအမှတ်၊ Paragraph ID နှင့် ဘာသာပြန် သို့မဟုတ် ရှင်းလင်းချက် တစ်ခုခု ဖြည့်ပါ။");return;}
    if(status.equals("submitted_for_review")){
      String a=value(reviewer1Input),b=value(reviewer2Input);
      if(a.isEmpty()||b.isEmpty()||a.equalsIgnoreCase(b)||value(sourceInput).isEmpty()||value(rightsInput).isEmpty()||value(reviewRefInput).isEmpty()){
        toast("Review တင်ရန် Reviewer နှစ်ဦး မတူညီရပါမည်။ ရင်းမြစ်၊ Rights Evidence နှင့် Review Reference တို့လည်း လိုအပ်ပါသည်။");return;
      }
    }
    ContentValues v=new ContentValues();v.put("volume",Integer.parseInt(vol));v.put("paragraph_id",pid);
    v.put("translation_my",tr);v.put("explanation_my",ex);v.put("source_ref",value(sourceInput));
    v.put("rights_evidence",value(rightsInput));v.put("reviewer_1",value(reviewer1Input));
    v.put("reviewer_2",value(reviewer2Input));v.put("review_reference",value(reviewRefInput));
    v.put("status",status);v.put("updated_at",new SimpleDateFormat("yyyy-MM-dd HH:mm:ss",Locale.US).format(new Date()));
    drafts.getWritableDatabase().insertWithOnConflict("editorial_drafts",null,v,SQLiteDatabase.CONFLICT_REPLACE);
    statusView.setText("အခြေအနေ — "+(status.equals("draft")?"Draft သိမ်းဆည်းပြီး":"စိစစ်ရန် တင်သွင်းပြီး (Pending Review)"));
    toast("Draft ကို App အတွင်း သီးခြားသိမ်းဆည်းပြီးပါပြီ။ Approved content မဟုတ်သေးပါ။");
  }

  private void showDrafts(){
    String[] rows=new String[0];java.util.ArrayList<String> labels=new java.util.ArrayList<>();java.util.ArrayList<String> ids=new java.util.ArrayList<>();
    try(Cursor c=drafts.getReadableDatabase().rawQuery("SELECT volume,paragraph_id,status,updated_at FROM editorial_drafts ORDER BY updated_at DESC",null)){
      while(c.moveToNext()){int vol=c.getInt(0);String id=c.getString(1);ids.add(vol+"|"+id);labels.add("ကျမ်း "+vol+" • § "+id+"\n"+c.getString(2)+" • "+c.getString(3));}
    }
    if(labels.isEmpty()){toast("သိမ်းထားသော Draft မရှိသေးပါ။");return;}
    new AlertDialog.Builder(this).setTitle("Editorial Drafts ("+labels.size()+")")
      .setItems(labels.toArray(new String[0]),(d,w)->{
        String[] key=ids.get(w).split("\\|",2); String volKey=key[0], id=key[1];
        try(Cursor c=drafts.getReadableDatabase().rawQuery("SELECT volume,paragraph_id,translation_my,explanation_my,source_ref,rights_evidence,reviewer_1,reviewer_2,review_reference,status FROM editorial_drafts WHERE volume=? AND paragraph_id=?",new String[]{volKey,id})){
          if(c.moveToFirst()){
            volumeInput.setText(Integer.toString(c.getInt(0)));paragraphInput.setText(c.getString(1));
            translationInput.setText(c.getString(2));explanationInput.setText(c.getString(3));
            sourceInput.setText(c.getString(4));rightsInput.setText(c.getString(5));
            reviewer1Input.setText(c.getString(6));reviewer2Input.setText(c.getString(7));reviewRefInput.setText(c.getString(8));
            statusView.setText("အခြေအနေ — "+c.getString(9));
            loadPali();
          }
        }
      }).setNegativeButton("ပိတ်မည်",null).show();
  }


  private void createReviewTable(SQLiteDatabase db){
    db.execSQL("CREATE TABLE IF NOT EXISTS editorial_reviews(volume INTEGER NOT NULL,paragraph_id TEXT NOT NULL,reviewer_name TEXT NOT NULL COLLATE NOCASE,decision TEXT NOT NULL CHECK(decision IN ('approve','revision','reject')),notes TEXT NOT NULL,reviewed_at TEXT NOT NULL,PRIMARY KEY(volume,paragraph_id,reviewer_name))");
  }
  private void showReviewQueue(){
    ArrayList<String> keys=new ArrayList<>(),labels=new ArrayList<>();
    try(Cursor c=drafts.getReadableDatabase().rawQuery("SELECT volume,paragraph_id,status FROM editorial_drafts WHERE status='submitted_for_review' ORDER BY updated_at",null)){
      while(c.moveToNext()){int vol=c.getInt(0);String pid=c.getString(1);keys.add(vol+"|"+pid);labels.add("ကျမ်း "+vol+" • § "+pid+" • "+c.getString(2));}
    }
    if(labels.isEmpty()){toast("စိစစ်ရန်တင်ထားသော Draft မရှိသေးပါ။");return;}
    new AlertDialog.Builder(this).setTitle("Reviewer Queue").setItems(labels.toArray(new String[0]),(d,w)->reviewDraft(keys.get(w))).setNegativeButton("ပိတ်မည်",null).show();
  }
  private void reviewDraft(String key){
    String[] k=key.split("\\|",2);int vol=Integer.parseInt(k[0]);String pid=k[1];
    LinearLayout form=new LinearLayout(this);form.setOrientation(1);form.setPadding(dp(16),dp(8),dp(16),dp(8));
    EditText reviewer=field("Reviewer အမည်",1,false),notes=field("စိစစ်မှတ်ချက်",3,true);
    RadioGroup decisions=new RadioGroup(this);decisions.setOrientation(RadioGroup.VERTICAL);
    String[] choices={"Approve","Revision လိုအပ်","Reject"};
    for(int i=0;i<choices.length;i++){RadioButton b=new RadioButton(this);b.setText(choices[i]);b.setId(100+i);decisions.addView(b);}
    form.addView(reviewer);form.addView(decisions);form.addView(notes);
    new AlertDialog.Builder(this).setTitle("ကျမ်း "+vol+" • § "+pid).setView(form)
      .setPositiveButton("ဆုံးဖြတ်ချက် သိမ်းမည်",(d,w)->{
        String name=reviewer.getText().toString().trim();int choice=decisions.getCheckedRadioButtonId()-100;
        if(name.isEmpty()||choice<0||choice>2){toast("Reviewer အမည်နှင့် ဆုံးဖြတ်ချက် ဖြည့်ပါ။");return;}
        saveReview(vol,pid,name,new String[]{"approve","revision","reject"}[choice],notes.getText().toString().trim());
      }).setNegativeButton("မလုပ်တော့ပါ",null).show();
  }
  private void saveReview(int vol,String pid,String reviewer,String decision,String notes){
    SQLiteDatabase db=drafts.getWritableDatabase();db.beginTransaction();
    try{
      ContentValues v=new ContentValues();v.put("volume",vol);v.put("paragraph_id",pid);v.put("reviewer_name",reviewer);v.put("decision",decision);v.put("notes",notes);
      v.put("reviewed_at",new SimpleDateFormat("yyyy-MM-dd HH:mm:ss",Locale.US).format(new Date()));
      db.insertWithOnConflict("editorial_reviews",null,v,SQLiteDatabase.CONFLICT_REPLACE);
      int approvals=0,revisions=0,rejects=0;
      try(Cursor c=db.rawQuery("SELECT decision,COUNT(*) FROM editorial_reviews WHERE volume=? AND paragraph_id=? GROUP BY decision",new String[]{Integer.toString(vol),pid})){
        while(c.moveToNext()){String d=c.getString(0);if(d.equals("approve"))approvals=c.getInt(1);else if(d.equals("revision"))revisions=c.getInt(1);else if(d.equals("reject"))rejects=c.getInt(1);}
      }
      String reviewState=rejects>0?"Reject ရှိ":revisions>0?"Revision လိုအပ်":approvals>=2?"Reviewer နှစ်ဦး Approve (Local)": "စိစစ်မှု ဆက်လက်လိုအပ်";
      db.setTransactionSuccessful();
      toast("Review သိမ်းပြီး — "+reviewState+" • Approve "+approvals+" ဦး။ Draft ကို မူရင်း Submitted အခြေအနေတွင်သာ ထားရှိသည်။");
    }catch(Exception e){toast("Review သိမ်းမရပါ: "+e.getMessage());}
    finally{db.endTransaction();}
  }

  private final class DraftDb extends SQLiteOpenHelper {
    DraftDb(){super(MyanmarEditorialActivity.this,"myanmar_editorial_drafts.db",null,2);}
    @Override public void onCreate(SQLiteDatabase db){
      createReviewTable(db);
      db.execSQL("CREATE TABLE editorial_drafts(volume INTEGER NOT NULL,paragraph_id TEXT NOT NULL,translation_my TEXT NOT NULL,explanation_my TEXT NOT NULL,source_ref TEXT NOT NULL,rights_evidence TEXT NOT NULL,reviewer_1 TEXT NOT NULL,reviewer_2 TEXT NOT NULL,review_reference TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('draft','submitted_for_review')),updated_at TEXT NOT NULL,PRIMARY KEY(volume,paragraph_id))");
    }
    @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion){if(oldVersion<2)createReviewTable(db);}
  }
  @Override protected void onDestroy(){if(drafts!=null)drafts.close();super.onDestroy();}
}
