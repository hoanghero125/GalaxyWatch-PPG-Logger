package kaist.iclab.galaxyppglogger.data

import androidx.room.Database
import androidx.room.RoomDatabase
import kaist.iclab.galaxyppglogger.collector.PPG.PpgDao
import kaist.iclab.galaxyppglogger.collector.PPG.PpgEntity

@Database(
    version = 1,
    entities = [
        PpgEntity::class,
    ],
    exportSchema = false,
)
abstract class RoomDB : RoomDatabase() {
    abstract fun ppgDao(): PpgDao
}
