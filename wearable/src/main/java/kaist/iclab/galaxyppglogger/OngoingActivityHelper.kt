package kaist.iclab.galaxyppglogger

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.wear.ongoing.OngoingActivity
import androidx.wear.ongoing.Status

class OngoingActivityHelper(private val context: Context) {
    
    companion object {
        const val NOTIFICATION_ID = 1001
        const val CHANNEL_ID = "ppg_collection_channel"
    }
    
    fun createOngoingActivityNotification(
        title: String = "PPG Data Collection",
        text: String = "Collecting sensor data..."
    ): Notification {
        
        // Create notification channel (Android 8.0+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "PPG Collection",
                NotificationManager.IMPORTANCE_LOW  // Low importance = no sound
            ).apply {
                description = "Ongoing PPG data collection"
                setShowBadge(false)
            }
            
            val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) 
                as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
        
        // Create intent to return to app
        val intent = Intent(context, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        // Create the notification
        val builder = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)  // dùng icon app của bạn
            .setContentTitle(title)
            .setContentText(text)
            .setOngoing(true)  // persistent
            .setContentIntent(pendingIntent)
            .setCategory(NotificationCompat.CATEGORY_WORKOUT)
            .setPriority(NotificationCompat.PRIORITY_LOW)
        
        // ========== Wrap with OngoingActivity ==========
        OngoingActivity.Builder(context, NOTIFICATION_ID, builder)
            .setAnimatedIcon(android.R.drawable.ic_dialog_info)
            .setStaticIcon(android.R.drawable.ic_dialog_info)
            .setTouchIntent(pendingIntent)
            .setStatus(
                Status.Builder()
                    .addTemplate(text)
                    .build()
            )
            .build()
            .apply(context)

        return builder.build()
    }
    
    fun stopOngoingActivity() {
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) 
            as NotificationManager
        notificationManager.cancel(NOTIFICATION_ID)
    }
}