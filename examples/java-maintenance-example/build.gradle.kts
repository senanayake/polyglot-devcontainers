import com.github.benmanes.gradle.versions.updates.DependencyUpdatesTask

plugins {
    java
    id("com.diffplug.spotless") version "8.0.0"
    id("com.github.spotbugs") version "6.4.4"
    id("com.github.ben-manes.versions") version "0.53.0"
    id("se.patrikerdes.use-latest-versions") version "0.2.19"
}

group = "dev.polyglot.examples"
version = "0.1.0"

repositories {
    mavenCentral()
}

dependencyLocking {
    lockAllConfigurations()
}

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

dependencies {
    implementation("com.fasterxml.jackson.core:jackson-databind:2.17.2")
    implementation("org.apache.commons:commons-lang3:3.14.0")
    implementation("org.slf4j:slf4j-simple:2.0.16")

    testImplementation(platform("org.junit:junit-bom:5.13.2"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")

    spotbugsPlugins("com.h3xstream.findsecbugs:findsecbugs-plugin:1.14.0")
}

tasks.test {
    useJUnitPlatform()
}

spotless {
    java {
        googleJavaFormat("1.25.2")
    }
}

spotbugs {
    showProgress.set(true)
    effort.set(com.github.spotbugs.snom.Effort.MAX)
    reportLevel.set(com.github.spotbugs.snom.Confidence.LOW)
}

fun isNonStable(version: String): Boolean {
    val stableKeyword = listOf("RELEASE", "FINAL", "GA").any { version.uppercase().contains(it) }
    val regex = "^[0-9,.v-]+(-r)?$".toRegex()
    return !stableKeyword && !regex.matches(version)
}

tasks.named<DependencyUpdatesTask>("dependencyUpdates").configure {
    checkForGradleUpdate = false
    outputFormatter = "json"
    outputDir = ".artifacts/scans"
    reportfileName = "gradle-dependency-updates"
    revision = "release"
    rejectVersionIf {
        isNonStable(candidate.version) && !isNonStable(currentVersion)
    }
}
