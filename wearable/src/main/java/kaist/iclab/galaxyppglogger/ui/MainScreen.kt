package kaist.iclab.galaxyppglogger.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.wear.compose.material.Button
import androidx.wear.compose.material.Icon
import androidx.wear.compose.material.Text
import org.koin.androidx.compose.koinViewModel

@Composable
fun MainScreen(
    viewModel: AbstractViewModel = koinViewModel()
) {
    val serviceState = viewModel.serviceState.collectAsState().value

    LaunchedEffect(Unit) {
        viewModel.bindService()
    }

    DisposableEffect(Unit) {
        onDispose {
            viewModel.unbindService()
        }
    }

    val scale = androidx.compose.ui.platform.LocalConfiguration.current
        .screenWidthDp / 360f

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding((12 * scale).dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        when (serviceState) {
            ServiceState.DISCONNECTED -> {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                    modifier = Modifier.size((72 * scale).dp)
                ) {
                    CircularProgressIndicator(modifier = Modifier.size((36 * scale).dp))
                    Spacer(modifier = Modifier.height((3 * scale).dp))
                    Text("Connecting Service...", style = MaterialTheme.typography.bodySmall)
                }
            }

            ServiceState.READY, ServiceState.RUNNING -> {
                FilledIconButton(
                    onClick = {
                        if (serviceState == ServiceState.READY) viewModel.start() else viewModel.stop()
                    },
                    modifier = Modifier.size((96 * scale).dp)
                ) {
                    Icon(
                        imageVector = if (serviceState == ServiceState.RUNNING) Icons.Filled.Pause else Icons.Filled.PlayArrow,
                        contentDescription = if (serviceState == ServiceState.RUNNING) "Pause" else "Start",
                        modifier = Modifier.fillMaxSize(0.6f)
                    )
                }
            }
        }
        Spacer(modifier = Modifier.height((10 * scale).dp))

        Button(
            onClick = { viewModel.flush() },
            modifier = Modifier.height((48 * scale).dp)
        ) {
            Text("Flush")
        }
    }
}
