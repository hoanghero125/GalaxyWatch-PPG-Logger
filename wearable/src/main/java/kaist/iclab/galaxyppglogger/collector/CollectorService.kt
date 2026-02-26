package kaist.iclab.galaxyppglogger.collector

import android.annotation.SuppressLint
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import android.util.Log
import kaist.iclab.galaxyppglogger.OngoingActivityHelper
import org.koin.android.ext.android.inject

class CollectorService : Service() {
    private val collectorController by inject<CollectorController>()
    private val TAG = javaClass.simpleName
    private lateinit var ongoingActivityHelper: OngoingActivityHelper

    private val binder = LocalBinder()
    override fun onBind(intent: Intent?): IBinder {
        return binder
    }
    inner class LocalBinder : Binder() {
        fun getService() = this@CollectorService
    }

    var isRunning = false

    @SuppressLint("ForegroundServiceType")
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        ongoingActivityHelper = OngoingActivityHelper(this)

        val notification = ongoingActivityHelper.createOngoingActivityNotification(
            title = "PPG Data Collection",
            text = "Recording sensor data..."
        )

        startForeground(OngoingActivityHelper.NOTIFICATION_ID, notification)
        Log.d(TAG, "Service started with Ongoing Activity")

        collectorController.collectors.forEach {
            it.start()
        }
        isRunning = true

        return START_STICKY
    }

    override fun onDestroy() {
        Log.d(TAG, "onDestroy called")
        isRunning = false
        if (::ongoingActivityHelper.isInitialized) {
            ongoingActivityHelper.stopOngoingActivity()
        }
    }
}
