package kaist.iclab.galaxyppglogger

import androidx.room.Room
import kaist.iclab.galaxyppglogger.collector.CollectorController
import kaist.iclab.galaxyppglogger.collector.PPG.PPGCollector
import kaist.iclab.galaxyppglogger.data.HealthTrackerService
import kaist.iclab.galaxyppglogger.data.RoomDB
import kaist.iclab.galaxyppglogger.ui.AbstractViewModel
import kaist.iclab.galaxyppglogger.ui.RealViewModelImpl
import org.koin.android.ext.koin.androidApplication
import org.koin.android.ext.koin.androidContext
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.core.module.dsl.singleOf
import org.koin.dsl.module

val koinModule = module {
    single {
        Room.databaseBuilder(
            androidContext(),
            RoomDB::class.java,
            "RoomDB"
        )
        .fallbackToDestructiveMigration(false)
        .build()
    }

    single {
        get<RoomDB>().ppgDao()
    }

    singleOf(::HealthTrackerService)
    singleOf(::PPGCollector)

    single {
        CollectorController(
            collectors = listOf(
                get<PPGCollector>(),
            ),
            androidContext = androidContext()
        )
    }

    viewModel<AbstractViewModel> {
        RealViewModelImpl(androidApplication(), get(), get())
    }
}
