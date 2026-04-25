import com.github.benmanes.gradle.versions.updates.DependencyUpdatesTask
import org.gradle.api.plugins.jvm.JvmTestSuite

plugins {
    java
    id("com.diffplug.spotless") version "8.0.0"
    id("com.github.spotbugs") version "6.4.4"
    id("com.github.ben-manes.versions") version "0.53.0"
    id("se.patrikerdes.use-latest-versions") version "0.2.19"
}

group = "dev.polyglot"
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
    spotbugsPlugins("com.h3xstream.findsecbugs:findsecbugs-plugin:1.14.0")
}

testing {
    suites {
        withType(JvmTestSuite::class).configureEach {
            useJUnitJupiter("5.13.4")
            dependencies {
                implementation(platform("org.junit:junit-bom:5.13.4"))
            }
        }

        val test by getting(JvmTestSuite::class) {
            dependencies {
                implementation(project())
            }
        }

        register<JvmTestSuite>("propertyTest") {
            dependencies {
                implementation(project())
                implementation("net.jqwik:jqwik:1.9.3")
            }
            targets {
                all {
                    testTask.configure {
                        shouldRunAfter(test)
                    }
                }
            }
        }

        register<JvmTestSuite>("integrationTest") {
            dependencies {
                implementation(project())
            }
            targets {
                all {
                    testTask.configure {
                        shouldRunAfter(test)
                    }
                }
            }
        }

        register<JvmTestSuite>("acceptanceTest") {
            dependencies {
                implementation(project())
                implementation("io.cucumber:cucumber-java:7.34.3")
                implementation("io.cucumber:cucumber-junit-platform-engine:7.34.3")
                implementation("org.junit.platform:junit-platform-suite")
            }
            targets {
                all {
                    testTask.configure {
                        shouldRunAfter(test)
                    }
                }
            }
        }
    }
}

tasks.named("check") {
    dependsOn(testing.suites.named("propertyTest"))
    dependsOn(testing.suites.named("integrationTest"))
    dependsOn(testing.suites.named("acceptanceTest"))
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
