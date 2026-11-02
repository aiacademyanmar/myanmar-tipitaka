package asia.aaii.myanmartipitaka;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;

/** Persists Pali source positions by stable segment ID + source file, not only page.
 * When the source edition changes, missing IDs are shown as missing on lookup.
 */
public final class PaliReadingState {
  private final SharedPreferences preferences;
  private static final String BOOKMARKS="segment_bookmarks_v1";
  public static final class Entry {
    public final String file,segment,revision;
    public final long created;
    Entry(String f,String s,String r,long time){file=f;segment=s;revision=r;created=time;}
  }
  public PaliReadingState(Context context){
    preferences=context.getApplicationContext().getSharedPreferences("pali_segment_reading_v1",Context.MODE_PRIVATE);
  }
  public List<Entry> bookmarks(){
    List<Entry> out=new ArrayList<>();
    try{
      JSONArray data=new JSONArray(preferences.getString(BOOKMARKS,"[]"));
      for(int i=0;i<data.length();i++){
        JSONObject item=data.optJSONObject(i);if(item==null)continue;
        String file=item.optString("file",""),segment=item.optString("segment","");
        if(file.isEmpty()||segment.isEmpty())continue;
        out.add(new Entry(file,segment,item.optString("revision",""),item.optLong("created",0)));
      }
    }catch(Exception ignored){}
    return out;
  }
  public void add(String file,String segment,String revision){
    if(file==null||segment==null||file.isEmpty()||segment.isEmpty())return;
    JSONArray items=new JSONArray();
    try{
      JSONObject current=new JSONObject();
      current.put("file",file);current.put("segment",segment);
      current.put("revision",revision==null?"":revision);
      current.put("created",System.currentTimeMillis());
      items.put(current);
      int count=1;
      for(Entry e:bookmarks()){
        if(e.file.equals(file)&&e.segment.equals(segment))continue;
        if(count>=200)break;
        JSONObject obj=new JSONObject();
        obj.put("file",e.file);obj.put("segment",e.segment);
        obj.put("revision",e.revision);obj.put("created",e.created);
        items.put(obj);count++;
      }
      preferences.edit().putString(BOOKMARKS,items.toString()).apply();
    }catch(Exception ignored){}
  }
  public void remove(String file,String segment){
    JSONArray array=new JSONArray();
    try{
      for(Entry e:bookmarks()){
        if(e.file.equals(file)&&e.segment.equals(segment))continue;
        JSONObject obj=new JSONObject();
        obj.put("file",e.file);obj.put("segment",e.segment);
        obj.put("revision",e.revision);obj.put("created",e.created);
        array.put(obj);
      }
      preferences.edit().putString(BOOKMARKS,array.toString()).apply();
    }catch(Exception ignored){}
  }
  public void lastRead(String file,String segment,String revision){
    if(file==null||segment==null||file.isEmpty()||segment.isEmpty())return;
    preferences.edit().putString("last_file",file).putString("last_segment",segment)
      .putString("last_revision",revision==null?"":revision).apply();
  }
  public Entry lastRead(){
    String f=preferences.getString("last_file","");
    String s=preferences.getString("last_segment","");
    if(f.isEmpty()||s.isEmpty())return null;
    return new Entry(f,s,preferences.getString("last_revision",""),0);
  }
}
