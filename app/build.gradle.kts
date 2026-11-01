plugins { id("com.android.application") }
android {
    namespace = "asia.aaii.myanmartipitaka"
    compileSdk = 35
    defaultConfig {
        applicationId = "asia.aaii.myanmartipitaka"
        minSdk = 24
        targetSdk = 35
        versionCode = 51
        versionName = "2.3.5.8"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
