package asia.aaii.myanmartipitaka

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import java.io.File

/**
 * Optional V2.3.8.0 reader data adapter.
 *
 * Only data explicitly exported from reviewed segments may be shown. The bundled
 * v2.3.7.7 catalog must never be interpreted as full Pāli text.
 * This is a reusable adapter, NOT yet wired into MainActivity.
 */
class ApprovedPaliReader(private val context: Context) {
    data class Passage(val id: String, val textUid: String, val pali: String)
    private val assetName = "approved_pali.sqlite"

    fun isAvailable(): Boolean =
        context.assets.list("")?.contains(assetName) == true

    fun passages(mcuVolume: Int, limit: Int = 100, offset: Int = 0): List<Passage> {
        require(mcuVolume in 1..45) { "MCU volume must be 1..45" }
        require(limit in 1..500 && offset >= 0)
        if (!isAvailable()) return emptyList()
        val target = File(context.filesDir, assetName)
        if (!target.exists()) {
            context.assets.open(assetName).use { input ->
                File(context.filesDir, "$assetName.tmp").also { tmp ->
                    try {
                        tmp.outputStream().use { output -> input.copyTo(output) }
                        if (!tmp.renameTo(target)) error("Could not initialize offline Pāli DB")
                    } finally { tmp.delete() }
                }
            }
        }
        val db = SQLiteDatabase.openDatabase(target.path, null, SQLiteDatabase.OPEN_READONLY)
        try {
            val results = mutableListOf<Passage>()
            db.rawQuery(
                "SELECT segment_id,text_uid,pali FROM approved_pali WHERE mcu_volume=? ORDER BY segment_id LIMIT ? OFFSET ?",
                arrayOf(mcuVolume.toString(), limit.toString(), offset.toString())
            ).use { c ->
                while (c.moveToNext()) {
                    results.add(Passage(c.getString(0), c.getString(1), c.getString(2)))
                }
            }
            return results
        } finally {
            db.close()
        }
    }
}
