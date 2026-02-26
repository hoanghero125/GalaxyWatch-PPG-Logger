package kaist.iclab.galaxyppglogger.ui

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.StateFlow

abstract class AbstractViewModel : ViewModel() {
    abstract val serviceState: StateFlow<ServiceState>

    abstract fun start()
    abstract fun stop()
    abstract fun flush()

    abstract fun bindService()
    abstract fun unbindService()
}
