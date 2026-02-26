plugins {
   alias(libs.plugins.customAndroidApplication)
}

dependencies {
    //  Include Samsung Health Sensor SDK
    implementation(fileTree("libs"))

    // Wear Compose
    implementation(libs.bundles.compose.wear)

    implementation("androidx.wear:wear-ongoing:1.1.0")
    implementation("androidx.wear:wear:1.3.0")
}
